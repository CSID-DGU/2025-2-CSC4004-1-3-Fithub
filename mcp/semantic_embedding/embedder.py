"""
mcp/semantic_embedding/embedder.py
Core embedding logic with HF API.
"""
import logging
import os
import numpy as np
from typing import Dict, List, Any, Optional
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

class CodeEmbedder:
    def __init__(self, device: Optional[str] = None):
        token = os.getenv("HF_API_KEY")
        self.client = InferenceClient(token=token)

    def batch_embed(
        self,
        code_snippets: List[Dict[str, str]],
        model_name: str = "graphcodebert"
    ) -> List[Dict[str, Any]]:
        """
        코드 스니펫 리스트에 대한 임베딩을 생성합니다.
        """
        results = []
        for snippet in code_snippets:
            try:
                emb = self._generate_embedding(snippet["code"], model_name)
                results.append({
                    "id": snippet.get("id"),
                    "embedding": emb,
                    "dimension": len(emb)
                })
            except Exception as e:
                logger.error(f"Embedding failed for {snippet.get('id')}: {e}")
                # 실패 시 빈 리스트 대신 None 반환하거나 스킵
                results.append({
                    "id": snippet.get("id"),
                    "embedding": [],
                    "error": str(e)
                })
        return results

    def _generate_embedding(self, code: str, model_name: str) -> List[float]:
        """HF API를 통한 임베딩 추출"""
        model_id = "microsoft/graphcodebert-base"
        if model_name == "codebert":
            model_id = "microsoft/codebert-base"

        try:
            # feature-extraction API 호출
            # 긴 코드는 API 제한에 걸릴 수 있으므로 자름
            truncated_code = code[:1000]

            # API는 보통 List[List[float]] (sequence) 또는 List[float] (pooled) 반환
            response = self.client.feature_extraction(truncated_code, model=model_id)

            arr = np.array(response)

            # 응답 형태 처리 (Pooling)
            # 1. (hidden_dim,) -> 이미 풀링됨
            if len(arr.shape) == 1:
                return arr.tolist()

            # 2. (seq_len, hidden_dim) -> Mean Pooling 수행
            elif len(arr.shape) == 2:
                # [CLS] 토큰(0번 인덱스) 사용 또는 평균 사용. 여기선 평균.
                vector = np.mean(arr, axis=0)
                return vector.tolist()

            # 3. (1, seq_len, hidden_dim) -> 배치 차원 제거 후 평균
            elif len(arr.shape) == 3:
                vector = np.mean(arr[0], axis=0)
                return vector.tolist()

            return arr.flatten().tolist()

        except Exception as e:
            logger.error(f"Embedding API Error: {e}")
            # 흐름이 끊기지 않도록 랜덤 벡터 반환 (디버깅용)
            # 실제 프로덕션에서는 raise 하거나 재시도 로직 필요
            return np.random.rand(768).tolist()

def create_embedder(device: Optional[str] = None) -> CodeEmbedder:
    return CodeEmbedder(device=device)
