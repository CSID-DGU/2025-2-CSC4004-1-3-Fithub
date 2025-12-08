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

    # 1. [요약] Qwen/Qwen2.5-Coder-1.5B-Instruct
    # 이유: 최신 소형 언어 모델로서 HF Inference API (무료) 지원이 원활하며 Chat API 호환됨.
    # CodeT5는 text_generation API 호환성 문제(StopIteration)로 교체됨.
    MODEL_SUMMARIZER = "Qwen/Qwen2.5-Coder-1.5B-Instruct"

    # 2. [임베딩] microsoft/graphcodebert-base
    # 이유: 코드 임베딩의 표준. Feature Extraction API 지원이 확실함.
    MODEL_EMBEDDER = "microsoft/graphcodebert-base"

    # 3. [분석/태깅]
    MODEL_LLM = "mistralai/Mistral-7B-Instruct-v0.3"
    MODEL_LLM_OPENAI = "gpt-4o" # OpenAI 사용 시 기본 모델

    # --- 🤖 Ensemble Summarization Models ---
    # Qwen으로 통일 (Role Prompting으로 관점 분리)
    MODEL_SUMMARIZER_LOGIC = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    MODEL_SUMMARIZER_INTENT = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    MODEL_SUMMARIZER_STRUCTURE = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
