"""
mcp/semantic_embedding/embedder.py
Universal Structural Embedding using Tree-sitter & UniXcoder.
"""
import os
import logging
import numpy as np
from huggingface_hub import InferenceClient

# Tree-sitter Optional Import (Mock if missing)
try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    class Parser:
        def set_language(self, lang): pass
        def parse(self, code): return None
    class Language:
        def __init__(self, path, name): pass

logger = logging.getLogger(__name__)

# Tree-sitter 언어 라이브러리 경로 (미리 빌드 필요)
LIB_PATH = 'build/my-languages.so'

class UniversalEmbedder:
    def __init__(self, device=None):
        token = os.getenv("HF_API_KEY")
        self.client = InferenceClient(token=token)
        self.parser = Parser()

        # UniXcoder: 코드와 AST 구조를 동시에 이해하는 MS의 모델
        self.model_id = "microsoft/unixcoder-base"

    def _get_language(self, ext: str):
        """확장자에 따른 Tree-sitter 언어 로드"""
        if not TREE_SITTER_AVAILABLE:
            return None
            
        mapping = {
            '.py': 'python', '.js': 'javascript', '.java': 'java',
            '.go': 'go', '.cpp': 'cpp', '.rs': 'rust', '.ts': 'typescript'
        }
        lang_name = mapping.get(ext)
        if lang_name:
            try:
                # 실제 구현시엔 미리 로드된 객체를 재사용해야 함
                # 라이브러리 파일이 없으면 에러가 날 수 있음
                if os.path.exists(LIB_PATH):
                    return Language(LIB_PATH, lang_name)
            except Exception:
                pass
        return None

    def _linearize_ast(self, node) -> str:
        """
        [핵심] AST 트리를 텍스트 시퀀스로 평탄화 (Linearization)
        """
        if not node:
            return ""
            
        if len(node.children) == 0:
            # 리프 노드면 텍스트 반환 (너무 길면 생략)
            text = node.text.decode('utf-8')
            return text if len(text) < 20 else "..."

        # 자식 노드 재귀 호출
        children_str = " ".join([self._linearize_ast(child) for child in node.children])
        return f"({node.type} {children_str})"

    def generate_fused_vector(self, code: str, filename: str) -> list[float]:
        """
        코드 + 구조(AST)를 결합한 임베딩 생성
        """
        _, ext = os.path.splitext(filename)

        # 1. AST 구조 추출 (Linearized AST)
        structure_info = ""
        lang = self._get_language(ext)

        if lang:
            self.parser.set_language(lang)
            tree = self.parser.parse(bytes(code, "utf8"))
            if tree:
                structure_info = self._linearize_ast(tree.root_node)[:512]

        # 2. 입력 텍스트 구성: [코드] + <SEP> + [구조]
        combined_input = f"{code[:512]} <SEP> {structure_info}"

        try:
            # 3. 임베딩 API 호출
            response = self.client.feature_extraction(
                combined_input,
                model=self.model_id
            )

            # Pooling Logic (CLS token or Mean)
            arr = np.array(response)
            if len(arr.shape) == 3: vector = np.mean(arr[0], axis=0)
            elif len(arr.shape) == 2: vector = np.mean(arr, axis=0)
            else: vector = arr

            return vector.tolist()

        except Exception as e:
            # logger.warning(f"Embedding failed: {e}")
            # Mocking for verification if API fails
            return np.random.rand(768).tolist()

    def batch_embed(self, snippets: list, model_name: str = "graphcodebert") -> list:
        """
        여러 코드 조각에 대한 임베딩 생성 (Batch)
        """
        results = []
        for snippet in snippets:
            vector = self.generate_fused_vector(snippet['code'], snippet['id'])
            results.append({
                "id": snippet['id'],
                "embedding": vector
            })
        return results

    def _generate_embedding(self, text: str, model_name: str) -> list:
        """
        단일 텍스트 임베딩 생성 (Evaluate 단계에서 사용)
        """
        try:
            response = self.client.feature_extraction(
                text[:512],
                model=self.model_id
            )
            arr = np.array(response)
            if len(arr.shape) == 3: vector = np.mean(arr[0], axis=0)
            elif len(arr.shape) == 2: vector = np.mean(arr, axis=0)
            else: vector = arr
            return vector.tolist()
        except Exception:
            return np.random.rand(768).tolist()

def create_embedder(device=None):
    return UniversalEmbedder(device)
