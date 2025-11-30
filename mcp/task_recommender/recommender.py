"""
mcp/task_recommender/recommender.py
Generate actionable tasks based on analysis results.
"""
from typing import Dict, List, Any, Optional
import logging
import os
import json
from huggingface_hub import InferenceClient
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from agent.config import Config

logger = logging.getLogger(__name__)

class TaskRecommender:
    def __init__(self, device=None):
        self.provider = Config.LLM_PROVIDER
        self.client = None
        self.model_id = None
        
        if self.provider == "openai":
            api_key = Config.OPENAI_API_KEY
            if api_key and OpenAI:
                self.client = OpenAI(api_key=api_key)
                self.model_id = Config.MODEL_LLM_OPENAI
            else:
                logger.warning("OpenAI API Key missing. AI features disabled.")
        else:
            token = Config.HF_API_KEY
            if token:
                self.client = InferenceClient(token=token)
                self.model_id = Config.MODEL_LLM
            else:
                logger.warning("HF_API_KEY missing. AI features disabled.")

    def recommend_tasks(self, analysis_results: Dict[str, Any], top_k: int = 10, selected_labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate task recommendations based on analysis results (AI-First Strategy).
        1. Request 20 tasks from AI (including Category).
        2. Fill with Rule-based recommendations if AI fails or returns fewer than 20.
        3. Select Top-K using LLM Filtering.
        """
        candidates = []
        target_pool_size = 20
        
        # Node IDs for Grounding Check
        graph = analysis_results.get("graph", {})
        nodes = graph.get("nodes", [])
        node_ids = {n['id'] for n in nodes}

        # 1. AI-based Recommendations (Priority)
        if self.client:
            try:
                # Request tasks from AI
                ai_recommendations = self._recommend_with_llm(analysis_results, limit=target_pool_size)
                
                # Reliability Check (Grounding & Confidence)
                for rec in ai_recommendations:
                    # Grounding Check: Exclude non-existent files
                    if rec['target'] not in node_ids:
                        logger.warning(f"Filtered out hallucinated file: {rec['target']}")
                        continue
                    
                    # Confidence Check: Exclude tasks with confidence < 70
                    confidence = rec.get('confidence', 0)
                    if confidence < 70:
                        logger.warning(f"Filtered out low confidence task ({confidence}): {rec['target']}")
                        continue
                        
                    candidates.append(rec)

            except Exception as e:
                logger.error(f"AI recommendation failed: {e}")

        # 2. Rule-based Recommendations (Fallback / Fill)
        # Fill with Rule-based if AI recommendations are insufficient
        if len(candidates) < target_pool_size:
            needed = target_pool_size - len(candidates)
            rule_recommendations = self._get_rule_based_recommendations(analysis_results)
            
            # Remove duplicates based on target
            existing_targets = {c['target'] for c in candidates}
            
            added_count = 0
            for rec in rule_recommendations:
                if added_count >= needed:
                    break
                if rec['target'] not in existing_targets:
                    # Assign category for rule-based tasks
                    rec['category'] = self._determine_category(rec['target'], rec.get('type'))
                    # Assume 100 confidence for rule-based tasks
                    rec['confidence'] = 100
                    candidates.append(rec)
                    added_count += 1
                    existing_targets.add(rec['target'])

        # 3. Label Filtering (if requested)
        if selected_labels:
            candidates = [c for c in candidates if c.get('category') in selected_labels]

        # 4. LLM Filtering & Ranking
        # Filter with LLM if candidates exceed top_k
        if self.client and len(candidates) > top_k:
            try:
                final_list = self._filter_with_llm(candidates, top_k)
            except Exception as e:
                logger.error(f"LLM filtering failed: {e}. Falling back to sorting.")
                final_list = self._sort_and_slice(candidates, top_k)
        else:
            final_list = self._sort_and_slice(candidates, top_k)

        return final_list

    def _sort_and_slice(self, recommendations: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Fallback sorting and slicing logic."""
        priority_map = {"High": 0, "Medium": 1, "Low": 2}
        recommendations.sort(key=lambda x: (priority_map.get(x['priority'], 3), -x.get('size', 0)))
        
        final_list = []
        for i, rec in enumerate(recommendations[:top_k]):
            rec['rank'] = i + 1
            if 'size' in rec: del rec['size']
            final_list.append(rec)
        return final_list

    def _filter_with_llm(self, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Select the most critical Top-K tasks using LLM."""
        candidate_summary = []
        for i, rec in enumerate(candidates):
            candidate_summary.append({
                "id": i,
                "target": rec['target'],
                "category": rec.get('category', 'Common'),
                "type": rec.get('type', 'unknown'),
                "priority": rec['priority'],
                "confidence": rec.get('confidence', 100),
                "reason": rec['reason']
            })
        
        candidates_str = json.dumps(candidate_summary, indent=2)

        prompt = f"""
You are a Senior Technical Lead.
Select the top {top_k} most critical tasks from the following list.
Prioritize: Security vulnerabilities, Critical architecture violations, and High-impact refactoring.

Candidates:
{candidates_str}

Return ONLY a JSON object with the list of selected IDs:
{{
  "selected_ids": [0, 2, 5, ...]
}}
"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": "You are a helpful software architect."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                content = response.choices[0].message.content
            else:
                response = self.client.text_generation(
                    prompt,
                    model=self.model_id,
                    max_new_tokens=200,
                    temperature=0.1,
                    return_full_text=False
                )
                content = response

            clean_json = content.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json.replace("```json", "").replace("```", "")
            
            data = json.loads(clean_json)
            selected_ids = data.get("selected_ids", [])
            
            final_list = []
            rank = 1
            for idx in selected_ids:
                if 0 <= idx < len(candidates):
                    rec = candidates[idx]
                    rec['rank'] = rank
                    if 'size' in rec: del rec['size']
                    final_list.append(rec)
                    rank += 1
            
            if len(final_list) < top_k:
                remaining = [c for i, c in enumerate(candidates) if i not in selected_ids]
                sorted_remaining = self._sort_and_slice(remaining, top_k - len(final_list))
                for rec in sorted_remaining:
                    rec['rank'] = rank
                    final_list.append(rec)
                    rank += 1
            
            return final_list[:top_k]

        except Exception as e:
            raise e

    def _get_rule_based_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        # ... (Existing logic) ...
        recommendations = []
        try:
            graph = analysis_results.get("graph", {})
            context = analysis_results.get("context", {}).get("file_metadata", {})
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            node_ids = {n['id'] for n in nodes}

            # 1. Architecture Violation Detection
            for edge in edges:
                src = edge['source']
                tgt = edge['target']
                
                if tgt not in node_ids and not tgt.startswith("external"):
                     recommendations.append({
                        "target": src,
                        "reason": f"Dead Link: References missing module '{tgt}'.",
                        "priority": "High",
                        "related_entities": [tgt],
                        "type": "dead_link"
                    })
                     continue

                src_layer = context.get(src, {}).get('layer', 'Unknown')
                tgt_layer = context.get(tgt, {}).get('layer', 'Unknown')

                if src_layer == "RepositoryLayer" and tgt_layer == "PresentationLayer":
                    recommendations.append({
                        "target": src,
                        "reason": f"Architecture Violation: Repository '{src}' depends on Presentation '{tgt}'.",
                        "priority": "High",
                        "related_entities": [tgt],
                        "type": "architecture_violation"
                    })

            # 2. Node-based Analysis
            for node in nodes:
                importance = node.get("size", 10)
                complexity = node.get("complexity", 0)
                summary = node.get("summary_text", "")
                loc = node.get("loc", 10)

                if importance > 50 and complexity > 20:
                    recommendations.append({
                        "target": node['id'],
                        "reason": "High complexity in critical file. Consider splitting.",
                        "priority": "Medium",
                        "related_entities": [],
                        "type": "refactor_needed"
                    })
                
                if "TODO" in summary or "FIXME" in summary:
                     recommendations.append({
                        "target": node['id'],
                        "reason": "Pending task detected (TODO/FIXME).",
                        "priority": "Low",
                        "related_entities": [],
                        "type": "todo_detected"
                    })

                if complexity == 0 and loc < 5:
                     recommendations.append({
                        "target": node['id'],
                        "reason": "Empty or minimal implementation detected.",
                        "priority": "Medium",
                        "related_entities": [],
                        "type": "empty_implementation"
                    })

        except Exception as e:
            logger.error(f"Rule-based recommendation failed: {e}")
        
        return recommendations

    def _recommend_with_llm(self, analysis_results: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
        """Generate semantic task recommendations using LLM (Diversity Strategy)."""
        import random
        graph = analysis_results.get("graph", {})
        context = analysis_results.get("context", {}).get("file_metadata", {})
        nodes = graph.get("nodes", [])

        if not nodes:
            return []

        # Diversity Strategy: 70% Top-Importance + 30% Random
        total_slots = limit
        top_slots = int(total_slots * 0.7)
        random_slots = total_slots - top_slots

        sorted_nodes = sorted(nodes, key=lambda x: x.get("size", 0), reverse=True)
        
        selected_nodes = sorted_nodes[:top_slots]
        remaining_nodes = sorted_nodes[top_slots:]

        if remaining_nodes:
            count = min(len(remaining_nodes), random_slots)
            random_selection = random.sample(remaining_nodes, count)
            selected_nodes.extend(random_selection)
        
        file_summaries = []
        for node in selected_nodes:
            fid = node['id']
            meta = context.get(fid, {})
            summary = node.get('summary_text', 'No summary available')
            layer = meta.get('layer', 'Unknown')
            file_summaries.append(f"- File: {fid}\n  Layer: {layer}\n  Summary: {summary[:200]}...")

        context_str = "\n".join(file_summaries)

        prompt = f"""
You are a Senior Technical Lead reviewing a codebase.
Based on the following file summaries and structure, suggest up to {limit} high-impact maintenance tasks.
Focus on: Refactoring, Security Improvements, Missing Documentation, or Feature Enhancements.

Code Context:
{context_str}

Return ONLY a JSON object with this structure:
{{
  "recommendations": [
    {{
      "target": "filename",
      "reason": "Specific reason why this task is needed based on the summary.",
      "priority": "High/Medium/Low",
      "type": "refactor/security/docs/feature",
      "category": "Frontend/Backend/AI/DevOps/Database/Common",
      "confidence": 85
    }}
  ]
}}
"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": "You are a helpful software architect. Assign a confidence score (0-100) to each recommendation."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                content = response.choices[0].message.content
            else:
                response = self.client.text_generation(
                    prompt,
                    model=self.model_id,
                    max_new_tokens=1000,
                    temperature=0.2,
                    return_full_text=False
                )
                content = response

            clean_json = content.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json.replace("```json", "").replace("```", "")
            
            data = json.loads(clean_json)
            return data.get("recommendations", [])

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return []

    def _determine_category(self, file_path: str, task_type: Optional[str] = None) -> str:
        """파일 경로와 작업 유형을 기반으로 6가지 카테고리 결정."""
        lower_path = file_path.lower()
        
        # 1. AI
        if any(x in lower_path for x in ["mcp/", "agent/", "models/", "torch", "openai", "ai/", "huggingface"]):
            return "AI"
        
        # 2. DevOps
        if any(x in lower_path for x in ["docker", "k8s", "kubernetes", "jenkins", ".yml", ".yaml", "ci/cd", "pipeline"]):
            return "DevOps"
            
        # 3. Database
        if any(x in lower_path for x in ["prisma", "sql", "migration", "db/", "database", "entity", "schema"]):
            return "Database"

        # 4. Frontend
        if any(lower_path.endswith(ext) for ext in [".tsx", ".jsx", ".css", ".html", ".scss", ".vue", ".svelte"]):
            return "Frontend"
        if "frontend" in lower_path or "client" in lower_path or "ui/" in lower_path or "components/" in lower_path:
            return "Frontend"

        # 5. Backend
        if any(lower_path.endswith(ext) for ext in [".py", ".go", ".java", ".rb", ".php", ".cs"]):
            return "Backend"
        if "backend" in lower_path or "server" in lower_path or "api" in lower_path or "controller" in lower_path:
            return "Backend"
        if task_type == "architecture_violation":
            return "Backend"

        # 6. Common (Default)
        if any(x in lower_path for x in ["utils", "shared", "config", "common", "lib"]):
            return "Common"
            
        return "Common"

def create_recommender(device=None) -> TaskRecommender:
    return TaskRecommender(device=device)
