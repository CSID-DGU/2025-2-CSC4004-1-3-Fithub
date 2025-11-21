# 🎯 당신이 해야 할 일들 (YOUR_TODO)

현재 **시스템 프레임워크는 완성**되었습니다. 아래는 당신이 직접 구현해야 하는 작업들입니다.

---

## ✅ 우선순위별 작업 목록

### **Phase 1: 모델 다운로드 및 설정** (필수)

#### 1. AI 모델 준비
- [ ] **각 MCP별로 필요한 모델을 로컬에 다운로드**
  - Summarization: CodeT5+, StarCoder2, CodeLlama, UniXcoder 등
  - Structural Analysis: GraphCodeBERT, CodeBERT
  - Semantic Embedding: CodeBERT, CuBERT
  - Repository Analysis: 분석용 CodeBERT
  - Task Recommender: 추천용 CodeBERT

**방법:**
```bash
# 자동 다운로드 (권장)
python setup_models.py --non-interactive

# 또는 수동으로
python -c "
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained('Salesforce/codet5p-base', cache_dir='models/summarization')
tokenizer = AutoTokenizer.from_pretrained('Salesforce/codet5p-base', cache_dir='models/summarization')
"
```

**결과 확인:**
```
models/
├── summarization/
│   ├── codet5/
│   ├── starcoder2/
│   ├── codellama/
│   └── unixcoder/
├── structural_analysis/
│   ├── graphcodebert/
│   └── codebert/
...
```

---

### **Phase 2: 모델 통합** (핵심 작업)

#### 2. Summarization MCP에 모델 통합
**파일:** `mcp/summarization/summarizer.py`

- [ ] `_generate_summary()` 메서드 구현
  - 현재: 휴리스틱 기반 요약 (데모용)
  - 변경: 실제 모델을 사용한 요약 생성

**예시 구현:**
```python
def _generate_summary(self, code: str, model_name: str = "codet5") -> str:
    """실제 모델을 사용하여 요약을 생성합니다."""

    if model_name == "codet5":
        model, tokenizer, _ = self.model_pool.get_primary_model()

        # 코드 토큰화
        inputs = tokenizer(
            code,
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).to(self.device)

        # 모델 추론
        with torch.no_grad():
            outputs = model(**inputs)

        # 결과 처리 (당신의 모델 출력 형식에 맞게)
        # 예: logits → summary text
        summary = self._decode_output(outputs)

        return summary

    # 다른 모델들...
```

#### 3. Structural Analysis MCP에 모델 통합
**파일:** `mcp/structural_analysis/analyzer.py`

- [ ] GraphCodeBERT를 실제로 사용한 그래프 생성
  - 현재: AST 파싱만 사용
  - 변경: 모델의 그래프 임베딩을 활용한 구조 분석

**구현할 메서드:**
```python
def _enhance_graph_with_embeddings(self, nodes, edges):
    """GraphCodeBERT로 노드 임베딩을 강화합니다."""
    # 각 노드를 모델로 임베딩
    # 유사도 기반으로 엣지 가중치 조정
    pass
```

#### 4. Semantic Embedding MCP에 모델 통합
**파일:** `mcp/semantic_embedding/embedder.py`

- [ ] CodeBERT를 실제로 사용한 임베딩 생성
  - 현재: 의사난수 기반 임베딩 (데모용)
  - 변경: 실제 모델의 768차원 벡터 생성

**구현할 메서드:**
```python
def _generate_embedding(self, code: str, model_name: str = "codebert") -> List[float]:
    """실제 모델을 사용하여 임베딩을 생성합니다."""

    model, tokenizer, _ = self.model_pool.get_primary_model()

    # 토큰화
    inputs = tokenizer(
        code,
        return_tensors="pt",
        max_length=512,
        truncation=True
    ).to(self.device)

    # 모델 추론
    with torch.no_grad():
        outputs = model(**inputs)

    # [CLS] 토큰의 임베딩 추출 (또는 평균 풀링)
    embedding = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()

    return embedding.tolist()
```

#### 5. Repository Analysis MCP에 모델 통합
**파일:** `mcp/repository_analysis/analyzer.py`

- [ ] 모델을 사용한 저장소 요약 개선
  - 현재: 기본 통계만 제공
  - 변경: 모델 기반 거시적 분석

#### 6. Task Recommender MCP에 모델 통합
**파일:** `mcp/task_recommender/recommender.py`

- [ ] 통합 분석 기반 스마트 추천
  - 현재: 규칙 기반 추천
  - 변경: 모델 기반 복잡도 분석 추가

---

### **Phase 3: 평가 메트릭 구현** (선택적이지만 권장)

#### 7. Agent Service의 평가 메트릭 개선
**파일:** `agent/nodes.py` - `evaluate_node()`

현재 메트릭은 더미 데이터입니다. 실제 메트릭 구현:

- [ ] **CodeBLEU** 계산
  ```python
  # CodeBLEU 점수 계산
  from codebeu import calc_code_bleu
  codebleu = calc_code_bleu(refs=[original], hyps=[summary], lang="python")
  ```

- [ ] **BLEURT** 스코어
  ```python
  # BLEURT (학습된 평가 메트릭)
  from bleurt import score as bleurt_score
  bleurt = bleurt_score.score(original, summary)
  ```

- [ ] **ROUGE-L** 점수
  ```python
  from rouge_score import rouge_scorer
  rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
  rouge_l = rouge.score(original, summary)
  ```

- [ ] **Graph Edit Distance (GED)**
  ```python
  # 원본 그래프와 생성 그래프 간 편집 거리
  import networkx as nx
  ged = nx.graph_edit_distance(original_graph, generated_graph)
  ```

---

### **Phase 4: 테스트 및 검증** (권장)

#### 8. 단위 테스트 작성
**디렉토리 생성:** `tests/`

- [ ] `tests/test_summarization.py`
  ```python
  def test_summarize_function():
      # 테스트 코드 작성
      pass
  ```

- [ ] `tests/test_structural_analysis.py`
  - 그래프 생성 검증

- [ ] `tests/test_embeddings.py`
  - 임베딩 차원 및 유사도 검증

- [ ] `tests/test_workflow.py`
  - LangGraph 워크플로우 검증

#### 9. 통합 테스트
- [ ] 전체 워크플로우 테스트
  ```bash
  python -m pytest tests/ -v
  ```

- [ ] Docker 환경에서 테스트
  ```bash
  docker-compose up -d
  curl http://localhost:8000/health
  ```

---

### **Phase 5: 성능 최적화** (선택적)

#### 10. 모델 최적화
- [ ] **양자화 (Quantization)**
  ```python
  # INT8 양자화로 메모리 30% 감소
  quantized_model = torch.quantization.quantize_dynamic(
      model, {torch.nn.Linear}, dtype=torch.qint8
  )
  ```

- [ ] **배치 처리**
  ```python
  # MCP 엔드포인트에 배치 처리 추가
  @app.post("/batch-summarize")
  async def batch_summarize(requests: List[SummarizeRequest]):
      # 여러 요청을 한번에 처리
      pass
  ```

- [ ] **캐싱**
  ```python
  # 동일한 입력에 대해 캐싱
  from functools import lru_cache
  @lru_cache(maxsize=1000)
  def _cached_embedding(code_hash):
      pass
  ```

- [ ] **GPU 지원 활성화**
  ```bash
  # docker-compose.yml에서
  environment:
    - DEVICE=cuda
    - CUDA_VISIBLE_DEVICES=0
  ```

#### 11. API 성능 개선
- [ ] **응답 압축**
- [ ] **요청 검증 강화**
- [ ] **레이트 리미팅 추가**

---

### **Phase 6: 배포 준비** (선택적)

#### 12. 프로덕션 설정
- [ ] **환경 변수 설정**
  ```bash
  cp .env.example .env
  # .env 파일 수정
  ```

- [ ] **로깅 설정**
  - 구조화된 로깅 추가
  - 로그 레벨 조정

- [ ] **모니터링 추가**
  - Prometheus 메트릭
  - 헬스 체크 엔드포인트

#### 13. 클라우드 배포
- [ ] **AWS 배포**
  - ECR에 이미지 푸시
  - ECS/EKS에 배포

- [ ] **GCP/Azure 배포**
  - Cloud Run / Container Instances

---

## 📋 구체적인 작업 흐름

### **Step 1: 모델 다운로드 (1-2시간)**
```bash
# 모든 모델 자동 다운로드
python setup_models.py --non-interactive

# 용량 확인
du -sh models/
```

### **Step 2: Summarization 통합 (2-3시간)**
1. `mcp/summarization/summarizer.py` 열기
2. `_generate_summary()` 메서드 구현
3. 로컬 테스트: `python -m pytest tests/test_summarization.py`

### **Step 3: 나머지 MCP 통합 (1-2시간 각각)**
- Structural Analysis
- Semantic Embedding
- Repository Analysis
- Task Recommender

### **Step 4: 평가 메트릭 구현 (2-3시간)**
- Agent의 `evaluate_node()` 메서드 구현
- 메트릭 라이브러리 설치

### **Step 5: 통합 테스트 (1시간)**
```bash
docker-compose up -d
# API 테스트
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo": {"source": "local", "uri": "/path/to/test/repo"}}'
```

---

## 🔍 모델 통합 체크리스트

각 MCP에 대해:

- [ ] 모델 다운로드 완료
- [ ] `models_loader.py`에서 모델 로드 확인
- [ ] 핵심 로직 파일에서 모델 사용 코드 작성
- [ ] 로컬 테스트 통과
- [ ] Docker 환경에서 테스트 통과
- [ ] 응답 형식 확인

---

## 📚 참고할 파일들

당신이 수정해야 할 주요 파일들:

```
mcp/
├── summarization/
│   ├── summarizer.py          ← 요약 로직 구현
│   ├── models_loader.py        ← 모델 로드 (이미 대부분 구현됨)
│   └── main.py                 ← 변경 불필요
│
├── structural_analysis/
│   ├── analyzer.py             ← 그래프 생성 로직 구현
│   ├── models_loader.py
│   └── main.py
│
├── semantic_embedding/
│   ├── embedder.py             ← 임베딩 로직 구현
│   ├── models_loader.py
│   └── main.py
│
├── repository_analysis/
│   ├── analyzer.py             ← 저장소 분석 로직 개선
│   ├── models_loader.py
│   └── main.py
│
└── task_recommender/
    ├── recommender.py          ← 추천 로직 개선
    ├── models_loader.py
    └── main.py

agent/
├── nodes.py                    ← evaluate_node() 메트릭 구현
├── workflow.py                 ← 변경 불필요
├── main.py                     ← 변경 불필요
└── config.py                   ← 필요시 설정 수정
```

## 💡 팁

1. **작은 저장소부터 시작**
   - Flask, requests 같은 작은 저장소로 테스트

2. **모델 실행 속도 확인**
   - CPU로 먼저 테스트 후 GPU 활성화

3. **디버깅**
   ```bash
   # 각 MCP 로그 확인
   docker logs summarization-mcp -f

   # Python 디버거 사용
   import pdb; pdb.set_trace()
   ```

4. **점진적 구현**
   - 한 번에 모든 모델 구현하지 말기
   - 하나씩 완성하고 테스트

5. **문서화**
   - 각 메서드에 docstring 추가
   - 모델별 파라미터 문서화

---

## ✨ 완료 후

모든 작업을 완료하면:

```bash
# 최종 테스트
docker-compose down && docker-compose up -d

# API 테스트
curl http://localhost:8000/health

# 첫 분석 실행
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo": {
      "source": "git",
      "uri": "https://github.com/pallets/flask"
    }
  }'

# 모든 테스트 통과
pytest tests/ -v --cov
```

---

**질문이 있으시면 이 파일의 해당 섹션을 참고하세요!** 🚀
