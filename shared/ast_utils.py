"""Abstract Syntax Tree (AST) parsing utilities for code analysis."""
import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import re

logger = logging.getLogger(__name__)


class PythonASTAnalyzer:
    """Python 코드의 AST를 분석합니다."""

    @staticmethod
    def parse_file(file_path: str) -> Optional[ast.Module]:
        """
        Python 파일을 파싱합니다.

        Args:
            file_path: Python 파일 경로

        Returns:
            AST Module 또는 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return None

    @staticmethod
    def extract_functions(tree: ast.Module) -> Dict[str, Dict]:
        """
        함수 정의들을 추출합니다.

        Args:
            tree: AST Module

        Returns:
            함수 정보 딕셔너리
        """
        functions = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node) or "",
                    "calls": PythonASTAnalyzer._extract_calls(node),
                    "decorators": [
                        ast.unparse(dec) if hasattr(ast, 'unparse') else str(dec)
                        for dec in node.decorator_list
                    ],
                }
                functions[node.name] = func_info

        return functions

    @staticmethod
    def extract_classes(tree: ast.Module) -> Dict[str, Dict]:
        """
        클래스 정의들을 추출합니다.

        Args:
            tree: AST Module

        Returns:
            클래스 정보 딕셔너리
        """
        classes = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                    "bases": [
                        ast.unparse(base) if hasattr(ast, 'unparse') else str(base)
                        for base in node.bases
                    ],
                    "docstring": ast.get_docstring(node) or "",
                    "methods": [],
                    "attributes": [],
                }

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info["methods"].append({
                            "name": item.name,
                            "lineno": item.lineno,
                            "args": [arg.arg for arg in item.args.args],
                        })
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                class_info["attributes"].append(target.id)

                classes[node.name] = class_info

        return classes

    @staticmethod
    def extract_imports(tree: ast.Module) -> Dict[str, List[str]]:
        """
        Import 문들을 추출합니다.

        Args:
            tree: AST Module

        Returns:
            import 정보 딕셔너리
        """
        imports = {
            "direct": [],  # import X
            "from": [],    # from X import Y
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports["direct"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports["from"].append(f"{module}.{alias.name}")

        return imports

    @staticmethod
    def extract_call_graph(tree: ast.Module, file_path: str = "") -> Dict[str, Set[str]]:
        """
        함수 호출 그래프를 추출합니다.

        Args:
            tree: AST Module
            file_path: 파일 경로 (ID 생성용)

        Returns:
            호출 그래프 (caller -> [callees])
        """
        graph = {}

        class CallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_func = None
                self.calls = {}

            def visit_FunctionDef(self, node):
                old_func = self.current_func
                self.current_func = node.name
                if node.name not in self.calls:
                    self.calls[node.name] = set()
                self.generic_visit(node)
                self.current_func = old_func

            def visit_Call(self, node):
                if self.current_func:
                    if isinstance(node.func, ast.Name):
                        self.calls[self.current_func].add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            self.calls[self.current_func].add(
                                f"{node.func.value.id}.{node.func.attr}"
                            )
                self.generic_visit(node)

        visitor = CallVisitor()
        visitor.visit(tree)

        return visitor.calls

    @staticmethod
    def _extract_calls(node: ast.FunctionDef) -> List[str]:
        """함수 내에서의 호출들을 추출합니다."""
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        calls.append(f"{child.func.value.id}.{child.func.attr}")

        return list(set(calls))


class JavaASTAnalyzer:
    """Java 코드의 구조를 분석합니다 (정규표현식 기반)."""

    @staticmethod
    def extract_classes(file_path: str) -> List[Dict]:
        """
        Java 클래스를 추출합니다.

        Args:
            file_path: Java 파일 경로

        Returns:
            클래스 정보 목록
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            classes = []

            # public class 또는 class 정의 찾기
            class_pattern = r'(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'

            for match in re.finditer(class_pattern, content):
                class_info = {
                    "name": match.group(1),
                    "extends": match.group(2) if match.group(2) else None,
                    "implements": [i.strip() for i in match.group(3).split(",")] if match.group(3) else [],
                }
                classes.append(class_info)

            return classes

        except Exception as e:
            logger.error(f"Failed to analyze Java file {file_path}: {e}")
            return []

    @staticmethod
    def extract_methods(file_path: str) -> List[Dict]:
        """
        Java 메서드를 추출합니다.

        Args:
            file_path: Java 파일 경로

        Returns:
            메서드 정보 목록
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            methods = []

            # 메서드 정의 찾기
            method_pattern = r'(?:public|private|protected)?\s+(?:static\s+)?(?:synchronized\s+)?(\w+(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)'

            for match in re.finditer(method_pattern, content):
                method_info = {
                    "return_type": match.group(1),
                    "name": match.group(2),
                    "parameters": [p.strip() for p in match.group(3).split(",") if p.strip()],
                }
                methods.append(method_info)

            return methods

        except Exception as e:
            logger.error(f"Failed to extract Java methods from {file_path}: {e}")
            return []


class CodeAnalyzer:
    """다양한 언어의 코드를 분석합니다."""

    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".java": "java",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
    }

    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
        """
        파일을 분석합니다.

        Args:
            file_path: 파일 경로

        Returns:
            분석 결과 딕셔너리
        """
        file_path = Path(file_path)
        extension = file_path.suffix
        language = CodeAnalyzer.LANGUAGE_EXTENSIONS.get(extension, "unknown")

        result = {
            "file": str(file_path),
            "language": language,
            "size": file_path.stat().st_size,
            "lines": 0,
            "functions": {},
            "classes": {},
            "imports": {},
            "call_graph": {},
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            result["lines"] = len(content.split('\n'))
        except:
            return result

        # 언어별 분석
        if language == "python":
            tree = PythonASTAnalyzer.parse_file(str(file_path))
            if tree:
                result["functions"] = PythonASTAnalyzer.extract_functions(tree)
                result["classes"] = PythonASTAnalyzer.extract_classes(tree)
                result["imports"] = PythonASTAnalyzer.extract_imports(tree)
                result["call_graph"] = PythonASTAnalyzer.extract_call_graph(tree)

        elif language == "java":
            result["classes"] = JavaASTAnalyzer.extract_classes(str(file_path))
            result["methods"] = JavaASTAnalyzer.extract_methods(str(file_path))

        # 다른 언어는 확장 가능

        return result


def analyze_repository(
    repo_path: str,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    저장소 전체를 분석합니다.

    Args:
        repo_path: 저장소 경로
        extensions: 분석할 파일 확장자

    Returns:
        저장소 분석 결과
    """
    if extensions is None:
        extensions = [".py", ".java", ".js", ".ts"]

    repo_path = Path(repo_path)
    analysis = {
        "repository": str(repo_path),
        "files": {},
        "statistics": {
            "total_files": 0,
            "total_lines": 0,
            "languages": {},
        }
    }

    for file_path in repo_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in extensions:
            if ".git" not in file_path.parts:
                try:
                    file_analysis = CodeAnalyzer.analyze_file(str(file_path))
                    rel_path = str(file_path.relative_to(repo_path))
                    analysis["files"][rel_path] = file_analysis

                    analysis["statistics"]["total_files"] += 1
                    analysis["statistics"]["total_lines"] += file_analysis["lines"]

                    lang = file_analysis["language"]
                    analysis["statistics"]["languages"][lang] = \
                        analysis["statistics"]["languages"].get(lang, 0) + 1

                except Exception as e:
                    logger.warning(f"Failed to analyze {file_path}: {e}")

    return analysis
