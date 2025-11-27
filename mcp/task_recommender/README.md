# MCP Task Recommender - 작업 추천 마이크로서비스

## 📋 개요

**Task Recommender MCP**는 분석된 코드, 그래프, 메타데이터를 기반으로 개선 작업을 추천합니다.

- **포트:** 9005 (FastAPI)
- **역할:** "Action Provider" - 개선 방안 제시
- **출력:** 5가지 카테고리의 우선순위 작업 목록

---

## 🎯 추천 카테고리

| 카테고리 | 목표 | 예시 |
|---------|------|------|
| **복잡도 개선** | 순환 의존성, 순환 참조 제거 | "Refactor circular imports in auth_service ↔ db_model" |
| **의존성 최적화** | 강한 결합도 분리 | "Decouple database from service layer" |
| **품질 향상** | 문서화, 타입 힌트, 명명 규칙 | "Add docstrings to 12 public functions" |
| **구조 개선** | 아키텍처 위반 수정 | "Service layer should not import from view layer" |
| **성능 최적화** | 병목 지점 제거 | "Optimize N+1 query in user_fetch function" |

---

## 📂 파일 구조

```
mcp/task_recommender/
├── main.py                 # FastAPI 서버 및 엔드포인트 ✅
├── recommender.py          # TaskRecommender 클래스 ⚠️ (부분 구현)
├── models_loader.py        # 모델 풀 (CodeT5) 📝
├── requirements.txt        # 의존성 ✅
├── Dockerfile              # 컨테이너 빌드 ✅
└── README.md               # 이 문서
```

---

## ⚙️ 구현 상태 및 필요 작업

### ⚠️ 긴급 필요 작업

#### **Task 1: `recommender.py` - 5개 분석 메서드 완성**

**파일:** `mcp/task_recommender/recommender.py`

```python
def recommend_tasks(self, graph: dict, metadata: dict, summaries: list) -> list[dict]:
    """
    모든 분석 실행 및 작업 추천

    Returns:
    [
        {
            "type": "refactor_circular_dependencies",
            "severity": "high",
            "description": "Circular imports detected between auth_service.py and db_model.py",
            "affected_files": ["auth_service.py", "db_model.py"],
            "effort_estimate": "medium",  # low, medium, high
            "impact_estimate": "high",     # low, medium, high
            "priority_score": 0.92,
            "suggested_actions": [
                "Extract shared interfaces to a separate module",
                "Implement dependency injection pattern",
                "Use type stubs for breaking circular imports"
            ]
        },
        ...
    ]
    """

    # 1️⃣ 복잡도 분석
    complexity_tasks = self._analyze_complexity(graph)

    # 2️⃣ 의존성 분석
    dependency_tasks = self._analyze_dependencies(graph, summaries)

    # 3️⃣ 품질 분석
    quality_tasks = self._analyze_quality(summaries)

    # 4️⃣ 구조 개선 분석
    structure_tasks = self._suggest_structure_improvements(metadata)

    # 5️⃣ 성능 분석
    performance_tasks = self._analyze_performance(graph, summaries)

    # 모든 작업 통합
    all_tasks = (
        complexity_tasks +
        dependency_tasks +
        quality_tasks +
        structure_tasks +
        performance_tasks
    )

    # 우선순위 정렬
    ranked_tasks = self._rank_recommendations(all_tasks)

    return ranked_tasks
```

**각 메서드 구현:**

##### **1️⃣ `_analyze_complexity()` - 복잡도 분석**

```python
def _analyze_complexity(self, graph: dict) -> list[dict]:
    """
    순환 의존성, 순환 참조 탐지

    Returns:
    [
        {
            "type": "refactor_circular_dependencies",
            "severity": "high",
            "affected_files": ["A.py", "B.py"],
            "cycles": [["A.py::func1", "B.py::func2", "A.py::func1"]],
            "effort_estimate": "medium"
        },
        {
            "type": "decompose_large_files",
            "severity": "medium",
            "affected_files": ["services/auth.py"],  # 500+ lines
            "current_lines": 523,
            "effort_estimate": "medium"
        }
    ]
    """

    tasks = []

    # 순환 의존성 탐지
    edges = graph.get("edges", [])
    node_graph = self._build_adjacency_list(edges)
    cycles = self._find_cycles(node_graph)

    if cycles:
        cycle_files = set()
        for cycle in cycles:
            for node in cycle:
                file_name = node.split("::")[0]
                cycle_files.add(file_name)

        tasks.append({
            "type": "refactor_circular_dependencies",
            "severity": "high",
            "description": f"{len(cycles)} circular dependencies detected",
            "affected_files": list(cycle_files),
            "cycles": cycles,
            "effort_estimate": "medium",
            "impact_estimate": "high",
            "suggested_actions": [
                "Use dependency injection to break cycles",
                "Extract shared utilities to separate module",
                "Reorganize package structure"
            ]
        })

    # 대형 파일 분해
    nodes = graph.get("nodes", [])
    for node in nodes:
        if node.get("type") == "file":
            # 파일 크기 계산 (자식 노드 수로 추정)
            child_count = len(node.get("children", []))
            if child_count > 15:  # 15개 이상의 함수/클래스
                tasks.append({
                    "type": "decompose_large_files",
                    "severity": "medium" if child_count < 25 else "high",
                    "description": f"File {node['label']} has {child_count} functions/classes",
                    "affected_files": [node["id"]],
                    "item_count": child_count,
                    "effort_estimate": "high",
                    "impact_estimate": "medium"
                })

    return tasks
```

##### **2️⃣ `_analyze_dependencies()` - 의존성 분석**

```python
def _analyze_dependencies(self, graph: dict, summaries: list) -> list[dict]:
    """
    강한 결합도, 높은 팬인/팬아웃 탐지
    """

    tasks = []
    edges = graph.get("edges", [])

    # 각 노드의 팬인/팬아웃 계산
    fan_in = {}
    fan_out = {}

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        fan_out[source] = fan_out.get(source, 0) + 1
        fan_in[target] = fan_in.get(target, 0) + 1

    # 높은 팬아웃 (많이 의존) 탐지
    high_fanout = {k: v for k, v in fan_out.items() if v > 5}
    if high_fanout:
        for file, count in sorted(high_fanout.items(), key=lambda x: -x[1])[:3]:
            tasks.append({
                "type": "reduce_coupling",
                "severity": "medium",
                "description": f"{file} has high fan-out ({count} dependencies)",
                "affected_files": [file],
                "dependency_count": count,
                "effort_estimate": "high",
                "impact_estimate": "high"
            })

    # 높은 팬인 (많이 의존됨) 탐지
    high_fanin = {k: v for k, v in fan_in.items() if v > 8}
    if high_fanin:
        for file, count in sorted(high_fanin.items(), key=lambda x: -x[1])[:2]:
            tasks.append({
                "type": "stabilize_core_module",
                "severity": "low",
                "description": f"{file} is a core module (used by {count} files)",
                "affected_files": [file],
                "dependents_count": count,
                "effort_estimate": "low",
                "impact_estimate": "high"
            })

    return tasks
```

##### **3️⃣ `_analyze_quality()` - 품질 분석**

```python
def _analyze_quality(self, summaries: list) -> list[dict]:
    """
    문서화, 명명 규칙, 중복 코드 탐지
    """

    tasks = []
    undocumented_count = 0

    for summary in summaries:
        desc = summary.get("summary", "")

        # 문서화 부재 탐지
        if not desc or len(desc) < 20:
            undocumented_count += 1

        # 기술 부채 신호
        if any(word in desc.lower() for word in ["todo", "fixme", "hack", "temporary"]):
            tasks.append({
                "type": "resolve_technical_debt",
                "severity": "medium",
                "description": f"Technical debt marker found in {summary.get('file_id')}",
                "affected_files": [summary.get("file_id")],
                "effort_estimate": "medium"
            })

    # 대량 미문서화
    if undocumented_count > len(summaries) * 0.3:  # 30% 이상
        tasks.append({
            "type": "improve_documentation",
            "severity": "medium",
            "description": f"{undocumented_count} files lack documentation",
            "affected_files_count": undocumented_count,
            "effort_estimate": "high",
            "impact_estimate": "medium"
        })

    return tasks
```

##### **4️⃣ `_suggest_structure_improvements()` - 구조 개선**

```python
def _suggest_structure_improvements(self, metadata: dict) -> list[dict]:
    """
    아키텍처 위반 탐지 (계층 위반 등)
    """

    tasks = []
    file_metadata = metadata.get("file_metadata", {})

    # 계층 규칙 정의
    layer_rules = {
        "View": {"can_import": ["View", "Util"]},
        "Controller": {"can_import": ["Service", "Util"]},
        "Service": {"can_import": ["Model", "Repository", "Util"]},
        "Repository": {"can_import": ["Model", "Util"]},
        "Model": {"can_import": ["Util"]},
        "Util": {"can_import": ["Util"]}
    }

    # 위반 탐지
    logical_edges = metadata.get("logical_edges", [])

    for edge in logical_edges:
        source = edge.get("source")
        target = edge.get("target")

        source_meta = file_metadata.get(source, {})
        target_meta = file_metadata.get(target, {})

        source_layer = source_meta.get("layer")
        target_layer = target_meta.get("layer")

        if source_layer in layer_rules:
            allowed = layer_rules[source_layer].get("can_import", [])
            if target_layer not in allowed:
                tasks.append({
                    "type": "fix_layer_violation",
                    "severity": "high",
                    "description": f"{source_layer} layer should not import {target_layer} layer",
                    "affected_files": [source, target],
                    "violation": f"{source_layer} → {target_layer}",
                    "effort_estimate": "high"
                })

    return tasks
```

##### **5️⃣ `_analyze_performance()` - 성능 분석**

```python
def _analyze_performance(self, graph: dict, summaries: list) -> list[dict]:
    """
    N+1 쿼리, 비효율적 순회 등 성능 문제 탐지
    """

    tasks = []

    for summary in summaries:
        desc = summary.get("summary", "").lower()

        # N+1 쿼리 패턴 탐지
        if any(word in desc for word in ["loop", "while", "for", "iterate"]):
            if any(word in desc for word in ["query", "fetch", "select", "find"]):
                tasks.append({
                    "type": "optimize_n_plus_1_query",
                    "severity": "medium",
                    "description": f"Potential N+1 query pattern in {summary.get('file_id')}",
                    "affected_files": [summary.get("file_id")],
                    "effort_estimate": "medium",
                    "impact_estimate": "high"
                })

        # 불필요한 복사 탐지
        if "copy" in desc and ("large" in desc or "array" in desc):
            tasks.append({
                "type": "optimize_memory_allocation",
                "severity": "low",
                "description": f"Potential inefficient memory usage in {summary.get('file_id')}",
                "affected_files": [summary.get("file_id")],
                "effort_estimate": "low"
            })

    return tasks
```

##### **6️⃣ `_rank_recommendations()` - 우선순위 정렬**

```python
def _rank_recommendations(self, tasks: list) -> list[dict]:
    """
    작업 우선순위 계산 및 정렬
    """

    # 심각도 점수
    severity_scores = {
        "high": 10,
        "medium": 5,
        "low": 1
    }

    # 영향도 점수
    impact_scores = {
        "high": 10,
        "medium": 5,
        "low": 1
    }

    # 노력도 점수 (역함수: 낮을수록 우선)
    effort_scores = {
        "low": 10,
        "medium": 5,
        "high": 1
    }

    for task in tasks:
        severity = severity_scores.get(task.get("severity", "medium"), 5)
        impact = impact_scores.get(task.get("impact_estimate", "medium"), 5)
        effort = effort_scores.get(task.get("effort_estimate", "medium"), 5)

        # 우선순위 = (심각도 + 영향도) * 노력 역함수
        priority_score = ((severity + impact) / 2) * effort / 10
        task["priority_score"] = min(1.0, priority_score)

    # 우선순위 순으로 정렬
    ranked = sorted(tasks, key=lambda x: -x.get("priority_score", 0))

    return ranked
```

---

## 📡 API 엔드포인트

### 1. 작업 추천

```bash
POST /recommend

{
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "metadata": {
    "file_metadata": {...},
    "logical_edges": [...]
  },
  "summaries": [...]
}

Response:
{
  "recommendations": [
    {
      "type": "refactor_circular_dependencies",
      "severity": "high",
      "description": "...",
      "affected_files": ["auth_service.py", "db_model.py"],
      "priority_score": 0.95,
      "effort_estimate": "medium",
      "impact_estimate": "high",
      "suggested_actions": [...]
    },
    ...
  ],
  "total_tasks": 12,
  "execution_time": 3.45
}
```

### 2. 헬스 체크

```bash
GET /health

Response:
{
  "status": "healthy"
}
```

---

## 🚀 실행 방법

```bash
cd mcp/task_recommender
pip install -r requirements.txt
python -m uvicorn main:app --port 9005 --reload
```

---

## 📝 개발 체크리스트

- [ ] `_analyze_complexity()` 구현
  - [ ] 순환 의존성 탐지 (DFS)
  - [ ] 대형 파일 분해 제안

- [ ] `_analyze_dependencies()` 구현
  - [ ] 팬인/팬아웃 계산
  - [ ] 높은 결합도 탐지

- [ ] `_analyze_quality()` 구현
  - [ ] 미문서화 탐지
  - [ ] 기술 부채 신호

- [ ] `_suggest_structure_improvements()` 구현
  - [ ] 계층 위반 탐지
  - [ ] 아키텍처 규칙 검증

- [ ] `_analyze_performance()` 구현
  - [ ] N+1 쿼리 패턴
  - [ ] 메모리 비효율

- [ ] `_rank_recommendations()` 구현
  - [ ] 우선순위 계산
  - [ ] 정렬

- [ ] 로컬 테스트
- [ ] Docker 빌드

---

**참고:** 자세한 내용은 `IMPLEMENTATION_STATUS.md` → Task 6을 참조하세요.