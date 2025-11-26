# MCP Structural Analysis - 구조 분석 마이크로서비스

## 📋 개요

**Structural Analysis MCP**는 AST(Abstract Syntax Tree) 파싱을 통해 코드의 구조를 분석합니다.

- **포트:** 9002 (FastAPI)
- **기술:** Tree-sitter, AST 파싱, 호출 그래프 분석
- **출력:** 노드(함수/클래스)와 엣지(관계) 그래프

---

## 🎯 목표

| 분석 항목 | 설명 | 출력 |
|---------|------|------|
| **노드 추출** | 함수, 클래스, 변수 | `{"nodes": [{"id": "auth_fn", "type": "function"}]}` |
| **엣지 관계** | 임포트, 호출, 상속, 사용 | `{"edges": [{"source": "A", "target": "B", "type": "calls"}]}` |
| **호출 그래프** | 함수 간 호출 관계 | 시각화용 DAG (Directed Acyclic Graph) |
| **의존성 그래프** | 파일 간 의존성 | 모듈 구조 파악 |

---

## 📂 파일 구조

```
mcp/structural_analysis/
├── main.py                 # FastAPI 서버 및 엔드포인트 ✅
├── analyzer.py             # StructuralAnalyzer 클래스 ⚠️
├── models_loader.py        # 모델 풀 (선택사항) 📝
├── requirements.txt        # 의존성 ✅
├── Dockerfile              # 컨테이너 빌드 ✅
└── README.md               # 이 문서
```

---

## ⚙️ 구현 상태 및 필요 작업

### ✅ 완성된 부분

| 파일 | 내용 | 상태 |
|------|------|------|
| `main.py` | 3개 엔드포인트 | ✅ |
| `requirements.txt` | 의존성 정의 | ✅ |
| `Dockerfile` | 컨테이너 빌드 | ✅ |

### ⚠️ 필요한 작업

#### **Task 1: `analyzer.py` - `analyze_repository()` 메서드 완성**

**파일:** `mcp/structural_analysis/analyzer.py`

**현재 상태:** 불완전 (100줄만 구현)

**필요 상태:** 저장소 전체 분석

```python
def analyze_repository(self, repo_path: str) -> dict:
    """
    저장소의 모든 Python 파일을 분석하여 구조 그래프 생성

    Returns:
    {
        "nodes": [
            {
                "id": "auth_service.py",
                "label": "auth_service",
                "type": "file",
                "children": [
                    {
                        "id": "auth_service.py::authenticate_user",
                        "label": "authenticate_user",
                        "type": "function",
                        "metadata": {
                            "start_line": 42,
                            "end_line": 65,
                            "params": ["username", "password"],
                            "returns": "bool"
                        }
                    },
                    {
                        "id": "auth_service.py::User",
                        "label": "User",
                        "type": "class",
                        "metadata": {
                            "start_line": 10,
                            "end_line": 40,
                            "bases": ["BaseModel"],
                            "methods": ["__init__", "validate"]
                        }
                    }
                ]
            }
        ],
        "edges": [
            {
                "source": "auth_service.py",
                "target": "db_model.py",
                "type": "imports",
                "label": "from db_model import User"
            },
            {
                "source": "auth_service.py::authenticate_user",
                "target": "db_model.py::query_user",
                "type": "calls",
                "label": "query_user(username)"
            },
            {
                "source": "auth_service.py::User",
                "target": "pydantic.BaseModel",
                "type": "inherits",
                "label": "class User(BaseModel)"
            }
        ]
    }
    """

    # 구현 단계:
    # 1. repo_path의 모든 Python 파일 찾기
    # 2. 각 파일에 대해 analyze_file() 호출
    # 3. 노드 목록 수집
    # 4. 파일 간 import 분석
    # 5. 함수 간 호출 관계 분석
    # 6. 모든 엣지 수집
    # 7. 그래프 JSON 반환
```

**구현 단계:**

```python
def analyze_repository(self, repo_path: str) -> dict:
    """저장소 분석"""
    all_nodes = []
    all_edges = []
    file_to_exports = {}  # 각 파일의 공개 함수/클래스

    # 1️⃣ 모든 Python 파일 찾기
    python_files = glob.glob(os.path.join(repo_path, "**/*.py"), recursive=True)

    # 2️⃣ 파일별 분석
    for file_path in python_files:
        try:
            file_rel_path = os.path.relpath(file_path, repo_path)
            result = self.analyze_file(file_path)

            # 노드 추가
            file_node = {
                "id": file_rel_path,
                "label": os.path.basename(file_path),
                "type": "file",
                "children": result.get("nodes", [])
            }
            all_nodes.append(file_node)

            # 파일의 공개 심볼 저장
            file_to_exports[file_rel_path] = {
                "functions": [n["id"] for n in result.get("nodes", []) if n["type"] == "function"],
                "classes": [n["id"] for n in result.get("nodes", []) if n["type"] == "class"]
            }

            # 엣지 추가 (파일 내부)
            all_edges.extend(result.get("edges", []))

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    # 3️⃣ 파일 간 import 관계 분석
    for file_path in python_files:
        try:
            file_rel_path = os.path.relpath(file_path, repo_path)
            imports = self._extract_imports(file_path)

            for imported_module in imports:
                # import 문을 파일 경로로 변환
                target_file = self._resolve_import_path(imported_module, repo_path)
                if target_file and target_file != file_rel_path:
                    all_edges.append({
                        "source": file_rel_path,
                        "target": target_file,
                        "type": "imports",
                        "label": f"from {imported_module} import ..."
                    })

        except Exception as e:
            print(f"Error extracting imports from {file_path}: {e}")

    # 4️⃣ 함수 간 호출 관계 분석
    for file_path in python_files:
        try:
            file_rel_path = os.path.relpath(file_path, repo_path)
            calls = self._extract_function_calls(file_path)

            for source_func, target_func_names in calls.items():
                for target_func in target_func_names:
                    # 호출된 함수가 현재 파일의 함수인지 다른 파일인지 확인
                    target_file = self._find_function_in_repo(target_func, file_to_exports, repo_path)
                    if target_file:
                        all_edges.append({
                            "source": f"{file_rel_path}::{source_func}",
                            "target": f"{target_file}::{target_func}",
                            "type": "calls",
                            "label": f"{target_func}()"
                        })

        except Exception as e:
            print(f"Error extracting calls from {file_path}: {e}")

    return {
        "nodes": all_nodes,
        "edges": all_edges,
        "file_count": len(python_files),
        "node_count": sum(len(n.get("children", [])) for n in all_nodes),
        "edge_count": len(all_edges)
    }

# 헬퍼 메서드들

def _extract_imports(self, file_path: str) -> list[str]:
    """파일에서 import 문 추출"""
    imports = []
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return list(set(imports))

def _extract_function_calls(self, file_path: str) -> dict:
    """파일에서 함수 호출 관계 추출"""
    calls = {}  # {함수명: [호출된 함수 목록]}

    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    current_function = "module_level"

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            current_function = node.name
            calls[current_function] = []

            # 함수 내의 모든 호출 찾기
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls[current_function].append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls[current_function].append(child.func.attr)

    return calls

def _resolve_import_path(self, module_name: str, repo_path: str) -> str:
    """import 경로를 파일 경로로 변환"""
    # "db_model" → "db_model.py"
    # "services.auth" → "services/auth.py"

    parts = module_name.split(".")
    potential_path = os.path.join(repo_path, *parts) + ".py"

    if os.path.exists(potential_path):
        return os.path.relpath(potential_path, repo_path)

    # __init__.py 확인
    potential_path = os.path.join(repo_path, *parts, "__init__.py")
    if os.path.exists(potential_path):
        return os.path.relpath(potential_path, repo_path)

    return None

def _find_function_in_repo(self, func_name: str, file_to_exports: dict, repo_path: str) -> str:
    """함수가 정의된 파일 찾기"""
    for file_path, exports in file_to_exports.items():
        if func_name in exports.get("functions", []):
            return file_path
    return None
```

#### **Task 2: 엣지 관계 정교화**

**현재 지원 관계:**
- IMPORTS
- CALLS

**추가 필요 관계:**
```python
# INHERITS: 클래스 상속
# "class User(BaseModel)" → User INHERITS from BaseModel

# USES: 변수 사용
# "user_id: int" → int USES

# DEFINES: 타입 정의
# "class Config" → defines Config

# EXPORTS: 모듈에서 공개
# "__all__ = ['User', 'authenticate']" → module EXPORTS User, authenticate
```

---

## 📡 API 엔드포인트

### 1. 파일 분석

```bash
POST /analyze-file

{
  "file_path": "/path/to/auth_service.py"
}

Response:
{
  "file_id": "auth_service.py",
  "nodes": [
    {
      "id": "auth_service.py::authenticate_user",
      "label": "authenticate_user",
      "type": "function",
      "metadata": {
        "start_line": 42,
        "end_line": 65,
        "params": ["username", "password"],
        "returns": "bool"
      }
    },
    {
      "id": "auth_service.py::User",
      "label": "User",
      "type": "class",
      "metadata": {
        "bases": ["BaseModel"],
        "methods": ["__init__", "validate"]
      }
    }
  ],
  "edges": [
    {
      "source": "auth_service.py::User",
      "target": "pydantic.BaseModel",
      "type": "inherits"
    }
  ]
}
```

### 2. 저장소 분석

```bash
POST /analyze-repository

{
  "repo_path": "/path/to/repo"
}

Response:
{
  "nodes": [
    {
      "id": "auth_service.py",
      "type": "file",
      "children": [...]
    }
  ],
  "edges": [...],
  "file_count": 42,
  "node_count": 256,
  "edge_count": 318
}
```

### 3. 호출 그래프

```bash
POST /call-graph

{
  "repo_path": "/path/to/repo",
  "entry_points": ["main"]  # 시작점
}

Response:
{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "depth": 5,
  "complexity_score": 0.72
}
```

### 4. 헬스 체크

```bash
GET /health

Response:
{
  "status": "healthy"
}
```

---

## 🚀 실행 방법

### 단독 실행 (개발용)

```bash
cd mcp/structural_analysis
pip install -r requirements.txt
python -m uvicorn main:app --port 9002 --reload
```

### Docker 실행

```bash
docker build -t fithub-structural mcp/structural_analysis/
docker run -p 9002:9002 fithub-structural
```

---

## 🧪 테스트

```bash
# 간단한 파일 분석
cat > test_code.py << 'EOF'
class User:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name
EOF

curl -X POST http://localhost:9002/analyze-file \
  -H "Content-Type: application/json" \
  -d "{\"file_path\": \"$(pwd)/test_code.py\"}"
```

---

## 🔗 의존성

```
fastapi==0.104.0
uvicorn==0.24.0
pydantic==2.4.0
tree-sitter==0.20.1
```

---

## 📝 개발 체크리스트

- [ ] `analyze_repository()` 메서드 완성
- [ ] `_extract_imports()` 헬퍼 함수
- [ ] `_extract_function_calls()` 헬퍼 함수
- [ ] `_resolve_import_path()` 헬퍼 함수
- [ ] 엣지 관계 확장 (INHERITS, USES 등)
- [ ] 에러 처리 및 로깅
- [ ] 대형 저장소 성능 테스트
- [ ] Docker 빌드 및 테스트

---

**참고:** 자세한 내용은 `IMPLEMENTATION_STATUS.md` → Task 3-1, 3-2를 참조하세요.