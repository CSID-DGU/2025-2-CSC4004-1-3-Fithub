"""Model loaders for Task Recommender MCP."""
import logging
from typing import Optional
from shared.model_utils import ModelPool

logger = logging.getLogger(__name__)


class TaskRecommenderModelPool:
    """작업 추천용 모델 풀."""

    def __init__(self, device: Optional[str] = None):
        self.pool = ModelPool("task_recommender", device=device)
        self._loaded = False

    def initialize(self) -> None:
        """모델들을 초기화합니다."""
        if self._loaded:
            return

        logger.info("Initializing Task Recommender models...")

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
        logger.info("Task Recommender models initialization complete")

    def get_analyzer_model(self):
        """분석 모델을 반환합니다."""
        model = self.pool.get_model("codebert")
        tokenizer = self.pool.get_tokenizer("codebert")
        return model, tokenizer, "CodeBERT"


# 글로벌 모델 풀
_model_pool: Optional[TaskRecommenderModelPool] = None


def get_model_pool(device: Optional[str] = None) -> TaskRecommenderModelPool:
    """글로벌 모델 풀을 가져옵니다."""
    global _model_pool

    if _model_pool is None:
        _model_pool = TaskRecommenderModelPool(device=device)
        _model_pool.initialize()

    return _model_pool
