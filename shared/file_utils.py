"""
shared/file_utils.py
File system utilities for repository processing.
"""
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def list_files(
    repo_path: str,
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None
) -> List[str]:
    """
    저장소의 파일 목록을 가져옵니다.
    """
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", ".venv", "venv", "node_modules"]

    files = []
    repo_path = Path(repo_path)

    for file_path in repo_path.rglob("*"):
        if file_path.is_file():
            if any(excl in file_path.parts for excl in exclude_dirs):
                continue

            if extensions:
                if file_path.suffix not in extensions:
                    continue

            files.append(str(file_path))

    return sorted(files)

def cleanup_directory(path: str) -> None:
    """디렉토리를 삭제합니다."""
    try:
        p = Path(path)
        if p.exists():
            shutil.rmtree(p)
            logger.info(f"Cleaned up: {path}")
    except Exception as e:
        logger.error(f"Failed to cleanup {path}: {e}")
