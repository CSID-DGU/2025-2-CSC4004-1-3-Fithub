"""FastAPI server for Semantic Embedding MCP."""
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .embedder import create_embedder

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Semantic Embedding MCP",
    description="Code embedding service",
    version="1.0.0"
)

# 글로벌 임베더
embedder = create_embedder()


# ==================== Request/Response Models ====================

class EmbedRequest(BaseModel):
    """임베딩 요청."""
    code: str
    code_id: str
    model_name: str = "codebert"


class EmbedResponse(BaseModel):
    """임베딩 응답."""
    code_id: str
    embedding: List[float]
    model: str
    dimension: int


class BatchEmbedRequest(BaseModel):
    """배치 임베딩 요청."""
    snippets: List[Dict[str, str]]
    model_name: str = "codebert"


class SimilarityRequest(BaseModel):
    """유사도 요청."""
    embedding1: List[float]
    embedding2: List[float]


class SimilarityResponse(BaseModel):
    """유사도 응답."""
    similarity: float


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """헬스 체크."""
    return {
        "status": "healthy",
        "service": "Semantic Embedding MCP",
        "version": "1.0.0"
    }


# ==================== Embedding Endpoints ====================

@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest) -> EmbedResponse:
    """
    코드를 임베딩합니다.

    Args:
        request: 임베딩 요청

    Returns:
        임베딩 결과
    """
    try:
        result = embedder.embed_code(request.code, request.code_id, request.model_name)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return EmbedResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error embedding code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-embed", response_model=List[EmbedResponse])
async def batch_embed(request: BatchEmbedRequest) -> List[EmbedResponse]:
    """
    여러 코드를 임베딩합니다.

    Args:
        request: 배치 임베딩 요청

    Returns:
        임베딩 결과 목록
    """
    try:
        results = embedder.batch_embed(request.snippets, request.model_name)

        # 에러 제거
        results = [r for r in results if "error" not in r]

        return [EmbedResponse(**r) for r in results]

    except Exception as e:
        logger.error(f"Error in batch embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity", response_model=SimilarityResponse)
async def similarity(request: SimilarityRequest) -> SimilarityResponse:
    """
    두 임베딩의 유사도를 계산합니다.

    Args:
        request: 유사도 요청

    Returns:
        유사도 점수
    """
    try:
        score = embedder.similarity(request.embedding1, request.embedding2)
        return SimilarityResponse(similarity=score)

    except Exception as e:
        logger.error(f"Error computing similarity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9003,
        log_level="info"
    )
