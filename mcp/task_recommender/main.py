"""FastAPI server for Task Recommender MCP."""
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .recommender import create_recommender

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Task Recommender MCP",
    description="Task recommendation service",
    version="1.0.0"
)

# 글로벌 추천기
recommender = create_recommender()


# ==================== Request/Response Models ====================

class RecommendationRequest(BaseModel):
    """추천 요청."""
    analysis_results: Dict[str, Any]
    top_k: int = 10


class Recommendation(BaseModel):
    """추천."""
    rank: int
    target: str
    reason: str
    priority: str
    category: str
    related_entities: Optional[List[str]] = None


class RecommendationResponse(BaseModel):
    """추천 응답."""
    recommendations: List[Recommendation]
    total_count: int


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """헬스 체크."""
    return {
        "status": "healthy",
        "service": "Task Recommender MCP",
        "version": "1.0.0"
    }


# ==================== Recommendation Endpoints ====================

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend_tasks(request: RecommendationRequest) -> RecommendationResponse:
    """
    분석 결과에 따라 작업을 추천합니다.

    Args:
        request: 추천 요청

    Returns:
        추천 응답
    """
    try:
        recommendations = recommender.recommend_tasks(
            request.analysis_results,
            request.top_k
        )

        return RecommendationResponse(
            recommendations=[Recommendation(**r) for r in recommendations],
            total_count=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9005,
        log_level="info"
    )
