"""
Model loaders for Structural Analysis MCP.
Local model loading for AWS Lambda/EC2 deployment (No API dependency).
"""
import logging
import os
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)


class StructuralAnalysisModelPool:
    """
    Local model pool for code structure analysis.
    AWS에 배포하기 위해 완전히 로컬 모델 로딩만 사용합니다.
    """

    def __init__(self, device: Optional[str] = None, cache_dir: Optional[str] = None):
        import torch

        cache_dir = cache_dir or os.getenv("HF_HOME", "./models/structural_analysis/")
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = cache_dir

        self.models = {}  # 로드된 모델 객체
        self.tokenizers = {}  # 로드된 토크나이저
        self.model_configs = {}  # 모델 설정
        self._initialized = False

        logger.info(f"StructuralAnalysisModelPool initialized on device={self.device}")

    def register_models(self) -> None:
        """
        사용할 모델들을 등록합니다.
        """
        # 1. GraphCodeBERT (데이터/제어 흐름 그래프 분석)
        self.model_configs["graphcodebert"] = "microsoft/graphcodebert-base"

        # 2. CodeBERT (구조적 임베딩)
        self.model_configs["codebert"] = "microsoft/codebert-base"

        logger.info(f"Registered {len(self.model_configs)} models for structure analysis")

    def initialize(self) -> None:
        """
        등록된 모든 모델과 토크나이저를 실제로 로드합니다.
        AWS 배포 시 서비스 시작 때 호출됨.
        """
        if self._initialized:
            logger.debug("Models already initialized")
            return

        from transformers import AutoModel, AutoTokenizer

        self.register_models()

        logger.info(f"Loading {len(self.model_configs)} structural analysis models...")

        for key, model_id in self.model_configs.items():
            try:
                logger.info(f"  Loading {key} ({model_id})...")

                # 토크나이저 로드
                tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                    trust_remote_code=True
                )
                self.tokenizers[key] = tokenizer

                # 모델 로드
                model = AutoModel.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                    trust_remote_code=True,
                    output_hidden_states=True
                ).to(self.device).eval()

                self.models[key] = model
                logger.info(f"  ✓ {key} loaded successfully to {self.device}")

            except Exception as e:
                logger.error(f"Failed to load {key} ({model_id}): {e}")
                raise

        self._initialized = True
        logger.info("✓ All structural analysis models loaded successfully")

    def get_graph_generator_model(self) -> Tuple[Any, Any, str]:
        """
        그래프 생성 모델 (GraphCodeBERT)을 반환합니다.

        Returns:
            (model, tokenizer, model_name)
        """
        if not self._initialized:
            raise RuntimeError("Models not initialized. Call initialize() first")

        return self.models["graphcodebert"], self.tokenizers["graphcodebert"], "GraphCodeBERT"

    def get_structure_embedding_model(self) -> Tuple[Any, Any, str]:
        """
        구조적 임베딩 모델 (CodeBERT)을 반환합니다.

        Returns:
            (model, tokenizer, model_name)
        """
        if not self._initialized:
            raise RuntimeError("Models not initialized. Call initialize() first")

        return self.models["codebert"], self.tokenizers["codebert"], "CodeBERT"

    def get_model_by_name(self, name: str) -> Tuple[Any, Any, str]:
        """
        이름으로 모델을 반환합니다.

        Args:
            name: "graphcodebert" 또는 "codebert"

        Returns:
            (model, tokenizer, model_name)
        """
        name_lower = name.lower()
        if name_lower == "graphcodebert":
            return self.get_graph_generator_model()
        elif name_lower == "codebert":
            return self.get_structure_embedding_model()
        else:
            raise ValueError(f"Unknown model: {name}. Available: graphcodebert, codebert")

    def get_device(self) -> str:
        """현재 사용 중인 디바이스 반환"""
        return self.device

    def clear(self) -> None:
        """메모리에서 모든 모델 언로드"""
        self.models.clear()
        self.tokenizers.clear()
        self._initialized = False
        logger.info("Cleared all structural analysis models")


# 글로벌 모델 풀 (싱글톤 패턴)
_model_pool: Optional[StructuralAnalysisModelPool] = None


def get_model_pool(device: Optional[str] = None, cache_dir: Optional[str] = None) -> StructuralAnalysisModelPool:
    """
    글로벌 모델 풀을 가져옵니다 (싱글톤).
    첫 호출 시 모든 모델을 메모리에 로드합니다.

    AWS 배포 시:
    - 서비스 시작 시 이 함수를 호출
    - HuggingFace 모델이 자동으로 다운로드되고 캐싱됨
    - 이후 호출은 캐시된 모델 사용
    - API 비용 없음, 레이트 제한 없음

    Args:
        device: "cuda" 또는 "cpu" (기본값: 자동 감지)
        cache_dir: 모델 캐시 디렉토리 (기본값: ./models/structural_analysis/)

    Returns:
        StructuralAnalysisModelPool 싱글톤 인스턴스
    """
    global _model_pool

    if _model_pool is None:
        _model_pool = StructuralAnalysisModelPool(device=device, cache_dir=cache_dir)
        _model_pool.initialize()

    return _model_pool
