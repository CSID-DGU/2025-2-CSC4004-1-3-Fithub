"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime


# ==================== Input Schemas ====================

class RepoInput(BaseModel):
    """저장소 입력 정보."""
    source: Literal["git", "local", "zip"] = Field(
        ...,
        description="저장소 소스 타입"
    )
    uri: str = Field(
        ...,
        description="저장소 URI (Git URL 또는 로컬 경로)"
    )
    branch: str = Field(
        default="main",
        description="Git 브랜치 (source='git'일 때만 사용)"
    )


class Thresholds(BaseModel):
    """품질 평가 임계값."""
    codebleu_min: float = Field(
        default=0.42,
        ge=0.0, le=1.0,
        description="CodeBLEU 최소값"
    )
    bleurt_min: float = Field(
        default=0.05,
        ge=0.0, le=1.0,
        description="BLEURT 최소값"
    )
    rougeL_min: float = Field(
        default=0.30,
        ge=0.0, le=1.0,
        description="ROUGE-L 최소값"
    )
    edge_f1_min: float = Field(
        default=0.80,
        ge=0.0, le=1.0,
        description="Edge F1 최소값"
    )
    ged_max: float = Field(
        default=50.0,
        ge=0.0,
        description="Graph Edit Distance 최대값"
    )
    retry_max: int = Field(
        default=2,
        ge=0,
        description="최대 재시도 횟수"
    )
    ensemble: bool = Field(
        default=True,
        description="앙상블 모델 사용 여부"
    )


class AnalyzeRequest(BaseModel):
    """분석 요청 스키마."""
    repo: RepoInput = Field(
        ...,
        description="저장소 정보"
    )
    options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "summary": "llm",
            "graph": "full",
            "metrics": "full"
        },
        description="분석 옵션"
    )
    thresholds: Thresholds = Field(
        default_factory=Thresholds,
        description="품질 임계값"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        description="상위 K개 결과 반환"
    )


# ==================== Data Structure Schemas ====================

class Node(BaseModel):
    """그래프 노드."""
    id: str = Field(
        ...,
        description="노드 고유 ID"
    )
    label: str = Field(
        ...,
        description="노드 레이블"
    )
    type: str = Field(
        ...,
        description="노드 타입 (repo, dir, file, class, function)"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="파일 경로"
    )
    lineno: Optional[int] = Field(
        default=None,
        description="시작 줄 번호"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 메타데이터"
    )


class Edge(BaseModel):
    """그래프 엣지."""
    source: str = Field(
        ...,
        description="소스 노드 ID"
    )
    target: str = Field(
        ...,
        description="대상 노드 ID"
    )
    type: str = Field(
        ...,
        description="엣지 타입 (IMPORTS, CALLS, INHERITS, USES)"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        description="엣지 가중치"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 메타데이터"
    )


class CodeGraph(BaseModel):
    """코드 그래프."""
    nodes: List[Node] = Field(
        default_factory=list,
        description="그래프 노드"
    )
    edges: List[Edge] = Field(
        default_factory=list,
        description="그래프 엣지"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="그래프 메타데이터"
    )


class SummaryUnit(BaseModel):
    """코드 요약 단위."""
    target_id: str = Field(
        ...,
        description="대상 코드 ID (파일, 클래스, 함수)"
    )
    level: str = Field(
        ...,
        description="요약 레벨 (file, class, function, repo)"
    )
    text: str = Field(
        ...,
        description="요약 텍스트"
    )
    model: str = Field(
        ...,
        description="생성에 사용된 모델명"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="요약 신뢰도"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="추가 메타데이터"
    )


class Metrics(BaseModel):
    """평가 메트릭."""
    codebleu: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="CodeBLEU 점수"
    )
    bleurt: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="BLEURT 점수"
    )
    bleu4: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="BLEU-4 점수"
    )
    rougeL: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="ROUGE-L 점수"
    )
    edge_f1: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="엣지 F1 점수"
    )
    ged: float = Field(
        default=0.0,
        ge=0.0,
        description="Graph Edit Distance"
    )
    ssi: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="Semantic Similarity Index"
    )


class Embedding(BaseModel):
    """코드 임베딩."""
    code_id: str = Field(
        ...,
        description="코드 ID"
    )
    embedding: List[float] = Field(
        ...,
        description="임베딩 벡터"
    )
    model: str = Field(
        ...,
        description="생성에 사용된 모델명"
    )


class Recommendation(BaseModel):
    """작업 추천."""
    rank: int = Field(
        ...,
        description="추천 순위"
    )
    target: str = Field(
        ...,
        description="추천 대상 (파일/클래스/함수)"
    )
    reason: str = Field(
        ...,
        description="추천 이유"
    )
    priority: str = Field(
        ...,
        description="우선순위 (high, medium, low)"
    )
    related_entities: List[str] = Field(
        default_factory=list,
        description="관련 엔티티"
    )


class AgentArtifact(BaseModel):
    """최종 분석 결과물."""
    graph: CodeGraph = Field(
        ...,
        description="코드 그래프"
    )
    summaries: List[SummaryUnit] = Field(
        default_factory=list,
        description="코드 요약들"
    )
    embeddings: List[Embedding] = Field(
        default_factory=list,
        description="코드 임베딩들"
    )
    metrics: Metrics = Field(
        default_factory=Metrics,
        description="평가 메트릭"
    )
    recommendations: List[Recommendation] = Field(
        default_factory=list,
        description="작업 추천"
    )
    repository_info: Dict[str, Any] = Field(
        default_factory=dict,
        description="저장소 정보"
    )


# ==================== Response Schemas ====================

class AnalyzeResponse(BaseModel):
    """분석 응답 스키마."""
    run_id: str = Field(
        ...,
        description="실행 ID"
    )
    status: str = Field(
        default="completed",
        description="실행 상태"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="응답 생성 시간"
    )
    artifact: AgentArtifact = Field(
        ...,
        description="분석 결과물"
    )
    execution_time: float = Field(
        default=0.0,
        description="실행 시간 (초)"
    )
    error: Optional[str] = Field(
        default=None,
        description="에러 메시지 (있을 경우)"
    )


class AsyncResponse(BaseModel):
    """비동기 실행 응답."""
    run_id: str = Field(
        ...,
        description="실행 ID (상태 조회에 사용)"
    )
    status: str = Field(
        default="queued",
        description="현재 상태"
    )
    message: str = Field(
        ...,
        description="상태 메시지"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="생성 시간"
    )


class ResultResponse(BaseModel):
    """실행 결과 조회 응답."""
    run_id: str = Field(
        ...,
        description="실행 ID"
    )
    status: str = Field(
        ...,
        description="실행 상태"
    )
    progress: int = Field(
        default=0,
        ge=0, le=100,
        description="진행률 (%)"
    )
    result: Optional[AnalyzeResponse] = Field(
        default=None,
        description="완료시 분석 결과"
    )
    error: Optional[str] = Field(
        default=None,
        description="에러 메시지"
    )
    created_at: datetime = Field(
        ...,
        description="생성 시간"
    )
    updated_at: datetime = Field(
        ...,
        description="마지막 업데이트 시간"
    )


class HealthResponse(BaseModel):
    """헬스 체크 응답."""
    status: str = Field(
        default="healthy",
        description="서비스 상태"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="시간"
    )
    version: str = Field(
        default="1.0.0",
        description="API 버전"
    )
