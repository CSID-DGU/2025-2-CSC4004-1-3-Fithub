"""
mcp/structural_analysis/analyzer.py
Graph-based structural analysis using Python AST and NetworkX.
Local model integration for AWS deployment.
"""
import logging
import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx
from collections import defaultdict

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

class CallGraphVisitor(ast.NodeVisitor):
    """
    AST를 순회하며 함수 호출 관계를 추출합니다.
    """
    def __init__(self, file_id: str, file_path: str):
        self.file_id = file_id
        self.file_path = file_path
        self.current_scope = None  # 현재 함수/클래스 scope
        self.calls = []  # (caller, callee) 튜플
        self.functions = {}  # function_id -> metadata

    def visit_FunctionDef(self, node):
        func_id = f"{self.file_id}::{node.name}"
        old_scope = self.current_scope
        self.current_scope = func_id

        # 함수 메타데이터 저장
        self.functions[func_id] = {
            "type": "function",
            "file": self.file_path,
            "lineno": node.lineno,
            "complexity": len(node.body)
        }

        # 함수 body 순회
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_ClassDef(self, node):
        class_id = f"{self.file_id}::{node.name}"
        old_scope = self.current_scope
        self.current_scope = class_id

        # 클래스 메타데이터 저장
        self.functions[class_id] = {
            "type": "class",
            "file": self.file_path,
            "lineno": node.lineno
        }

        # 클래스 body 순회
        self.generic_visit(node)
        self.current_scope = old_scope

    def visit_Call(self, node):
        """함수 호출 감지"""
        if self.current_scope is None:
            self.generic_visit(node)
            return

        # 호출되는 함수 이름 추출
        callee = None
        if isinstance(node.func, ast.Name):
            callee = node.func.id
        elif isinstance(node.func, ast.Attribute):
            callee = node.func.attr

        if callee:
            # 간단한 추론: 같은 파일 내 함수면 직접 링크
            full_callee = f"{self.file_id}::{callee}"
            self.calls.append((self.current_scope, full_callee))

        self.generic_visit(node)


class StructuralAnalyzer:
    def __init__(self, device: Optional[str] = None):
        self.device = device
        self.model_pool = None
        self._models_initialized = False

    def initialize_models(self) -> None:
        """
        로컬 모델들을 초기화합니다.
        AWS 배포 시 서비스 시작 때 호출됨.
        """
        if self._models_initialized:
            return

        try:
            # 동적 import로 모델 로더 로드
            from .models_loader import get_model_pool
            self.model_pool = get_model_pool(device=self.device)
            self._models_initialized = True
            logger.info("✓ StructuralAnalyzer models initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize models: {e}. Continuing without model-based analysis.")
            self._models_initialized = False

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        단일 파일의 구조를 분석합니다.

        Returns:
            파일 내 함수/클래스/의존성 정보
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                return {"nodes": [], "edges": [], "error": f"File not found: {file_path}"}

            file_id = file_path.name

            # 파일 노드
            nodes = [{
                "id": file_id,
                "type": "file",
                "label": file_path.name
            }]

            # 파일 읽기 및 파싱
            with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
                source = f.read()

            tree = ast.parse(source)

            # AST 방문
            visitor = DependencyVisitor(file_id)
            visitor.visit(tree)

            nodes.extend(visitor.nodes)
            edges = visitor.edges

            return {
                "nodes": nodes,
                "edges": edges,
                "statistics": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges)
                }
            }

        except Exception as e:
            logger.error(f"File analysis failed for {file_path}: {e}")
            return {"nodes": [], "edges": [], "error": str(e)}

    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        저장소 전체 구조를 분석합니다.
        AST 기반으로 노드/엣지 추출
        """
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

    def build_call_graph(self, repo_path: str) -> nx.DiGraph:
        """
        저장소의 함수 호출 그래프를 생성합니다.
        NetworkX 기반으로 호출 관계를 나타내는 방향성 그래프를 반환합니다.

        Returns:
            NetworkX DiGraph (함수 호출 관계)
        """
        try:
            repo_path = Path(repo_path)
            graph = nx.DiGraph()

            # 모든 Python 파일 순회
            py_files = [
                p for p in repo_path.rglob("*.py")
                if not any(part.startswith(".") or part == "venv" for part in p.parts)
            ]

            for py_file in py_files:
                try:
                    rel_path = str(py_file.relative_to(repo_path))
                    file_id = rel_path.replace("\\", "/")

                    with open(py_file, "r", encoding="utf-8", errors='ignore') as f:
                        source = f.read()

                    tree = ast.parse(source)

                    # 호출 그래프 방문자
                    call_visitor = CallGraphVisitor(file_id, str(py_file))
                    call_visitor.visit(tree)

                    # 함수/클래스를 노드로 추가
                    for func_id, metadata in call_visitor.functions.items():
                        graph.add_node(func_id, **metadata)

                    # 호출 관계를 엣지로 추가
                    for caller, callee in call_visitor.calls:
                        if callee in call_visitor.functions:
                            graph.add_edge(caller, callee, relation="calls")

                except SyntaxError:
                    logger.warning(f"Syntax Error parsing {py_file}")
                except Exception as e:
                    logger.warning(f"Failed to build call graph for {py_file}: {e}")

            logger.info(f"Built call graph with {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
            return graph

        except Exception as e:
            logger.error(f"Call graph generation failed: {e}")
            return nx.DiGraph()

def create_analyzer(device: Optional[str] = None) -> StructuralAnalyzer:
    return StructuralAnalyzer(device=device)
