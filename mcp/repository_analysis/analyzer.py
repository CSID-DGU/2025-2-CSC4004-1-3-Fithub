"""Core repository analysis logic."""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from shared.git_utils import get_repository_info, list_files
from shared.ast_utils import analyze_repository
from .models_loader import get_model_pool

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """저장소 분석 엔진."""

    def __init__(self, device: Optional[str] = None):
        self.model_pool = get_model_pool(device=device)
        self.device = device or "cpu"

    def analyze(self, repo_path: str) -> Dict[str, Any]:
        """
        저장소를 분석합니다.

        Args:
            repo_path: 저장소 경로

        Returns:
            저장소 분석 결과
        """
        try:
            repo_path = Path(repo_path)

            # 저장소 정보
            repo_info = get_repository_info(str(repo_path))

            # AST 분석
            ast_analysis = analyze_repository(str(repo_path))

            # 파일 목록
            py_files = list_files(str(repo_path), extensions=[".py"])

            # 통계
            statistics = {
                "total_files": len(py_files),
                "total_lines": ast_analysis["statistics"]["total_lines"],
                "languages": ast_analysis["statistics"]["languages"],
                "functions": sum(
                    len(f.get("functions", {}))
                    for f in ast_analysis["files"].values()
                ),
                "classes": sum(
                    len(f.get("classes", {}))
                    for f in ast_analysis["files"].values()
                ),
            }

            # 저장소 전체 요약
            overview = self._generate_overview(repo_path.name, statistics)

            return {
                "repository": str(repo_path),
                "repository_info": repo_info,
                "overview": overview,
                "statistics": statistics,
                "files": list(ast_analysis["files"].keys()),
                "structure": self._extract_structure(ast_analysis),
            }

        except Exception as e:
            logger.error(f"Failed to analyze repository {repo_path}: {e}")
            return {
                "repository": str(repo_path),
                "error": str(e),
                "overview": "",
                "statistics": {},
            }

    def _generate_overview(self, repo_name: str, stats: Dict) -> str:
        """저장소 개요를 생성합니다."""
        overview = f"Repository: {repo_name}\n"
        overview += f"Total Files: {stats.get('total_files', 0)}\n"
        overview += f"Total Lines: {stats.get('total_lines', 0)}\n"
        overview += f"Functions: {stats.get('functions', 0)}\n"
        overview += f"Classes: {stats.get('classes', 0)}\n"

        if "languages" in stats:
            overview += "Languages: "
            langs = ", ".join(f"{k}({v})" for k, v in stats["languages"].items())
            overview += langs

        return overview

    def _extract_structure(self, ast_analysis: Dict) -> Dict[str, Any]:
        """저장소 구조를 추출합니다."""
        structure = {
            "modules": {},
            "main_files": [],
        }

        for file_path, file_info in ast_analysis["files"].items():
            if file_info.get("functions") or file_info.get("classes"):
                structure["modules"][file_path] = {
                    "functions": len(file_info.get("functions", {})),
                    "classes": len(file_info.get("classes", {})),
                }

        # 주요 파일 추출 (함수/클래스가 많은 파일)
        main_files = sorted(
            structure["modules"].items(),
            key=lambda x: x[1]["functions"] + x[1]["classes"],
            reverse=True
        )[:5]

        structure["main_files"] = [f[0] for f in main_files]

        return structure


def create_analyzer(device: Optional[str] = None) -> RepositoryAnalyzer:
    """분석기를 생성합니다."""
    return RepositoryAnalyzer(device=device)
