"""Configuration for Agent Service."""
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


class Config:
    """기본 설정."""

    # FastAPI 설정
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    WORKERS = int(os.getenv("WORKERS", 4))

    # MCP 서비스 URL
    SUMMARIZATION_MCP_URL = os.getenv(
        "SUMMARIZATION_MCP_URL",
        "http://localhost:9001"
    )
    STRUCTURAL_ANALYSIS_MCP_URL = os.getenv(
        "STRUCTURAL_ANALYSIS_MCP_URL",
        "http://localhost:9002"
    )
    SEMANTIC_EMBEDDING_MCP_URL = os.getenv(
        "SEMANTIC_EMBEDDING_MCP_URL",
        "http://localhost:9003"
    )
    REPOSITORY_ANALYSIS_MCP_URL = os.getenv(
        "REPOSITORY_ANALYSIS_MCP_URL",
        "http://localhost:9004"
    )
    TASK_RECOMMENDER_MCP_URL = os.getenv(
        "TASK_RECOMMENDER_MCP_URL",
        "http://localhost:9005"
    )

    # 임시 저장소 설정
    TEMP_REPO_DIR = os.getenv("TEMP_REPO_DIR", "/tmp/code_analysis_repos")

    # LangGraph 설정
    MAX_RETRIES = 2
    TIMEOUT = 300  # 5분

    # 기본 임계값
    DEFAULT_THRESHOLDS = {
        "codebleu_min": 0.42,
        "bleurt_min": 0.05,
        "rougeL_min": 0.30,
        "edge_f1_min": 0.80,
        "ged_max": 50.0,
        "retry_max": 2,
        "ensemble": True,
    }

    # MCP 엔드포인트 매핑
    @classmethod
    def get_mcp_endpoints(cls) -> Dict[str, str]:
        """모든 MCP 엔드포인트를 반환합니다."""
        return {
            "summarization": cls.SUMMARIZATION_MCP_URL,
            "structural_analysis": cls.STRUCTURAL_ANALYSIS_MCP_URL,
            "semantic_embedding": cls.SEMANTIC_EMBEDDING_MCP_URL,
            "repository_analysis": cls.REPOSITORY_ANALYSIS_MCP_URL,
            "task_recommender": cls.TASK_RECOMMENDER_MCP_URL,
        }

    @classmethod
    def health_check_urls(cls) -> Dict[str, str]:
        """헬스 체크 URL을 반환합니다."""
        return {
            "summarization": f"{cls.SUMMARIZATION_MCP_URL}/health",
            "structural_analysis": f"{cls.STRUCTURAL_ANALYSIS_MCP_URL}/health",
            "semantic_embedding": f"{cls.SEMANTIC_EMBEDDING_MCP_URL}/health",
            "repository_analysis": f"{cls.REPOSITORY_ANALYSIS_MCP_URL}/health",
            "task_recommender": f"{cls.TASK_RECOMMENDER_MCP_URL}/health",
        }
