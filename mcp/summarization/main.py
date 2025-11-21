"""FastAPI server for Summarization MCP."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio

from .summarizer import create_summarizer
from shared.ast_utils import CodeAnalyzer, analyze_repository

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Summarization MCP",
    description="Code summarization service",
    version="1.0.0"
)

# 글로벌 요약기
summarizer = create_summarizer()


# ==================== Request/Response Models ====================

class SummarizeFileRequest(BaseModel):
    """파일 요약 요청."""
    file_path: str
    model_name: str = "starcoder2"


class SummarizeCodeRequest(BaseModel):
    """코드 요약 요청."""
    code: str
    code_id: str
    level: str  # "function" | "class" | "snippet"
    model_name: str = "codet5"


class SummarizeRepositoryRequest(BaseModel):
    """저장소 요약 요청."""
    repo_path: str
    max_files: int = 10


class SummaryResponse(BaseModel):
    """요약 응답."""
    code_id: str
    level: str
    text: str
    model: str
    confidence: float


class RepositorySummaryResponse(BaseModel):
    """저장소 요약 응답."""
    repository: str
    summaries: List[SummaryResponse]
    statistics: Dict[str, Any]


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """헬스 체크."""
    return {
        "status": "healthy",
        "service": "Summarization MCP",
        "version": "1.0.0"
    }


# ==================== Summarization Endpoints ====================

@app.post("/summarize-file")
async def summarize_file(request: SummarizeFileRequest) -> SummaryResponse:
    """
    파일을 요약합니다.

    Args:
        request: 파일 요약 요청

    Returns:
        요약 결과
    """
    try:
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        result = summarizer.summarize_file(str(file_path), request.model_name)

        return SummaryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing file {request.file_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize-code")
async def summarize_code(request: SummarizeCodeRequest) -> SummaryResponse:
    """
    코드를 요약합니다.

    Args:
        request: 코드 요약 요청

    Returns:
        요약 결과
    """
    try:
        if request.level == "function":
            result = summarizer.summarize_function(
                code=request.code,
                function_name=request.code_id,
                file_path=request.code_id,
                model_name=request.model_name
            )
        elif request.level == "class":
            result = summarizer.summarize_class(
                code=request.code,
                class_name=request.code_id,
                file_path=request.code_id,
                model_name=request.model_name
            )
        else:
            # 기본 스니펫 요약
            summary = summarizer._generate_summary(request.code, request.model_name)
            result = {
                "code_id": request.code_id,
                "level": request.level,
                "text": summary,
                "model": summarizer._get_model_display_name(request.model_name),
                "confidence": 0.80,
            }

        return SummaryResponse(**result)

    except Exception as e:
        logger.error(f"Error summarizing code {request.code_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize-repository")
async def summarize_repository(request: SummarizeRepositoryRequest) -> RepositorySummaryResponse:
    """
    저장소를 요약합니다.

    Args:
        request: 저장소 요약 요청

    Returns:
        저장소 요약 결과
    """
    try:
        repo_path = Path(request.repo_path)

        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

        # 저장소 분석
        analysis = analyze_repository(str(repo_path))

        # 파일별 요약 생성
        summaries = []
        file_count = 0

        for file_rel_path, file_analysis in analysis["files"].items():
            if file_count >= request.max_files:
                break

            full_path = repo_path / file_rel_path
            if full_path.exists():
                summary = summarizer.summarize_file(str(full_path))
                summaries.append(SummaryResponse(**summary))
                file_count += 1

        return RepositorySummaryResponse(
            repository=str(repo_path),
            summaries=summaries,
            statistics=analysis["statistics"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing repository {request.repo_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-summarize")
async def batch_summarize(requests: List[SummarizeCodeRequest]) -> List[SummaryResponse]:
    """
    여러 코드를 한번에 요약합니다.

    Args:
        requests: 요약 요청 목록

    Returns:
        요약 결과 목록
    """
    try:
        results = []

        for request in requests:
            result = await summarize_code(request)
            results.append(result)

        return results

    except Exception as e:
        logger.error(f"Error in batch summarization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9001,
        log_level="info"
    )
