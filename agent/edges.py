"""
agent/edges.py
Conditional Logic.
"""
from typing import Literal
from .state import AgentState

def check_quality(state: AgentState) -> Literal["pass", "refine"]:
    metrics = state.get("metrics", {})
    score = metrics.get("consistency_score", 0.0)
    retry_count = state.get("retry_count", 0)

    # 임계값 0.7 이상이면 통과
    if score >= 0.7:
        return "pass"

    # 재시도는 최대 2번까지만 (무한루프 방지)
    if retry_count >= 2:
        return "pass"

    return "refine"
