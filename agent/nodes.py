"""
agent/nodes.py
Node functions for Monolith Lite Mode.
HTTP 요청을 제거하고, 내부 로직을 직접 실행하여 메모리를 절약합니다.
"""
import logging
import time
import networkx as nx
import numpy as np
from typing import Dict, Any, List
from .state import AgentState, log_node_execution
from .config import Config

# Lazy Import를 통해 초기 구동 속도 확보 및 순환 참조 방지
# 실제 실행 시점에 해당 모듈들을 로드합니다.

logger = logging.getLogger(__name__)

# ==================== Service Logic (Bridge to MCPs) ====================

def _service_summarize(repo_path: str) -> List[Dict]:
    """Summarization MCP 호출 (CodeT5+ via HF API)"""
    from mcp.summarization.summarizer import create_summarizer

    # device='cpu'로 설정하지만, 내부적으로는 HF API를 쓰므로 RAM을 안 먹음
    summarizer = create_summarizer(device="cpu")

    # 저장소 분석 (최대 15개 파일 제한으로 속도 조절)
    result = summarizer.summarize_repository(repo_path, max_files=15)

    # 결과가 메타데이터에 있는지, 텍스트에 있는지 확인 후 리스트 반환
    if result.get("metadata", {}).get("file_summaries"):
        return result["metadata"]["file_summaries"]

    return []

def _service_build_graph(repo_path: str) -> Dict[str, Any]:
    """Structural Analysis MCP 호출 (AST Parsing)"""
    from mcp.structural_analysis.analyzer import create_analyzer

    analyzer = create_analyzer(device="cpu")
    result = analyzer.analyze_repository(repo_path)

    return {
        "nodes": result.get("nodes", []),
        "edges": result.get("edges", [])
    }

def _service_embed(summaries: List[Dict]) -> List[Dict]:
    """Semantic Embedding MCP 호출 (GraphCodeBERT via HF API)"""
    from mcp.semantic_embedding.embedder import create_embedder

    embedder = create_embedder(device="cpu")

    # 요약문이 없는 경우 처리
    if not summaries:
        return []

    # 벡터화할 텍스트 추출 (요약 내용 사용)
    snippets = [
        {"id": s["code_id"], "code": s["text"]}
        for s in summaries
    ]

    # 배치 임베딩 실행
    results = embedder.batch_embed(snippets, model_name="graphcodebert")
    return results

# ==================== LangGraph Nodes ====================

async def summarize_node(state: AgentState) -> Dict[str, Any]:
    """코드 요약 노드"""
    start_time = time.time()
    try:
        logger.info("--- Summarize Node (Real) ---")
        repo_path = state.get("repo_path")

        # 실제 로직 호출
        summaries = _service_summarize(repo_path)

        duration = time.time() - start_time
        log_node_execution(state, "summarize", "success", duration)
        return {"initial_summaries": summaries}
    except Exception as e:
        logger.error(f"Summarize failed: {e}")
        return {"initial_summaries": [], "error_message": str(e)}

async def build_graph_node(state: AgentState) -> Dict[str, Any]:
    """구조 분석 노드"""
    start_time = time.time()
    try:
        logger.info("--- Build Graph Node (Real) ---")
        repo_path = state.get("repo_path")

        # 실제 로직 호출
        raw_graph = _service_build_graph(repo_path)

        duration = time.time() - start_time
        log_node_execution(state, "build_graph", "success", duration)
        return {"code_graph_raw": raw_graph}
    except Exception as e:
        logger.error(f"Build graph failed: {e}")
        return {
            "code_graph_raw": {"nodes": [], "edges": []},
            "error_message": str(e)
        }

async def embed_code_node(state: AgentState) -> Dict[str, Any]:
    """임베딩 생성 노드"""
    start_time = time.time()
    try:
        logger.info("--- Embed Code Node (Real) ---")

        summaries = state.get("initial_summaries", [])
        if not summaries:
            logger.warning("No summaries to embed.")
            return {"embeddings": []}

        # 실제 로직 호출
        embeddings = _service_embed(summaries)

        duration = time.time() - start_time
        log_node_execution(state, "embed_code", "success", duration)
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return {"embeddings": [], "error_message": str(e)}

# -------------------- 데이터 융합 및 평가 노드 --------------------

async def fusion_node(state: AgentState) -> Dict[str, Any]:
    """
    [Fusion] 요약 + 구조 + 임베딩을 하나의 데이터 패키지로 결합
    """
    from agent.fusion import fuse_data  # 융합 로직 모듈 (별도 파일 권장)

    start_time = time.time()
    logger.info("--- Fusion Node ---")

    try:
        summaries = state.get("initial_summaries", [])
        embeddings = state.get("embeddings", [])
        raw_graph = state.get("code_graph_raw", {})

        # 데이터 융합 수행
        fused_package = fuse_data(summaries, embeddings, raw_graph.get("edges", []))

        duration = time.time() - start_time
        log_node_execution(state, "fusion", "success", duration)

        return {"fused_data_package": fused_package}

    except Exception as e:
        logger.error(f"Fusion failed: {e}")
        # 실패 시 빈 패키지 반환
        return {
            "fused_data_package": {"nodes": [], "edges": [], "metadata": {}},
            "error_message": str(e)
        }

async def evaluate_node(state: AgentState) -> Dict[str, Any]:
    """[Quality Gate] 데이터 일관성 평가"""
    start_time = time.time()
    try:
        fused_data = state.get("fused_data_package", {})
        nodes = fused_data.get("nodes", [])

        if not nodes:
            return {"metrics": {"score": 0.0}}

        # 간단한 품질 평가: 요약문 길이 및 벡터 존재 여부 확인
        valid_nodes = sum(1 for n in nodes if len(n.get("summary_text", "")) > 10 and n.get("embedding"))
        score = valid_nodes / len(nodes) if len(nodes) > 0 else 0.0

        metrics = {"consistency_score": score, "total_nodes": len(nodes)}

        log_node_execution(state, "evaluate", "success", time.time() - start_time)
        return {"metrics": metrics}

    except Exception as e:
        return {"metrics": {"score": 0.0}, "error_message": str(e)}

async def refine_node(state: AgentState) -> Dict[str, Any]:
    """재분석 파라미터 조정"""
    retry_count = state.get("retry_count", 0) + 1
    logger.warning(f"Refining Analysis... Attempt {retry_count}")
    return {"retry_count": retry_count}

def _service_analyze_repo(fused_data: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
    """Repository Analysis MCP 호출 (도메인 태깅, 계층 분류, 논리적 엣지)"""
    from mcp.repository_analysis.analyzer import RepositoryAnalyzer

    analyzer = RepositoryAnalyzer(device="cpu")
    context_metadata = analyzer.analyze(fused_data)

    return context_metadata


def _service_recommend_tasks(fused_data: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Task Recommender MCP 호출 (개선 작업 추천)"""
    from mcp.task_recommender.recommender import TaskRecommender

    recommender = TaskRecommender(device="cpu")

    # Task Recommender에 넘길 입력 형식
    analysis_results = {
        "graph": fused_data,
        "context": context,
        "metrics": {}
    }

    recommendations = recommender.recommend(analysis_results)
    return recommendations


async def analyze_repo_node(state: AgentState) -> Dict[str, Any]:
    """[Repo Analysis] 문맥 메타데이터 생성 (도메인 태깅, 계층 분류)"""
    start_time = time.time()
    try:
        logger.info("--- Analyze Repo Node ---")

        fused_data = state.get("fused_data_package", {})
        repo_path = state.get("repo_path", "")

        # 실제 Repository Analysis 로직 호출
        context_metadata = _service_analyze_repo(fused_data, repo_path)

        # 추천 작업 생성
        recommendations = _service_recommend_tasks(fused_data, context_metadata)

        duration = time.time() - start_time
        log_node_execution(state, "analyze_repo", "success", duration)

        return {
            "context_metadata": context_metadata,
            "recommendations": recommendations
        }

    except Exception as e:
        logger.error(f"Repo analysis failed: {e}")
        return {
            "context_metadata": {"file_metadata": {}, "logical_edges": []},
            "recommendations": [],
            "error_message": str(e)
        }


async def synthesize_node(state: AgentState) -> Dict[str, Any]:
    """
    [Synthesis] 모든 분석 결과를 종합하여 최종 아티팩트 생성

    Returns:
        - final_artifact: 사용자에게 반환할 최종 결과물
    """
    start_time = time.time()
    try:
        logger.info("--- Synthesize Node ---")

        # 상태에서 각 부분 추출
        fused_data = state.get("fused_data_package", {})
        context_metadata = state.get("context_metadata", {})
        recommendations = state.get("recommendations", [])
        metrics = state.get("metrics", {})

        # 최종 그래프 구성 (Fused Data + Context Metadata)
        final_graph_json = {
            "nodes": fused_data.get("nodes", []),
            "edges": fused_data.get("edges", []),
            "metadata": context_metadata
        }

        # 최종 요약
        summaries = state.get("initial_summaries", [])
        embeddings = state.get("embeddings", [])

        # 최종 결과물
        final_artifact = {
            "graph": final_graph_json,
            "summaries": summaries,
            "embeddings": embeddings,
            "metrics": metrics,
            "recommendations": recommendations[:10],  # 상위 10개 추천
            "context": context_metadata
        }

        duration = time.time() - start_time
        log_node_execution(state, "synthesize", "success", duration)

        logger.info(f"Synthesis complete. Generated artifact with {len(final_graph_json['nodes'])} nodes.")

        return {
            "final_artifact": final_artifact,
            "status": "completed"
        }

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return {
            "final_artifact": {},
            "status": "failed",
            "error_message": str(e)
        }
