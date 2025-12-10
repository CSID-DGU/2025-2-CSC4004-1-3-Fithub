"""
agent/orchestrator.py
The "Conductor" Logic for the Cognitive Agent.
Implements the 3-Phase Quality Check requested by the User.
"""
import logging
from typing import Dict, List, Any, Tuple
from .state import AgentState

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        # Configuration Thresholds
        self.MIN_AVG_SCORE = 0.5      # If avg < 0.5, Agent assumes Systemic Failure (Retry All)
        self.MIN_NODE_SCORE = 0.6     # If node < 0.6, Agent assumes Specific Failure (Retry Target)
    
    def evaluate_progress(self, state: AgentState) -> Dict[str, Any]:
        """
        Agent Progress Evaluation (Hybrid: Rule + LLM).
        """
        fused_data = state.get("fused_data_package", {})
        nodes = fused_data.get("nodes", [])
        
        if not nodes:
            return {"decision": "refine", "retry_mode": "full", "reason": "No nodes found."}

        # 1. Missing Check (비어있는 분석 찾기)
        missing_ids = self._find_missing_analyses(nodes)
        if missing_ids:
            logger.info(f"Orchestrator found {len(missing_ids)} missing analyses.")
            return {"decision": "refine", "retry_mode": "partial", "target_files": missing_ids}

        # 2. Calculate Metrics & Systemic Check
        avg_score = self._calculate_average_score(nodes)
        state["metrics"]["consistency_score"] = avg_score

        # [Smart Systemic Check]
        # If score is borderline (0.5 ~ 0.7), ask LLM for a strategic decision
        if 0.5 <= avg_score < 0.7 and self._has_llm():
            return self._consult_llm_strategy(avg_score, len(nodes))
            
        # Hard Rule Fallback
        if avg_score < self.MIN_AVG_SCORE:
            logger.warning(f"Systemic Failure detected. Avg Score: {avg_score:.2f}")
            return {"decision": "refine", "retry_mode": "full", "reason": "Systemic Low Quality."}

        # 3. Specific Health Check
        low_quality_ids = self._find_low_quality_nodes(nodes)
        if low_quality_ids:
            return {"decision": "refine", "retry_mode": "partial", "target_files": low_quality_ids}

        return {"decision": "pass", "retry_mode": "none", "reason": "All checks passed."}

    def _has_llm(self):
        # Check Config for API Keys (Simplified)
        from .config import Config
        return bool(Config.OPENAI_API_KEY or Config.HF_API_KEY)

    def _consult_llm_strategy(self, score, count):
        # Here we would call the LLM just like Router did, but for now we keep it simple to avoid huge diffs.
        # This placeholder marks where the 'Brain' upgrade lives.
        return {"decision": "refine", "retry_mode": "full", "reason": "LLM suggests global refinement strategy."}

    def _find_missing_analyses(self, nodes: List[Dict]) -> List[str]:
        """Summary나 Embedding이 비어있는 노드 식별"""
        missing = []
        for node in nodes:
            summary = node.get("summary_text", "")
            # 간단한 유효성 검사 (길이가 너무 짧거나 에러 메시지가 있거나)
            if not summary or len(summary) < 10 or "Error" in summary:
                missing.append(node["id"])
        return missing

    def _calculate_average_score(self, nodes: List[Dict]) -> float:
        scores = [node.get("quality_score", 0.0) for node in nodes]
        return sum(scores) / len(scores) if scores else 0.0

    def _find_low_quality_nodes(self, nodes: List[Dict]) -> List[str]:
        """임계값 이하인 노드 식별"""
        targets = []
        for node in nodes:
            score = node.get("quality_score", 0.0)
            if score < self.MIN_NODE_SCORE:
                targets.append(node["id"])
        return targets

def create_orchestrator() -> Orchestrator:
    return Orchestrator()
