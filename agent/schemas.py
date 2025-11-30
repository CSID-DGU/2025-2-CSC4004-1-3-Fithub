"""
agent/schemas.py
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

# --- Requests ---

class RepoInput(BaseModel):
    repo_id: str = Field(..., description="Backend Repository ID")
    name: Optional[str] = Field(None, description="Repository Name")

class Thresholds(BaseModel):
    consistency_min: float = 0.7
    retry_max: int = 2

class AnalyzeRequest(BaseModel):
    repo: RepoInput
    options: Dict[str, Any] = {}
    thresholds: Optional[Thresholds] = Field(default_factory=Thresholds)

# --- Responses ---

class AnalyzeResponse(BaseModel):
    run_id: str
    status: str

class ResultResponse(BaseModel):
    run_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
