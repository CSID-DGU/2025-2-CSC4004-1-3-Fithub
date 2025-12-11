"""
agent/edges.py
Conditional Logic.
"""
from typing import Literal
from .state import AgentState
from .router import create_router

def check_quality(state: AgentState) -> Literal["pass", "refine"]:
    """
    Reads the decision already made by the Orchestrator node.
    Enforces MAX_RETRIES to prevent infinite loops.
    """
    from .config import Config
    decision = state.get("decision", "pass")
    retry_count = state.get("retry_count", 0)

    if decision == "refine" and retry_count >= Config.MAX_RETRIES:
        return "pass"
        
    return decision
