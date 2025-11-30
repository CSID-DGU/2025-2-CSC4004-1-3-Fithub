"""
agent/edges.py
Conditional Logic.
"""
from typing import Literal
from .state import AgentState
from .router import create_router

def check_quality(state: AgentState) -> Literal["pass", "refine"]:
    """
    Delegates the decision to the LLM-based Orchestrator (Router).
    """
    router = create_router()
    return router.route(state)
