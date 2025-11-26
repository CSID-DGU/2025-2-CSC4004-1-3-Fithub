"""
mcp/graph_analysis/visualizer.py
Local Graph Model Adapter (Uses downloaded GitHub code).
"""
import sys
import os
import logging
import networkx as nx
import torch
from agent.config import Config

logger = logging.getLogger(__name__)

sys.path.append(Config.LOCAL_MODEL_DIR)

# 예외 처리: 다운받은 모델이 없을 경우 대비
try:
    # 다운받은 레포지토리의 파일명에 따라 수정 필요 (예: model.py의 GNN 클래스)
    # from model import GNNPredictor
    # 여기서는 시뮬레이션을 위해 더미 클래스를 둡니다.
    class GNNPredictor:
        def predict(self, graph, vectors):
            # 실제로는 여기서 torch model forward pass 실행
            return {node: 0.8 for node in graph.nodes()}
except ImportError:
    logger.warning("Local graph model not found. Using fallback.")
    GNNPredictor = None


class GraphBuilder:
    def __init__(self):
        self.model = GNNPredictor() if GNNPredictor else None

    def build_graph(self, nodes, edges, context_metadata):
        """
        Phase 3: Graph Construction
        """
        G = nx.DiGraph()

        # 1. 노드 추가 (Context 주입)
        vectors = {}
        for node in nodes:
            nid = node['id']
            meta = context_metadata.get('file_metadata', {}).get(nid, {})

            G.add_node(nid,
                       label=node['label'],
                       domain=meta.get('domain', 'General'),  # Color
                       layer=meta.get('layer', 'Module')  # Layout
                       )
            if 'vector' in node:
                vectors[nid] = node['vector']

        # 2. 엣지 추가
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], type='physical')

        for logic in context_metadata.get('logical_edges', []):
            G.add_edge(logic['source'], logic['target'], type='logical')

        # 3. [Local Model] 중요도 계산
        importance = {}
        if self.model:
            try:
                # 로컬 모델 실행
                importance = self.model.predict(G, vectors)
            except Exception as e:
                logger.error(f"Local model inference failed: {e}")
                importance = nx.pagerank(G)
        else:
            importance = nx.pagerank(G)

        # 4. 최종 JSON 변환
        final_nodes = []
        for nid in G.nodes:
            meta = G.nodes[nid]
            final_nodes.append({
                "id": nid,
                "label": meta['label'],
                "size": 20 + (importance.get(nid, 0) * 100),  # Size
                "color": self._get_color(meta['domain']),  # Color
                "group": meta['layer']  # Layout Group
            })

        return {"nodes": final_nodes, "edges": [{"source": u, "target": v} for u, v in G.edges]}

    def _get_color(self, domain):
        colors = {
            "Security": "#FF5733", "User": "#33FF57",
            "Database": "#3357FF", "General": "#888888"
        }
        return colors.get(domain, "#888888")


def create_visualizer():
    return GraphBuilder()
