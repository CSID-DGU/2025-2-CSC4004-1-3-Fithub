# 빠른 시작 가이드

## 📋 필수 사항

- Python 3.11+
- Docker & Docker Compose (프로덕션용)
- Git
- GPU (선택사항, 하지만 권장됨)

## 🚀 5분 안에 시작하기

### 방법 1: Docker Compose (권장)

```bash
# 1. 프로젝트 디렉토리로 이동
cd /Users/iyeonglag/PycharmProjects/2025-2-CSC4004-1-3-Fithub

# 2. .env 파일 생성
cp .env.example .env

# 3. 모든 서비스 시작
docker-compose up -d

# 4. 헬스 체크
curl http://localhost:8000/health

# 5. API 문서 보기
# http://localhost:8000/docs (Swagger UI)
```

### 방법 2: 로컬 실행 (개발용)

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. MCP 서비스 시작 (터미널 1-5)
python -m uvicorn mcp.summarization.main:app --port 9001
python -m uvicorn mcp.structural_analysis.main:app --port 9002
python -m uvicorn mcp.semantic_embedding.main:app --port 9003
python -m uvicorn mcp.repository_analysis.main:app --port 9004
python -m uvicorn mcp.task_recommender.main:app --port 9005

# 3. Agent Service 시작 (터미널 6)
python -m uvicorn agent.main:app --port 8000
```

## 🧠 AI 모델 다운로드 및 설정

### 모델 다운로드 스크립트

```python
# setup_models.py 실행
python setup_models.py
```

또는 수동으로:

```python
from transformers import AutoModel, AutoTokenizer
import os

# 디렉토리 생성
os.makedirs('models/summarization', exist_ok=True)

# CodeT5+ 다운로드
model = AutoModel.from_pretrained(
    'Salesforce/codet5p-base',
    cache_dir='models/summarization'
)
tokenizer = AutoTokenizer.from_pretrained(
    'Salesforce/codet5p-base',
    cache_dir='models/summarization'
)

print("✓ 모델 다운로드 완료!")
```

## 📊 첫 번째 분석 실행

### 1. 공개 저장소 분석

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo": {
      "source": "git",
      "uri": "https://github.com/pallets/flask",
      "branch": "main"
    },
    "options": {
      "summary": "llm",
      "graph": "full",
      "metrics": "full"
    }
  }'
```

### 2. 로컬 저장소 분석

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo": {
      "source": "local",
      "uri": "/path/to/your/repo"
    }
  }'
```

### 3. 비동기 분석 (오래 걸리는 저장소)

```bash
# 분석 시작
curl -X POST http://localhost:8000/analyze-async \
  -H "Content-Type: application/json" \
  -d '{
    "repo": {
      "source": "git",
      "uri": "https://github.com/torvalds/linux"
    }
  }'

# 응답: {"run_id": "abc-123", "status": "queued"}

# 결과 조회
curl http://localhost:8000/result/abc-123

# HTML 리포트
curl http://localhost:8000/report/abc-123 > report.html
```

## 🔧 모델 통합하기

당신의 커스텀 모델을 Summarization MCP에 추가:

### 1. models_loader.py 수정

```python
# mcp/summarization/models_loader.py

class SummarizationModelPool:
    def initialize(self):
        # 기존 코드...

        # 당신의 커스텀 모델 추가
        try:
            self.pool.add_model(
                "my_custom_model",
                "/path/to/local/model",  # 또는 HuggingFace ID
                model_type="transformer"
            )
            logger.info("✓ My Custom Model loaded")
        except Exception as e:
            logger.warning(f"Failed to load: {e}")
```

### 2. summarizer.py 수정

```python
# mcp/summarization/summarizer.py

def _generate_summary(self, code: str, model_name: str = "codebert") -> str:
    """모델을 사용하여 요약을 생성합니다."""

    if model_name == "my_custom_model":
        # 당신의 커스텀 모델 로직
        model, tokenizer, name = self.model_pool.pool.get_model("my_custom_model"), ...

        # 모델 추론 로직
        inputs = tokenizer(code, return_tensors="pt", max_length=512, truncation=True)
        outputs = model(**inputs)

        # 결과 처리
        summary = "생성된 요약..."
        return summary

    # 기존 로직...
```

## 📊 시스템 상태 확인

```bash
# 모든 서비스 상태
curl http://localhost:8000/mcp-status

# Agent Service 로그
docker logs agent-service -f

# 특정 MCP 로그
docker logs summarization-mcp -f
```

## 🐛 문제 해결

### "Connection refused" 오류
```bash
# MCP 서비스가 시작되었는지 확인
curl http://localhost:9001/health

# Docker에서 실행 중이면
docker ps | grep mcp
```

### 모델 다운로드 오류
```bash
# HuggingFace 토큰 설정
huggingface-cli login

# 또는 환경변수 설정
export HF_TOKEN=your_token_here
```

### 메모리 부족
```bash
# CPU 전용으로 실행
export DEVICE=cpu

# 배치 크기 감소 (mcp/*/main.py에서)
# batch_size = 4  # 기본값에서 감소
```

## 📚 다음 단계

1. **구조 이해**: `structure.md` 읽기
2. **API 탐색**: `http://localhost:8000/docs` (Swagger UI)
3. **모델 커스터마이징**: 당신의 모델 통합
4. **배포**: Docker Compose를 AWS/GCP/Azure에 배포
5. **성능 최적화**: GPU 활성화, 배치 처리, 캐싱

## 🆘 지원

- 문제 발생 시: `README.md`의 "문제 해결" 섹션 참고
- 상세 문서: `structure.md`
- API 문서: `http://localhost:8000/docs`
