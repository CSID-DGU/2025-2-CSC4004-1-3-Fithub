"""
mcp/semantic_embedding/embedder.py
"""
import logging
import numpy as np
from typing import Dict, List, Any, Optional
from huggingface_hub import InferenceClient
from agent.config import Config  # 👈 Config 임포트

logger = logging.getLogger(__name__)

class CodeEmbedder:
    def __init__(self, device: Optional[str] = None):
        token = Config.HF_API_KEY
        self.client = InferenceClient(token=token)
        self.model_id = Config.MODEL_EMBEDDER  # 👈 중앙 설정 사용 ("microsoft/graphcodebert-base")

    def embed_code(self, code: str, code_id: str, file_path: str = "", structure_info: Dict = None) -> Dict[str, Any]:
        try:
            # Context Injection (Code2Vec Simulation)
            context_header = f"File: {file_path}"
            if structure_info:
                classes = ",".join(structure_info.get("classes", []))
                funcs = ",".join(structure_info.get("functions", []))
                context_header += f" | Classes: {classes} | Functions: {funcs}"

            enriched_input = f"{context_header}\n\n{code}"
            vector = self._generate_embedding(enriched_input)

            return {
                "code_id": code_id,
                "embedding": vector,
                "model": self.model_id,
                "dimension": len(vector)
            }
        except Exception as e:
            logger.error(f"Embedding failed for {code_id}: {e}")
            return {"error": str(e)}

    def batch_embed(self, snippets: List[Dict[str, Any]], model_name: str = None) -> List[Dict[str, Any]]:
        results = []
        for snippet in snippets:
            res = self.embed_code(
                code=snippet["code"],
                code_id=snippet.get("id"),
                file_path=snippet.get("file_path", ""),
                structure_info=snippet.get("structure", {})
            )
            if "error" not in res:
                results.append(res)
        return results

    def _generate_embedding(self, text: str) -> List[float]:
        try:
            truncated_text = text[:1500]
            response = self.client.feature_extraction(
                truncated_text,
                model=self.model_id  # 👈 설정된 모델 사용
            )
            arr = np.array(response)
            if len(arr.shape) == 2: return np.mean(arr, axis=0).tolist()
            elif len(arr.shape) == 3: return np.mean(arr[0], axis=0).tolist()
            elif len(arr.shape) == 1: return arr.tolist()
            return arr.flatten().tolist()
        except Exception as e:
            logger.error(f"API Error: {e}")
            raise e

    def similarity(self, emb1: List[float], emb2: List[float]) -> float:
        a = np.array(emb1)
        b = np.array(emb2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def create_embedder(device: Optional[str] = None) -> CodeEmbedder:
    return CodeEmbedder(device=device)
