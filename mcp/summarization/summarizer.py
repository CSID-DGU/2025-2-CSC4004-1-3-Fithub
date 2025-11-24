"""
mcp/summarization/summarizer.py
Core summarization logic with Hugging Face API support.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)

class CodeSummarizer:
    def __init__(self, device: Optional[str] = None):
        # API Key 로드 (config 또는 env에서)
        token = os.getenv("HF_API_KEY")
        if not token:
            logger.warning("HF_API_KEY is missing. Summarization will fail or use mock.")

        self.client = InferenceClient(token=token)
        self.device = device  # Lite 모드에서는 실제로 사용하지 않음 (API 위임)

    def summarize_repository(self, repo_path: str, max_files: int = 15) -> Dict[str, Any]:
        """
        저장소 내의 Python 파일들을 찾아 요약합니다.
        """
        try:
            repo_path = Path(repo_path)
            # 숨김 폴더나 venv 제외하고 py 파일 검색
            py_files = [
                p for p in repo_path.rglob("*.py")
                if not any(part.startswith(".") or part == "venv" for part in p.parts)
            ][:max_files]

            file_summaries = []
            logger.info(f"Found {len(py_files)} files to summarize.")

            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()

                    # 파일 경로 ID 생성
                    code_id = str(py_file.relative_to(repo_path))

                    # API 호출 (최대 1500자까지만 전송하여 토큰 절약)
                    summary_text = self._generate_summary(code[:1500], "codet5")

                    file_summaries.append({
                        "code_id": code_id,
                        "text": summary_text,
                        "level": "file",
                        "model": "codet5-api"
                    })
                    logger.debug(f"Summarized {code_id}")

                except Exception as e:
                    logger.warning(f"Skipping {py_file}: {e}")

            return {
                "text": "Repository analysis completed.",
                "metadata": {
                    "file_summaries": file_summaries,
                    "total_analyzed": len(file_summaries)
                }
            }
        except Exception as e:
            logger.error(f"Repo summary failed: {e}")
            return {"error": str(e)}

    def _generate_summary(self, code: str, model_name: str = "codet5") -> str:
        """
        Hugging Face API를 통해 요약문을 생성합니다.
        """
        # 무료 티어에서 사용 가능한 가벼운 모델 ID
        hf_model_id = "Salesforce/codet5p-220m"

        if model_name == "starcoder2":
            hf_model_id = "bigcode/starcoder2-3b"

        prompt = f"Summarize this Python code in one sentence:\n\n{code}"

        try:
            # text_generation API 호출
            response = self.client.text_generation(
                prompt,
                model=hf_model_id,
                max_new_tokens=60,
                temperature=0.2,
                do_sample=False
            )
            return response.strip()

        except Exception as e:
            logger.error(f"HF API Error ({model_name}): {e}")
            return "Summary generation failed."

def create_summarizer(device: Optional[str] = None) -> CodeSummarizer:
    return CodeSummarizer(device=device)
