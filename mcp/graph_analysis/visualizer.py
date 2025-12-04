"""
mcp/graph_analysis/visualizer.py
Local Graph Model Adapter (Uses RepoGraph for detailed analysis).
"""
import sys
import os
import logging
import networkx as nx
import torch
from agent.config import Config

logger = logging.getLogger(__name__)

# Add local model directory to path
if Config.LOCAL_MODEL_DIR and os.path.exists(Config.LOCAL_MODEL_DIR):
    sys.path.append(Config.LOCAL_MODEL_DIR)
    # Also add the subpackage directory in case of absolute imports inside RepoGraph
    sys.path.append(os.path.join(Config.LOCAL_MODEL_DIR, "repograph"))
    try:
        from repograph.construct_graph import CodeGraph
        logger.info("RepoGraph module loaded successfully.")
    except ImportError as e:
        logger.error(f"Failed to import RepoGraph: {e}")
        CodeGraph = None
else:
    logger.warning(f"LOCAL_MODEL_DIR not found: {Config.LOCAL_MODEL_DIR}")
    CodeGraph = None


class RepoGraphPredictor:
    def __init__(self):
        self.enabled = CodeGraph is not None

    def calculate_importance(self, repo_path: str) -> dict:
        """
        RepoGraph를 사용하여 상세 호출 그래프를 생성하고, PageRank로 중요도를 계산합니다.
        """
        if not self.enabled or not repo_path:
            return {}

        try:
            # 1. RepoGraph 초기화 및 그래프 생성
            cg = CodeGraph(root=repo_path, verbose=False)
            files = cg.find_files([repo_path])
            tags, G = cg.get_code_graph(files)
            
            if not G or len(G.nodes) == 0:
                return {}

            # 2. PageRank 계산
            importance_scores = nx.pagerank(G, weight='weight')
            
            # 3. 파일 단위로 점수 집계 (Aggregation)
            file_importance = {}
            
            for node_id in G.nodes:
                node_data = G.nodes[node_id]
                fname = node_data.get('fname') # 절대 경로
                
                if fname:
                    # 절대 경로를 상대 경로로 변환하여 저장
                    # 이렇게 해야 build_graph에서 node['id']와 매칭하기 쉬움
                    try:
                        rel_path = os.path.relpath(fname, repo_path)
                    except ValueError:
                        rel_path = fname # 경로가 안 맞으면 그냥 절대 경로 사용

                    file_importance[rel_path] = file_importance.get(rel_path, 0) + importance_scores.get(node_id, 0)

            # 정규화 (0~1)
            if file_importance:
                max_score = max(file_importance.values())
                if max_score > 0:
                    for k in file_importance:
                        file_importance[k] /= max_score
            
            return file_importance

        except Exception as e:
            logger.error(f"RepoGraph analysis failed: {e}")
            return {}


class GraphBuilder:
    def __init__(self):
        self.predictor = RepoGraphPredictor()

    def build_graph(self, nodes, edges, context_metadata, repo_path=None):
        """
        Phase 3: Graph Construction
        """
        # [Validation] 입력 데이터 유효성 검사
        if not isinstance(nodes, list):
            logger.error(f"Invalid nodes format: {type(nodes)}. Expected list.")
            nodes = []
        if not isinstance(edges, list):
            logger.error(f"Invalid edges format: {type(edges)}. Expected list.")
            edges = []
        
        G = nx.DiGraph()
        
        # 1. RepoGraph 중요도 계산
        importance_map = {}
        if repo_path and self.predictor.enabled:
            importance_map = self.predictor.calculate_importance(repo_path)
            logger.info(f"Calculated importance for {len(importance_map)} files using RepoGraph.")

        # 2. 노드 추가 (Context 주입)
        for node in nodes:
            nid = node['id'] # 보통 상대 경로 (e.g., "mcp/analyzer.py")
            meta = context_metadata.get('file_metadata', {}).get(nid, {})
            
            # 중요도 매핑 (Robust Matching)
            score = 0.5 # 기본값
            
            # 1차 시도: 정확한 키 매칭 (상대 경로)
            if nid in importance_map:
                score = importance_map[nid]
            else:
                # 2차 시도: 경로 끝부분 매칭 (파일명 등)
                # importance_map의 키가 절대 경로일 수도 있고, nid가 일부만 있을 수도 있음
                for path, val in importance_map.items():
                    if str(path).endswith(nid) or nid.endswith(str(path)):
                        score = val
                        break
            
            # Context Hint가 있으면 가중치 부여
            if meta.get('importance_hint') == 'High':
                score = max(score, 0.8)

            G.add_node(nid,
                       label=node.get('label', nid.split('/')[-1]),
                       domain=meta.get('domain_tag', 'General'),  # Color
                       layer=meta.get('layer', 'Module'),  # Layout
                       summary_text=node.get('summary_text', ''),
                       summary_details=node.get('summary_details', {}),
                       type=node.get('type', 'file')
                       )
            
            # 노드 속성에 점수 저장 (나중에 시각화용)
            G.nodes[nid]['importance'] = score

        # 3. 엣지 추가
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], type=edge.get('type', 'physical'))

        for logic in context_metadata.get('logical_edges', []):
            G.add_edge(logic['source'], logic['target'], type='logical')

        # [NEW] Pre-process edges to find parent-child relationships for subgraphs
        parent_map = {}
        for edge in edges:
            if edge.get('type') == 'defines':
                parent_map[edge['target']] = edge['source']

        # 4. 최종 JSON 변환
        final_nodes = []
        for nid in G.nodes:
            meta = G.nodes[nid]
            
            # Color Decision
            color = self._get_color(meta.get('domain', 'General'))
            
            # Size Decision (RepoGraph Score 기반)
            # [NEW] Hierarchy Visualization: Files are larger, structural nodes are smaller
            base_size = 20
            if meta.get('type') == 'file':
                size = 20 + (meta.get('importance', 0.5) * 80) # 20 ~ 100
            else:
                size = 10 + (meta.get('importance', 0.5) * 20) # 10 ~ 30 (Smaller for sub-nodes)

            final_nodes.append({
                "id": nid,
                "label": meta.get('label', nid),
                "size": size,
                "color": color,
                "group": meta.get('layer', 'Unknown'),
                "type": meta.get('type', 'file'), # [NEW] Node Type
                "parent": parent_map.get(nid), # [NEW] Parent ID for Subgraph
                "summary": meta.get('summary_text', ''),
                "summary_details": meta.get('summary_details', {}), # [NEW] Detailed Summaries
                "domain": meta.get('domain', 'General'),
                "importance": meta.get('importance', 0.5)
            })

        return {"nodes": final_nodes, "edges": [{"source": u, "target": v, "type": d.get("type", "physical")} for u, v, d in G.edges(data=True)]}

    def _get_color(self, domain):
        colors = {
            "Security": "#FF5733", "User": "#33FF57",
            "Database": "#3357FF", "Commerce": "#F39C12", 
            "General": "#888888", "Common": "#95A5A6"
        }
        return colors.get(domain, "#888888")


def create_visualizer():
    return GraphBuilder()
