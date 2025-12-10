# Fithub 라벨링 시스템 분석 (실제 구현 기반)

## 개요

이 문서는 Fithub 프로젝트에서 실제로 구현된 코드 라벨링 및 Task 분류 시스템을 분석한 결과입니다.

---

## 1. 코드 요약 라벨링 (`mcp/summarization/summarizer.py`)

### 1.1 앙상블 3-Expert 시스템

**구현 위치:** Lines 112-152

Fithub은 **3개의 서로 다른 LLM 모델**을 사용하여 코드를 다양한 관점에서 분석합니다.

#### 사전정의된 3가지 관점 (Lines 222-227)

```python
prompts = {
    "logic": "Summarize the function inputs, outputs, and core algorithm in one sentence",
    "intent": "Explain the business purpose and why this code exists in one sentence",
    "structure": "Describe the code structure, patterns, and design in one sentence"
}
```

| 관점 | 설명 | 사용 모델 |
|------|------|-----------|
| **logic** | 함수 입출력과 핵심 알고리즘 분석 | `Salesforce/codet5-base` |
| **intent** | 비즈니스 목적과 존재 이유 설명 | `bigcode/starcoder2-3b` |
| **structure** | 코드 구조, 패턴, 디자인 설명 | `microsoft/unixcoder-base` |

#### 출력 형식 (Lines 141-152)

```json
{
    "code_id": "파일명",
    "text": "통합 요약문",
    "unified_summary": "통합 요약문",
    "expert_views": {
        "logic": "알고리즘 요약",
        "intent": "비즈니스 목적",
        "structure": "구조 설명"
    },
    "quality_score": 0.87,
    "level": "file"
}
```

#### 품질 점수 계산 (Lines 195-218)

- **방법:** TF-IDF 벡터화 + 코사인 유사도
- **목적:** 3개 요약 간 일관성 측정
- **계산식:** `(sim_12 + sim_23 + sim_13) / 3`

#### 통합 요약 생성 (Lines 166-193)

1. 가장 긴 요약을 기본(base)으로 선택
2. 다른 요약에서 unique 키워드 추출
3. `"{base} Related aspects: {keywords}."`

---

## 2. 도메인/레이어 라벨링 (`mcp/repository_analysis/analyzer.py`)

### 2.1 규칙 기반 분류 (Lines 171-228)

#### A. 도메인 태그 (5개 카테고리) - Lines 186-194

```python
domain = "Common"  # 기본값

if 키워드 in ['auth', 'login', 'security', 'jwt']:
    domain = "Security"
elif 키워드 in ['user', 'member', 'profile']:
    domain = "User"
elif 키워드 in ['order', 'cart', 'pay']:
    domain = "Commerce"
elif 키워드 in ['db', 'model', 'entity', 'schema']:
    domain = "Database"
```

| 도메인 | 키워드 | 분류 대상 |
|--------|--------|-----------|
| **Security** | auth, login, security, jwt | 인증/보안 관련 코드 |
| **User** | user, member, profile | 사용자 관리 |
| **Commerce** | order, cart, pay | 전자상거래 |
| **Database** | db, model, entity, schema | 데이터베이스 |
| **Common** | (기본값) | 기타 |

**분류 방법:** 파일명 또는 요약문에서 키워드 매칭

#### B. 아키텍처 레이어 태그 (5개) - Lines 197-205

```python
layer = "Other"  # 기본값

if 키워드 in ["service", "manager", "business"]:
    layer = "ServiceLayer"
elif 키워드 in ["repo", "dao", "store", "db"]:
    layer = "RepositoryLayer"
elif 키워드 in ["controller", "route", "view", "api"]:
    layer = "PresentationLayer"
elif 키워드 in ["model", "dto", "schema"]:
    layer = "DomainLayer"
```

| 레이어 | 키워드 | 역할 |
|--------|--------|------|
| **ServiceLayer** | service, manager, business | 비즈니스 로직 |
| **RepositoryLayer** | repo, dao, store, db | 데이터 접근 |
| **PresentationLayer** | controller, route, view, api | UI/API 계층 |
| **DomainLayer** | model, dto, schema | 도메인 모델 |
| **Other** | (기본값) | 유틸리티 등 |

**분류 방법:** 파일명에서 키워드 매칭

#### C. 중요도 힌트 (2개 레벨) - Lines 207-209

```python
importance = "Medium"  # 기본값

if layer in ["ServiceLayer", "DomainLayer"]:
    importance = "High"
```

**규칙:** Service/Domain 레이어는 자동으로 High 중요도

#### 출력 형식 (Lines 212-216)

```json
{
    "file_metadata": {
        "auth_service.py": {
            "domain_tag": "Security",
            "layer": "ServiceLayer",
            "importance_hint": "High"
        }
    }
}
```

---

### 2.2 LLM 기반 분류 (Fallback) - Lines 80-169

규칙 기반 분석이 실패하거나 불충분할 경우 LLM을 사용합니다.

#### LLM 프롬프트 (Lines 96-114)

```
You are a software architect analyzing a codebase.
Analyze the following files and their summaries to identify:
1. Domain (e.g., Security, User, Commerce, Database, Common)
2. Layer (e.g., ServiceLayer, RepositoryLayer, PresentationLayer, DomainLayer)
3. Logical dependencies between files (e.g., Auth uses User).

Return ONLY a JSON object with this structure:
{
  "file_metadata": {
    "filename": { "domain_tag": "...", "layer": "...", "importance_hint": "High/Medium/Low" }
  },
  "logical_edges": [
    { "source": "filename", "target": "filename", "type": "logical", "relation": "reason" }
  ]
}
```

#### 지원 모델

| Provider | 모델 | 구현 위치 |
|----------|------|-----------|
| **HuggingFace** | `mistralai/Mistral-7B-Instruct-v0.3` | Line 42 |
| **OpenAI** | `gpt-4o` | Lines 32, 132-169 |

#### 동작 순서 (Lines 58-70)

1. LLM 분석 시도
2. 실패 시 → 규칙 기반 분석 (Fallback)
3. 벡터 유사도 엣지 추가 (RepoCoder Logic)

---

### 2.3 관계 엣지 라벨링

#### A. 논리적 엣지 (3가지 타입) - Lines 304-318

**분류 기준:** 파일명 stem이 같고 + 레이어 패턴 일치

```python
if src['stem'] == tgt['stem'] and len(src['stem']) > 2:
    if src['layer'] == "PresentationLayer" and tgt['layer'] == "ServiceLayer":
        relation = "architectural_flow"  # Controller → Service

    elif src['layer'] == "ServiceLayer" and tgt['layer'] == "RepositoryLayer":
        relation = "data_access"  # Service → Repository

    elif src['layer'] == "ServiceLayer" and tgt['layer'] == "DomainLayer":
        relation = "uses_model"  # Service → Model
```

| 관계 타입 | 의미 | 예시 |
|-----------|------|------|
| **architectural_flow** | Presentation → Service | `user_controller.py` → `user_service.py` |
| **data_access** | Service → Repository | `user_service.py` → `user_repository.py` |
| **uses_model** | Service → Domain | `user_service.py` → `user_model.py` |

#### B. 벡터 유사도 엣지 (RepoCoder Logic) - Lines 230-294

**분류 기준:** 임베딩 코사인 유사도 ≥ 0.85

```python
threshold = 0.85  # Line 275

if cosine_similarity(embedding1, embedding2) >= threshold:
    {
        "source": "file1.py",
        "target": "file2.py",
        "type": "logical",
        "relation": "semantic_similarity",
        "weight": 0.87
    }
```

**특징:**
- 명시적 import 없이도 의미적으로 관련된 파일 연결
- RepoCoder 논문의 Context Retrieval 로직 구현
- 벡터가 있는 노드만 분석 대상

---

## 3. Task 라벨링 (`mcp/task_recommender/recommender.py`)

### 3.1 구현된 Task 타입 (2가지)

#### A. Architecture Violation - Lines 28-43

**감지 규칙:** Repository Layer → Presentation Layer 의존성

```python
if src_layer == "RepositoryLayer" and tgt_layer == "PresentationLayer":
    {
        "type": "architecture_violation",
        "file": "user_repository.py",
        "severity": "High",
        "description": "Repository layer should not depend on Presentation layer."
    }
```

**분류 기준:**
- Edge의 source layer가 `RepositoryLayer`
- Edge의 target layer가 `PresentationLayer`
- 아키텍처 원칙 위반 (하위 레이어가 상위 레이어 참조)

#### B. Refactor Needed - Lines 45-57

**감지 규칙:** 높은 중요도 + 높은 복잡도

```python
if importance > 50 and complexity > 20:
    {
        "type": "refactor_needed",
        "file": "complex_service.py",
        "severity": "Medium",
        "description": "Critical file with high complexity. Consider splitting."
    }
```

**분류 기준:**
- `importance` (GNN 노드 크기) > 50
- `complexity` (AST 복잡도) > 20
- 중요한데 복잡한 파일 = 리팩토링 후보

### 3.2 Task 속성

| 속성 | 타입 | 값 |
|------|------|-----|
| **type** | string | `architecture_violation`, `refactor_needed` |
| **file** | string | 대상 파일 경로 |
| **severity** | string | `High`, `Medium` |
| **description** | string | 추천 이유 설명 |

---

## 4. 전체 라벨링 시스템 요약

### 4.1 분류 체계 비교표

| 분류 대상 | 카테고리 수 | 분류 방법 | LLM 사용 | 구현 파일 |
|-----------|-------------|-----------|----------|-----------|
| **코드 요약 관점** | 3개 | LLM 앙상블 | ✅ (주요) | `summarizer.py:222` |
| **도메인 태그** | 5개 | 규칙 → LLM fallback | ✅ (보조) | `analyzer.py:186` |
| **레이어 태그** | 5개 | 규칙 → LLM fallback | ✅ (보조) | `analyzer.py:197` |
| **중요도 힌트** | 2개 | 규칙 기반 | ❌ | `analyzer.py:207` |
| **관계 타입** | 4개 | 규칙 + 벡터 유사도 | ❌ | `analyzer.py:310, 285` |
| **Task 타입** | 2개 | 규칙 기반 | ❌ | `recommender.py:38, 52` |
| **Task Severity** | 2개 | 하드코딩 | ❌ | `recommender.py:41, 55` |

### 4.2 카테고리 상세

#### 코드 요약 관점 (3개)
- `logic` - 알고리즘 분석
- `intent` - 비즈니스 목적
- `structure` - 구조/패턴

#### 도메인 태그 (5개)
- `Security` - 인증/보안
- `User` - 사용자 관리
- `Commerce` - 전자상거래
- `Database` - 데이터베이스
- `Common` - 기타

#### 레이어 태그 (5개)
- `ServiceLayer` - 비즈니스 로직
- `RepositoryLayer` - 데이터 접근
- `PresentationLayer` - UI/API
- `DomainLayer` - 도메인 모델
- `Other` - 유틸리티

#### 관계 타입 (4개)
- `architectural_flow` - 아키텍처 계층 흐름
- `data_access` - 데이터 접근 관계
- `uses_model` - 모델 사용
- `semantic_similarity` - 의미적 유사성

#### Task 타입 (2개 구현됨)
- `architecture_violation` - 아키텍처 위반
- `refactor_needed` - 리팩토링 필요

---

## 5. 핵심 설계 원칙

### 5.1 하이브리드 접근법

1. **코드 요약 = LLM 중심**
   - 3개 모델 앙상블로 다각도 분석
   - 품질 점수로 신뢰도 측정

2. **메타데이터 분류 = 규칙 우선, LLM Fallback**
   - 빠른 키워드 매칭 우선
   - 실패 시 LLM으로 정밀 분석

3. **Task 분류 = 순수 규칙 기반**
   - 정량적 임계값 사용
   - LLM 없이 빠른 판단

### 5.2 사전정의된 카테고리

- **모든 라벨은 사전에 정의됨** (동적 생성 없음)
- **확장 가능한 구조**: 새 카테고리 추가 시 if-elif 블록 확장
- **일관성 보장**: 제한된 카테고리로 예측 가능한 결과

### 5.3 Multi-Level 분석

```
Repository
    ↓
[Summarization] → logic, intent, structure 요약
    ↓
[Analysis] → domain, layer, importance 태깅
    ↓
[Graph] → logical edges (architectural + semantic)
    ↓
[Task Recommendation] → architecture_violation, refactor_needed
```

---

## 6. 주요 파일 및 라인 참조

| 기능 | 파일 | 핵심 라인 |
|------|------|-----------|
| 앙상블 요약 생성 | `mcp/summarization/summarizer.py` | 112-152 |
| 3-Expert 프롬프트 | `mcp/summarization/summarizer.py` | 222-227 |
| 품질 점수 계산 | `mcp/summarization/summarizer.py` | 195-218 |
| 도메인 태깅 (규칙) | `mcp/repository_analysis/analyzer.py` | 186-194 |
| 레이어 태깅 (규칙) | `mcp/repository_analysis/analyzer.py` | 197-205 |
| LLM 분석 프롬프트 | `mcp/repository_analysis/analyzer.py` | 96-114 |
| 논리적 엣지 감지 | `mcp/repository_analysis/analyzer.py` | 304-318 |
| 벡터 유사도 엣지 | `mcp/repository_analysis/analyzer.py` | 230-294 |
| Architecture Violation | `mcp/task_recommender/recommender.py` | 28-43 |
| Refactor Needed | `mcp/task_recommender/recommender.py` | 45-57 |

---

## 7. 확장 가능성

### 현재 미구현되었지만 문서화된 Task 타입 (`mcp/task_recommender/README.md`)

1. **Complexity Improvement**
   - `refactor_circular_dependencies` - 순환 의존성 제거
   - `decompose_large_files` - 대용량 파일 분해

2. **Dependency Optimization**
   - `reduce_coupling` - 결합도 감소 (Fan-out)
   - `stabilize_core_module` - 코어 모듈 안정화 (Fan-in)

3. **Quality Improvement**
   - `resolve_technical_debt` - TODO/FIXME 해결
   - `improve_documentation` - 문서화 개선

4. **Performance Optimization**
   - `optimize_n_plus_1_query` - N+1 쿼리 최적화
   - `optimize_memory_allocation` - 메모리 최적화

**구현 방법:** `recommender.py`에 추가 규칙 로직 작성

---

## 8. 결론

Fithub의 라벨링 시스템은 다음과 같은 특징을 가집니다:

1. **Multi-Model Ensemble**: 3개 LLM으로 코드를 다각도 분석
2. **Hybrid Classification**: 규칙 기반 + LLM fallback으로 정확도와 속도 균형
3. **Structured Categories**: 사전정의된 카테고리로 일관성 보장
4. **Graph-Aware**: 벡터 유사도로 암묵적 관계까지 포착
5. **Actionable Tasks**: 분석 결과를 실행 가능한 작업으로 변환

**핵심 장점:**
- 규칙 기반으로 빠른 분류
- LLM으로 정밀한 분석
- 확장 가능한 구조
- 정량적 품질 점수

**개선 가능 영역:**
- Task 타입 확장 (현재 2개 → 12+ 구현)
- 동적 임계값 조정
- 사용자 피드백 학습