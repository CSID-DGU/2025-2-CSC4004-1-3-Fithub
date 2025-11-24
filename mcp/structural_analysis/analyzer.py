"""
mcp/structural_analysis/analyzer.py
Lightweight structural analysis using Python AST.
"""
import logging
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DependencyVisitor(ast.NodeVisitor):
    """
    AST를 순회하며 함수 정의, 클래스 정의, Import 관계를 추출합니다.
    """
    def __init__(self, file_id: str):
        self.file_id = file_id
        self.nodes = []
        self.edges = []

    def visit_FunctionDef(self, node):
        func_id = f"{self.file_id}::{node.name}"
        self.nodes.append({
            "id": func_id,
            "type": "function",
            "label": node.name,
            "complexity": len(node.body)  # 간단한 복잡도 측정 (Body 길이)
        })
        # 파일이 함수를 정의함 (Contains 관계)
        self.edges.append({
            "source": self.file_id,
            "target": func_id,
            "relation": "defines"
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_id = f"{self.file_id}::{node.name}"
        self.nodes.append({
            "id": class_id,
            "type": "class",
            "label": node.name
        })
        self.edges.append({
            "source": self.file_id,
            "target": class_id,
            "relation": "defines"
        })
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            # 단순화를 위해 모듈명.py를 타겟으로 가정
            target = alias.name.replace(".", "/") + ".py"
            self.edges.append({
                "source": self.file_id,
                "target": target,
                "relation": "imports"
            })

    def visit_ImportFrom(self, node):
        if node.module:
            target = node.module.replace(".", "/") + ".py"
            self.edges.append({
                "source": self.file_id,
                "target": target,
                "relation": "imports"
            })

class StructuralAnalyzer:
    def __init__(self, device: Optional[str] = None):
        pass

    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """Python AST를 사용하여 저장소 구조 분석"""
        try:
            repo_path = Path(repo_path)
            all_nodes = []
            all_edges = []

            # 1. 파일 순회
            py_files = [
                p for p in repo_path.rglob("*.py")
                if not any(part.startswith(".") or part == "venv" for part in p.parts)
            ]

            for py_file in py_files:
                try:
                    rel_path = str(py_file.relative_to(repo_path))
                    # Windows 경로 호환성을 위해 역슬래시 변환
                    file_id = rel_path.replace("\\", "/")

                    # 파일 노드 추가
                    all_nodes.append({
                        "id": file_id,
                        "type": "file",
                        "label": py_file.name
                    })

                    with open(py_file, "r", encoding="utf-8", errors='ignore') as f:
                        source = f.read()

                    tree = ast.parse(source)

                    # 2. AST Visitor로 정보 추출
                    visitor = DependencyVisitor(file_id)
                    visitor.visit(tree)

                    all_nodes.extend(visitor.nodes)
                    all_edges.extend(visitor.edges)

                except SyntaxError:
                    logger.warning(f"Syntax Error parsing {py_file}")
                except Exception as e:
                    logger.warning(f"Failed to parse {py_file}: {e}")

            return {
                "nodes": all_nodes,
                "edges": all_edges,
                "statistics": {"total_files": len(py_files)}
            }

        except Exception as e:
            logger.error(f"Repo analysis failed: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}

def create_analyzer(device: Optional[str] = None) -> StructuralAnalyzer:
    return StructuralAnalyzer(device=device)
