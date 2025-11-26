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
        run_id = state.get("run_id", "default")

        # 임시 저장소 경로 설정 및 초기화
        temp_dir = Path(Config.TEMP_DIR) / run_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Fetching files for repo {repo_id} into {temp_dir}...")

        # TODO: 실제 백엔드 연동 시 아래 코드를 활성화하세요.
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     res = await client.get(f"{Config.BACKEND_API_URL}/repos/{repo_id}/files")
        #     if res.status_code == 200:
        #         files = res.json()
        #     else:
        #         logger.warning(f"Backend fetch failed. Status: {res.status_code}")
        #         files = _get_mock_files() # Fallback

        # [Mock Data for Testing]
        # 백엔드가 없을 때도 Agent가 동작하는지 확인하기 위함
        files = _get_mock_files()

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
        res = summ.summarize_repository(state["repo_path"])

        summaries = res.get("metadata", {}).get("file_summaries", [])
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

        # 실제 파일 읽기 (최대 20개 제한)
        py_files = list(repo_path.rglob("*.py"))[:20]
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
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error(f"Embed error: {e}")
        return {"embeddings": []}

# ==================== Phase 2: Fusion & Eval ====================

async def fusion_process_node(state: AgentState) -> Dict[str, Any]:
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
    """[Quality Gate] 벡터 일관성 평가"""
    start_time = time.time()
    try:
        fused_data = state.get("fused_data_package", {})
        nodes = fused_data.get("nodes", [])

        # 임베딩 유틸 재사용
        from mcp.semantic_embedding.embedder import create_embedder
        embedder = create_embedder(device="cpu")

        total_sim = 0
        count = 0

        for node in nodes:
            summary = node.get("summary_text", "")
            code_vec = node.get("embedding", [])

            # 요약문과 코드가 모두 있는 경우만 평가
            if summary and code_vec and len(summary) > 5:
                # 요약문 벡터화
                sum_vec = embedder._generate_embedding(summary, "graphcodebert")
                # 코사인 유사도 계산
                sim = cosine_similarity([code_vec], [sum_vec])[0][0]

                node['quality_score'] = float(sim)
                total_sim += sim
                count += 1
            else:
                node['quality_score'] = 0.5 # 기본값

        avg_score = total_sim / count if count > 0 else 0.6 # 기본값 0.6

        log_node_execution(state, "evaluate", "success", time.time() - start_time)
        return {"metrics": {"consistency_score": avg_score}, "fused_data_package": fused_data}

    except Exception as e:
        logger.error(f"Evaluate error: {e}")
        return {"metrics": {"consistency_score": 0.0}}

async def refine_node(state: AgentState) -> Dict[str, Any]:
    """[Refine] 재시도 횟수 증가"""
    return {"retry_count": state.get("retry_count", 0) + 1}

# ==================== Phase 3: Context & Visual ====================

async def analyze_repo_node(state: AgentState) -> Dict[str, Any]:
    """[Repo Analysis] 문맥 태깅 및 계층 분석"""
    start_time = time.time()
    try:
        from mcp.repository_analysis.analyzer import create_analyzer
        anlz = create_analyzer()
        ctx = anlz.analyze(state.get("fused_data_package", {}))

        log_node_execution(state, "analyze_repo", "success", time.time() - start_time)
        return {"context_metadata": ctx}
    except Exception as e:
        logger.error(f"Repo analysis error: {e}")
        return {"context_metadata": {}}

async def generate_graph_node(state: AgentState) -> Dict[str, Any]:
    """[Graph Visual] 시각화 데이터 생성 (NetworkX Layout)"""
    start_time = time.time()
    try:
        fused = state.get("fused_data_package", {})
        ctx = state.get("context_metadata", {})

        nodes = fused.get("nodes", [])
        # 물리적 엣지 + 논리적 엣지
        edges = fused.get("edges", []) + ctx.get("logical_edges", [])

        # NetworkX로 그래프 구성
        G = nx.Graph()
        for n in nodes: G.add_node(n['id'])
        for e in edges: G.add_edge(e['source'], e['target'])

        # 레이아웃 계산 (좌표 생성)
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

        final_nodes = []
        meta_map = ctx.get("file_metadata", {})

        for n in nodes:
            nid = n['id']
            nm = meta_map.get(nid, {})

            # 좌표 및 시각적 속성 주입
            item = {
                "id": nid,
                "label": nid.split('/')[-1], # 파일명만 라벨로
                "type": n.get("type", "file"),
                "x": float(pos[nid][0]) * 1000 if nid in pos else 0.0,
                "y": float(pos[nid][1]) * 1000 if nid in pos else 0.0,
                "color": "#FF5733" if nm.get("domain_tag") == "Security" else "#3498DB",
                "size": 60 if nm.get("importance_hint") == "High" else 30,
                "group": nm.get("layer", "Unknown"),
                "summary": n.get("summary_text", ""),
                "icon": "file" # 추후 Code2Vec으로 고도화 가능
            }
            final_nodes.append(item)

        log_node_execution(state, "generate_graph", "success", time.time() - start_time)
        return {"final_graph_json": {"nodes": final_nodes, "edges": edges}}

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

        final_artifact = {
            "graph": state.get("final_graph_json"),
            "context": state.get("context_metadata"),
            "recommendations": tasks,
            "metrics": state.get("metrics")
        }

        log_node_execution(state, "synthesize", "success", time.time() - start_time)
        return {"final_artifact": final_artifact, "status": "completed"}

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        return {"status": "failed", "error_message": str(e)}
