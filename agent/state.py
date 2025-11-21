"""Agent state definition for LangGraph workflow."""
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
    """품질 평가 임계값 설정"""

    options: Dict[str, Any]
    """분석 옵션"""

    top_k: int
    """상위 K개 결과 반환"""

    # ==================== 분석 결과물 ====================

    initial_summaries: Optional[List[Dict[str, Any]]]
    """초기 요약 결과 (첫 번째 분석)"""

    refined_summaries: Optional[List[Dict[str, Any]]]
    """개선된 요약 결과 (재시도 후)"""

    final_summaries: List[Dict[str, Any]]
    """최종 요약 (선택: refined or initial)"""

    code_graph: Optional[Dict[str, Any]]
    """코드 구조 그래프 (노드, 엣지)"""

    embeddings: Optional[List[Dict[str, Any]]]
    """의미 기반 코드 임베딩"""

    repository_info: Optional[Dict[str, Any]]
    """저장소 레벨 분석 정보"""

    recommendations: Optional[List[Dict[str, Any]]]
    """작업 추천 목록"""

    # ==================== 평가 및 제어 ====================

    metrics: Optional[Dict[str, Any]]
    """평가 메트릭 (CodeBLEU, BLEURT, ROUGE-L, Edge F1, GED 등)"""

    retry_count: int
    """현재까지의 재시도 횟수"""

    error_message: Optional[str]
    """발생한 에러 메시지 (있을 경우)"""

    # ==================== 실행 정보 ====================

    start_time: Optional[float]
    """실행 시작 시간 (timestamp)"""

    end_time: Optional[float]
    """실행 종료 시간 (timestamp)"""

    execution_time: float
    """총 실행 시간 (초)"""

    status: str
    """현재 상태 (pending, processing, completed, failed)"""

    # ==================== 헬퍼 정보 ====================

    node_execution_log: Optional[List[Dict[str, Any]]]
    """각 노드 실행 로그"""

    intermediate_results: Optional[Dict[str, Any]]
    """중간 결과 저장소"""


def create_initial_state(
    run_id: str,
    repo_input: Dict[str, Any],
    repo_path: str,
    thresholds: Dict[str, Any],
    options: Dict[str, Any],
    top_k: int = 10,
) -> AgentState:
    """
    초기 상태를 생성합니다.

    Args:
        run_id: 실행 고유 ID
        repo_input: 저장소 입력 정보
        repo_path: 저장소 경로
        thresholds: 품질 임계값
        options: 분석 옵션
        top_k: 상위 K개 결과

    Returns:
        초기 AgentState
    """
    import time

    return AgentState(
        run_id=run_id,
        repo_input=repo_input,
        repo_path=repo_path,
        thresholds=thresholds,
        options=options,
        top_k=top_k,
        initial_summaries=None,
        refined_summaries=None,
        final_summaries=[],
        code_graph=None,
        embeddings=None,
        repository_info=None,
        recommendations=None,
        metrics=None,
        retry_count=0,
        error_message=None,
        start_time=time.time(),
        end_time=None,
        execution_time=0.0,
        status="pending",
        node_execution_log=[],
        intermediate_results={},
    )


def log_node_execution(
    state: AgentState,
    node_name: str,
    status: str,
    duration: float,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    노드 실행 로그를 기록합니다.

    Args:
        state: AgentState
        node_name: 노드 이름
        status: 실행 상태 (success, error, skipped)
        duration: 실행 시간 (초)
        details: 추가 세부 정보
    """
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
