"""FastAPI server for Structural Analysis MCP."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .analyzer import create_analyzer

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Structural Analysis MCP",
    description="Code structure analysis service",
    version="1.0.0"
)

# 글로벌 분석기
analyzer = create_analyzer()


# ==================== Request/Response Models ====================

class Node(BaseModel):
    """그래프 노드."""
    id: str
    type: str
    label: str
    file_path: Optional[str] = None
    lineno: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class Edge(BaseModel):
    """그래프 엣지."""
    source: str
    target: str
    type: str
    weight: float = 1.0


class GraphResponse(BaseModel):
    """그래프 응답."""
    nodes: List[Node]
    edges: List[Edge]
    statistics: Dict[str, Any]


class AnalyzeFileRequest(BaseModel):
    """파일 분석 요청."""
    file_path: str


class AnalyzeRepositoryRequest(BaseModel):
    """저장소 분석 요청."""
    repo_path: str


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """헬스 체크."""
    return {
        "status": "healthy",
        "service": "Structural Analysis MCP",
        "version": "1.0.0"
    }


# ==================== Analysis Endpoints ====================

@app.post("/analyze-file")
async def analyze_file(request: AnalyzeFileRequest) -> GraphResponse:
    """
    파일의 구조를 분석합니다.

    Args:
        request: 파일 분석 요청

    Returns:
        그래프 응답
    """
    try:
        file_path = Path(request.file_path)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")

        result = analyzer.analyze_file(str(file_path))

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Node와 Edge 객체로 변환
        nodes = [Node(**node) for node in result.get("nodes", [])]
        edges = [Edge(**edge) for edge in result.get("edges", [])]

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            statistics=result.get("statistics", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing file {request.file_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-repository")
async def analyze_repository(request: AnalyzeRepositoryRequest) -> GraphResponse:
    """
    저장소의 구조를 분석합니다.

    Args:
        request: 저장소 분석 요청

    Returns:
        그래프 응답
    """
    try:
        repo_path = Path(request.repo_path)

        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

        result = analyzer.analyze_repository(str(repo_path))

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Node와 Edge 객체로 변환
        nodes = [Node(**node) for node in result.get("nodes", [])]
        edges = [Edge(**edge) for edge in result.get("edges", [])]

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            statistics=result.get("statistics", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing repository {request.repo_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call-graph")
async def build_call_graph(request: AnalyzeRepositoryRequest) -> GraphResponse:
    """
    저장소의 호출 그래프를 생성합니다.

    Args:
        request: 저장소 분석 요청

    Returns:
        호출 그래프
    """
    try:
        repo_path = Path(request.repo_path)

        if not repo_path.exists():
            raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

        graph = analyzer.build_call_graph(str(repo_path))

        # NetworkX 그래프를 응답 형식으로 변환
        nodes = [
            Node(
                id=node,
                type=data.get("type", "function"),
                label=node.split(":")[-1],
                file_path=data.get("file"),
            )
            for node, data in graph.nodes(data=True)
        ]

        edges = [
            Edge(source=src, target=tgt, type="CALLS")
            for src, tgt in graph.edges()
        ]

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            statistics={
                "nodes": len(nodes),
                "edges": len(edges),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building call graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9002,
        log_level="info"
    )
