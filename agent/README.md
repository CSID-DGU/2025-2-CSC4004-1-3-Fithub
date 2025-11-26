# Agent 모듈 - LangGraph 오케스트레이션

## 📋 개요

**Agent**는 전체 분석 파이프라인의 중심 오케스트레이터입니다.

- **포트:** 8000 (FastAPI)
- **역할:** 5개 MCP 서비스를 조율하여 코드 분석 워크플로우 실행
- **아키텍처:** LangGraph 상태 머신 + Monolith Lite (MCP를 로컬 함수로 통합)

---

## 🏗️ 디렉토리 구조

```
agent/
├── main.py                 # FastAPI 서버 및 엔드포인트
├── workflow.py             # LangGraph 워크플로우 정의
├── nodes.py                # 7개 분석 노드 (⚠️ Mock 함수 필요)
├── edges.py                # 노드 간 라우팅 로직
├── state.py                # AgentState TypedDict 정의
├── schemas.py              # Pydantic 요청/응답 모델
├── config.py               # 환경변수 및 설정
├── Dockerfile              # 컨테이너 빌드
└── requirements.txt        # 의존성
```

---

## ⚙️ 구현 상태 및 필요 작업

### ✅ 완성된 부분

| 파일 | 상태 | 설명 |
|------|------|------|
| `main.py` | ✅ | FastAPI 서버 (분석 요청/응답 처리) |
| `workflow.py` | ✅ | LangGraph 워크플로우 정의 및 컴파일 |
| `edges.py` | ✅ | 조건부 라우팅 (품질 평가 분기) |
| `state.py` | ✅ | 상태 타입 정의 |
| `schemas.py` | ✅ | Pydantic 모델 |
| `config.py` | ✅ | 환경변수 관리 |

### ⚠️ 필요한 작업

#### **Task 1: `nodes.py` - Mock 함수를 실제 로직으로 대체**

**현재 상태:** Mock 함수로 데이터 생성
```python
def _service_summarize(code: str) -> str:
    return f"Mock summary for {len(code)} chars"  # ❌ 이렇게 되어있음
```

**필요 상태:** 실제 MCP 로직 호출
```python
def _service_summarize(code: str) -> str:
    # 실제 summarization 로직
    summarizer = CodeSummarizer()
    return summarizer.summarize_code(code)
```

**대체 필요한 함수들:**

1. **`_service_summarize()`**
   - 호출: `mcp/summarization/summarizer.py` → `CodeSummarizer.summarize_file()`
   - 반환: 코드 요약 텍스트

2. **`_service_build_graph()`**
   - 호출: `mcp/structural_analysis/analyzer.py` → `StructuralAnalyzer.analyze_repository()`
   - 반환: `{"nodes": [...], "edges": [...]}`

3. **`_service_embed()`**
   - 호출: `mcp/semantic_embedding/embedder.py` → `CodeEmbedder.batch_embed()`
   - 반환: `{"embeddings": [[...], [...]]}`

4. **`_service_analyze_repo()`**
   - 호출: `mcp/repository_analysis/analyzer.py` → `RepositoryAnalyzer.analyze()`
   - 반환: `{"file_metadata": {...}, "logical_edges": [...]}`

#### **Task 2: `edges.py` - 중복 코드 정리**

**현재:** `check_quality()` 함수가 2개 정의되어 있음
**필요:** 1개로 통합 (더 나은 버전 선택)

#### **Task 3: `evaluate_node()` - 메트릭 확장**

**현재:** 기본 CodeBLEU, ROUGE-L 계산만 수행

**필요:** 추가 메트릭
```python
# 추가해야 할 메트릭:
- edge_f1: 구조 그래프의 F1 스코어
- embedding_consistency: 임베딩의 일관성
- summary_coverage: 요약이 커버하는 코드 범위
- graph_density: 그래프의 밀도 (복잡도)
```

---

## 🔄 워크플로우 흐름

```
START
  ↓
[병렬] summarize_node + build_graph_node + embed_code_node
  ↓
fusion_node (요약 + 그래프 + 임베딩 결합)
  ↓
evaluate_node (품질 평가)
  ↓
check_quality (조건 분기)
  ├─ Pass → analyze_repo_node → synthesize_node → END
  └─ Fail → refine_node → [재시도]
```

---

## 📡 API 엔드포인트

### 1. 분석 요청 (비동기)

```bash
POST /analyze-async
Content-Type: application/json

{
  "repo": {
    "type": "github",
    "owner": "facebook",
    "repo": "react",
    "branch": "main"
  },
  "options": {
    "depth": 2,
    "max_files": 100
  },
  "thresholds": {
    "codebleu_min": 0.42,
    "rougeL_min": 0.30,
    "edge_f1_min": 0.80
  },
  "top_k": 10
}

Response:
{
  "run_id": "abc123xyz",
  "status": "processing"
}
```

### 2. 분석 요청 (동기)

```bash
POST /analyze
Content-Type: application/json

[동일한 본문]

Response:
{
  "run_id": "abc123xyz",
  "status": "completed",
  "artifact": { ... },
  "execution_time": 45.5
}
```

### 3. 결과 조회

```bash
GET /result/<run_id>

Response:
{
  "run_id": "abc123xyz",
  "status": "completed",
  "artifact": {
    "graph": { "nodes": [...], "edges": [...] },
    "summaries": [...],
    "embeddings": [...],
    "metrics": {...},
    "recommendations": [...]
  }
}
```

### 4. 헬스 체크

```bash
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🚀 실행 방법

### 단독 실행 (개발용)

```bash
# 가상 환경 활성화
source venv/bin/activate

# 의존성 설치
cd agent && pip install -r requirements.txt

# 서버 시작
cd .. && python -m uvicorn agent.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker 실행

```bash
# 이미지 빌드
docker build -t fithub-agent agent/

# 컨테이너 실행
docker run -p 8000:8000 \
  -e MCP_SUMMARIZATION_URL=http://localhost:9001 \
  -e MCP_STRUCTURAL_ANALYSIS_URL=http://localhost:9002 \
  fithub-agent
```

### Docker Compose 실행

```bash
docker-compose up agent
```

---

## 🧪 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 간단한 분석 요청
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo": {"type": "local", "path": "/path/to/repo"},
    "options": {},
    "thresholds": {},
    "top_k": 5
  }'
```

---

## 📚 주요 클래스 및 함수

### AgentState (state.py)

```python
class AgentState(TypedDict):
    # 입력
    run_id: str
    repo_input: dict
    repo_path: str
    options: dict
    thresholds: dict
    top_k: int

    # 출력
    initial_summaries: list
    code_graph_raw: dict
    embeddings: dict
    reinforced_graph_obj: nx.DiGraph
    final_graph_json: dict
    repository_info: dict
    recommendations: list

    # 제어
    retry_count: int
    error_message: str
    status: str
    node_execution_log: dict
```

### 주요 Pydantic 모델 (schemas.py)

```python
class AnalyzeRequest:
    repo: RepoInput
    options: dict
    thresholds: dict
    top_k: int

class AnalyzeResponse:
    run_id: str
    artifact: AgentArtifact
    execution_time: float

class AgentArtifact:
    graph: CodeGraph
    summaries: list[SummaryUnit]
    embeddings: list[Embedding]
    metrics: Metrics
    recommendations: list[Recommendation]
```

---

## 🔗 의존성

```
fastapi==0.104.0
uvicorn==0.24.0
pydantic==2.4.0
langgraph==0.0.1
langchain==0.0.334
httpx==0.25.0
requests==2.31.0
python-dotenv==1.0.0
networkx==3.2
numpy==1.24.0
```

---

## ⚡ 주의사항

1. **MCP 서비스 필수:** agent는 5개 MCP가 실행 중이어야 합니다.
2. **메모리 관리:** 대형 저장소 분석 시 메모리 사용량이 많을 수 있습니다.
3. **타임아웃:** 대형 분석은 `config.py`에서 타임아웃을 조정하세요.
4. **로깅:** `node_execution_log`에 각 노드의 실행 시간이 기록됩니다.

---

## 📝 개발 체크리스트

- [ ] Mock 함수 4개 대체 (`nodes.py`)
- [ ] 중복 코드 정리 (`edges.py`)
- [ ] 메트릭 확장 (`evaluate_node()`)
- [ ] 로컬 테스트 (mock MCP 데이터)
- [ ] Docker 빌드 및 테스트
- [ ] End-to-End 테스트

---

**참고:** 자세한 내용은 `IMPLEMENTATION_STATUS.md`를 참조하세요.