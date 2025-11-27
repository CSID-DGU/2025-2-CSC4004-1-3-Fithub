"""
shared/model_utils.py
Model loading utilities compatible with HF API (Monolith Lite).
"""
import logging
import os
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

def get_hf_client():
    """HuggingFace Inference Client 반환 (Singleton 패턴 권장)"""
    from huggingface_hub import InferenceClient
    token = os.getenv("HF_API_KEY")
    if not token:
        logger.warning("HF_API_KEY not set in environment variables.")
    return InferenceClient(token=token)

class ModelPool:
    """
    Lite 모드용 ModelPool.
    실제 무거운 모델 객체 대신 API 클라이언트나 설정을 관리합니다.
    """
    def __init__(self, mcp_name: str, device: Optional[str] = None):
        self.mcp_name = mcp_name
        self.device = device
        self.client = get_hf_client()
        self.model_configs: Dict[str, str] = {}

    def add_model(self, key: str, model_name: str, **kwargs) -> None:
        """모델 설정만 저장 (실제 로드 X)"""
        logger.info(f"Registering model config: {key} -> {model_name}")
        self.model_configs[key] = model_name

    def get_model(self, key: str) -> Any:
        """API 클라이언트 반환 (모델 객체 대신)"""
        return self.client

    def get_model_name(self, key: str) -> str:
        return self.model_configs.get(key, "")

# 하위 호환성을 위한 함수 (로컬 로드 시도 시 경고)
def load_model(model_name: str, **kwargs) -> Any:
    logger.warning(
        f"Attempting to load local model '{model_name}'. "
        "This is NOT recommended in Monolith Lite mode due to RAM constraints."
    )
    try:
        from transformers import AutoModel
        return AutoModel.from_pretrained(model_name, **kwargs)
    except Exception as e:
        logger.error(f"Failed to load local model: {e}")
        return None
