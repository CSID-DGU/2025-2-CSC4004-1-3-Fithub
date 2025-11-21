"""Model loaders for Repository Analysis MCP."""
import logging
from typing import Optional
from shared.model_utils import ModelPool

logger = logging.getLogger(__name__)


class RepositoryAnalysisModelPool:
    """저장소 분석용 모델 풀."""

    def __init__(self, device: Optional[str] = None):
        self.pool = ModelPool("repository_analysis", device=device)
        self._loaded = False

    def initialize(self) -> None:
        """모델들을 초기화합니다."""
        if self._loaded:
            return

        logger.info("Initializing Repository Analysis models...")

        # CodeBERT (범용 모델)
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
        logger.info("Repository Analysis models initialization complete")

    def get_analyzer_model(self):
        """분석 모델 (CodeBERT)을 반환합니다."""
        model = self.pool.get_model("codebert")
        tokenizer = self.pool.get_tokenizer("codebert")
        return model, tokenizer, "CodeBERT"


# 글로벌 모델 풀
_model_pool: Optional[RepositoryAnalysisModelPool] = None


def get_model_pool(device: Optional[str] = None) -> RepositoryAnalysisModelPool:
    """글로벌 모델 풀을 가져옵니다."""
    global _model_pool

    if _model_pool is None:
        _model_pool = RepositoryAnalysisModelPool(device=device)
        _model_pool.initialize()

    return _model_pool
