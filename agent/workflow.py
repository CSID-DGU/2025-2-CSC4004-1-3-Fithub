"""
agent/workflow.py
Modified Monolith Lite Workflow with Backend Ingestion & Context-First Pipeline.
"""
import logging
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    fetch_from_backend_node, # [New] 데이터 수집 (진입점)
    summarize_node,
    build_graph_node,
    embed_code_node,
    fusion_node,
    evaluate_node,
    refine_node,
    analyze_repo_node,       # 문맥 분석 (Context)
    generate_graph_node,     # [New] 그래프 시각화 생성 (Visual)
    synthesize_node,
)
from .edges import check_quality

logger = logging.getLogger(__name__)

def create_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    # 1. 노드 등록
    # [Phase 0] 데이터 수집 (백엔드 연동)
    workflow.add_node("ingest", fetch_from_backend_node)

    # [Phase 1] 병렬 분석
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("build_graph", build_graph_node)
    workflow.add_node("embed_code", embed_code_node)

    # [Phase 2] 융합 및 평가
    workflow.add_node("fusion", fusion_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("refine", refine_node)

    # [Phase 3] 문맥 분석 및 시각화 (순차적)
    workflow.add_node("analyze_repo", analyze_repo_node)     # 태그/레이어 분석
    workflow.add_node("generate_graph", generate_graph_node) # 좌표/색상 계산 (NetworkX)

    # [Phase 4] 종합
    workflow.add_node("synthesize", synthesize_node)

    # 2. 엣지 연결
    # 진입점: 백엔드에서 데이터 가져오기
    workflow.set_entry_point("ingest")

    # Ingest -> 병렬 실행 시작
    workflow.add_edge("ingest", "summarize")
    workflow.add_edge("ingest", "build_graph")
    workflow.add_edge("ingest", "embed_code")

    # 병렬 실행 종료 -> Fusion
    workflow.add_edge("summarize", "fusion")
    workflow.add_edge("build_graph", "fusion")
    workflow.add_edge("embed_code", "fusion")

    # Fusion -> 평가
    workflow.add_edge("fusion", "evaluate")

    # 평가 분기 (Pass or Refine)
    workflow.add_conditional_edges(
        "evaluate",
        check_quality,
        {
            "pass": "analyze_repo", # 통과 시 문맥 분석으로
            "refine": "refine",     # 실패 시 재분석
        }
    )

    # 재분석 루프 (옵션만 조정해서 다시 요약/임베딩)
    workflow.add_edge("refine", "summarize")
    workflow.add_edge("refine", "embed_code")

    # 문맥 분석 -> 그래프 생성 -> 종합 -> 끝
    workflow.add_edge("analyze_repo", "generate_graph")
    workflow.add_edge("generate_graph", "synthesize")
    workflow.add_edge("synthesize", END)

    logger.info("Workflow compiled successfully")
    return workflow.compile() # 바로 컴파일해서 반환

def get_workflow():
    return create_workflow()
