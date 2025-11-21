"""Core structural analysis logic."""
import logging
import torch
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from shared.ast_utils import CodeAnalyzer, PythonASTAnalyzer
from .models_loader import get_model_pool
import networkx as nx

logger = logging.getLogger(__name__)


class StructuralAnalyzer:
    """코드 구조 분석 엔진."""

    def __init__(self, device: Optional[str] = None):
        self.model_pool = get_model_pool(device=device)
        self.analyzer = CodeAnalyzer()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        파일의 구조를 분석합니다.

        Args:
            file_path: 파일 경로

        Returns:
            구조 분석 결과
        """
        try:
            analysis = self.analyzer.analyze_file(file_path)

            # 노드와 엣지 생성
            nodes = self._create_nodes(file_path, analysis)
            edges = self._create_edges(file_path, analysis)

            return {
                "file": file_path,
                "language": analysis["language"],
                "nodes": nodes,
                "edges": edges,
                "statistics": {
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "functions": len(analysis.get("functions", {})),
                    "classes": len(analysis.get("classes", {})),
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return {
                "file": file_path,
                "error": str(e),
                "nodes": [],
                "edges": [],
            }

    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        저장소 전체의 구조를 분석합니다.

        Args:
            repo_path: 저장소 경로

        Returns:
            저장소 구조 분석 결과
        """
        try:
            repo_path = Path(repo_path)

            # 그래프 생성
            graph = nx.DiGraph()

            # 저장소 노드 추가
            repo_id = "repo_root"
            graph.add_node(repo_id, type="repo", label=repo_path.name)

            # 파일 수집 및 분석
            all_nodes = [{"id": repo_id, "type": "repo", "label": repo_path.name}]
            all_edges = []
            file_analyses = {}

            for py_file in repo_path.rglob("*.py"):
                if ".git" in py_file.parts:
                    continue

                try:
                    rel_path = str(py_file.relative_to(repo_path))
                    file_analysis = self.analyze_file(str(py_file))
                    file_analyses[rel_path] = file_analysis

                    # 파일 노드 추가
                    file_id = f"file_{rel_path.replace('/', '_')}"
                    all_nodes.append({
                        "id": file_id,
                        "type": "file",
                        "label": py_file.name,
                        "file_path": rel_path,
                    })

                    # 저장소 -> 파일 엣지
                    all_edges.append({
                        "source": repo_id,
                        "target": file_id,
                        "type": "CONTAINS",
                    })

                    # 파일 내부 노드와 엣지 추가
                    all_nodes.extend(file_analysis.get("nodes", []))
                    all_edges.extend(file_analysis.get("edges", []))

                except Exception as e:
                    logger.warning(f"Failed to analyze {py_file}: {e}")

            return {
                "repository": str(repo_path),
                "nodes": all_nodes,
                "edges": all_edges,
                "files_analyzed": len(file_analyses),
                "statistics": {
                    "total_nodes": len(all_nodes),
                    "total_edges": len(all_edges),
                    "total_files": len(file_analyses),
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze repository {repo_path}: {e}")
            return {
                "repository": str(repo_path),
                "error": str(e),
                "nodes": [],
                "edges": [],
            }

    def _create_nodes(self, file_path: str, analysis: Dict) -> List[Dict[str, Any]]:
        """파일 분석에서 노드를 생성합니다."""
        nodes = []
        file_id = f"file_{Path(file_path).stem}"

        # 파일 노드
        nodes.append({
            "id": file_id,
            "type": "file",
            "label": Path(file_path).name,
            "file_path": file_path,
        })

        # 클래스 노드
        for class_name, class_info in analysis.get("classes", {}).items():
            class_id = f"{file_id}:class:{class_name}"
            nodes.append({
                "id": class_id,
                "type": "class",
                "label": class_name,
                "file_path": file_path,
                "lineno": class_info.get("lineno"),
                "bases": class_info.get("bases", []),
            })

            # 메서드 노드
            for method_info in class_info.get("methods", []):
                method_id = f"{class_id}:method:{method_info['name']}"
                nodes.append({
                    "id": method_id,
                    "type": "function",
                    "label": method_info["name"],
                    "file_path": file_path,
                    "lineno": method_info.get("lineno"),
                    "parent": class_id,
                })

        # 함수 노드
        for func_name, func_info in analysis.get("functions", {}).items():
            func_id = f"{file_id}:function:{func_name}"
            nodes.append({
                "id": func_id,
                "type": "function",
                "label": func_name,
                "file_path": file_path,
                "lineno": func_info.get("lineno"),
                "args": func_info.get("args", []),
            })

        return nodes

    def _create_edges(self, file_path: str, analysis: Dict) -> List[Dict[str, Any]]:
        """파일 분석에서 엣지를 생성합니다."""
        edges = []
        file_id = f"file_{Path(file_path).stem}"

        # 파일 내 상속 관계
        for class_name, class_info in analysis.get("classes", {}).items():
            class_id = f"{file_id}:class:{class_name}"

            for base in class_info.get("bases", []):
                # 기본 상속 엣지 (외부 클래스는 명시하지 않음)
                pass

        # 함수 호출 관계
        call_graph = analysis.get("call_graph", {})
        for caller, callees in call_graph.items():
            caller_id = f"{file_id}:function:{caller}"

            for callee in callees:
                # 같은 파일 내 호출
                callee_id = f"{file_id}:function:{callee}"
                edges.append({
                    "source": caller_id,
                    "target": callee_id,
                    "type": "CALLS",
                    "weight": 1.0,
                })

        return edges

    def build_call_graph(self, repo_path: str) -> nx.DiGraph:
        """
        저장소의 호출 그래프를 생성합니다.

        Args:
            repo_path: 저장소 경로

        Returns:
            NetworkX DiGraph
        """
        graph = nx.DiGraph()

        try:
            repo_path = Path(repo_path)

            for py_file in repo_path.rglob("*.py"):
                if ".git" in py_file.parts:
                    continue

                tree = PythonASTAnalyzer.parse_file(str(py_file))
                if not tree:
                    continue

                call_graph = PythonASTAnalyzer.extract_call_graph(tree)
                rel_path = str(py_file.relative_to(repo_path))

                for func_name, callees in call_graph.items():
                    caller_id = f"{rel_path}:{func_name}"
                    graph.add_node(caller_id, file=rel_path, type="function")

                    for callee in callees:
                        callee_id = f"{rel_path}:{callee}"
                        graph.add_edge(caller_id, callee_id)

        except Exception as e:
            logger.error(f"Failed to build call graph: {e}")

        return graph


def create_analyzer(device: Optional[str] = None) -> StructuralAnalyzer:
    """분석기를 생성합니다."""
    return StructuralAnalyzer(device=device)
