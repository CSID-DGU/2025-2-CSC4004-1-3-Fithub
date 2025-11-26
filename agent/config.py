"""
agent/config.py
Central configuration for Fithub Agent.
Manages API Keys, Service URLs, and AI Model IDs.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- 1. External APIs ---
    HF_API_KEY = os.getenv("HF_API_KEY")
    if not HF_API_KEY:
        print("⚠️ Warning: HF_API_KEY is missing in .env file.")

    # --- 2. Internal Services ---
    # Docker Compose Network: 'backend' service at port 4000
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:4000/api")

    # --- 3. File System ---
    TEMP_DIR = "/app/shared/temp_repos"

    # [Local Graph Model Path]
    # GitHub에서 다운로드 받은 GNN 모델 코드가 위치할 경로
    # Docker 환경 기준: /app/local_models/graph_model_source
    LOCAL_MODEL_DIR = os.getenv("LOCAL_MODEL_DIR", os.path.abspath("local_models/graph_model_source"))

    # --- 4. Settings ---
    MAX_RETRIES = 2
    TIMEOUT = 60.0

    # --- 5. 🤖 Model Configurations (Centralized Safe List) ---
    # Hugging Face Free API에서 안정적으로 동작하는 검증된 모델들입니다.

    # [Phase 1: Summarization]
    # CodeT5-base: API 호환성이 좋고 요약 성능이 준수한 모델
    MODEL_SUMMARIZER = "Salesforce/codet5-base"

    # [Phase 1: Embedding]
    # GraphCodeBERT: 코드 구조 임베딩의 표준
    MODEL_EMBEDDER = "microsoft/graphcodebert-base"

    # [Phase 2: Repository Analysis (The Architect)]
    # Mistral-7B-Instruct-v0.3: Llama-3와 달리 승인(Gate) 없이 즉시 사용 가능한 고성능 LLM
    MODEL_LLM = "mistralai/Mistral-7B-Instruct-v0.3"
