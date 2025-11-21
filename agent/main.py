"""FastAPI server for Agent Service (LangGraph)."""
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
import httpx

from .state import create_initial_state, AgentState
from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AsyncResponse,
    ResultResponse,
    HealthResponse,
    AgentArtifact,
    CodeGraph,
    Metrics,
)
from .config import Config
from .workflow import get_workflow
from shared.git_utils import clone_repository, load_local_repository, cleanup_repository

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Code Analysis Agent Service",
    description="LangGraph-based code analysis agent",
    version="1.0.0"
)

# 실행 결과 저장소 (메모리)
execution_store: Dict[str, Dict[str, Any]] = {}


# ==================== Helper Functions ====================

def _prepare_repository(repo_input: Dict[str, Any]) -> str:
    """저장소를 준비합니다 (클론 또는 로드)."""
    source = repo_input.get("source", "git")
    uri = repo_input.get("uri", "")

    try:
        if source == "git":
            # Git 클론
            repo_path = clone_repository(
                uri,
                target_dir=None,
                branch=repo_input.get("branch", "main")
            )
            return repo_path

        elif source == "local":
            # 로컬 경로 로드
            repo_path = load_local_repository(uri)
            return repo_path

        elif source == "zip":
            # ZIP 파일 처리 (미구현)
            raise NotImplementedError("ZIP source not yet implemented")

        else:
            raise ValueError(f"Unknown source: {source}")

    except Exception as e:
        logger.error(f"Failed to prepare repository: {e}")
        raise


async def _run_analysis(run_id: str, state: AgentState) -> None:
    """분석을 비동기로 실행합니다."""
    try:
        # 실행 상태 업데이트
        execution_store[run_id]["status"] = "processing"

        # 워크플로우 실행
        workflow = get_workflow()
        logger.info(f"Starting workflow execution for {run_id}")

        # 비동기 워크플로우 실행 (실제로는 invoke를 사용)
        final_state = workflow.invoke(state)

        # 결과 저장
        execution_store[run_id]["result"] = final_state
        execution_store[run_id]["status"] = "completed"
        execution_store[run_id]["updated_at"] = datetime.utcnow()
        execution_store[run_id]["progress"] = 100

        logger.info(f"Workflow completed for {run_id}")

    except Exception as e:
        logger.error(f"Workflow execution failed for {run_id}: {e}")
        execution_store[run_id]["status"] = "failed"
        execution_store[run_id]["error"] = str(e)
        execution_store[run_id]["updated_at"] = datetime.utcnow()


# ==================== Health Check ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크."""
    try:
        # MCP 서비스들 헬스 체크
        mcp_health = {}
        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, url in Config.health_check_urls().items():
                try:
                    response = await client.get(url)
                    mcp_health[name] = "healthy" if response.status_code == 200 else "unhealthy"
                except:
                    mcp_health[name] = "unreachable"

        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0"
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/mcp-status")
async def mcp_status():
    """모든 MCP 서비스의 상태를 반환합니다."""
    mcp_health = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in Config.health_check_urls().items():
            try:
                response = await client.get(url)
                mcp_health[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": url,
                }
            except Exception as e:
                mcp_health[name] = {
                    "status": "unreachable",
                    "url": url,
                    "error": str(e),
                }

    return mcp_health


# ==================== Analysis Endpoints ====================

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_sync(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    동기적으로 저장소를 분석합니다.

    Args:
        request: 분석 요청

    Returns:
        분석 결과
    """
    run_id = str(uuid.uuid4())
    repo_path = None

    try:
        logger.info(f"Starting synchronous analysis: {run_id}")

        # 저장소 준비
        repo_path = _prepare_repository(request.repo.model_dump())

        # 초기 상태 생성
        initial_state = create_initial_state(
            run_id=run_id,
            repo_input=request.repo.model_dump(),
            repo_path=repo_path,
            thresholds=request.thresholds.model_dump(),
            options=request.options,
            top_k=request.top_k,
        )

        # 워크플로우 실행
        workflow = get_workflow()
        final_state = workflow.invoke(initial_state)

        # 응답 생성
        artifact = AgentArtifact(
            graph=CodeGraph(
                nodes=final_state.get("code_graph", {}).get("nodes", []),
                edges=final_state.get("code_graph", {}).get("edges", []),
            ),
            summaries=final_state.get("final_summaries", []),
            embeddings=final_state.get("embeddings", []),
            metrics=Metrics(**final_state.get("metrics", {})),
            recommendations=final_state.get("recommendations", []),
            repository_info=final_state.get("repository_info", {}),
        )

        execution_time = final_state.get("end_time", 0) - final_state.get("start_time", 0)

        return AnalyzeResponse(
            run_id=run_id,
            status="completed",
            artifact=artifact,
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Synchronous analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 저장소 정리
        if repo_path:
            try:
                cleanup_repository(repo_path)
            except:
                pass


@app.post("/analyze-async", response_model=AsyncResponse)
async def analyze_async(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> AsyncResponse:
    """
    비동기적으로 저장소를 분석합니다.

    Args:
        request: 분석 요청
        background_tasks: 백그라운드 작업

    Returns:
        실행 ID와 초기 상태
    """
    run_id = str(uuid.uuid4())
    repo_path = None

    try:
        logger.info(f"Starting asynchronous analysis: {run_id}")

        # 저장소 준비
        repo_path = _prepare_repository(request.repo.model_dump())

        # 초기 상태 생성
        initial_state = create_initial_state(
            run_id=run_id,
            repo_input=request.repo.model_dump(),
            repo_path=repo_path,
            thresholds=request.thresholds.model_dump(),
            options=request.options,
            top_k=request.top_k,
        )

        # 실행 정보 저장
        execution_store[run_id] = {
            "status": "queued",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "progress": 0,
            "repo_path": repo_path,
        }

        # 백그라운드에서 실행
        background_tasks.add_task(_run_analysis, run_id, initial_state)

        return AsyncResponse(
            run_id=run_id,
            status="queued",
            message=f"Analysis queued with run_id: {run_id}",
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Asynchronous analysis queueing failed: {e}")
        # 저장소 정리
        if repo_path:
            try:
                cleanup_repository(repo_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/result/{run_id}", response_model=ResultResponse)
async def get_result(run_id: str) -> ResultResponse:
    """
    실행 결과를 조회합니다.

    Args:
        run_id: 실행 ID

    Returns:
        실행 결과
    """
    if run_id not in execution_store:
        raise HTTPException(status_code=404, detail=f"Run ID not found: {run_id}")

    execution_info = execution_store[run_id]

    if execution_info["status"] == "completed":
        final_state = execution_info.get("result", {})

        artifact = AgentArtifact(
            graph=CodeGraph(
                nodes=final_state.get("code_graph", {}).get("nodes", []),
                edges=final_state.get("code_graph", {}).get("edges", []),
            ),
            summaries=final_state.get("final_summaries", []),
            embeddings=final_state.get("embeddings", []),
            metrics=Metrics(**final_state.get("metrics", {})),
            recommendations=final_state.get("recommendations", []),
            repository_info=final_state.get("repository_info", {}),
        )

        execution_time = final_state.get("end_time", 0) - final_state.get("start_time", 0)

        result = AnalyzeResponse(
            run_id=run_id,
            status="completed",
            artifact=artifact,
            execution_time=execution_time,
        )

        return ResultResponse(
            run_id=run_id,
            status="completed",
            progress=100,
            result=result,
            created_at=execution_info["created_at"],
            updated_at=execution_info["updated_at"],
        )

    else:
        return ResultResponse(
            run_id=run_id,
            status=execution_info.get("status", "unknown"),
            progress=execution_info.get("progress", 0),
            error=execution_info.get("error"),
            created_at=execution_info.get("created_at", datetime.utcnow()),
            updated_at=execution_info.get("updated_at", datetime.utcnow()),
        )


# ==================== Report Endpoint ====================

@app.get("/report/{run_id}", response_class=HTMLResponse)
async def get_report(run_id: str):
    """
    분석 결과 리포트를 HTML 형식으로 반환합니다.

    Args:
        run_id: 실행 ID

    Returns:
        HTML 리포트
    """
    if run_id not in execution_store:
        raise HTTPException(status_code=404, detail=f"Run ID not found: {run_id}")

    execution_info = execution_store[run_id]

    if execution_info["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Status: {execution_info['status']}"
        )

    final_state = execution_info.get("result", {})

    # 간단한 HTML 리포트 생성
    html = f"""
    <html>
    <head>
        <title>Code Analysis Report - {run_id}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
            .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
            .metric-label {{ color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>Code Analysis Report</h1>
        <p><strong>Run ID:</strong> {run_id}</p>
        <p><strong>Repository:</strong> {final_state.get('repository_info', {}).get('repository', 'N/A')}</p>

        <h2>Metrics</h2>
        <div class="metric">
            <div class="metric-value">{final_state.get('metrics', {}).get('codebleu', 0):.2f}</div>
            <div class="metric-label">CodeBLEU</div>
        </div>
        <div class="metric">
            <div class="metric-value">{final_state.get('metrics', {}).get('rougeL', 0):.2f}</div>
            <div class="metric-label">ROUGE-L</div>
        </div>
        <div class="metric">
            <div class="metric-value">{final_state.get('metrics', {}).get('edge_f1', 0):.2f}</div>
            <div class="metric-label">Edge F1</div>
        </div>

        <h2>Summary</h2>
        <p>{final_state.get('repository_info', {}).get('overview', 'N/A')}</p>

        <h2>Files Analyzed</h2>
        <ul>
            {f''.join(f'<li>{s.get("target_id", "N/A")}</li>' for s in final_state.get('final_summaries', [])[:5])}
        </ul>

        <h2>Recommendations</h2>
        <ol>
            {f''.join(f'<li><strong>{r.get("target", "N/A")}</strong> ({r.get("priority", "N/A")}): {r.get("reason", "N/A")}</li>' for r in final_state.get('recommendations', [])[:5])}
        </ol>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        workers=1,  # LangGraph는 단일 워커에서 실행
        log_level="info"
    )
