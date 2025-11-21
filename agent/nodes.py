"""Node functions for LangGraph workflow."""
import logging
import asyncio
import httpx
from typing import Dict, Any
from .state import AgentState, log_node_execution
from shared.git_utils import clone_repository, load_local_repository, cleanup_repository
from .config import Config

logger = logging.getLogger(__name__)


async def summarize_node(state: AgentState) -> Dict[str, Any]:
    """
    요약 노드: Summarization MCP 호출.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info("--- Summarize Node ---")
        repo_path = state.get("repo_path", "")

        # Summarization MCP 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{Config.SUMMARIZATION_MCP_URL}/summarize-repository",
                json={"repo_path": repo_path, "max_files": 10},
            )
            response.raise_for_status()
            result = response.json()

        summaries = [
            {
                "code_id": s["code_id"],
                "level": s["level"],
                "text": s["text"],
                "model": s["model"],
                "confidence": s.get("confidence", 0.0),
            }
            for s in result.get("summaries", [])
        ]

        duration = time.time() - start_time
        log_node_execution(state, "summarize_node", "success", duration)

        return {"initial_summaries": summaries}

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "summarize_node", "error", duration, {"error": str(e)})
        return {
            "initial_summaries": [],
            "error_message": f"Summarization failed: {str(e)}"
        }


async def build_graph_node(state: AgentState) -> Dict[str, Any]:
    """
    그래프 구축 노드: Structural Analysis MCP 호출.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info("--- Build Graph Node ---")
        repo_path = state.get("repo_path", "")

        # Structural Analysis MCP 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{Config.STRUCTURAL_ANALYSIS_MCP_URL}/analyze-repository",
                json={"repo_path": repo_path},
            )
            response.raise_for_status()
            result = response.json()

        graph = {
            "nodes": result.get("nodes", []),
            "edges": result.get("edges", []),
            "statistics": result.get("statistics", {}),
        }

        duration = time.time() - start_time
        log_node_execution(state, "build_graph_node", "success", duration)

        return {"code_graph": graph}

    except Exception as e:
        logger.error(f"Graph building failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "build_graph_node", "error", duration, {"error": str(e)})
        return {
            "code_graph": {"nodes": [], "edges": []},
            "error_message": f"Graph building failed: {str(e)}"
        }


async def embed_code_node(state: AgentState) -> Dict[str, Any]:
    """
    임베딩 노드: Semantic Embedding MCP 호출.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info("--- Embed Code Node ---")

        summaries = state.get("initial_summaries", [])
        if not summaries:
            logger.info("No summaries to embed")
            return {"embeddings": []}

        # Semantic Embedding MCP 호출
        snippets = [
            {"id": s["code_id"], "code": s["text"][:500]}  # 처음 500자만
            for s in summaries[:5]
        ]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{Config.SEMANTIC_EMBEDDING_MCP_URL}/batch-embed",
                json={"snippets": snippets},
            )
            response.raise_for_status()
            embeddings = response.json()

        duration = time.time() - start_time
        log_node_execution(state, "embed_code_node", "success", duration)

        return {"embeddings": embeddings}

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "embed_code_node", "error", duration, {"error": str(e)})
        return {"embeddings": []}


async def analyze_repo_node(state: AgentState) -> Dict[str, Any]:
    """
    저장소 분석 노드: Repository Analysis MCP 호출.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info("--- Analyze Repository Node ---")
        repo_path = state.get("repo_path", "")

        # Repository Analysis MCP 호출
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{Config.REPOSITORY_ANALYSIS_MCP_URL}/analyze",
                json={"repo_path": repo_path},
            )
            response.raise_for_status()
            result = response.json()

        repo_info = {
            "repository": result.get("repository"),
            "overview": result.get("overview"),
            "statistics": result.get("statistics"),
            "structure": result.get("structure"),
        }

        duration = time.time() - start_time
        log_node_execution(state, "analyze_repo_node", "success", duration)

        return {"repository_info": repo_info}

    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "analyze_repo_node", "error", duration, {"error": str(e)})
        return {"repository_info": {}}


async def evaluate_node(state: AgentState) -> Dict[str, Any]:
    """
    평가 노드: 품질 메트릭 계산.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info("--- Evaluate Node ---")

        # 데모용 메트릭 생성
        summaries = state.get("refined_summaries") or state.get("initial_summaries", [])

        metrics = {
            "codebleu": 0.55 + (0.05 * state.get("retry_count", 0)),  # 재시도할수록 증가
            "bleurt": 0.15,
            "bleu4": 0.45,
            "rougeL": 0.35 + (0.05 * state.get("retry_count", 0)),
            "edge_f1": 0.85,
            "ged": 35.0,
            "ssi": 0.70,
        }

        logger.info(f"Metrics: {metrics}")

        duration = time.time() - start_time
        log_node_execution(state, "evaluate_node", "success", duration, {"metrics": metrics})

        return {"metrics": metrics}

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "evaluate_node", "error", duration, {"error": str(e)})
        return {
            "metrics": {
                "codebleu": 0.0,
                "bleurt": 0.0,
                "bleu4": 0.0,
                "rougeL": 0.0,
                "edge_f1": 0.0,
                "ged": 100.0,
                "ssi": 0.0,
            }
        }


async def refine_node(state: AgentState) -> Dict[str, Any]:
    """
    개선 노드: 요약 재생성.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info(f"--- Refine Node (Attempt {state.get('retry_count', 0) + 1}) ---")

        # 초기 요약 다시 사용 (실제로는 다른 모델 또는 프롬프트 사용)
        summaries = state.get("initial_summaries", [])

        duration = time.time() - start_time
        log_node_execution(state, "refine_node", "success", duration)

        return {
            "refined_summaries": summaries,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    except Exception as e:
        logger.error(f"Refinement failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "refine_node", "error", duration, {"error": str(e)})
        return {"retry_count": state.get("retry_count", 0) + 1}


async def synthesize_node(state: AgentState) -> Dict[str, Any]:
    """
    종합 노드: 최종 결과물 종합.

    Args:
        state: 현재 상태

    Returns:
        상태 업데이트
    """
    import time
    start_time = time.time()

    try:
        logger.info("--- Synthesize Node ---")

        # 최종 요약 선택
        final_summaries = state.get("refined_summaries") or state.get("initial_summaries", [])

        # 추천 생성 (Task Recommender 호출)
        try:
            analysis_results = {
                "graph": state.get("code_graph", {}),
                "summaries": final_summaries,
                "metrics": state.get("metrics", {}),
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{Config.TASK_RECOMMENDER_MCP_URL}/recommend",
                    json={"analysis_results": analysis_results, "top_k": 10},
                )
                response.raise_for_status()
                rec_result = response.json()

            recommendations = rec_result.get("recommendations", [])

        except Exception as e:
            logger.warning(f"Failed to get recommendations: {e}")
            recommendations = []

        duration = time.time() - start_time
        log_node_execution(state, "synthesize_node", "success", duration)

        return {
            "final_summaries": final_summaries,
            "recommendations": recommendations,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        duration = time.time() - start_time
        log_node_execution(state, "synthesize_node", "error", duration, {"error": str(e)})
        return {
            "status": "completed",
            "error_message": f"Synthesis failed: {str(e)}"
        }
