# MCP Repository Analysis - 저장소 분석 마이크로서비스

## 📋 개요

**Repository Analysis MCP**는 전체 저장소를 분석하여 그래프 생성에 필요한 메타데이터를 생성합니다.

- **포트:** 9004 (FastAPI)
- **역할:** "The Architect" - 문맥 이해 및 정보 주입
- **출력:** 도메인 태그, 계층 정보, 논리적 엣지, 프로젝트 설명

---

## 🎯 핵심 역할

### Context Injection Pipeline

```
Phase 1: 기초 데이터 수집 (Summarization + Structural Analysis + Embedding)
    ↓
Phase 2: **Repository Analysis** ← YOU ARE HERE
    ├─ 도메인 태깅 (각 파일의 역할 분류)
    ├─ 계층 판단 (Service/Model/View/Controller 등)
    ├─ 논리적 엣지 발견 (물리적 연결 없는 의도적 연결)
    └─ 프로젝트 문맥 파악 (전체 설명서)
    ↓
Phase 3: Graph Visualization (Graph Analysis MCP)
    - 색상 결정 (도메인 태그 사용)
    - 레이아웃 결정 (계층 정보 사용)
    - 중요도 가중치 (논리적 엣지 반영)
```

---

## 📂 파일 구조

```
mcp/repository_analysis/
├── main.py                 # FastAPI 서버 및 엔드포인트 ✅
├── analyzer.py             # RepositoryAnalyzer 클래스 ⚠️ (불완전)
├── models_loader.py        # 모델 풀 (RepoCoder) 📝
├── requirements.txt        # 의존성 ✅
├── Dockerfile              # 컨테이너 빌드 ✅
└── README.md               # 이 문서
```

---

## ⚙️ 구현 상태 및 필요 작업

### ⚠️ 긴급 필요 작업

#### **Task 1: `analyzer.py` - `analyze()` 메서드 완성**

**파일:** `mcp/repository_analysis/analyzer.py`

**필요 반환 구조:**

```python
def analyze(self, repo_path: str, summaries: list, vectors: list) -> dict:
    """
    저장소 전체 분석 및 메타데이터 생성

    Args:
        repo_path: 저장소 경로
        summaries: [{"file_id": "...", "summary": "..."}]
        vectors: [{"file_id": "...", "embedding": [...]}]

    Returns:
    {
        "file_metadata": {
            "auth_service.py": {
                "domain_tag": "Security",           # 그래프 색상 결정
                "layer": "Service",                 # 레이아웃 그룹
                "importance_hint": "High",          # GNN 입력
                "description": "User authentication service"
            },
            "db_model.py": {
                "domain_tag": "Database",
                "layer": "Model",
                "importance_hint": "Critical",
                "description": "Database models and ORM"
            }
        },
        "logical_edges": [
            {
                "source": "auth_service.py",
                "target": "user_log.py",
                "type": "logical",
                "reason": "Authentication events are logged"
            }
        ],
        "project_summary": "This is a Flask-based REST API backend...",
        "architecture_style": "MVC",
        "primary_language": "Python"
    }
    """

    # 구현 단계:
    # 1. 모든 파일 순회
    # 2. 각 파일의 도메인 태깅 (규칙 기반 + LLM 기반)
    # 3. 각 파일의 계층 판단 (아키텍처 패턴 분석)
    # 4. 논리적 엣지 발견 (문맥 및 벡터 유사도 사용)
    # 5. 프로젝트 문서 생성
```

**상세 구현:**

```python
def analyze(self, repo_path: str, summaries: list, vectors: list) -> dict:
    """저장소 분석"""
    file_metadata = {}
    logical_edges = []
    all_files = self._get_all_files(repo_path)

    # 1️⃣ 파일 메타데이터 생성
    for file_path in all_files:
        file_name = os.path.basename(file_path)
        file_rel = os.path.relpath(file_path, repo_path)

        # 요약 정보 찾기
        summary = next((s for s in summaries if s.get("file_id") == file_name), None)
        embedding = next((v for v in vectors if v.get("file_id") == file_name), None)

        # 도메인 태깅
        domain_tag = self._tag_domain(file_name, file_path, summary)

        # 계층 판단
        layer = self._detect_layer(file_name, file_path, summary)

        # 중요도 계산
        importance = self._calculate_importance(file_name, file_path, summary)

        # 설명 생성
        description = summary.get("summary", "") if summary else "No description"

        file_metadata[file_rel] = {
            "domain_tag": domain_tag,
            "layer": layer,
            "importance_hint": importance,
            "description": description
        }

    # 2️⃣ 논리적 엣지 발견
    logical_edges = self._find_logical_edges(file_metadata, summaries, vectors)

    # 3️⃣ 프로젝트 요약 생성
    project_summary = self._generate_project_summary(repo_path, file_metadata)

    # 4️⃣ 아키텍처 스타일 감지
    arch_style = self._detect_architecture(file_metadata)

    # 5️⃣ 주 언어 감지
    primary_lang = self._detect_primary_language(all_files)

    return {
        "file_metadata": file_metadata,
        "logical_edges": logical_edges,
        "project_summary": project_summary,
        "architecture_style": arch_style,
        "primary_language": primary_lang
    }

# ============ 헬퍼 메서드들 ============

def _tag_domain(self, file_name: str, file_path: str, summary: dict) -> str:
    """
    파일의 도메인 태깅 (규칙 기반)
    """
    keywords = {
        "Security": ["auth", "security", "token", "jwt", "password", "encrypt"],
        "Database": ["model", "database", "db", "orm", "schema"],
        "API": ["api", "endpoint", "route", "controller", "view", "handler"],
        "Testing": ["test", "spec", "mock"],
        "Configuration": ["config", "setting", "env", "constants"],
        "Utils": ["util", "helper", "common", "base", "abstract"]
    }

    # 파일명 기반 검사
    file_lower = file_name.lower()
    for domain, keywords_list in keywords.items():
        if any(kw in file_lower for kw in keywords_list):
            return domain

    # 요약 내용 기반 검사
    if summary:
        summary_lower = summary.get("summary", "").lower()
        for domain, keywords_list in keywords.items():
            if any(kw in summary_lower for kw in keywords_list):
                return domain

    return "General"

def _detect_layer(self, file_name: str, file_path: str, summary: dict) -> str:
    """
    파일의 아키텍처 계층 판단
    """
    file_lower = file_name.lower()
    path_lower = file_path.lower()

    # 경로 기반 판단
    if "service" in path_lower or "services" in path_lower:
        return "Service"
    elif "model" in path_lower or "models" in path_lower:
        return "Model"
    elif "view" in path_lower or "views" in path_lower:
        return "View"
    elif "controller" in path_lower or "controllers" in path_lower:
        return "Controller"
    elif "repository" in path_lower or "repositories" in path_lower:
        return "Repository"
    elif "util" in path_lower or "utils" in path_lower:
        return "Util"
    elif "test" in path_lower or "tests" in path_lower:
        return "Test"

    # 파일명 기반 판단
    if file_lower.endswith("service.py"):
        return "Service"
    elif file_lower.endswith("model.py"):
        return "Model"
    elif file_lower.endswith("view.py"):
        return "View"
    elif file_lower.endswith("controller.py"):
        return "Controller"

    return "Unknown"

def _calculate_importance(self, file_name: str, file_path: str, summary: dict) -> str:
    """
    파일의 중요도 계산
    """
    importance_score = 0

    # 경로 깊이 (루트에 가까울수록 중요)
    depth = file_path.count(os.sep)
    if depth < 2:
        importance_score += 2
    elif depth < 4:
        importance_score += 1

    # 파일명 길이 (일반적으로 더 짧은 이름이 코어 모듈)
    if len(file_name) < 15:
        importance_score += 1

    # 요약 내용의 길이 (더 자세한 설명 = 더 중요)
    if summary and len(summary.get("summary", "")) > 100:
        importance_score += 1

    # 특별 파일
    if file_name in ["__init__.py", "main.py", "app.py", "settings.py"]:
        importance_score += 2

    if importance_score >= 4:
        return "Critical"
    elif importance_score >= 2:
        return "High"
    else:
        return "Normal"

def _find_logical_edges(self, file_metadata: dict, summaries: list, vectors: list) -> list:
    """
    물리적 연결 없이 논리적으로 연결된 엣지 발견
    """
    logical_edges = []

    # 의미론적 유사도로 암묵적 관계 발견
    for i, file1 in enumerate(list(file_metadata.keys())):
        for file2 in list(file_metadata.keys())[i+1:]:
            # 벡터 유사도 계산
            vec1 = next((v for v in vectors if v.get("file_id") == file1), None)
            vec2 = next((v for v in vectors if v.get("file_id") == file2), None)

            if vec1 and vec2:
                similarity = self._cosine_similarity(vec1["embedding"], vec2["embedding"])

                # 높은 유사도 but 같은 도메인
                if similarity > 0.7 and file_metadata[file1]["domain_tag"] == file_metadata[file2]["domain_tag"]:
                    logical_edges.append({
                        "source": file1,
                        "target": file2,
                        "type": "logical",
                        "reason": f"Semantically similar ({similarity:.2f})",
                        "strength": min(1.0, similarity)
                    })

                # 다른 도메인이지만 높은 유사도
                elif similarity > 0.8:
                    logical_edges.append({
                        "source": file1,
                        "target": file2,
                        "type": "logical",
                        "reason": f"Cross-domain collaboration ({similarity:.2f})",
                        "strength": similarity
                    })

    return logical_edges

def _generate_project_summary(self, repo_path: str, file_metadata: dict) -> str:
    """
    프로젝트 전체 요약 생성
    """
    # 도메인 통계
    domains = {}
    for meta in file_metadata.values():
        domain = meta["domain_tag"]
        domains[domain] = domains.get(domain, 0) + 1

    # 계층 통계
    layers = {}
    for meta in file_metadata.values():
        layer = meta["layer"]
        layers[layer] = layers.get(layer, 0) + 1

    # 요약 생성
    summary_parts = []

    # 기본 정보
    summary_parts.append(f"Project with {len(file_metadata)} files organized in {len(layers)} layers.")

    # 도메인 설명
    domain_str = ", ".join([f"{d} ({c})" for d, c in sorted(domains.items(), key=lambda x: -x[1])[:3]])
    summary_parts.append(f"Primary domains: {domain_str}.")

    # 아키텍처 설명
    layer_str = ", ".join([f"{l} ({c})" for l, c in sorted(layers.items(), key=lambda x: -x[1])[:3]])
    summary_parts.append(f"Architecture layers: {layer_str}.")

    return " ".join(summary_parts)

def _detect_architecture(self, file_metadata: dict) -> str:
    """
    아키텍처 패턴 감지 (MVC, MVVM, Clean, Layered 등)
    """
    layers = {}
    for meta in file_metadata.values():
        layer = meta["layer"]
        layers[layer] = layers.get(layer, 0) + 1

    # 패턴 인식
    if "Model" in layers and "View" in layers and "Controller" in layers:
        return "MVC"
    elif "Repository" in layers and "Service" in layers and "Controller" in layers:
        return "Layered"
    elif all(l in layers for l in ["Model", "View", "ViewModel"]):
        return "MVVM"
    else:
        return "Unknown"

def _detect_primary_language(self, files: list) -> str:
    """
    주 프로그래밍 언어 감지
    """
    extensions = {}
    for file_path in files:
        ext = os.path.splitext(file_path)[1]
        extensions[ext] = extensions.get(ext, 0) + 1

    if not extensions:
        return "Unknown"

    most_common = max(extensions.items(), key=lambda x: x[1])
    ext_to_lang = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".cpp": "C++",
        ".cs": "C#"
    }

    return ext_to_lang.get(most_common[0], "Mixed")

def _cosine_similarity(self, vec1: list, vec2: list) -> float:
    """코사인 유사도 계산"""
    from scipy.spatial.distance import cosine
    return 1 - cosine(vec1, vec2)

def _get_all_files(self, repo_path: str) -> list:
    """저장소의 모든 파일 반환"""
    all_files = []
    for root, dirs, files in os.walk(repo_path):
        # .git, __pycache__ 등 무시
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.env']]
        for file in files:
            if not file.startswith('.'):
                all_files.append(os.path.join(root, file))
    return all_files
```

---

## 📡 API 엔드포인트

### 1. 저장소 분석

```bash
POST /analyze

{
  "repo_path": "/path/to/repo",
  "summaries": [
    {"file_id": "auth_service.py", "summary": "..."},
    {"file_id": "db_model.py", "summary": "..."}
  ],
  "vectors": [
    {"file_id": "auth_service.py", "embedding": [0.1, -0.2, ...]},
    {"file_id": "db_model.py", "embedding": [0.3, -0.4, ...]}
  ]
}

Response:
{
  "file_metadata": {
    "auth_service.py": {
      "domain_tag": "Security",
      "layer": "Service",
      "importance_hint": "Critical",
      "description": "User authentication service"
    }
  },
  "logical_edges": [
    {
      "source": "auth_service.py",
      "target": "user_log.py",
      "type": "logical",
      "reason": "Authentication events trigger logging"
    }
  ],
  "project_summary": "Django REST API with 45 files...",
  "architecture_style": "Layered",
  "primary_language": "Python"
}
```

---

## 🚀 실행 방법

```bash
cd mcp/repository_analysis
pip install -r requirements.txt
python -m uvicorn main:app --port 9004 --reload
```

---

## 📝 개발 체크리스트

- [ ] `_tag_domain()` 구현 (규칙 기반)
- [ ] `_detect_layer()` 구현 (계층 판단)
- [ ] `_calculate_importance()` 구현
- [ ] `_find_logical_edges()` 구현
- [ ] `_generate_project_summary()` 구현
- [ ] `_detect_architecture()` 구현
- [ ] `_detect_primary_language()` 구현
- [ ] 로컬 테스트
- [ ] Docker 빌드

---

**참고:** 자세한 내용은 `IMPLEMENTATION_STATUS.md` → Task 5를 참조하세요.