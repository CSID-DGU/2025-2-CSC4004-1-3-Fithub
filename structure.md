***

# 프로젝트 명세서: 코드 분석 AI 에이전트 (Powered by LangGraph)

## 1. 시스템 목표

| 목표 | 설명 |
| :--- | :--- |
| **코드 리포지토리 자동 분석** | GitHub/Zip/Local repo를 입력받아 구조·요약·의존관계를 자동 분석합니다. |
| **LangGraph 기반 워크플로우** | 전문화된 MCP(Tools)를 **LangGraph의 노드(Node)**로 정의하고, **상태(State)**를 기반으로 결과를 개선하는 순환 그래프를 구축합니다. |
| **관계 기반 이해 제공** | 함수/클래스/모듈 관계를 그래프로 시각화하여 프로젝트 구조를 한눈에 파악할 수 있도록 합니다. |
| **분석 결과 API로 제공** | LangGraph 실행 결과물(그래프, 요약, 점수)을 백엔드/웹/CLI에서 호출할 수 있도록 HTTP API로 제공합니다. |
| **서버 환경에서 안정적으로 동작** | Agent와 MCP Tool을 Docker 기반으로 컨테이너화하여 서버(AWS/온프레미스)에서 안정적인 배포와 확장이 가능하도록 합니다. |
| **확장 가능한 모듈형 아키텍처** | 새로운 분석기(MCP)를 새로운 LangGraph 노드로 쉽게 추가할 수 있는 모듈형 구조로 설계합니다. |
| **UI/프론트엔드 연동 고려** | 분석 결과를 프론트엔드에서 시각화할 수 있도록 JSON, GraphML 등 표준 형식으로 출력합니다. |

## 2. 시스템 아키텍처 (LangGraph 기반)

### 2.1. 아키텍처 개요

본 시스템의 핵심은 **LangGraph**의 `StatefulGraph`입니다. 기존의 오케스트레이터 역할을 LangGraph가 대체하여, 상태(`State`)를 중심으로 각 전문 MCP(노드)를 호출하고, 조건부 엣지(`Conditional Edge`)를 통해 품질 평가 루프를 실행합니다.

```text
                  ▲
                  │ Client/Backend
                  │ POST /analyze
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
                  ▼
│           ┌──────────────────────────────────────────────────┐
│           │      Agent Service (FastAPI + LangGraph Core)      │
│           │ ┌──────────────────────────────────────────────┐ │
│           │ │        StatefulGraph Workflow Instance         │ │
│           │ └──────────────────────────────────────────────┘ │
│           └──────────────────────┬───────────────────────────────────┘                 │
│                                  │ (State passing between nodes)
│         ┌────────────────────────┼─────────────────────────┐
│         ▼                        ▼                         ▼                         │
│┌─────────────────┐      ┌───────────────────┐      ┌──────────────────┐
││  summarize_node │      │ build_graph_node  │      │ embed_code_node  │ ... (Parallel Nodes)
│└─────────────────┘      └───────────────────┘      └──────────────────┘                       │
│         │                        │                         │
│         └────────────────────────┼─────────────────────────┘
│                                  │ (Update State with initial results)                       │
│                                  ▼
│                          ┌─────────────────┐                                                 │
│                          │  evaluate_node  │
│                          └─────────────────┘                                                 │
│                                  │ (Conditional Edge: check_quality)
│         ┌────────────────────────┴─────────────────────────┐
│         │ (quality_OK)                                     │ (quality_FAIL)                  │
│         ▼                                                    ▼                                 │
│┌─────────────────┐                                  ┌─────────────────┐
││ synthesize_node │                                  │  refine_node    │                       │
││ (Finalize)      │                                  │ (Retry/Fallback)│                       │
│└─────────────────┘                                  └────────┬────────┘                       │
│         │                                                    │ (Loop back)
│         └────────────────────────────────────────────────────┘                                 │
│                                  │ (Final State)
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┴ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
                  │
                  ▼
                  API Response (from Final State)
```

### 2.2. 프로젝트 구성요소와 LangGraph 개념 매핑

| **프로젝트 구성요소** | **LangGraph 개념** | **설명** |
| :--- | :--- | :--- |
| **오케스트레이터** | **`StatefulGraph` 또는 `Graph`** | 전체 워크플로우의 실행 흐름을 정의하고 관리하는 핵심 객체입니다. |
| **MCP (분석 도구)** | **Node (노드)** | `summarize_node`, `build_graph_node` 등 특정 작업을 수행하는 Python 함수입니다. 각 노드는 상태를 입력받아 수정된 상태의 일부를 반환합니다. |
| **에이전트 메모리** | **`AgentState` (TypedDict)** | 그래프의 모든 노드 간에 전달되는 중앙 데이터 구조입니다. 분석 결과, 재시도 횟수, 중간 산출물 등이 모두 이 상태에 저장됩니다. |
| **품질 보장 루프** | **Conditional Edge (조건부 엣지)** | `evaluate_node`의 결과에 따라 다음에 실행할 노드(`synthesize_node` 또는 `refine_node`)를 동적으로 결정하는 라우팅 로직입니다. |
| **데이터 흐름** | **Edge (엣지)** | 한 노드에서 다음 노드로 제어 흐름을 넘기는 연결선입니다. |

## 3. AI 에이전트 통합 파이프라인 (LangGraph Workflow)

1.  **진입점 (Entry Point)**: API 요청을 받으면, `AnalyzeRequest`를 기반으로 초기 `AgentState`를 생성하고 LangGraph 워크플로우를 실행합니다.
2.  **병렬 분석 노드**: `summarize_node`, `build_graph_node` 등 주요 분석 노드들을 병렬로 실행하여 초기 분석을 수행하고 `AgentState`를 업데이트합니다.
3.  **평가 노드 (`evaluate_node`)**: 초기 분석 결과를 바탕으로 `metrics_mcp`를 호출하여 품질 점수를 계산하고, 결과를 `AgentState`에 저장합니다.
4.  **조건부 라우팅 (`check_quality`)**: `evaluate_node` 이후, `AgentState`의 메트릭 점수와 재시도 횟수를 확인합니다.
    *   **기준 충족 시**: `synthesize_node`로 제어 흐름을 전달합니다.
    *   **기준 미달 시**: `refine_node`로 제어 흐름을 전달하여 재분석을 시도합니다.
5.  **개선 노드 (`refine_node`)**: 대체 모델(Fallback)이나 다른 프롬프트를 사용하여 요약/분석을 재실행하고, `AgentState`의 재시도 횟수를 1 증가시킵니다. 작업 완료 후, 다시 `evaluate_node`로 돌아가 루프를 형성합니다.
6.  **종합 노드 (`synthesize_node`)**: 모든 분석이 완료되면, 최종 결과물을 종합하여 `AgentState`에 저장하고 워크플로우를 종료(`END`)합니다.
7.  **최종 응답**: 실행이 끝난 후의 최종 `AgentState`를 바탕으로 API 응답을 생성하여 클라이언트에게 반환합니다.

## 4. MCP (Modular Component Processors) 상세 명세

### 4.1. Summarization_MCP (코드 요약)

*   **🎯 핵심 역할**: 코드를 입력받아 사람이 이해할 수 있는 자연어 설명(요약문)을 생성합니다.
*   **🧠 내부 모델 구성 및 역할 분담**:

| 모델 | MCP 내 역할 | 세부 활용 전략 |
| :--- | :--- | :--- |
| **CodeT5 / CodeT5+** | **주력 (Primary)** | 표준적인 길이의 함수/메소드 단위 요약을 위한 1순위 모델입니다. |
| **StarCoder2** | **장문 특화 (Long-Context)** | 긴 함수나 클래스 전체, 파일 단위 요약을 담당합니다. |
| **CodeLlama-Instruct** | **의도 기반 (Intent-based)** | 특정 질문에 답하거나 비즈니스 로직 중심의 깊이 있는 요약이 필요할 때 활용합니다. |
| **PLBART** | **문서화 보조 (Doc-Helper)** | 생성된 요약문을 공식 Docstring 형태로 변환하거나 기초 문서화 초안을 생성합니다. |
| **UniXcoder** | **컨텍스트 강화 (Context-Aware)** | AST 정보를 활용하여 코드의 구조적 맥락까지 고려한 더 정확한 요약을 생성합니다. |

*   **📤 최종 출력물**: `[ { "code_id": "file.py:func_A", "summary": "...", "model": "CodeT5+" }, ... ]` 형태의 구조화된 요약 데이터.

### 4.2. Structural_Analysis_MCP (코드 구조 분석)

*   **🎯 핵심 역할**: 코드의 정적 구조를 분석하여 함수/클래스 간의 호출, 상속 관계를 그래프 데이터로 추출합니다.
*   **🧠 내부 모델 구성 및 역할 분담**:

| 모델 | MCP 내 역할 | 세부 활용 전략 |
| :--- | :--- | :--- |
| **GraphCodeBERT** | **그래프 생성 (Graph-Generator)** | 코드의 Call/Define/Use 관계를 명시적으로 추출하여 호출 그래프의 뼈대를 생성합니다. |
| **DeepWalker / Code2Vec** | **구조적 임베딩 (Structural-Embedding)** | AST 경로 기반으로 코드의 '구조적 특징'을 벡터화하여 구조적으로 유사한 함수를 찾는 데 사용합니다. |

*   **📤 최종 출력물**: 노드(함수, 클래스)와 엣지(호출)로 구성된 그래프 데이터. 각 노드는 구조적 임베딩 값을 속성으로 포함합니다.

### 4.3. Semantic_Embedding_MCP (의미 기반 임베딩)

*   **🎯 핵심 역할**: 모든 코드 조각을 의미적 유사도 비교가 가능한 고차원 벡터(임베딩)로 변환합니다.
*   **🧠 내부 모델 구성 및 역할 분담**:

| 모델 | MCP 내 역할 | 세부 활용 전략 |
| :--- | :--- | :--- |
| **CodeBERT** | **주력 (Primary)** | 코드의 문맥적, 의미적 정보를 벡터로 변환하는 기본 모델입니다. |
| **CuBERT** | **품질 검증/대체 (QA & Fallback)** | CodeBERT 결과를 보완하거나, 요약 품질 평가 시 원본 코드와 요약문의 의미 유사도 측정에 사용합니다. |

*   **📤 최종 출력물**: `[ { "code_id": "file.py:func_A", "embedding": [0.12, ...] }, ... ]` 형태의 코드 유닛별 벡터 데이터.

### 4.4. Repository_Analysis_MCP (저장소 레벨 분석)

*   **🎯 핵심 역할**: 프로젝트 전체를 조망하며 거시적인 아키텍처와 모듈 간의 관계를 분석합니다.
*   **🧠 내부 모델 구성 및 역할 분담**:

| 모델 | MCP 내 역할 | 세부 활용 전략 |
| :--- | :--- | :--- |
| **RepoCoder** | **전체 요약 (Global-Summarizer)** | 프로젝트의 목적, 핵심 아키텍처에 대한 최상위 레벨의 자연어 개요를 생성합니다. |
| **RepoGraph** | **모듈 그래프화 (Module-Grapher)** | 파일과 디렉토리 구조를 분석하여 모듈 간의 의존성을 시각적인 그래프로 도출합니다. |

*   **📤 최종 출력물**: 1) 프로젝트 전체 요약 텍스트, 2) 모듈 의존성 그래프 데이터.

### 4.5. Task_Recommender_MCP (태스크 추천 및 인사이트)

*   **🎯 핵심 역할**: 다른 MCP들의 분석 결과를 종합하여 "어디부터 봐야 할지", "어떤 코드가 중요한지" 등 실행 가능한 인사이트를 제공합니다.
*   **🧠 내부 모델 구성 및 역할 분담**:

| 모델 | MCP 내 역할 | 세부 활용 전략 |
| :--- | :--- | :--- |
| **CodeSage / SWE-Agent** | **분석의 뇌 (The Brain)** | 통합된 지식 그래프를 입력받아 프로젝트의 '핫스팟'을 식별합니다. |
| **(모든 MCP 결과)** | **입력 데이터 (Input Context)** | 다른 MCP들의 출력물을 종합적으로 해석하여 최종 결론을 도출합니다. |

*   **📤 최종 출력물**: `[ { "recommendation": "프로젝트 이해를 위해 'AuthService.java' 분석 시작", ... }, ... ]` 형태의 추천 목록.

## 5. API 명세 및 데이터 스키마

### 5.1. 주요 엔드포인트

*   `POST /analyze`: 동기 실행 요청
*   `POST /analyze_async`: 비동기 실행 요청 (즉시 `run_id` 반환)
*   `GET /result/{run_id}`: 비동기 실행 상태 및 결과 조회
*   `GET /report/{run_id}`: 분석 결과 리포트(HTML) 조회

### 5.2. 요청/응답 스키마 (Pydantic)

```python
from pydantic import BaseModel
from typing import List, Dict, Any

# --- API 요청 모델 ---
class RepoInput(BaseModel):
    source: str  # "git", "zip", "local"
    uri: str
    branch: str = "main"

class Thresholds(BaseModel):
    codebleu_min: float = 0.42
    bleurt_min: float = 0.05
    rougeL_min: float = 0.30
    edge_f1_min: float = 0.80
    ged_max: float = 50.0
    retry_max: int = 2
    ensemble: bool = True

class AnalyzeRequest(BaseModel):
    repo: RepoInput
    options: Dict[str, Any] = {"summary": "llm", "graph": "full", "metrics": "full"}
    thresholds: Thresholds = Thresholds()
    top_k: int = 10

# --- 핵심 데이터 구조 ---
class Node(BaseModel):
    id: str
    label: str
    type: str  # 'repo', 'dir', 'file', 'class', 'function'
    # ... other attributes

class Edge(BaseModel):
    source: str
    target: str
    type: str  # 'IMPORTS', 'CALLS', 'INHERITS'
    # ... other attributes

class CodeGraph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]

class SummaryUnit(BaseModel):
    target_id: str
    level: str  # "file", "class", "function", "repo"
    text: str
    model: str

class Metrics(BaseModel):
    codebleu: float
    bleurt: float
    bleu4: float
    rougeL: float
    edge_f1: float
    ged: float
    ssi: float

class AgentArtifact(BaseModel):
    graph: CodeGraph
    summaries: List[SummaryUnit]
    metrics: Metrics

# --- API 응답 모델 ---
class AnalyzeResponse(BaseModel):
    run_id: str
    artifact: AgentArtifact
```

### 5.3. API 호출 예시

**요청 (Request)**

```json
POST /analyze
{
  "repo": {
    "source": "git",
    "uri": "https://github.com/USER/REPO",
    "branch": "main"
  },
  "options": {
    "summary": "llm",
    "graph": "full",
    "metrics": "full"
  }
}
```

**응답 (Response)**

```json
{
  "run_id": "2025-01-01-14-22",
  "artifact": {
    "graph": {
      "nodes": [...],
      "edges": [...]
    },
    "summaries": [
      {
        "target_id": "...",
        "level": "function",
        "text": "...",
        "model": "CodeT5+"
      }
    ],
    "metrics": {
      "codebleu": 0.51,
      "bleurt": 0.12,
      ...
    }
  }
}
```

## 6. LangGraph 구현 및 배포

### 6.1. LangGraph 구현 스켈레톤 (Claude를 위한 가이드)

Claude, 아래는 우리가 구현할 LangGraph 워크플로우의 핵심 뼈대입니다. 이 구조에 맞춰 코드를 작성해주세요.

**1. 상태 정의 (AgentState)**
그래프의 모든 노드가 공유하고 수정할 중앙 데이터 구조입니다.

```python
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    repo_input: Dict[str, Any]      # 사용자 초기 요청
    repo_path: str                  # 코드가 클론된 로컬 경로
    thresholds: Dict[str, Any]      # 품질 임계치 설정

    # 분석 결과물
    initial_summaries: Optional[List[Dict]]
    refined_summaries: Optional[List[Dict]]
    final_summaries: List[Dict]
    code_graph: Optional[Dict]
    embeddings: Optional[List]
    
    # 평가 및 제어
    metrics: Optional[Dict]
    retry_count: int
    error_message: Optional[str]
```

**2. 노드 함수 정의**
각 MCP는 상태(State)를 입력받아 일부를 수정하여 반환하는 노드 함수로 래핑됩니다.

```python
# 예시: 요약 노드
def summarize_node(state: AgentState) -> Dict[str, Any]:
    print("--- Running Summarization MCP ---")
    summaries = summarization_mcp.run(repo_path=state["repo_path"])
    return {"initial_summaries": summaries}

# 예시: 평가 노드
def evaluate_node(state: AgentState) -> Dict[str, Any]:
    print("--- Running Metrics MCP for evaluation ---")
    summaries_to_evaluate = state.get("refined_summaries") or state["initial_summaries"]
    metrics = metrics_mcp.run(pred_summaries=summaries_to_evaluate, ...)
    return {"metrics": metrics}

# 예시: 개선 노드
def refine_node(state: AgentState) -> Dict[str, Any]:
    print(f"--- Refining Summaries (Attempt: {state['retry_count'] + 1}) ---")
    # 대체 모델이나 다른 프롬프트 사용
    refined = summarization_mcp.run(
        repo_path=state["repo_path"], use_fallback_model=True
    )
    return {"refined_summaries": refined, "retry_count": state["retry_count"] + 1}

# 예시: 종합 노드
def synthesize_node(state: AgentState) -> Dict[str, Any]:
    print("--- Synthesizing final results ---")
    # 최종 결과물을 AgentState의 final_ 필드에 정리
    final_summaries = state.get("refined_summaries") or state["initial_summaries"]
    return {"final_summaries": final_summaries}

# ... 다른 모든 MCP에 대한 노드 함수들 (build_graph_node, embed_code_node 등) ...
```

**3. 조건부 엣지 함수 정의**
품질 평가 결과에 따라 다음 경로를 결정합니다.

```python
def check_quality(state: AgentState) -> str:
    print("--- Checking Quality Thresholds ---")
    metrics = state["metrics"]
    thresholds = state["thresholds"]
    
    if state["retry_count"] >= thresholds["retry_max"]:
        print("Max retries reached. Proceeding to synthesis.")
        return "synthesize" # 최대 재시도 도달
        
    if metrics["codebleu"] >= thresholds["codebleu_min"]:
        print("Quality is sufficient. Proceeding to synthesis.")
        return "synthesize" # 품질 만족
    else:
        print("Quality is not sufficient. Proceeding to refinement.")
        return "refine" # 품질 미달 -> 개선 필요
```

**4. 그래프 구성 및 컴파일**
정의된 상태, 노드, 엣지를 사용하여 워크플로우 그래프를 조립합니다.

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

# 1. 노드 추가
workflow.add_node("summarizer", summarize_node)
workflow.add_node("graph_builder", build_graph_node) # 참고: 병렬 실행은 LangChain의 RunnableParallel 등을 사용해 한 노드 내에서 구현하거나, 별도 그래프 분기가 필요합니다.
workflow.add_node("evaluator", evaluate_node)
workflow.add_node("refiner", refine_node)
workflow.add_node("synthesizer", synthesize_node)

# 2. 엣지 연결
workflow.set_entry_point("summarizer") # 예시 진입점 (실제로는 여러 초기 노드를 묶는 진입 노드가 필요할 수 있음)
workflow.add_edge("summarizer", "evaluator")
workflow.add_edge("refiner", "evaluator") # 개선 후 다시 평가

# 3. 조건부 엣지 연결
workflow.add_conditional_edges(
    "evaluator",
    check_quality,
    {
        "synthesize": "synthesizer",
        "refine": "refiner"
    }
)

workflow.add_edge("synthesizer", END)

# 4. 그래프 컴파일
app = workflow.compile()

# 5. 실행
# inputs = {"repo_input": ..., "thresholds": ..., "retry_count": 0}
# result = app.invoke(inputs)
```

### 6.2. 컨테이너 기반 배포 (`docker-compose.yml`)

```yaml
version: "3.9"
services:
  agent-service:
    build: ./agent # 이 컨테이너 안에 LangGraph 코드가 포함됩니다.
    ports:
      - "8000:8000"
    depends_on:
      - summarization-mcp
      - structural-analysis-mcp
      - semantic-embedding-mcp
      - repository-analysis-mcp
      - task-recommender-mcp
    # 역할: API Gateway + LangGraph Workflow Runner

  summarization-mcp:
    build: ./mcp/summarization
    expose: ["9001"]

  structural-analysis-mcp:
    build: ./mcp/structural_analysis
    expose: ["9002"]

  semantic-embedding-mcp:
    build: ./mcp/semantic_embedding
    expose: ["9003"]

  repository-analysis-mcp:
    build: ./mcp/repository_analysis
    expose: ["9004"]

  task-recommender-mcp:
    build: ./mcp/task_recommender
    expose: ["9005"]

# 참고: MCP들은 내부 네트워크로만 통신하며, 외부에는 Agent Service만 노출됩니다.
```
