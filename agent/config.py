"""
agent/config.py
Central configuration with Verified Safe Models for Free Tier.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # --- External APIs ---
    HF_API_KEY = os.getenv("HF_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # --- Model Provider Settings ---
    # Options: "huggingface", "openai"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "huggingface")

    # --- Internal Services ---
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://backend:4000/api")
    GRAPH_MODEL_SERVER_URL = os.getenv("GRAPH_MODEL_SERVER_URL", "http://localhost:9000")

    # --- File System ---
    TEMP_DIR = "./temp_repos"
    LOCAL_MODEL_DIR = "/Users/iyeonglag/PycharmProjects/2025-2-CSC4004-1-3-Fithub/models/RepoGraph"

    # --- Settings ---
    MAX_RETRIES = 2
    TIMEOUT = 60.0
    MAX_ANALYSIS_FILES = 50 # Reduced for testing (was 10000)

    # --- 🤖 Model Configurations (Verified for Free Tier) ---

    # 1. [요약] Salesforce/codet5-base
    # 이유: CodeT5+ 보다 구형이지만, HF Free API에서 호환성이 훨씬 좋음 (에러 확률 낮음)
    MODEL_SUMMARIZER = "Salesforce/codet5-base"

    # 2. [임베딩] microsoft/graphcodebert-base
    # 이유: 코드 임베딩의 표준. Feature Extraction API 지원이 확실함.
    MODEL_EMBEDDER = "microsoft/graphcodebert-base"

    # 3. [분석/태깅]
    MODEL_LLM = "mistralai/Mistral-7B-Instruct-v0.3"
    MODEL_LLM_OPENAI = "gpt-4o" # OpenAI 사용 시 기본 모델

    # --- 🤖 Ensemble Summarization Models ---
    # Logic Expert: 기능 요약 (입출력, 알고리즘)
    MODEL_SUMMARIZER_LOGIC = "Salesforce/codet5-base"

    # Intent Expert: 의도 분석 (비즈니스 로직, 존재 이유)
    MODEL_SUMMARIZER_INTENT = "bigcode/starcoder2-3b"

    # Structure Expert: 구조적 특징 (AST 패턴, 디자인 패턴)
    MODEL_SUMMARIZER_STRUCTURE = "microsoft/unixcoder-base"
