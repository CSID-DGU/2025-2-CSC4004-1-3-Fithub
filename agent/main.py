"""
agent/main.py
FastAPI Entry point for the Agent Service.
"""
import logging
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, BackgroundTasks, HTTPException

from .state import AgentState
from .schemas import AnalyzeRequest, AnalyzeResponse, ResultResponse
from .workflow import get_workflow
from .config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fithub Agent Service")

# CORS Settings
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for now (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    import os
    if os.getenv("LANGCHAIN_TRACING_V2") == "true":
        logger.info("🛠️ LangSmith Tracing is ENABLED.")
    else:
        logger.info("LangSmith Tracing is DISABLED.")

# 실행 결과 저장소 (In-Memory Database Substitute)
# 실제 프로덕션에서는 Redis나 DB를 사용해야 합니다.
execution_store: Dict[str, Dict[str, Any]] = {}

async def _run_analysis(run_id: str, initial_state: AgentState):
    """
    백그라운드에서 LangGraph 워크플로우를 실행합니다.
    """
    try:
        logger.info(f"[{run_id}] Starting workflow execution.")
        execution_store[run_id]["status"] = "processing"

        # 워크플로우 컴파일 및 실행
        workflow = get_workflow()

        # LangGraph 비동기 실행 (ainvoke)
        final_state = await workflow.ainvoke(initial_state)

        logger.info(f"[{run_id}] Workflow completed successfully.")

        # 결과 업데이트
        execution_store[run_id].update({
            "status": "completed",
            "result": final_state.get("final_artifact"),
            "updated_at": datetime.utcnow(),
            "progress": 100
        })

        # 임시 파일 정리 (Clean up)
        repo_path = final_state.get("repo_path")
        if repo_path and Path(repo_path).exists():
            try:
                shutil.rmtree(repo_path)
                logger.info(f"[{run_id}] Cleaned up temp directory: {repo_path}")
            except Exception as e:
                logger.warning(f"[{run_id}] Failed to clean up temp dir: {e}")

    except Exception as e:
        logger.error(f"[{run_id}] Workflow failed: {e}", exc_info=True)
        execution_store[run_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.utcnow()
        })

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, bg_tasks: BackgroundTasks):
    """
    분석 요청을 받아 백그라운드 작업을 시작합니다.
    """
    run_id = str(uuid.uuid4())

    # 초기 상태 생성 (TypedDict 구조 준수)
    # repo_path는 workflow 내부의 ingest 노드에서 결정되므로 여기서는 비워둡니다.
    initial_state: AgentState = {
        "run_id": run_id,
        "repo_input": request.repo.model_dump(),
        "options": request.options,
        "thresholds": request.thresholds.model_dump() if hasattr(request.thresholds, 'model_dump') else {},
        "retry_count": 0,
        "initial_summaries": [],
        "embeddings": [],
        "code_graph_raw": {},
        "fused_data_package": {},
        "context_metadata": {},
        "final_graph_json": {},
        "metrics": {},
        "recommendations": [],
        "node_execution_log": []
    }

    # 실행 스토어 초기화
    execution_store[run_id] = {
        "status": "queued",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "progress": 0
    }

    # 백그라운드 작업 추가
    bg_tasks.add_task(_run_analysis, run_id, initial_state)

    return AnalyzeResponse(run_id=run_id, status="queued")

@app.get("/result/{run_id}", response_model=ResultResponse)
async def get_result(run_id: str):
    """
    실행 결과를 조회합니다.
    """
    if run_id not in execution_store:
        raise HTTPException(status_code=404, detail="Run ID not found")

    info = execution_store[run_id]

    return ResultResponse(
        run_id=run_id,
        status=info["status"],
        result=info.get("result"),
        error=info.get("error"),
        created_at=info.get("created_at"),
        updated_at=info.get("updated_at")
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
