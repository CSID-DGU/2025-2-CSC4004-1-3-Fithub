# MCP Summarization - 코드 요약 마이크로서비스

## 📋 개요

**Summarization MCP**는 소스코드를 3가지 관점(기능, 의도, 구조)에서 분석하여 정확한 요약을 생성합니다.

- **포트:** 9001 (FastAPI)
- **모델:** CodeT5+ (기능) + StarCoder2 (의도) + UniXcoder (구조)
- **앙상블:** 품질 검증을 통한 통합 요약 생성

---

## 🎯 목표

| 관점 | 모델 | 역할 | 출력 |
|------|------|------|------|
| **기능** | CodeT5+ | 입출력 및 핵심 알고리즘 | "DB 조회를 통한 사용자 인증" |
| **의도** | StarCoder2 | 비즈니스 로직 및 존재 이유 | "보안 강화를 위해 JWT 토큰 발행" |
| **구조** | UniXcoder | 구조적 특징 (클래스, 함수 계층) | "async/await 패턴, 데코레이터 사용" |

---

## 📂 파일 구조

```
mcp/summarization/
├── main.py                 # FastAPI 서버 및 엔드포인트 ✅
├── summarizer.py           # CodeSummarizer 클래스 ⚠️
├── models_loader.py        # 모델 풀 관리 ⚠️
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

#### **Task 1: `summarizer.py` - `_generate_summary()` 메서드 구현**

**파일:** `mcp/summarization/summarizer.py`

**현재 상태:**
```python
def _generate_summary(self, code: str, summary_type: str) -> str:
    # 휴리스틱 기반 하드코딩 (데모)
    return f"Mock summary of {len(code)} lines"
```

**필요 상태:**
```python
def _generate_summary(self, code: str, summary_type: str) -> tuple[str, float]:
    """
    실제 모델 추론을 통한 요약 생성

    Args:
        code: 소스 코드
        summary_type: "function", "class", "file", "repository"

    Returns:
        (요약 텍스트, 신뢰도 점수)
    """

    # 1️⃣ 코드 전처리
    tokens = self.tokenizer.encode(code, max_length=512, truncation=True)

    # 2️⃣ 3개 모델 병렬 추론
    codet5_summary = self._infer_codet5(tokens)      # 기능
    starcoder2_summary = self._infer_starcoder2(tokens)  # 의도
    unixcoder_summary = self._infer_unixcoder(tokens)    # 구조

    # 3️⃣ 유사도 검증 (ROUGE, BLEU)
    similarity = self._validate_consistency(
        codet5_summary, starcoder2_summary, unixcoder_summary
    )

    # 4️⃣ 앙상블 결합
    if similarity > 0.7:
        # 높은 유사도 → 세 요약을 통합
        final_summary = self._ensemble_summaries(
            codet5_summary, starcoder2_summary, unixcoder_summary
        )
    else:
        # 낮은 유사도 → 최고 점수 선택
        final_summary = max(
            [codet5_summary, starcoder2_summary, unixcoder_summary],
            key=lambda x: self._score_summary(x, code)
        )

    confidence = similarity
    return final_summary, confidence
```

**구현 단계:**

1. **모델 초기화 (models_loader.py에서)**
   ```python
   self.codet5 = AutoModelForSeq2SeqLM.from_pretrained("Salesforce/codet5p-base")
   self.starcoder2 = AutoModelForCausalLM.from_pretrained("bigcode/starcoder2-3b")
   self.unixcoder = AutoModel.from_pretrained("microsoft/unixcoder-base")
   ```

2. **각 모델 추론 함수 작성**
   ```python
   def _infer_codet5(self, tokens):
       outputs = self.codet5.generate(input_ids=tokens, max_length=128)
       return self.tokenizer.decode(outputs[0])

   def _infer_starcoder2(self, tokens):
       outputs = self.starcoder2.generate(input_ids=tokens, max_length=256)
       return self.tokenizer.decode(outputs[0])

   def _infer_unixcoder(self, tokens):
       outputs = self.unixcoder(input_ids=tokens)
       # 구조 정보 추출
       return extract_structure_summary(outputs)
   ```

3. **유사도 검증**
   ```python
   def _validate_consistency(self, sum1, sum2, sum3):
       # ROUGE-L 스코어로 유사도 계산
       score12 = rouge_l(sum1, sum2)
       score23 = rouge_l(sum2, sum3)
       score13 = rouge_l(sum1, sum3)
       return (score12 + score23 + score13) / 3
   ```

#### **Task 2: `models_loader.py` - 모델 풀 구현**

**파일:** `mcp/summarization/models_loader.py`

**필요 구현:**
```python
from transformers import AutoModelForSeq2SeqLM, AutoModelForCausalLM, AutoModel

class SummarizationModelPool:
    def __init__(self):
        self.models = {}
        self.tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_models(self):
        """모든 모델 로드"""
        print("Loading CodeT5+...")
        self.models["codet5"] = AutoModelForSeq2SeqLM.from_pretrained(
            "Salesforce/codet5p-base"
        ).to(self.device)

        print("Loading StarCoder2...")
        self.models["starcoder2"] = AutoModelForCausalLM.from_pretrained(
            "bigcode/starcoder2-3b"
        ).to(self.device)

        print("Loading UniXcoder...")
        self.models["unixcoder"] = AutoModel.from_pretrained(
            "microsoft/unixcoder-base"
        ).to(self.device)

        print("Loading Tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5p-base")

    def get_model(self, model_name: str):
        """모델 반환 (없으면 로드)"""
        if model_name not in self.models:
            self.load_models()
        return self.models[model_name]

    def unload_model(self, model_name: str):
        """메모리에서 모델 제거"""
        if model_name in self.models:
            del self.models[model_name]
            torch.cuda.empty_cache()
```

---

## 📡 API 엔드포인트

### 1. 파일 요약

```bash
POST /summarize-file

{
  "file_path": "/path/to/auth_service.py",
  "code_type": "python"
}

Response:
{
  "file_id": "auth_service.py",
  "unified_summary": "DB 조회를 통한 사용자 인증 및 JWT 토큰 발행 함수",
  "keyword_summaries": {
    "function": "사용자 인증",
    "intent": "보안 강화",
    "structure": "async 함수, 데코레이터 사용"
  },
  "keywords": ["Authentication", "JWT", "Security"],
  "quality_score": 0.95
}
```

### 2. 코드 스니펫 요약

```bash
POST /summarize-code

{
  "code": "def authenticate_user(username, password): ...",
  "code_type": "function"  # "function", "class", "snippet"
}

Response: [위와 동일]
```

### 3. 저장소 요약 (배치)

```bash
POST /summarize-repository

{
  "repo_path": "/path/to/repo",
  "code_type": "python"
}

Response:
{
  "file_summaries": [
    {
      "file_id": "auth_service.py",
      "unified_summary": "...",
      "quality_score": 0.95
    },
    {
      "file_id": "db_model.py",
      "unified_summary": "...",
      "quality_score": 0.88
    }
  ],
  "total_quality_score": 0.92,
  "execution_time": 12.5
}
```

### 4. 헬스 체크

```bash
GET /health

Response:
{
  "status": "healthy",
  "models_loaded": ["codet5", "starcoder2", "unixcoder"],
  "memory_usage_mb": 8420
}
```

---

## 🚀 실행 방법

### 단독 실행 (개발용)

```bash
cd mcp/summarization
pip install -r requirements.txt
python -m uvicorn main:app --port 9001 --reload
```

### Docker 실행

```bash
docker build -t fithub-summarization mcp/summarization/
docker run -p 9001:9001 \
  -e TORCH_HOME=/tmp/torch_cache \
  fithub-summarization
```

### Docker Compose 실행

```bash
docker-compose up mcp-summarization
```

---

## 🧪 테스트

```bash
# 헬스 체크
curl http://localhost:9001/health

# 간단한 코드 요약
curl -X POST http://localhost:9001/summarize-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello(): return 42",
    "code_type": "function"
  }'
```

---

## 📊 성능 최적화

### 메모리 관리

```python
# models_loader.py에서
class SummarizationModelPool:
    def unload_idle_models(self, timeout_seconds=300):
        """오래 사용 안 한 모델 자동 언로드"""
        for model_name, last_used in self.last_used.items():
            if time.time() - last_used > timeout_seconds:
                self.unload_model(model_name)
```

### 배치 처리

```python
# main.py에서
@app.post("/batch-summarize")
async def batch_summarize(request: BatchSummarizeRequest):
    # 여러 파일을 큐에 넣고 병렬 처리
    results = await asyncio.gather(*[
        summarize_code(code) for code in request.codes
    ])
    return results
```

---

## 🔗 의존성

```
fastapi==0.104.0
uvicorn==0.24.0
pydantic==2.4.0
torch==2.0.1
transformers==4.34.0
numpy==1.24.0
scipy==1.11.0
rouge-score==0.1.2  # ROUGE 메트릭
sacrebleu==2.3.1    # BLEU 메트릭
```

---

## 📚 모델 정보

| 모델 | 크기 | 전문 분야 | 특징 |
|------|------|---------|------|
| CodeT5+ | 223M | 함수/클래스 | 코드-텍스트 정렬 최고 성능 |
| StarCoder2 | 3B | 의도/비즈니스 | 자연어 생성 특화 |
| UniXcoder | 125M | 구조/관계 | 멀티 언어 지원 |

---

## ⚡ 주의사항

1. **GPU 필수:** 3개 모델 동시 로드 시 VRAM 8GB 이상 필요
2. **첫 실행:** 모델 다운로드로 5-10분 소요
3. **타임아웃:** 대형 파일 분석 시 `timeout` 설정 필요
4. **배치 크기:** 메모리에 따라 배치 크기 조정 필요

---

## 📝 개발 체크리스트

- [ ] `_generate_summary()` 메서드 구현
- [ ] 3개 모델 추론 함수 작성
- [ ] ROUGE/BLEU 검증 로직
- [ ] 앙상블 통합 로직
- [ ] 모델 풀 구현 (models_loader.py)
- [ ] 메모리 관리 (모델 언로드)
- [ ] 배치 처리 최적화
- [ ] 로컬 테스트 (작은 코드 샘플)
- [ ] Docker 빌드 및 테스트

---

**참고:** 자세한 내용은 `IMPLEMENTATION_STATUS.md` → Task 2-1, 2-2를 참조하세요.