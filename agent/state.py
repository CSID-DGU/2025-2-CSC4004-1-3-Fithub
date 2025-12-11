"""
agent/state.py
"""
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    # --- Input ---
    run_id: str
    repo_input: Dict[str, Any]  # {repo_id: "..."}
    repo_path: str              # Ingest 노드가 채워줄 경로
    options: Dict[str, Any]
    retry_count: int

    # --- Phase 1: Parallel Results ---
    initial_summaries: List[Dict]
    embeddings: List[Dict]
    code_graph_raw: Dict        # AST 결과

    # --- Phase 2: Fused ---
    fused_data_package: Dict    # [New] Fusion 결과물

    # --- Phase 3: Context & Visual ---
    context_metadata: Dict      # [New] Repo Analysis 결과 (태그, 레이어)
    final_graph_json: Dict      # [New] Graph Generation 결과 (좌표 포함)

    # --- Orchestrator Control ---
    metrics: Dict               # 점수 및 통계
    decision: str               # "pass" or "refine"
    retry_mode: str             # "none", "partial", "full"
    target_files: List[str]     # [Selective Retry] 재분석할 파일 ID 목록

    # --- Final ---
    final_artifact: Dict        # 최종 클라이언트 응답
    recommendations: List[Dict]

    # --- System ---
    status: str
    error_message: str
    node_execution_log: List[Dict]
    start_time: float
    end_time: float

def log_node_execution(state: AgentState, node_name: str, status: str, duration: float):
    if state.get("node_execution_log") is None:
        state["node_execution_log"] = []
    state["node_execution_log"].append({
        "node": node_name, "status": status, "duration": duration
    })
