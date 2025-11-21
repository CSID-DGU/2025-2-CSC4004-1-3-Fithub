"""Core summarization logic."""
import logging
import torch
from pathlib import Path
from typing import Dict, List, Any, Optional
from shared.ast_utils import CodeAnalyzer
from .models_loader import get_model_pool

logger = logging.getLogger(__name__)


class CodeSummarizer:
    """코드 요약 엔진."""

    def __init__(self, device: Optional[str] = None):
        self.model_pool = get_model_pool(device=device)
        self.analyzer = CodeAnalyzer()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def summarize_function(
        self,
        code: str,
        function_name: str,
        file_path: str,
        model_name: str = "codet5"
    ) -> Dict[str, Any]:
        """
        함수를 요약합니다.

        Args:
            code: 함수 코드
            function_name: 함수 이름
            file_path: 파일 경로
            model_name: 사용할 모델명

        Returns:
            요약 결과
        """
        code_id = f"{file_path}:{function_name}"

        try:
            # 간단한 요약 생성 (데모용 - 실제로는 모델에서)
            summary = self._generate_summary(code, model_name)

            return {
                "code_id": code_id,
                "level": "function",
                "text": summary,
                "model": self._get_model_display_name(model_name),
                "confidence": 0.85,
                "metadata": {
                    "file": file_path,
                    "name": function_name,
                }
            }

        except Exception as e:
            logger.error(f"Failed to summarize {code_id}: {e}")
            return {
                "code_id": code_id,
                "level": "function",
                "text": f"Error summarizing function: {str(e)}",
                "model": self._get_model_display_name(model_name),
                "confidence": 0.0,
                "error": str(e),
            }

    def summarize_class(
        self,
        code: str,
        class_name: str,
        file_path: str,
        model_name: str = "codet5"
    ) -> Dict[str, Any]:
        """
        클래스를 요약합니다.

        Args:
            code: 클래스 코드
            class_name: 클래스 이름
            file_path: 파일 경로
            model_name: 사용할 모델명

        Returns:
            요약 결과
        """
        code_id = f"{file_path}:{class_name}"

        try:
            summary = self._generate_summary(code, model_name)

            return {
                "code_id": code_id,
                "level": "class",
                "text": summary,
                "model": self._get_model_display_name(model_name),
                "confidence": 0.85,
                "metadata": {
                    "file": file_path,
                    "name": class_name,
                }
            }

        except Exception as e:
            logger.error(f"Failed to summarize {code_id}: {e}")
            return {
                "code_id": code_id,
                "level": "class",
                "text": f"Error summarizing class: {str(e)}",
                "model": self._get_model_display_name(model_name),
                "confidence": 0.0,
                "error": str(e),
            }

    def summarize_file(
        self,
        file_path: str,
        model_name: str = "starcoder2"
    ) -> Dict[str, Any]:
        """
        파일을 요약합니다.

        Args:
            file_path: 파일 경로
            model_name: 사용할 모델명 (기본: 장문 특화)

        Returns:
            요약 결과
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            summary = self._generate_summary(code[:2000], model_name)  # 처음 2000자만

            return {
                "code_id": file_path,
                "level": "file",
                "text": summary,
                "model": self._get_model_display_name(model_name),
                "confidence": 0.80,
                "metadata": {
                    "file": file_path,
                    "lines": len(code.split('\n')),
                }
            }

        except Exception as e:
            logger.error(f"Failed to summarize {file_path}: {e}")
            return {
                "code_id": file_path,
                "level": "file",
                "text": f"Error summarizing file: {str(e)}",
                "model": self._get_model_display_name(model_name),
                "confidence": 0.0,
                "error": str(e),
            }

    def summarize_repository(
        self,
        repo_path: str,
        max_files: int = 10
    ) -> Dict[str, Any]:
        """
        저장소를 요약합니다.

        Args:
            repo_path: 저장소 경로
            max_files: 분석할 최대 파일 수

        Returns:
            저장소 요약 결과
        """
        try:
            repo_path = Path(repo_path)

            # Python 파일 찾기
            py_files = list(repo_path.rglob("*.py"))[:max_files]

            if not py_files:
                return {
                    "code_id": str(repo_path),
                    "level": "repo",
                    "text": "No Python files found in repository",
                    "model": "CodeT5+",
                    "confidence": 0.5,
                }

            # 각 파일 분석
            summaries = []
            for py_file in py_files:
                rel_path = str(py_file.relative_to(repo_path))
                file_summary = self.summarize_file(str(py_file))
                summaries.append(file_summary)

            # 저장소 전체 요약 생성
            combined_text = "\n".join([s["text"] for s in summaries[:3]])  # 상위 3개
            repo_summary = f"Repository Overview:\n{combined_text}"

            return {
                "code_id": str(repo_path),
                "level": "repo",
                "text": repo_summary,
                "model": "CodeT5+",
                "confidence": 0.75,
                "metadata": {
                    "files_analyzed": len(summaries),
                    "total_files": len(py_files),
                }
            }

        except Exception as e:
            logger.error(f"Failed to summarize repository {repo_path}: {e}")
            return {
                "code_id": str(repo_path),
                "level": "repo",
                "text": f"Error summarizing repository: {str(e)}",
                "model": "CodeT5+",
                "confidence": 0.0,
                "error": str(e),
            }

    def _generate_summary(self, code: str, model_name: str = "codet5") -> str:
        """
        모델을 사용하여 요약을 생성합니다.

        Args:
            code: 코드 스니펫
            model_name: 모델명

        Returns:
            생성된 요약
        """
        # 주의: 이 메서드는 데모용입니다.
        # 실제 구현에서는 모델을 로드하고 추론을 실행합니다.

        # 코드 길이에 따라 기본 요약 생성
        lines = code.split('\n')

        # 간단한 휴리스틱 기반 요약
        if "def " in code or "class " in code:
            summary = "This code defines a Python function or class. "
        else:
            summary = "This code snippet contains Python logic. "

        # 주요 키워드 추출
        if "import" in code:
            summary += "It imports external modules. "
        if "async" in code or "await" in code:
            summary += "It uses async/await patterns. "
        if "try:" in code or "except" in code:
            summary += "It includes error handling. "

        summary += f"The code consists of {len(lines)} lines."

        return summary

    def _get_model_display_name(self, model_name: str) -> str:
        """모델 이름을 표시용으로 변환합니다."""
        mapping = {
            "codet5": "CodeT5+",
            "starcoder2": "StarCoder2",
            "codellama": "CodeLlama-Instruct",
            "unixcoder": "UniXcoder",
        }
        return mapping.get(model_name, model_name)


def create_summarizer(device: Optional[str] = None) -> CodeSummarizer:
    """요약기를 생성합니다."""
    return CodeSummarizer(device=device)
