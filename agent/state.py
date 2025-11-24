"""
Agent state definition for LangGraph workflow (Monolith Lite Version).
"""
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    """
    LangGraph 워크플로우의 중앙 상태 객체입니다.
    모든 노드가 이 상태를 공유하고 필요에 따라 수정합니다.
    """

    # ==================== 초기 입력 정보 ====================
    run_id: str
    """실행 고유 ID"""

    repo_input: Dict[str, Any]
    """사용자 초기 요청 (source, uri, branch)"""

    repo_path: str
    """클론된 로컬 저장소 경로"""

    thresholds: Dict[str, Any]
    """품질 평가 임계값 설정 (예: {'similarity': 0.7})"""

    options: Dict[str, Any]
    """분석 옵션"""

    top_k: int
    """상위 K개 결과 반환"""

    # ==================== 1단계: 개별 분석 결과 (Raw Data) ====================
    initial_summaries: Optional[List[Dict[str, Any]]]
    """초기 요약 결과 (CodeT5+ 등에서 생성)"""

    refined_summaries: Optional[List[Dict[str, Any]]]
    """개선된 요약 결과 (재시도 후)"""

    final_summaries: List[Dict[str, Any]]
    """최종 확정된 요약"""

    code_graph_raw: Optional[Dict[str, Any]]
    """구조 분석 결과 (Raw JSON: nodes, edges)"""

    embeddings: Optional[List[Dict[str, Any]]]
    """의미 기반 코드 임베딩 리스트"""

    # ==================== 2단계: 데이터 융합 (Input Reinforcement) ====================
    reinforced_graph_obj: Optional[Any]
    """
    [핵심] NetworkX DiGraph 객체.
    노드 속성으로 Summary(Text) + Embedding(Vector) + AST(Structure)가 모두 포함됨.
    메모리 상에만 존재하며 분석용으로 사용.
    """

    final_graph_json: Optional[Dict[str, Any]]
    """프론트엔드 시각화를 위해 직렬화된 최종 그래프 데이터"""

    # ==================== 3단계: 종합 분석 결과 ====================
    repository_info: Optional[Dict[str, Any]]
    """저장소 레벨 분석 정보 (PageRank 상위 파일 등)"""

    recommendations: Optional[List[Dict[str, Any]]]
    """작업 추천 목록 (Refactoring, Bug fix 등)"""

    # ==================== 평가 및 제어 ====================
    metrics: Optional[Dict[str, Any]]
    """평가 메트릭 (Consistency, Complexity, Coherence)"""

    retry_count: int
    """현재까지의 재시도 횟수"""

    error_message: Optional[str]
    """발생한 에러 메시지"""

    status: str
    """현재 상태 (pending, processing, completed, failed)"""

    # ==================== 로깅 ====================
    node_execution_log: Optional[List[Dict[str, Any]]]
    """각 노드 실행 로그"""

    start_time: float
    end_time: float

def log_node_execution(
    state: AgentState,
    node_name: str,
    status: str,
    duration: float,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """노드 실행 로그를 기록합니다."""
    import time
    if state.get("node_execution_log") is None:
        state["node_execution_log"] = []

    log_entry = {
        "timestamp": time.time(),
        "node_name": node_name,
        "status": status,
        "duration": duration,
        "details": details or {},
    }
    state["node_execution_log"].append(log_entry)
