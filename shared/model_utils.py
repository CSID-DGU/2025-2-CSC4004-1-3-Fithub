"""Model loading and caching utilities."""
import os
import torch
from pathlib import Path
from typing import Any, Dict, Optional, Union
from transformers import AutoModel, AutoTokenizer, pipeline
import logging

logger = logging.getLogger(__name__)

# 프로젝트 루트의 models 디렉토리
MODELS_CACHE_DIR = Path(__file__).parent.parent / "models"


def get_model_cache_path(mcp_name: str) -> Path:
    """MCP별 모델 캐시 경로를 반환합니다."""
    cache_path = MODELS_CACHE_DIR / mcp_name
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def load_model(
    model_name: str,
    mcp_name: str,
    model_type: str = "transformer",
    device: Optional[str] = None,
    **kwargs
) -> Any:
    """
    모델을 로드합니다 (로컬 캐시 사용).

    Args:
        model_name: HuggingFace 모델 ID (예: "microsoft/CodeBERT-base")
        mcp_name: MCP 이름 (summarization, structural_analysis 등)
        model_type: 'transformer', 'pipeline' 등
        device: 'cpu' 또는 'cuda'
        **kwargs: 추가 인자

    Returns:
        로드된 모델
    """
    cache_path = get_model_cache_path(mcp_name)

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        if model_type == "transformer":
            logger.info(f"Loading model {model_name} from cache {cache_path}")
            model = AutoModel.from_pretrained(
                model_name,
                cache_dir=str(cache_path),
                device_map=device,
                **kwargs
            )
            return model

        elif model_type == "pipeline":
            task = kwargs.get("task", "feature-extraction")
            logger.info(f"Loading pipeline {task} with model {model_name}")
            pipe = pipeline(
                task=task,
                model=model_name,
                cache_dir=str(cache_path),
                device=device,
                **{k: v for k, v in kwargs.items() if k != "task"}
            )
            return pipe

        else:
            raise ValueError(f"Unknown model_type: {model_type}")

    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise


def load_tokenizer(
    model_name: str,
    mcp_name: str,
    **kwargs
) -> Any:
    """
    토크나이저를 로드합니다.

    Args:
        model_name: HuggingFace 모델 ID
        mcp_name: MCP 이름
        **kwargs: 추가 인자

    Returns:
        로드된 토크나이저
    """
    cache_path = get_model_cache_path(mcp_name)

    try:
        logger.info(f"Loading tokenizer {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=str(cache_path),
            **kwargs
        )
        return tokenizer
    except Exception as e:
        logger.error(f"Failed to load tokenizer {model_name}: {e}")
        raise


class ModelPool:
    """여러 모델을 관리하는 풀입니다."""

    def __init__(self, mcp_name: str, device: Optional[str] = None):
        self.mcp_name = mcp_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.models: Dict[str, Any] = {}
        self.tokenizers: Dict[str, Any] = {}

    def add_model(
        self,
        key: str,
        model_name: str,
        model_type: str = "transformer",
        **kwargs
    ) -> None:
        """풀에 모델을 추가합니다."""
        if key not in self.models:
            logger.info(f"Adding model {key} ({model_name}) to pool")
            self.models[key] = load_model(
                model_name,
                self.mcp_name,
                model_type=model_type,
                device=self.device,
                **kwargs
            )

    def add_tokenizer(
        self,
        key: str,
        model_name: str,
        **kwargs
    ) -> None:
        """풀에 토크나이저를 추가합니다."""
        if key not in self.tokenizers:
            logger.info(f"Adding tokenizer {key} ({model_name}) to pool")
            self.tokenizers[key] = load_tokenizer(
                model_name,
                self.mcp_name,
                **kwargs
            )

    def get_model(self, key: str) -> Optional[Any]:
        """키로 모델을 가져옵니다."""
        return self.models.get(key)

    def get_tokenizer(self, key: str) -> Optional[Any]:
        """키로 토크나이저를 가져옵니다."""
        return self.tokenizers.get(key)

    def get_model_and_tokenizer(self, key: str) -> tuple:
        """모델과 토크나이저를 함께 가져옵니다."""
        return self.models.get(key), self.tokenizers.get(key)


def clear_cache(mcp_name: Optional[str] = None) -> None:
    """캐시를 정리합니다."""
    if mcp_name:
        cache_path = get_model_cache_path(mcp_name)
        logger.info(f"Clearing cache for {mcp_name} at {cache_path}")
        # 주의: 실제 삭제는 신중하게 구현
    else:
        logger.info("Clearing all model caches")


def get_device() -> str:
    """사용 가능한 디바이스를 반환합니다."""
    return "cuda" if torch.cuda.is_available() else "cpu"
