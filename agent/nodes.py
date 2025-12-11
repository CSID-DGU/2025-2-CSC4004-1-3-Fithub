"""
agent/nodes.py
Core logic implementation for each workflow node.
"""
import logging
import time
import shutil
import networkx as nx
import numpy as np
from pathlib import Path
from typing import Dict, Any, List
from sklearn.metrics.pairwise import cosine_similarity

from .state import AgentState, log_node_execution
from .config import Config
from .fusion import fuse_data
from .utils import save_mcp_result

logger = logging.getLogger(__name__)

# ==================== Phase 0: Ingestion ====================

async def fetch_from_backend_node(state: AgentState) -> Dict[str, Any]:
    """
    [Ingest] 백엔드 API에서 파일 데이터를 받아와 로컬 임시 폴더에 저장합니다.
    """
    start_time = time.time()
    try:
        repo_input = state.get("repo_input", {})
        repo_id = repo_input.get("repo_id", "unknown")
        local_path = repo_input.get("local_path")
        run_id = state.get("run_id", "default")

        # 임시 저장소 경로 설정 및 초기화
        temp_dir = Path(Config.TEMP_DIR) / run_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Fetching files for repo {repo_id} into {temp_dir}...")

        # [Option 1] Local Path Ingestion (For Testing)
        if local_path:
            src_path = Path(local_path)
            if src_path.exists() and src_path.is_dir():
                logger.info(f"Ingesting from local path: {src_path}")
                # Copy all files recursively
                # ignore .git, venv, __pycache__ to avoid clutter
                shutil.copytree(
                    src_path, 
                    temp_dir, 
                    dirs_exist_ok=True, 
                    ignore=shutil.ignore_patterns('.git', '.venv', '__pycache__', '*.pyc', '.DS_Store', 'temp_repos', 'brain')
                )
                log_node_execution(state, "ingest", "success", time.time() - start_time)
                return {"repo_path": str(temp_dir)}
            else:
                logger.warning(f"Provided local_path {local_path} does not exist. Falling back to mock.")

        # [Option 2] Backend API (Production)
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                # 타임아웃 설정 (대용량 레포지토리 고려)
                res = await client.get(f"{Config.BACKEND_API_URL}/github/repos/{repo_id}/files", timeout=60.0) # 엔드포인트 수정
                if res.status_code == 200:
                    files = res.json()
                    logger.info(f"Successfully fetched {len(files)} files from backend.")
                else:
                    logger.warning(f"Backend fetch failed. Status: {res.status_code}. Using mock data.")
                    files = _get_mock_files() # Fallback
        except Exception as e:
            logger.error(f"Backend connection error: {e}. Using mock data.")
            files = _get_mock_files() # Fallback

        # [Option 3] Mock Data (Removed as default, now fallback)
        # files = _get_mock_files()

        # 파일 시스템에 쓰기
        for f in files:
            file_path = temp_dir / f['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(f['content'])

        log_node_execution(state, "ingest", "success", time.time() - start_time)
        return {"repo_path": str(temp_dir)}

    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        return {"error_message": str(e)}

def _get_mock_files():
    """테스트용 가상 파일 데이터"""
    return [
        {
            "path": "auth_service.py",
            "content": "import jwt\ndef login(user, pw):\n    # User authentication logic\n    pass\ndef logout():\n    pass"
        },
        {
            "path": "user_model.py",
            "content": "class User:\n    def __init__(self, name, email):\n        self.name = name\n        self.email = email"
        },
        {
            "path": "utils.py",
            "content": "def hash_password(pw):\n    return 'hashed'"
        }
    ]

# ==================== Phase 1: Parallel Analysis ====================

async def summarize_node(state: AgentState) -> Dict[str, Any]:
    """[Summarization] CodeT5+를 사용하여 코드 요약"""
    from mcp.summarization.summarizer import create_summarizer
    start_time = time.time()
    try:
        summ = create_summarizer(device="cpu")
        
        # [Selective Retry Logic]
        target_ids = state.get("target_files") # Orchestrator가 지정한 재분석 리스트
        
        res = summ.summarize_repository(state["repo_path"], target_ids=target_ids)

        summaries = res.get("file_summaries", [])
        save_mcp_result(state.get("run_id", "default"), "summarization", summaries)
        log_node_execution(state, "summarize", "success", time.time() - start_time)
        return {"initial_summaries": summaries}
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        return {"initial_summaries": [], "error_message": str(e)}

async def build_graph_node(state: AgentState) -> Dict[str, Any]:
    """[Structural] AST 파싱을 통한 의존성 추출"""
    from mcp.structural_analysis.analyzer import create_analyzer
    start_time = time.time()
    try:
        anlz = create_analyzer(device="cpu")
        res = anlz.analyze_repository(state["repo_path"])
        save_mcp_result(state.get("run_id", "default"), "structural", res)
        log_node_execution(state, "build_graph", "success", time.time() - start_time)
        return {"code_graph_raw": res}
    except Exception as e:
        return {"code_graph_raw": {}}

async def embed_code_node(state: AgentState) -> Dict[str, Any]:
    """[Embedding] GraphCodeBERT를 사용하여 벡터화"""
    from mcp.semantic_embedding.embedder import create_embedder
    start_time = time.time()
    try:
        embedder = create_embedder(device="cpu")
        repo_path = Path(state.get("repo_path"))
        snippets = []

        # 실제 파일 읽기 (Config 제한 적용)
        py_files = list(repo_path.rglob("*.py"))[:Config.MAX_ANALYSIS_FILES]
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()[:1000] # 너무 긴 코드는 자름
                    snippets.append({
                        "id": str(py_file.relative_to(repo_path)).replace("\\", "/"),
                        "code": code
                    })
            except Exception:
                continue

        if not snippets:
            return {"embeddings": []}

        # API 호출
        results = embedder.batch_embed(snippets, model_name="graphcodebert")

        # 결과 포맷팅
        embeddings = []
        for r in results:
            if r.get("embedding"):
                embeddings.append({"id": r["id"], "embedding": r["embedding"]})

        log_node_execution(state, "embed_code", "success", time.time() - start_time)
        save_mcp_result(state.get("run_id", "default"), "embedding", embeddings)
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error(f"Embed error: {e}")
        return {"embeddings": []}

# ==================== Phase 2: Fusion & Eval ====================

async def fusion_node(state: AgentState) -> Dict[str, Any]:
    """[Fusion] 데이터 결합"""
    start_time = time.time()
    try:
        fused = fuse_data(
            state.get("initial_summaries", []),
            state.get("embeddings", []),
            state.get("code_graph_raw", {})
        )
        log_node_execution(state, "fusion", "success", time.time() - start_time)
        return {"fused_data_package": fused}
    except Exception as e:
        logger.error(f"Fusion error: {e}")
        return {"error_message": str(e)}

async def evaluate_node(state: AgentState) -> Dict[str, Any]:
    """[Quality Gate] Orchestrator를 통한 진행 판단"""
    from .orchestrator import create_orchestrator
    
    start_time = time.time()
    try:
        fused_data = state.get("fused_data_package", {})
        nodes = fused_data.get("nodes", [])

        # 1. 평가를 위한 기본 점수 계산 (Cosine Sim) - 기존 로직 유지
        # (Orchestrator 내부에서 할 수도 있지만, 여기서 계산해서 넘겨주는 구조가 데이터 흐름상 깔끔함)
        from mcp.semantic_embedding.embedder import create_embedder
        try:
            embedder = create_embedder(device="cpu")
            total_sim = 0
            count = 0
            for node in nodes:
                summary = node.get("summary_text", "")
                code_vec = node.get("embedding", [])
                
                if summary and code_vec and len(summary) > 5:
                    sum_vec = embedder._generate_embedding(summary, "graphcodebert")
                    sim = cosine_similarity([code_vec], [sum_vec])[0][0]
                    node['quality_score'] = float(sim)
                    total_sim += sim
                    count += 1
                else:
                    node['quality_score'] = 0.5
        except Exception as e:
            logger.warning(f"Score calculation failed (skipping): {e}")

        # 2. Orchestrator에게 판단 위임
        orchestrator = create_orchestrator()
        evaluation = orchestrator.evaluate_progress(state) # State의 노드 정보를 보고 판단
        
        logger.info(f"👮‍♂️ Orchestrator Decision: {evaluation['decision']} (Mode: {evaluation['retry_mode']})")
        if evaluation['retry_mode'] == 'partial':
            logger.info(f"   -> Targeting {len(evaluation['target_files'])} files for retry.")

        log_node_execution(state, "evaluate", "success", time.time() - start_time)
        
        return {
            "metrics": state.get("metrics", {}), # Score는 Orchestrator 내부에서 state 업데이트함
            "decision": evaluation["decision"],
            "retry_mode": evaluation["retry_mode"],
            "target_files": evaluation.get("target_files", []), # Safe access
            "fused_data_package": fused_data # 점수가 업데이트된 노드 정보 반환
        }

    except Exception as e:
        logger.error(f"Evaluate error: {e}")
        return {
            "decision": "refine", # 에러나면 안전하게 재시도
            "retry_mode": "full",
            "metrics": {"consistency_score": 0.0}
        }

async def refine_node(state: AgentState) -> Dict[str, Any]:
    """[Refine] 재시도 횟수 증가"""
    return {"retry_count": state.get("retry_count", 0) + 1}

# ==================== Phase 3: Context & Visual ====================

async def analyze_repo_node(state: AgentState) -> Dict[str, Any]:
    """[Repo Analysis] 문맥 태깅 및 계층 분석"""
    start_time = time.time()
    try:
        from mcp.repository_analysis.analyzer import create_analyzer
        # 1. Repository Analysis (LLM + RepoCoder)
        analyzer = create_analyzer()
        analysis_result = analyzer.analyze(state.get("fused_data_package", {}))

        log_node_execution(state, "analyze_repo", "success", time.time() - start_time)
        save_mcp_result(state.get("run_id", "default"), "repository_analysis", analysis_result)
        return {"context_metadata": analysis_result}
    except Exception as e:
        logger.error(f"Repo analysis error: {e}")
        return {"context_metadata": {}}

async def generate_graph_node(state: AgentState) -> Dict[str, Any]:
    """[Graph Visual] 시각화 데이터 생성 (Delegates to Visualizer MCP)"""
    start_time = time.time()
    try:
        from mcp.graph_analysis.visualizer import create_visualizer
        
        fused = state.get("fused_data_package", {})
        ctx = state.get("context_metadata", {})
        repo_path = state.get("repo_path") # RepoGraph needs this!

        nodes = fused.get("nodes", [])
        edges = fused.get("edges", [])

        visualizer = create_visualizer()
        # Visualizer MCP가 RepoGraph 중요도 계산 및 색상/크기 로직을 전담함
        graph_json = visualizer.build_graph(nodes, edges, ctx, repo_path=repo_path)

        log_node_execution(state, "generate_graph", "success", time.time() - start_time)
        return {"final_graph_json": graph_json}

    except Exception as e:
        logger.error(f"Graph gen error: {e}")
        return {"final_graph_json": {"nodes": [], "edges": []}}

async def synthesize_node(state: AgentState) -> Dict[str, Any]:
    """[Synthesis] 최종 결과 조립"""
    start_time = time.time()
    try:
        from mcp.task_recommender.recommender import create_recommender
        rec = create_recommender()

        analysis_res = {
            "graph": state.get("final_graph_json"),
            "context": state.get("context_metadata")
        }
        tasks = rec.recommend(analysis_res)

        # Coverage Statistics
        total_files_found = state.get("context_metadata", {}).get("statistics", {}).get("total_files", 0)
        # If context statistics missing, try to infer from graph
        if total_files_found == 0:
             total_files_found = len(state.get("final_graph_json", {}).get("nodes", []))

        analyzed_count = len(state.get("initial_summaries", []))
        coverage_pct = (analyzed_count / total_files_found * 100) if total_files_found > 0 else 0.0

        final_artifact = {
            "graph": state.get("final_graph_json"),
            "context": state.get("context_metadata"),
            "recommendations": tasks,
            "metrics": {
                **state.get("metrics", {}),
                "coverage": {
                    "total_files": total_files_found,
                    "analyzed_files": analyzed_count,
                    "percentage": round(coverage_pct, 1)
                }
            }
        }

        log_node_execution(state, "synthesize", "success", time.time() - start_time)
        return {"final_artifact": final_artifact, "status": "completed"}

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        return {"status": "failed", "error_message": str(e)}
