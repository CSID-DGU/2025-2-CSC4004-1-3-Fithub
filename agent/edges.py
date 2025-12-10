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
    """
    decision = state.get("decision", "pass")
    return decision # "pass" or "refine"
