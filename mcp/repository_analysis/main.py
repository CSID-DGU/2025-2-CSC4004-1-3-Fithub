"""FastAPI server for Repository Analysis MCP."""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .analyzer import create_analyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Repository Analysis MCP",
    description="Repository-level analysis service",
    version="1.0.0"
)

# 글로벌 분석기
analyzer = create_analyzer()


# ==================== Request/Response Models ====================

class AnalyzeRequest(BaseModel):
    """분석 요청."""
    repo_path: str


class RepositoryInfo(BaseModel):
    """저장소 정보."""
    path: str
    name: str
    url: Optional[str] = None
    branch: Optional[str] = None
    commit: Optional[str] = None


class Statistics(BaseModel):
    """통계."""
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    functions: int
    classes: int


class Structure(BaseModel):
    """구조."""
    modules: Dict[str, Dict[str, int]]
    main_files: List[str]


class AnalyzeResponse(BaseModel):
    """분석 응답."""
    repository: str
    repository_info: Optional[Dict[str, Any]] = None
    overview: str
    statistics: Statistics
    structure: Structure
    files: List[str]


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """헬스 체크."""
    return {
        "status": "healthy",
        "service": "Repository Analysis MCP",
        "version": "1.0.0"
    }


# ==================== Analysis Endpoints ====================

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    저장소를 분석합니다.

    Args:
        request: 분석 요청

    Returns:
        분석 결과
    """
    try:
        repo_path = Path(request.repo_path)

        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

        result = analyzer.analyze(str(repo_path))

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return AnalyzeResponse(
            repository=result["repository"],
            repository_info=result.get("repository_info"),
            overview=result["overview"],
            statistics=Statistics(**result["statistics"]),
            structure=Structure(**result["structure"]),
            files=result["files"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9004,
        log_level="info"
    )
