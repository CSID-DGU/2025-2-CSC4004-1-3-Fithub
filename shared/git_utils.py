"""Git repository utilities for cloning and processing."""
import os
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def parse_git_url(url: str) -> Tuple[str, str]:
    """
    Git URL을 파싱하여 owner와 repo를 추출합니다.

    Args:
        url: Git URL (https://github.com/owner/repo 형식)

    Returns:
        (owner, repo) 튜플
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.split("/")
    if len(parts) >= 2:
        return parts[-2], parts[-1]

    raise ValueError(f"Invalid git URL: {url}")


def clone_repository(
    repo_url: str,
    target_dir: Optional[str] = None,
    branch: str = "main",
    depth: Optional[int] = None,
    single_branch: bool = True
) -> str:
    """
    Git 저장소를 클론합니다.

    Args:
        repo_url: 저장소 URL
        target_dir: 클론할 디렉토리 (None이면 temp 사용)
        branch: 클론할 브랜치
        depth: shallow clone depth (None이면 전체)
        single_branch: 단일 브랜치만 클론할지 여부

    Returns:
        클론된 디렉토리 경로
    """
    try:
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix="repo_")

        # 디렉토리 생성
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # git clone 명령 구성
        cmd = ["git", "clone"]

        if depth:
            cmd.extend(["--depth", str(depth)])

        if single_branch:
            cmd.append("--single-branch")

        if branch:
            cmd.extend(["--branch", branch])

        cmd.extend([repo_url, target_dir])

        logger.info(f"Cloning {repo_url} to {target_dir}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")

        logger.info(f"Successfully cloned to {target_dir}")
        return target_dir

    except subprocess.TimeoutExpired:
        logger.error(f"Clone timeout for {repo_url}")
        raise
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        raise


def load_local_repository(repo_path: str) -> str:
    """
    로컬 저장소를 로드합니다 (이미 존재하는 경로).

    Args:
        repo_path: 로컬 저장소 경로

    Returns:
        저장소 절대 경로
    """
    path = Path(repo_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Repository path not found: {repo_path}")

    if not (path / ".git").exists():
        logger.warning(f"Not a git repository: {repo_path}")

    logger.info(f"Loaded local repository: {path}")
    return str(path)


def get_repository_info(repo_path: str) -> Dict[str, str]:
    """
    저장소 정보를 가져옵니다.

    Args:
        repo_path: 저장소 경로

    Returns:
        저장소 정보 딕셔너리
    """
    repo_path = Path(repo_path).resolve()

    info = {
        "path": str(repo_path),
        "name": repo_path.name,
    }

    try:
        # 리모트 URL 가져오기
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            info["url"] = result.stdout.strip()

        # 현재 브랜치 가져오기
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()

        # 현재 커밋 가져오기
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()

    except Exception as e:
        logger.warning(f"Failed to get git info: {e}")

    return info


def cleanup_repository(repo_path: str) -> None:
    """
    클론된 저장소를 정리합니다.

    Args:
        repo_path: 저장소 경로
    """
    try:
        if Path(repo_path).exists():
            logger.info(f"Cleaning up repository: {repo_path}")
            shutil.rmtree(repo_path)
    except Exception as e:
        logger.error(f"Failed to cleanup repository: {e}")


def list_files(
    repo_path: str,
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None
) -> List[str]:
    """
    저장소의 파일 목록을 가져옵니다.

    Args:
        repo_path: 저장소 경로
        extensions: 필터링할 확장자 (None이면 모두)
        exclude_dirs: 제외할 디렉토리 (.git, __pycache__ 등)

    Returns:
        파일 경로 목록
    """
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"]

    files = []
    repo_path = Path(repo_path)

    for file_path in repo_path.rglob("*"):
        if file_path.is_file():
            # 제외 디렉토리 확인
            if any(excl in file_path.parts for excl in exclude_dirs):
                continue

            # 확장자 필터링
            if extensions:
                if file_path.suffix in extensions:
                    files.append(str(file_path))
            else:
                files.append(str(file_path))

    return sorted(files)


def get_file_tree(
    repo_path: str,
    max_depth: int = 10,
    exclude_dirs: Optional[List[str]] = None
) -> Dict:
    """
    저장소의 파일 트리를 구성합니다.

    Args:
        repo_path: 저장소 경로
        max_depth: 최대 깊이
        exclude_dirs: 제외할 디렉토리

    Returns:
        파일 트리 딕셔너리
    """
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"]

    def build_tree(path: Path, depth: int = 0) -> Dict:
        if depth > max_depth:
            return {}

        tree = {
            "name": path.name,
            "type": "dir" if path.is_dir() else "file",
            "path": str(path.relative_to(repo_path)),
        }

        if path.is_dir() and path.name not in exclude_dirs:
            try:
                children = []
                for item in sorted(path.iterdir()):
                    if item.name not in exclude_dirs:
                        children.append(build_tree(item, depth + 1))
                if children:
                    tree["children"] = children
            except PermissionError:
                pass

        return tree

    repo_path = Path(repo_path)
    return build_tree(repo_path)


