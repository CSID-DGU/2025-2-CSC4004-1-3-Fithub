"""
mcp/summarization/summarizer.py
Core summarization logic with Hugging Face API support (Polyglot).
"""
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from huggingface_hub import InferenceClient
from agent.config import Config

logger = logging.getLogger(__name__)

class CodeSummarizer:
    def __init__(self, device: Optional[str] = None):
        token = Config.HF_API_KEY
        if not token:
            logger.warning("HF_API_KEY is missing via Config.")

        self.client = InferenceClient(token=token)
        self.model_id = Config.MODEL_SUMMARIZER

        # 지원 확장자 (Polyglot)
        self.valid_exts = {'.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.cs', '.rs'}

    def summarize_file(self, file_path: str, model_name: str = None) -> Dict[str, Any]:
        """단일 파일 요약"""
        target_model = self.model_id
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            summary = self._generate_summary(code, target_model)

            return {
                "code_id": Path(file_path).name,
                "text": summary,
                "level": "file",
                "model": target_model,
                "confidence": 0.85
            }
        except Exception as e:
            logger.error(f"File summary failed: {e}")
            return {"error": str(e)}

    def summarize_code(self, code: str, code_id: str, model_name: str = None) -> Dict[str, Any]:
        """코드 조각 요약"""
        target_model = self.model_id
        summary = self._generate_summary(code, target_model)
        return {
            "code_id": code_id,
            "text": summary,
            "level": "snippet",
            "model": target_model,
            "confidence": 0.85
        }

    def summarize_repository(self, repo_path: str, max_files: int = 20) -> Dict[str, Any]:
        """저장소 전체 요약 (다국어 지원)"""
        try:
            repo_path = Path(repo_path)
            target_files = []

            # 파일 검색
            for root, dirs, files in os.walk(repo_path):
                # 불필요한 디렉토리 제외
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'venv', 'node_modules', 'dist', 'build', '.git'}]
                for file in files:
                    if Path(file).suffix in self.valid_exts:
                        target_files.append(Path(root) / file)

            # 파일 수 제한
            target_files = target_files[:max_files]
            file_summaries = []

            logger.info(f"Summarizing {len(target_files)} files in {repo_path}")

            for file_path in target_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()

                    # 상대 경로 ID
                    code_id = str(file_path.relative_to(repo_path)).replace("\\", "/")

                    # API 호출 (토큰 제한 고려하여 2000자 제한)
                    summary_text = self._generate_summary(code[:2000], self.model_id)

                    file_summaries.append({
                        "code_id": code_id,
                        "text": summary_text,
                        "level": "file",
                        "model": "api"
                    })
                except Exception as e:
                    logger.warning(f"Failed to summarize {file_path}: {e}")

            return {
                "summary": f"Analyzed {len(file_summaries)} files.",
                "file_summaries": file_summaries,
                "statistics": {"total_files": len(target_files)}
            }
        except Exception as e:
            logger.error(f"Repo summary failed: {e}")
            return {"error": str(e)}

    def _generate_summary(self, code: str, model_id: str) -> str:
        """HF API 호출"""
        prompt = f"Summarize the following code's functionality in one sentence:\n\n{code}"
        try:
            response = self.client.text_generation(
                prompt,
                model=model_id,
                max_new_tokens=100,
                temperature=0.2,
                do_sample=False
            )
            return response.strip()
        except Exception as e:
            logger.error(f"HF API Error: {e}")
            return "Summary generation failed."

def create_summarizer(device: Optional[str] = None) -> CodeSummarizer:
    return CodeSummarizer(device=device)
