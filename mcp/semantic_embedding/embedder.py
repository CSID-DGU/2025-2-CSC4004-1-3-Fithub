"""Core embedding logic."""
import logging
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Any, Optional
from .models_loader import get_model_pool

logger = logging.getLogger(__name__)


class CodeEmbedder:
    """코드 임베딩 엔진."""

    def __init__(self, device: Optional[str] = None):
        self.model_pool = get_model_pool(device=device)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def embed_code(
        self,
        code: str,
        code_id: str,
        model_name: str = "codebert"
    ) -> Dict[str, Any]:
        """
        코드를 임베딩합니다.

        Args:
            code: 코드 텍스트
            code_id: 코드 ID
            model_name: 사용할 모델명

        Returns:
            임베딩 결과
        """
        try:
            # 데모용 임베딩 생성
            embedding = self._generate_embedding(code, model_name)

            return {
                "code_id": code_id,
                "embedding": embedding,
                "model": self._get_model_name(model_name),
                "dimension": len(embedding),
            }

        except Exception as e:
            logger.error(f"Failed to embed {code_id}: {e}")
            return {
                "code_id": code_id,
                "embedding": [],
                "model": self._get_model_name(model_name),
                "error": str(e),
            }

    def batch_embed(
        self,
        code_snippets: List[Dict[str, str]],
        model_name: str = "codebert"
    ) -> List[Dict[str, Any]]:
        """
        여러 코드를 임베딩합니다.

        Args:
            code_snippets: 코드 목록 [{"id": ..., "code": ...}, ...]
            model_name: 사용할 모델명

        Returns:
            임베딩 결과 목록
        """
        results = []

        for snippet in code_snippets:
            result = self.embed_code(
                snippet["code"],
                snippet.get("id", "unknown"),
                model_name
            )
            results.append(result)

        return results

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        두 임베딩 사이의 코사인 유사도를 계산합니다.

        Args:
            embedding1: 첫 번째 임베딩
            embedding2: 두 번째 임베딩

        Returns:
            유사도 점수 (0-1)
        """
        try:
            e1 = np.array(embedding1)
            e2 = np.array(embedding2)

            # 코사인 유사도
            dot_product = np.dot(e1, e2)
            norm1 = np.linalg.norm(e1)
            norm2 = np.linalg.norm(e2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(max(0, min(1, similarity)))

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0

    def _generate_embedding(self, code: str, model_name: str = "codebert") -> List[float]:
        """
        임베딩을 생성합니다.

        Args:
            code: 코드 텍스트
            model_name: 모델명

        Returns:
            768차원 임베딩 벡터
        """
        # 데모용 임베딩: 코드의 해시 기반 의사난수
        import hashlib

        hash_obj = hashlib.md5(code.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        # 768차원 벡터 생성 (CodeBERT의 출력 차원)
        np.random.seed(hash_int % (2**32))
        embedding = np.random.randn(768).astype(np.float32)

        # 정규화
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.tolist()

    def _get_model_name(self, model_name: str) -> str:
        """모델명을 표시용으로 변환합니다."""
        mapping = {
            "codebert": "CodeBERT",
            "cubert": "CuBERT",
        }
        return mapping.get(model_name, model_name)


def create_embedder(device: Optional[str] = None) -> CodeEmbedder:
    """임베더를 생성합니다."""
    return CodeEmbedder(device=device)
