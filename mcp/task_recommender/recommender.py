"""
mcp/task_recommender/recommender.py
Generate actionable tasks based on analysis results.
"""
from typing import Dict, List, Any, Optional
import logging
import os
import json
import random
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
        elif self.provider == "upstage":
            api_key = Config.UPSTAGE_API_KEY
            if api_key and OpenAI:
                self.client = OpenAI(api_key=api_key, base_url=Config.UPSTAGE_BASE_URL)
                self.model_id = Config.MODEL_LLM_UPSTAGE
            else:
                logger.warning("Upstage API Key missing. AI features disabled.")
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
        graph = analysis_results.get("graph") or {}
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
                    # Allow 'General' or 'Project' targets for high-level tasks
                    if rec['target'] not in node_ids and '/' in rec['target']: 
                        logger.warning(f"Filtered out hallucinated file: {rec['target']}")
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
                    # Assume 80 confidence for rule-based tasks (Lower than high-confidence LLM)
                    rec['confidence'] = 80
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

        # 5. Global Strict Filtering (Enforce User Constraint)
        # Allowed: target, reason, priority, type, category, confidence, rank
        allowed_final_keys = {"target", "reason", "priority", "type", "category", "confidence", "rank"}
        sanitized_list = []
        for rec in final_list:
            sanitized = {k: v for k, v in rec.items() if k in allowed_final_keys}
            sanitized_list.append(sanitized)

        return sanitized_list

    def _sort_and_slice(self, recommendations: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Fallback sorting and slicing logic."""
        priority_map = {"High": 0, "Medium": 1, "Low": 2}
        # Sort by Priority then Confidence
        recommendations.sort(key=lambda x: (priority_map.get(x['priority'], 3), -x.get('confidence', 0)))
        
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
            if self.provider == "openai" or self.provider == "upstage":
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
                response = self.client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a helpful software architect."},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_id,
                    max_tokens=200,
                    temperature=0.1
                )
                content = response.choices[0].message.content

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
            
            # If LLM returned fewer, fill from remaining
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
            graph = analysis_results.get("graph") or {}
            context = (analysis_results.get("context") or {}).get("file_metadata", {})
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

                if importance > 50:
                    recommendations.append({
                        "target": node['id'],
                        "reason": f"High importance module (Size: {int(importance)}). Consider reviewing for modularization.",
                        "priority": "Medium",
                        "related_entities": [],
                        "type": "refactor_needed"
                    })

                if complexity > 20:
                    recommendations.append({
                        "target": node['id'],
                        "reason": f"High complexity ({complexity}). Refactoring recommended.",
                        "priority": "High",
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

                if not summary or summary.strip() == "":
                     recommendations.append({
                        "target": node['id'],
                        "reason": "Missing documentation/summary.",
                        "priority": "Low",
                        "related_entities": [],
                        "type": "documentation_needed"
                    })

        except Exception as e:
            logger.error(f"Rule-based recommendation failed: {e}")
        
        return recommendations

    def _recommend_with_llm(self, analysis_results: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Generate semantic task recommendations using LLM (Few-Shot Strategy)."""
        graph = analysis_results.get("graph") or {}
        context = (analysis_results.get("context") or {}).get("file_metadata", {})
        nodes = graph.get("nodes", [])
        
        if not nodes:
            return []

        # 1. Prepare Context (Top 20 important files)
        sorted_nodes = sorted(nodes, key=lambda x: x.get("importance", x.get("size", 0)), reverse=True)
        top_nodes = sorted_nodes[:20]

        file_summaries = []
        for node in top_nodes:
            fid = node['id']
            summary = node.get('summary_text', 'No summary available')
            file_summaries.append(f"- File: {fid}\n  Summary: {summary[:300]}...")

        context_str = "\n".join(file_summaries)

        # 2. Few-Shot Prompt with User's Exact Examples
        prompt = f'''
You are a Senior Technical Lead. Review the code summaries and suggest exactly {limit} critical maintenance tasks.

Output Style Requirement:
- **target**: usage of filename.
- **reason**: Must follow "Type: Description" format.
- **priority**: High, Medium, or Low.
- **type**: refactor, security, feature, fix, docs.
- **category**: Backend, Frontend, AI, DevOps, Database, Common.
- **confidence**: 0-100.

STRICTLY IGNORE ANY OTHER FIELD. OUTPUT MUST NOT CONTAIN ANY ADDITIONAL KEYS.

Reference Examples (Follow this style):
[
  {{
    "target": "backend/src/server.ts",
    "reason": "Security Alert: 'DATABASE_URL' is being logged to the console exposing credentials.",
    "priority": "High",
    "type": "security",
    "category": "Backend",
    "confidence": 98
  }},
  {{
    "target": "agent/nodes.py",
    "reason": "Refactor: 'nodes.py' is becoming a 'God Class'. Split into 'ingestion.py' and 'analysis.py'.",
    "priority": "High",
    "type": "refactor",
    "category": "AI",
    "confidence": 92
  }}
]

Code Context:
{context_str}

Return ONLY a JSON object with a "recommendations" list containing exactly {limit} items:
{{
  "recommendations": [ ... ]
}}
'''
        try:
            if self.provider == "openai" or self.provider == "upstage":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": "You are a specific JSON generator. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                content = response.choices[0].message.content
            else:
                response = self.client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a specific JSON generator. Output only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.model_id,
                    max_tokens=2000,
                    temperature=0.1
                )
                content = response.choices[0].message.content

            clean_json = content.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json.replace("```json", "").replace("```", "")
            
            data = json.loads(clean_json)
            recommendations = data.get("recommendations", [])
            
            # Post-processing to strictly ensure only allowed keys
            allowed_keys = {"target", "reason", "priority", "type", "category", "confidence"}
            cleaned_recs = []
            for rec in recommendations:
                cleaned = {k: v for k, v in rec.items() if k in allowed_keys}
                cleaned_recs.append(cleaned)
                
            return cleaned_recs

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return []

    def _determine_category(self, file_path: str, task_type: Optional[str] = None) -> str:
        """Category logic."""
        lower_path = file_path.lower()
        if any(x in lower_path for x in ["mcp/", "agent/", "models/", "torch", "openai", "ai/", "huggingface"]): return "AI"
        if any(x in lower_path for x in ["docker", "k8s", "kubernetes", "jenkins", ".yml", ".yaml", "ci/cd"]): return "DevOps"
        if any(x in lower_path for x in ["prisma", "sql", "migration", "db/", "database", "entity", "schema"]): return "Database"
        if any(lower_path.endswith(ext) for ext in [".tsx", ".jsx", ".css", ".html", ".scss", ".vue"]): return "Frontend"
        if "frontend" in lower_path or "client" in lower_path or "ui/" in lower_path: return "Frontend"
        if any(lower_path.endswith(ext) for ext in [".py", ".go", ".java", ".rb", ".php", ".cs"]): return "Backend"
        if "backend" in lower_path or "server" in lower_path: return "Backend"
        if any(x in lower_path for x in ["utils", "shared", "config", "common", "lib"]): return "Common"
        return "Common"

def create_recommender(device=None) -> TaskRecommender:
    return TaskRecommender(device=device)
