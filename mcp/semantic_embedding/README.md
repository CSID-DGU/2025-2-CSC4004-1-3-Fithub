# MCP Semantic Embedding - 의미 임베딩 마이크로서비스

## 📋 개요

**Semantic Embedding MCP**는 소스코드를 고차원 벡터 공간으로 변환하여 의미 기반 유사도 계산을 수행합니다.

- **포트:** 9003 (FastAPI)
- **모델:** CodeBERT + GraphCodeBERT (앙상블)
- **출력:** 768차원 임베딩 벡터 + 유사도 스코어

---

## 🎯 목표

| 항목 | 설명 | 활용 |
|------|------|------|
| **코드 임베딩** | 코드를 768D 벡터로 변환 | 유사 코드 검색, 클러스터링 |
| **벡터 유사도** | 두 코드의 의미 유사도 계산 | 코드 재사용 추천, 중복 탐지 |
| **배치 임베딩** | 여러 파일 병렬 임베딩 | 저장소 전체 벡터화 |

---

## 📂 파일 구조

```
mcp/semantic_embedding/
├── main.py                 # FastAPI 서버 및 엔드포인트 ✅
├── embedder.py             # CodeEmbedder 클래스 ⚠️ (40% 구현)
├── models_loader.py        # EmbeddingModelPool ⚠️
├── requirements.txt        # 의존성 ✅
├── Dockerfile              # 컨테이너 빌드 ✅
└── README.md               # 이 문서
```

---

## ⚙️ 구현 상태 및 필요 작업

### ⚠️ 긴급 필요 작업

#### **Task 1: `embedder.py` - `_generate_embedding()` 메서드 구현**

**파일:** `mcp/semantic_embedding/embedder.py`

**현재 상태:**
```python
def _generate_embedding(self, code: str) -> list[float]:
    # 랜덤 벡터 (데모)
    return [random.random() for _ in range(768)]  # ❌
```

**필요 상태:**
```python
def _generate_embedding(self, code: str) -> list[float]:
    """
    실제 모델을 사용한 임베딩 생성

    파이프라인:
    1. 코드 전처리 (토크나이징, 길이 제한)
    2. 2개 모델 병렬 추론
       - CodeBERT: 기본 의미 벡터
       - GraphCodeBERT: 데이터 흐름 반영 벡터
    3. 벡터 앙상블 (0.5 + 0.5 가중 평균)
    4. L2 정규화 후 반환

    Args:
        code: 소스 코드 문자열

    Returns:
        768차원 정규화된 임베딩 벡터
    """

    # 1️⃣ 코드 전처리
    tokens = self.tokenizer.encode(
        code,
        max_length=512,
        truncation=True,
        padding=True,
        return_tensors="pt"
    ).to(self.device)

    # 2️⃣ 2개 모델 병렬 추론
    with torch.no_grad():
        # CodeBERT 추론
        codebert_output = self.codebert_model(tokens)
        codebert_embedding = codebert_output.last_hidden_state[:, 0, :]  # [CLS] 토큰

        # GraphCodeBERT 추론
        graphcodebert_output = self.graphcodebert_model(tokens)
        graphcodebert_embedding = graphcodebert_output.last_hidden_state[:, 0, :]

    # 3️⃣ 앙상블 (가중 평균)
    fused_embedding = 0.5 * codebert_embedding + 0.5 * graphcodebert_embedding

    # 4️⃣ L2 정규화
    normalized_embedding = F.normalize(fused_embedding, p=2, dim=1)

    return normalized_embedding[0].cpu().tolist()
```

#### **Task 2: `models_loader.py` - 모델 풀 구현**

**파일:** `mcp/semantic_embedding/models_loader.py`

```python
from transformers import AutoModel, AutoTokenizer
import torch

class EmbeddingModelPool:
    """임베딩용 모델 풀 관리"""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.models = {}
        self.tokenizer = None

    def load_models(self):
        """모델 초기화"""
        print("Loading CodeBERT...")
        self.models["codebert"] = AutoModel.from_pretrained(
            "microsoft/codebert-base"
        ).to(self.device)

        print("Loading GraphCodeBERT...")
        self.models["graphcodebert"] = AutoModel.from_pretrained(
            "microsoft/graphcodebert-base"
        ).to(self.device)

        print("Loading Tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

        # 평가 모드 (드롭아웃 비활성화)
        for model in self.models.values():
            model.eval()

    def get_model(self, model_name: str):
        """특정 모델 반환"""
        if model_name not in self.models:
            self.load_models()
        return self.models[model_name]

    def get_tokenizer(self):
        """토크나이저 반환"""
        if self.tokenizer is None:
            self.load_models()
        return self.tokenizer

    def unload_all(self):
        """모든 모델 메모리에서 제거"""
        self.models.clear()
        self.tokenizer = None
        torch.cuda.empty_cache()
```

---

## 📡 API 엔드포인트

### 1. 단일 코드 임베딩

```bash
POST /embed

{
  "code": "def authenticate_user(username, password): ..."
}

Response:
{
  "code_id": "snippet_001",
  "embedding": [0.123, -0.456, ..., 0.789],  # 768D 벡터
  "dimension": 768,
  "model": "codebert+graphcodebert"
}
```

### 2. 배치 임베딩

```bash
POST /batch-embed

{
  "codes": [
    "def func1(): ...",
    "def func2(): ...",
    "class MyClass: ..."
  ]
}

Response:
{
  "embeddings": [
    [0.123, -0.456, ...],
    [0.234, -0.567, ...],
    [0.345, -0.678, ...]
  ],
  "count": 3,
  "execution_time": 2.34
}
```

### 3. 유사도 계산

```bash
POST /similarity

{
  "code1": "def authenticate(): ...",
  "code2": "def login(): ..."
}

Response:
{
  "similarity_score": 0.8742,  # 코사인 유사도 [0, 1]
  "code1_id": "auth_fn",
  "code2_id": "login_fn"
}
```

### 4. 헬스 체크

```bash
GET /health

Response:
{
  "status": "healthy",
  "models_loaded": ["codebert", "graphcodebert"],
  "memory_usage_mb": 2048
}
```

---

## 🚀 실행 방법

### 단독 실행

```bash
cd mcp/semantic_embedding
pip install -r requirements.txt
python -m uvicorn main:app --port 9003 --reload
```

### Docker 실행

```bash
docker build -t fithub-embedding mcp/semantic_embedding/
docker run -p 9003:9003 -e TORCH_HOME=/tmp/torch fithub-embedding
```

---

## 🧪 테스트

```bash
# 헬스 체크
curl http://localhost:9003/health

# 임베딩 생성
curl -X POST http://localhost:9003/embed \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello(): return 42"
  }'

# 유사도 계산
curl -X POST http://localhost:9003/similarity \
  -H "Content-Type: application/json" \
  -d '{
    "code1": "def add(a, b): return a + b",
    "code2": "def sum(x, y): return x + y"
  }'
```

---

## 📊 모델 정보

| 모델 | 크기 | 특징 | 용도 |
|------|------|------|------|
| **CodeBERT** | 125M | 기본 의미 벡터 | 코드-문서 정렬 |
| **GraphCodeBERT** | 125M | 데이터 흐름 그래프 반영 | 제어 흐름 분석 |

**앙상블 방식:**
```
최종 임베딩 = 0.5 * CodeBERT + 0.5 * GraphCodeBERT
```

---

## ⚡ 성능 최적화

### 메모리 효율

```python
# 모델을 평가 모드로 설정 (메모리 절감)
model.eval()

# 그래디언트 계산 비활성화
with torch.no_grad():
    embeddings = model(**inputs)
```

### 배치 처리

```python
# 여러 코드를 한 번에 처리
def batch_embed(self, codes: list) -> list:
    results = []
    for code in codes:
        embedding = self._generate_embedding(code)
        results.append(embedding)
    return results
```

### GPU 활용

```python
# GPU 자동 감지
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
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
scipy==1.11.0  # cosine_similarity
```

---

## 📝 개발 체크리스트

- [ ] `_generate_embedding()` 메서드 구현
- [ ] CodeBERT 모델 로드 및 추론
- [ ] GraphCodeBERT 모델 로드 및 추론
- [ ] 벡터 앙상블 (0.5 + 0.5)
- [ ] L2 정규화
- [ ] models_loader.py 완성
- [ ] batch_embed() 최적화
- [ ] 유사도 계산 함수
- [ ] 메모리 관리 (모델 언로드)
- [ ] 로컬 테스트
- [ ] Docker 빌드

---

**참고:** 자세한 내용은 `IMPLEMENTATION_STATUS.md` → Task 4-1, 4-2를 참조하세요.