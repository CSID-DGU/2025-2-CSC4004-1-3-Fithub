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

    # --- Local Mode Settings ---
    USE_LOCAL_LLM = True # Use Local Mistral/Chat for Analysis (Rule-based Fallback effectively)
    USE_LOCAL_SUMMARIZER = True # Use Local CodeT5 for Summarization

    # --- 🤖 Model Configurations (Verified for Free Tier) ---

    # 1. [요약] Salesforce/codet5-base
    # 이유: User preferred CodeT5. API compatibility issues are resolved by using proper endpoint or local fallback.
    MODEL_SUMMARIZER = "Salesforce/codet5-base"

    # 2. [임베딩] microsoft/graphcodebert-base
    # 이유: 코드 임베딩의 표준. Feature Extraction API 지원이 확실함.
    MODEL_EMBEDDER = "microsoft/graphcodebert-base"

    # 3. [분석/태깅]
    MODEL_LLM = "mistralai/Mistral-7B-Instruct-v0.3"
    MODEL_LLM_OPENAI = "gpt-4o" # OpenAI 사용 시 기본 모델

    # --- 🤖 Ensemble Summarization Models (Robust Role-Based Strategy) ---
    # Unified Model: Qwen/Qwen2.5-Coder-32B-Instruct (SOTA Open Source Code Model)
    # We use ONE powerful model with 3 different "System Prompts" (Personas).
    MODEL_SUMMARIZER_LOGIC = "Qwen/Qwen2.5-Coder-32B-Instruct"
    MODEL_SUMMARIZER_INTENT = "Qwen/Qwen2.5-Coder-32B-Instruct"
    MODEL_SUMMARIZER_STRUCTURE = "Qwen/Qwen2.5-Coder-32B-Instruct"
    
    # Flag to enable the new Prompt-based dispatch logic
    USE_ROLE_BASED_ENSEMBLE = True
