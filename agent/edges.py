"""Conditional edges for LangGraph workflow."""
import logging
from typing import Literal
from .state import AgentState

logger = logging.getLogger(__name__)


def check_quality(state: AgentState) -> Literal["synthesize", "refine"]:
    """
    품질 평가 결과에 따라 다음 노드를 결정합니다.

    Args:
        state: 현재 상태

    Returns:
        다음 노드명 ("synthesize" 또는 "refine")
    """
    try:
        metrics = state.get("metrics", {})
        thresholds = state.get("thresholds", {})
        retry_count = state.get("retry_count", 0)
        retry_max = thresholds.get("retry_max", 2)

        # 최대 재시도 도달
        if retry_count >= retry_max:
            logger.info("Max retries reached. Moving to synthesis.")
            return "synthesize"

        # 임계값 확인
        codebleu = metrics.get("codebleu", 0.0)
        codebleu_min = thresholds.get("codebleu_min", 0.42)

        rougeL = metrics.get("rougeL", 0.0)
        rougeL_min = thresholds.get("rougeL_min", 0.30)

        # 모든 조건 충족
        if codebleu >= codebleu_min and rougeL >= rougeL_min:
            logger.info("Quality metrics satisfied. Moving to synthesis.")
            return "synthesize"
        else:
            logger.info(
                f"Quality metrics not satisfied. "
                f"CodeBLEU: {codebleu:.3f} (min: {codebleu_min}), "
                f"ROUGE-L: {rougeL:.3f} (min: {rougeL_min}). "
                f"Refining (attempt {retry_count + 1})."
            )
            return "refine"

    except Exception as e:
        logger.error(f"Error in check_quality: {e}")
        # 에러 시 synthesis로 진행
        return "synthesize"
