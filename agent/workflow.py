"""
LangGraph workflow definition for Monolith Lite Architecture.
"""
import logging
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    summarize_node,
    build_graph_node,
    embed_code_node,
    fusion_node,       # [New] 데이터 융합 노드
    evaluate_node,
    refine_node,
    analyze_repo_node, # [Moved] 융합 이후 실행
    synthesize_node,
)
from .edges import check_quality

logger = logging.getLogger(__name__)

def create_workflow() -> StateGraph:
    """
    Monolith Lite 워크플로우 생성
    Flow: Start -> Parallel(3) -> Fusion -> Evaluate -> (Loop/Next) -> Analyze -> End
    """
    # 1. 상태 그래프 생성
    workflow = StateGraph(AgentState)

    # 2. 노드 등록
    # 2.1 병렬 처리 노드 (Input Analysis)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("build_graph", build_graph_node)
    workflow.add_node("embed_code", embed_code_node)

    # 2.2 데이터 융합 (Input Reinforcement)
    workflow.add_node("fusion", fusion_node)

    # 2.3 평가 및 개선 (Quality Gate)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("refine", refine_node)

    # 2.4 심화 분석 및 종합 (Global Analysis)
    workflow.add_node("analyze_repo", analyze_repo_node)
    workflow.add_node("synthesize", synthesize_node)

    # 2.5 진입점 (Dummy Entry)
    workflow.add_node("__start__", lambda state: state)

    # 3. 엣지 연결
    workflow.set_entry_point("__start__")

    # [Parallel] 시작 -> 요약, 구조, 임베딩 동시 실행
    workflow.add_edge("__start__", "summarize")
    workflow.add_edge("__start__", "build_graph")
    workflow.add_edge("__start__", "embed_code")

    # [Sync] 모든 병렬 작업 종료 후 Fusion으로 집결
    workflow.add_edge("summarize", "fusion")
    workflow.add_edge("build_graph", "fusion")
    workflow.add_edge("embed_code", "fusion")

    # Fusion -> 평가
    workflow.add_edge("fusion", "evaluate")

    # [Conditional] 평가 결과에 따른 분기
    workflow.add_conditional_edges(
        "evaluate",
        check_quality,
        {
            "pass": "analyze_repo",  # 통과 시 저장소 전체 분석
            "refine": "refine",      # 실패 시 재분석
        }
    )

    # 재분석 -> 다시 평가 (Evaluate로 돌아가서 개선 여부 확인)
    # (참고: 실제 구현 시 refine 후 다시 summarize 등을 돌리려면 엣지를 그쪽으로 연결해야 함.
    #  여기서는 refine 노드에서 데이터를 수정하고 바로 재평가한다고 가정)
    workflow.add_edge("refine", "evaluate")

    # 전체 분석 -> 종합 -> 종료
    workflow.add_edge("analyze_repo", "synthesize")
    workflow.add_edge("synthesize", END)

    logger.info("Monolith Lite Workflow created successfully")
    return workflow

# 글로벌 인스턴스
_workflow_app = None

def get_workflow():
    global _workflow_app
    if _workflow_app is None:
        workflow = create_workflow()
        _workflow_app = workflow.compile()
    return _workflow_app
