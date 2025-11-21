"""Model loaders for Summarization MCP."""
import logging
from typing import Optional
from shared.model_utils import ModelPool

logger = logging.getLogger(__name__)


class SummarizationModelPool:
    """요약용 모델 풀."""

    def __init__(self, device: Optional[str] = None):
        self.pool = ModelPool("summarization", device=device)
        self._loaded = False

    def initialize(self) -> None:
        """모델들을 초기화합니다."""
        if self._loaded:
            return

        logger.info("Initializing Summarization models...")

        # CodeT5+ (주력 모델)
        try:
            self.pool.add_model(
                "codet5",
                "Salesforce/codet5p-base",
                model_type="transformer"
            )
            self.pool.add_tokenizer("codet5", "Salesforce/codet5p-base")
            logger.info("✓ CodeT5+ loaded")
        except Exception as e:
            logger.warning(f"Failed to load CodeT5+: {e}")

        # StarCoder2 (장문 특화)
        try:
            self.pool.add_model(
                "starcoder2",
                "bigcode/starcoder2-3b",
                model_type="transformer"
            )
            self.pool.add_tokenizer("starcoder2", "bigcode/starcoder2-3b")
            logger.info("✓ StarCoder2 loaded")
        except Exception as e:
            logger.warning(f"Failed to load StarCoder2: {e}")

        # CodeLlama-Instruct (의도 기반)
        try:
            self.pool.add_model(
                "codellama",
                "meta-llama/CodeLlama-7b-Instruct-hf",
                model_type="transformer"
            )
            self.pool.add_tokenizer("codellama", "meta-llama/CodeLlama-7b-Instruct-hf")
            logger.info("✓ CodeLlama-Instruct loaded")
        except Exception as e:
            logger.warning(f"Failed to load CodeLlama-Instruct: {e}")

        # UniXcoder (컨텍스트 강화)
        try:
            self.pool.add_model(
                "unixcoder",
                "microsoft/unixcoder-base",
                model_type="transformer"
            )
            self.pool.add_tokenizer("unixcoder", "microsoft/unixcoder-base")
            logger.info("✓ UniXcoder loaded")
        except Exception as e:
            logger.warning(f"Failed to load UniXcoder: {e}")

        self._loaded = True
        logger.info("Summarization models initialization complete")

    def get_primary_model(self):
        """주력 모델 (CodeT5+)을 반환합니다."""
        model = self.pool.get_model("codet5")
        tokenizer = self.pool.get_tokenizer("codet5")
        return model, tokenizer, "CodeT5+"

    def get_long_context_model(self):
        """장문 특화 모델 (StarCoder2)을 반환합니다."""
        model = self.pool.get_model("starcoder2")
        tokenizer = self.pool.get_tokenizer("starcoder2")
        return model, tokenizer, "StarCoder2"

    def get_intent_model(self):
        """의도 기반 모델 (CodeLlama)을 반환합니다."""
        model = self.pool.get_model("codellama")
        tokenizer = self.pool.get_tokenizer("codellama")
        return model, tokenizer, "CodeLlama-Instruct"

    def get_context_aware_model(self):
        """컨텍스트 강화 모델 (UniXcoder)을 반환합니다."""
        model = self.pool.get_model("unixcoder")
        tokenizer = self.pool.get_tokenizer("unixcoder")
        return model, tokenizer, "UniXcoder"


# 글로벌 모델 풀
_model_pool: Optional[SummarizationModelPool] = None


def get_model_pool(device: Optional[str] = None) -> SummarizationModelPool:
    """
    글로벌 모델 풀을 가져옵니다.

    Args:
        device: CPU 또는 CUDA

    Returns:
        SummarizationModelPool 인스턴스
    """
    global _model_pool

    if _model_pool is None:
        _model_pool = SummarizationModelPool(device=device)
        _model_pool.initialize()

    return _model_pool
