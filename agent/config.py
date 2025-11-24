"""
agent/config.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    HF_API_KEY = os.getenv("HF_API_KEY")

    # URLs
    # GPU Server URL (Graph Generation)
    GRAPH_MODEL_SERVER_URL = os.getenv("GRAPH_MODEL_SERVER_URL", "http://localhost:9000")

    # Settings
    MAX_RETRIES = 2
    TIMEOUT = 60.0
