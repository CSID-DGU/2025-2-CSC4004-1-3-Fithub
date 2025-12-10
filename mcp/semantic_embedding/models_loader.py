"""Model loaders for Semantic Embedding MCP."""
import logging
from typing import Optional
from shared.model_utils import ModelPool

logger = logging.getLogger(__name__)


class EmbeddingModelPool:
    """임베딩용 모델 풀."""

    def __init__(self, device: Optional[str] = None):
        self.pool = ModelPool("semantic_embedding", device=device)
        self._loaded = False

    def initialize(self) -> None:
        """모델들을 초기화합니다."""
        if self._loaded:
            return

        logger.info("Initializing Embedding models...")

        # CodeBERT (주력 모델)
        try:
            self.pool.add_model(
                "codebert",
                "microsoft/codebert-base",
                model_type="transformer"
            )
            self.pool.add_tokenizer("codebert", "microsoft/codebert-base")
            logger.info("✓ CodeBERT loaded")
        except Exception as e:
            logger.warning(f"Failed to load CodeBERT: {e}")

        # CuBERT (품질 검증/대체)
        try:
            self.pool.add_model(
                "cubert",
                "google/cubert-base-pytorch",
                model_type="transformer"
            )
            self.pool.add_tokenizer("cubert", "google/cubert-base-pytorch")
            logger.info("✓ CuBERT loaded")
        except Exception as e:
            logger.warning(f"Failed to load CuBERT: {e}")

        self._loaded = True
        logger.info("Embedding models initialization complete")

    def get_primary_model(self):
        """주력 모델 (CodeBERT)을 반환합니다."""
        model = self.pool.get_model("codebert")
        tokenizer = self.pool.get_tokenizer("codebert")
        return model, tokenizer, "CodeBERT"

    def get_qa_model(self):
        """품질 검증 모델 (CuBERT)을 반환합니다."""
        model = self.pool.get_model("cubert")
        tokenizer = self.pool.get_tokenizer("cubert")
        return model, tokenizer, "CuBERT"


# 글로벌 모델 풀
_model_pool: Optional[EmbeddingModelPool] = None


def get_model_pool(device: Optional[str] = None) -> EmbeddingModelPool:
    """글로벌 모델 풀을 가져옵니다."""
    global _model_pool

    if _model_pool is None:
        _model_pool = EmbeddingModelPool(device=device)
        _model_pool.initialize()

    return _model_pool
