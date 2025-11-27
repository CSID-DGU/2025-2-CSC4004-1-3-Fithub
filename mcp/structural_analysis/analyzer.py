"""
mcp/structural_analysis/analyzer.py
Multi-language Structural Analysis using Robust Regex Patterns.
Supports: Python, JavaScript, TypeScript, Java, Go, C++
"""
import logging
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class LanguageConfig:
    """
    언어별 파싱 규칙 정의 (Regex Patterns)
    Tree-sitter 없이도 주요 구조를 추출하기 위한 경량화된 접근법입니다.
    """
    PATTERNS = {
        ".py": {
            "name": "Python",
            "function": r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            "class": r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]",
            "import": r"^(?:import|from)\s+([a-zA-Z0-9_\.]+)"
        },
        ".js": {
            "name": "JavaScript",
            "function": r"(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(|([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{)",
            "class": r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            "import": r"(?:import\s+.*?from\s+['\"](.*?)['\"]|require\(['\"](.*?)['\"]\))"
        },
        ".ts": {
            "name": "TypeScript",
            "function": r"(?:function\s+([a-zA-Z0-9_]+)|const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?\(|([a-zA-Z0-9_]+)\s*\(.*?\)\s*[:\{])",
            "class": r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            "import": r"(?:import\s+.*?from\s+['\"](.*?)['\"]|require\(['\"](.*?)['\"]\))"
        },
        ".java": {
            "name": "Java",
            "function": r"(?:public|protected|private|static|\s) +[\w\<\>\[\]]+\s+([a-zA-Z0-9_]+)\s*\(",
            "class": r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
            "import": r"import\s+([a-zA-Z0-9_\.]+);"
        },
        ".go": {
            "name": "Go",
            "function": r"func\s+([a-zA-Z0-9_]+)\s*\(",
            "class": r"type\s+([a-zA-Z0-9_]+)\s+struct",
            "import": r"import\s+[\"\(](.*?)[\"\)]"
        },
        ".cpp": {
            "name": "C++",
            "function": r"\w+\s+([a-zA-Z0-9_]+)\s*\(",
            "class": r"class\s+([a-zA-Z0-9_]+)",
            "import": r"#include\s+[<\"](.*?)[>\"]"
        }
    }

    @staticmethod
    def get_config(ext: str):
        return LanguageConfig.PATTERNS.get(ext)

class PolyglotParser:
    """다국어 지원 정규식 파서"""
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.config = LanguageConfig.get_config(self.file_path.suffix)
        self.content = ""

        if self.config:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    self.content = f.read()
            except Exception:
                self.content = ""

    def parse(self, file_id: str) -> Dict[str, List[Dict]]:
        """노드(함수/클래스)와 엣지(Import/Define) 추출"""
        if not self.config or not self.content:
            return {"nodes": [], "edges": []}

        nodes = []
        edges = []

        # 1. 함수 추출 (Function Definitions)
        # 정규식은 여러 그룹 중 매칭된 하나를 찾아야 함
        for match in re.finditer(self.config["function"], self.content, re.MULTILINE):
            func_name = next((g for g in match.groups() if g), "unknown")
            func_node_id = f"{file_id}::{func_name}"

            nodes.append({
                "id": func_node_id,
                "type": "function",
                "label": func_name,
                "language": self.config["name"]
            })

            # File defines Function (Contains)
            edges.append({
                "source": file_id,
                "target": func_node_id,
                "relation": "defines"
            })

        # 2. 클래스 추출 (Class Definitions)
        for match in re.finditer(self.config["class"], self.content, re.MULTILINE):
            class_name = next((g for g in match.groups() if g), "unknown")
            class_node_id = f"{file_id}::{class_name}"

            nodes.append({
                "id": class_node_id,
                "type": "class",
                "label": class_name,
                "language": self.config["name"]
            })
            edges.append({
                "source": file_id,
                "target": class_node_id,
                "relation": "defines"
            })

        # 3. Import 추출 (Dependencies)
        seen_imports = set()
        for match in re.finditer(self.config["import"], self.content, re.MULTILINE):
            imp = next((g for g in match.groups() if g), None)

            if imp and imp not in seen_imports:
                seen_imports.add(imp)

                # Import 타겟 ID 생성 (단순화: 경로/확장자 추론은 어려우므로 모듈명 사용)
                # 예: import utils -> utils.py (추정)
                target_hint = imp.split('.')[-1] + self.file_path.suffix

                edges.append({
                    "source": file_id,
                    "target": target_hint, # 나중에 그래프 단계에서 실제 파일 ID와 매칭 시도
                    "relation": "imports"
                })

        return {"nodes": nodes, "edges": edges}

class StructuralAnalyzer:
    def __init__(self, device=None):
        # Lite 모드: 모델 로드 없음
        pass

    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        저장소 내의 지원되는 모든 언어 파일을 분석합니다.
        """
        try:
            repo_path = Path(repo_path)
            all_nodes = []
            all_edges = []

            # 지원하는 확장자 목록
            valid_exts = set(LanguageConfig.PATTERNS.keys())

            # 1. 파일 검색 (Git, node_modules 등 제외)
            target_files = [
                p for p in repo_path.rglob("*")
                if p.suffix in valid_exts and not any(x in p.parts for x in ["node_modules", ".git", "venv", "dist", "build"])
            ]

            logger.info(f"Analyzing structure for {len(target_files)} files...")

            for file_path in target_files:
                try:
                    # ID 생성 (상대 경로, Windows 역슬래시 처리)
                    rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
                    file_id = rel_path

                    # 2. 파일 노드 추가
                    all_nodes.append({
                        "id": file_id,
                        "type": "file",
                        "label": file_path.name,
                        "language": LanguageConfig.get_config(file_path.suffix)["name"]
                    })

                    # 3. 내부 구조 파싱 (Polyglot Parser)
                    parser = PolyglotParser(str(file_path))
                    result = parser.parse(file_id)

                    all_nodes.extend(result["nodes"])
                    all_edges.extend(result["edges"])

                except Exception as e:
                    logger.warning(f"Parse error {file_path.name}: {e}")

            return {
                "nodes": all_nodes,
                "edges": all_edges,
                "statistics": {"total_files": len(target_files)}
            }

        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            return {"nodes": [], "edges": []}

def create_analyzer(device=None):
    return StructuralAnalyzer(device)
