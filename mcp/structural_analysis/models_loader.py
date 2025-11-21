"""Model loaders for Structural Analysis MCP."""
import logging
from typing import Optional
from shared.model_utils import ModelPool

logger = logging.getLogger(__name__)


class StructuralAnalysisModelPool:
    """구조 분석용 모델 풀."""

    def __init__(self, device: Optional[str] = None):
        self.pool = ModelPool("structural_analysis", device=device)
        self._loaded = False

    def initialize(self) -> None:
        """모델들을 초기화합니다."""
        if self._loaded:
            return

        logger.info("Initializing Structural Analysis models...")

        # GraphCodeBERT (그래프 생성)
        try:
            self.pool.add_model(
                "graphcodebert",
                "microsoft/graphcodebert-base",
                model_type="transformer"
            )
            self.pool.add_tokenizer("graphcodebert", "microsoft/graphcodebert-base")
            logger.info("✓ GraphCodeBERT loaded")
        except Exception as e:
            logger.warning(f"Failed to load GraphCodeBERT: {e}")

        # Code2Vec 기반 구조 분석용 모델
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

        self._loaded = True
        logger.info("Structural Analysis models initialization complete")

    def get_graph_generator_model(self):
        """그래프 생성 모델 (GraphCodeBERT)을 반환합니다."""
        model = self.pool.get_model("graphcodebert")
        tokenizer = self.pool.get_tokenizer("graphcodebert")
        return model, tokenizer, "GraphCodeBERT"

    def get_embedding_model(self):
        """구조적 임베딩 모델 (CodeBERT)을 반환합니다."""
        model = self.pool.get_model("codebert")
        tokenizer = self.pool.get_tokenizer("codebert")
        return model, tokenizer, "CodeBERT"


# 글로벌 모델 풀
_model_pool: Optional[StructuralAnalysisModelPool] = None


def get_model_pool(device: Optional[str] = None) -> StructuralAnalysisModelPool:
    """
    글로벌 모델 풀을 가져옵니다.

    Args:
        device: CPU 또는 CUDA

    Returns:
        StructuralAnalysisModelPool 인스턴스
    """
    global _model_pool

    if _model_pool is None:
        _model_pool = StructuralAnalysisModelPool(device=device)
        _model_pool.initialize()

    return _model_pool
