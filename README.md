# LangGraph 기반 코드 분석 AI 에이전트

LangGraph를 기반으로 한 종합적인 코드 분석 시스템입니다. GitHub, ZIP, 로컬 저장소에서 코드를 자동으로 분석하고, 구조, 요약, 의미 임베딩, 품질 메트릭을 생성합니다.

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────┐
│      Client / Backend            │
│     (POST /analyze)              │
└──────────────┬────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────┐
│   Agent Service (FastAPI + LangGraph)            │
│  - Workflow orchestration                        │
│  - State management                              │
│  - API endpoints                                 │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
┌──────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│Summary  │ │Struct  │ │Semantic│ │Repo    │ │Task      │
│MCP      │ │Analysis│ │Embedding│ │Analysis│ │Recommender
│(9001)   │ │(9002)  │ │(9003)  │ │(9004)  │ │(9005)
└──────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```

## 📦 주요 구성 요소

### 1. Agent Service (`agent/`)
- **main.py**: FastAPI 서버 및 REST API 엔드포인트
- **workflow.py**: LangGraph 워크플로우 정의
- **nodes.py**: 각 분석 노드 함수
- **edges.py**: 조건부 라우팅 로직
- **state.py**: AgentState 정의
- **schemas.py**: Pydantic 데이터 모델

### 2. MCP Services (`mcp/`)
- **Summarization** (Port 9001): 코드 요약 생성
- **Structural Analysis** (Port 9002): 코드 구조 분석
- **Semantic Embedding** (Port 9003): 의미 기반 임베딩
- **Repository Analysis** (Port 9004): 저장소 레벨 분석
- **Task Recommender** (Port 9005): 작업 추천

### 3. Shared Utilities (`shared/`)
- **model_utils.py**: 모델 로딩 및 캐싱
- **git_utils.py**: Git 저장소 관리
- **ast_utils.py**: 코드 분석 (AST 파싱)

### 4. Models Cache (`models/`)
당신이 다운로드한 AI 모델들을 저장하는 디렉토리:
```
models/
├── summarization/          # CodeT5+, StarCoder2, CodeLlama 등
├── structural_analysis/    # GraphCodeBERT, CodeBERT
├── semantic_embedding/     # CodeBERT, CuBERT
├── repository_analysis/    # 저장소 분석 모델
└── task_recommender/       # 추천 모델
```

## 🚀 설치 및 실행

### 1. 로컬 실행 (개발)

```bash
# 1. 저장소 클론
git clone <repo_url>
cd 2025-2-CSC4004-1-3-Fithub

# 2. Python 의존성 설치
pip install -r requirements.txt

# 3. 각 MCP 서비스 실행 (별도 터미널에서)
python -m uvicorn mcp.summarization.main:app --host 0.0.0.0 --port 9001
python -m uvicorn mcp.structural_analysis.main:app --host 0.0.0.0 --port 9002
python -m uvicorn mcp.semantic_embedding.main:app --host 0.0.0.0 --port 9003
python -m uvicorn mcp.repository_analysis.main:app --host 0.0.0.0 --port 9004
python -m uvicorn mcp.task_recommender.main:app --host 0.0.0.0 --port 9005

# 4. Agent Service 실행
python -m uvicorn agent.main:app --host 0.0.0.0 --port 8000
```

### 2. Docker로 실행 (프로덕션)

```bash
# .env 파일 생성
cp .env.example .env

# Docker Compose로 모든 서비스 시작
docker-compose up -d

# 헬스 체크
curl http://localhost:8000/health
```

## 📡 API 엔드포인트

### 헬스 체크
```bash
GET /health
```

### 동기 분석 (실시간 결과 반환)
```bash
POST /analyze
Content-Type: application/json

{
  "repo": {
    "source": "git",
    "uri": "https://github.com/user/repo",
    "branch": "main"
  },
  "options": {
    "summary": "llm",
    "graph": "full",
    "metrics": "full"
  },
  "thresholds": {
    "codebleu_min": 0.42,
    "rougeL_min": 0.30
  }
}
```

### 비동기 분석 (run_id 반환)
```bash
POST /analyze-async
Content-Type: application/json

{
  "repo": {
    "source": "git",
    "uri": "https://github.com/user/repo"
  }
}

# 응답
{
  "run_id": "abc-123",
  "status": "queued",
  "message": "Analysis queued..."
}
```

### 결과 조회
```bash
GET /result/{run_id}
```

### HTML 리포트 생성
```bash
GET /report/{run_id}
```

### MCP 상태 확인
```bash
GET /mcp-status
```

## 🔧 LangGraph 워크플로우

```
START
  ↓
Parallel Execution:
  ├─ summarize_node (요약)
  ├─ build_graph_node (구조 분석)
  ├─ embed_code_node (임베딩)
  └─ analyze_repo_node (저장소 분석)
  ↓
evaluate_node (품질 평가)
  ↓
check_quality (조건부 분기)
  ├─ Quality OK → synthesize_node (최종 결과)
  └─ Quality Low → refine_node (재분석) → evaluate_node (루프)
  ↓
END
```

## 🎯 모델 통합 가이드

당신의 커스텀 모델을 통합하려면:

### 1. 모델 다운로드
```bash
# 로컬에서 모델 다운로드 및 캐싱
python -c "
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained('YOUR_MODEL_ID', cache_dir='models/summarization')
tokenizer = AutoTokenizer.from_pretrained('YOUR_MODEL_ID', cache_dir='models/summarization')
"
```

### 2. Model Loader 수정
`mcp/{service}/models_loader.py`에서:
```python
def initialize(self):
    self.pool.add_model(
        'your_model_key',
        'local_or_huggingface_path',
        model_type='transformer'
    )
```

### 3. Core Logic 수정
`mcp/{service}/analyzer.py` 또는 `summarizer.py`에서 모델 활용 로직 구현

## 📊 성능 최적화

### GPU 지원
```bash
# docker-compose.yml에서 CUDA 활성화
environment:
  - DEVICE=cuda  # 또는 cpu
```

### 모델 양자화
Large 모델을 양자화하여 메모리 사용량 감소:
```python
from transformers import AutoModelForSequenceClassification
import torch

model = AutoModelForSequenceClassification.from_pretrained(...)
quantized_model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear}, dtype=torch.qint8
)
```

## 🧪 테스트

### 단위 테스트 실행
```bash
pytest tests/ -v
```

### API 테스트
```bash
# Swagger UI에서 테스트
http://localhost:8000/docs
```

## 📝 로깅

각 서비스는 구조화된 로깅을 사용합니다:

```bash
# 로그 확인
docker-compose logs agent-service
docker-compose logs summarization-mcp
```

## 🔐 보안

- `.env` 파일에 민감한 정보 저장 (환경변수)
- 프로덕션에서는 HTTPS 사용
- API 인증 추가 권장 (API Key, JWT 등)

## 📚 문서

- `structure.md`: 상세 명세서
- `RESTAPI/`: 기존 REST API 구현

## 🤝 커스터마이제이션

### 새로운 MCP 추가
1. `mcp/new_service/` 디렉토리 생성
2. `main.py`, `analyzer.py`, `models_loader.py`, `Dockerfile` 작성
3. `docker-compose.yml`에 서비스 추가
4. `agent/nodes.py`에 새 노드 함수 추가
5. `agent/workflow.py`에 워크플로우 업데이트

### 평가 메트릭 커스터마이징
`agent/nodes.py`의 `evaluate_node`에서 메트릭 계산 방식 수정

## 🐛 문제 해결

### MCP 서비스 연결 실패
```bash
# 헬스 체크
curl http://localhost:9001/health
# 또는 Docker 내부에서
docker exec summarization-mcp curl http://localhost:9001/health
```

### 메모리 부족
- 배치 크기 감소
- 모델 양자화 활성화
- 임시 저장소 정리: `rm -rf /tmp/code_analysis_repos/*`

### GPU 메모리 부족
```python
import torch
torch.cuda.empty_cache()
```

## 📄 라이선스

[프로젝트 라이선스]

## 👨‍💻 기여

Pull Request는 환영합니다!