"""
agent/fusion.py
Data Fusion Logic: Combines Text, Vector, and Structure.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def fuse_data(
    summaries: List[Dict[str, Any]],
    embeddings: List[Dict[str, Any]],
    raw_graph: Dict[str, Any]
) -> Dict[str, Any]:
    """
    3가지 소스를 하나로 합쳐서 '강화된 노드 데이터'를 생성합니다.
    """
    try:
        fused_nodes = []

        # 1. 빠른 검색을 위한 매핑 (ID 기준)
        # embeddings는 [{"id":..., "vector":...}] 형태
        embed_map = {item['id']: item['embedding'] for item in embeddings if 'id' in item}

        # raw_graph['nodes']는 AST에서 나온 파일/함수 정보
        ast_nodes_map = {node['id']: node for node in raw_graph.get('nodes', [])}

        # 2. Summaries를 기준으로 메인 루프 (요약된 파일이 핵심이므로)
        for summary_item in summaries:
            node_id = summary_item.get('code_id')
            if not node_id: continue

            ast_info = ast_nodes_map.get(node_id, {})

            # 3. Node 객체 생성 (Input Reinforcement)
            node = {
                "id": node_id,
                "type": summary_item.get('level', 'file'),

                # Semantic Info (Text)
                "summary_text": summary_item.get('text', ''),

                # Vector Info (Numbers) - GNN Input
                "embedding": embed_map.get(node_id, []),

                # Structural Info (AST)
                "complexity": ast_info.get('complexity', 0),
                "label": ast_info.get('label', node_id.split('/')[-1]),

                # Meta Info (Placeholders for next phases)
                "quality_score": 0.0,
                "tags": [],        # Repo Analysis에서 채워질 예정
                "layer": "Unknown" # Repo Analysis에서 채워질 예정
            }
            fused_nodes.append(node)

        # 4. 엣지 데이터 정제 (AST Raw Edges)
        formatted_edges = []
        for edge in raw_graph.get('edges', []):
            formatted_edges.append({
                "source": edge['source'],
                "target": edge['target'],
                "type": edge.get('relation', 'related')
            })

        logger.info(f"Fused {len(fused_nodes)} nodes and {len(formatted_edges)} edges.")

        return {
            "nodes": fused_nodes,
            "edges": formatted_edges,
            "metadata": {
                "total_files": len(fused_nodes),
                "total_edges": len(formatted_edges)
            }
        }
    except Exception as e:
        logger.error(f"Data fusion failed: {e}")
        return {"nodes": [], "edges": [], "error": str(e)}
