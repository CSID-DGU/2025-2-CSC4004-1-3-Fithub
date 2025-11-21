"""LangGraph workflow definition."""
import logging
import asyncio
from langgraph.graph import StateGraph, END
from .state import AgentState, create_initial_state
from .nodes import (
    summarize_node,
    build_graph_node,
    embed_code_node,
    analyze_repo_node,
    evaluate_node,
    refine_node,
    synthesize_node,
)
from .edges import check_quality

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """
    LangGraph 워크플로우를 생성합니다.

    Returns:
        컴파일된 워크플로우 그래프
    """
    # 1. 상태 그래프 생성
    workflow = StateGraph(AgentState)

    # 2. 노드 추가
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("build_graph", build_graph_node)
    workflow.add_node("embed_code", embed_code_node)
    workflow.add_node("analyze_repo", analyze_repo_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("refine", refine_node)
    workflow.add_node("synthesize", synthesize_node)

    # 3. 병렬 진입점 설정
    # 초기 분석 노드들을 병렬로 실행하기 위해서는 진입 함수 필요
    def _entry(state: AgentState):
        """진입점: 상태 반환"""
        return state

    workflow.add_node("__start__", _entry)

    # 4. 엣지 연결
    # 진입점 -> 병렬 분석 노드들
    workflow.add_edge("__start__", "summarize")
    workflow.add_edge("__start__", "build_graph")
    workflow.add_edge("__start__", "embed_code")
    workflow.add_edge("__start__", "analyze_repo")

    # 병렬 노드들 -> 평가 노드 (암묵적으로 병렬 처리됨)
    workflow.add_edge("summarize", "evaluate")
    workflow.add_edge("build_graph", "evaluate")
    workflow.add_edge("embed_code", "evaluate")
    workflow.add_edge("analyze_repo", "evaluate")

    # 5. 조건부 엣지: 평가 후 분기
    workflow.add_conditional_edges(
        "evaluate",
        check_quality,
        {
            "synthesize": "synthesize",
            "refine": "refine",
        }
    )

    # 개선 -> 평가 (루프)
    workflow.add_edge("refine", "evaluate")

    # 종합 -> 끝
    workflow.add_edge("synthesize", END)

    # 6. 진입점 설정
    workflow.set_entry_point("__start__")

    logger.info("Workflow graph created successfully")
    return workflow


def compile_workflow() -> object:
    """
    워크플로우를 컴파일합니다.

    Returns:
        컴파일된 워크플로우 실행기
    """
    workflow = create_workflow()
    app = workflow.compile()
    logger.info("Workflow compiled successfully")
    return app


# 글로벌 워크플로우 앱
_workflow_app = None


def get_workflow():
    """글로벌 워크플로우 앱을 가져옵니다."""
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = compile_workflow()
    return _workflow_app
