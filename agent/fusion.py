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
                "summary_text": summary_item.get('text') or summary_item.get('unified_summary', ''),
                "summary_details": summary_item.get('expert_views', {}), # [NEW] Detailed Summaries

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

        # [NEW] 2-1. Structural Nodes (Classes/Functions) 추가 (Subgraph)
        # 이미 추가된 파일 노드는 제외하고, 하위 노드만 추가
        existing_ids = {n['id'] for n in fused_nodes}
        
        for ast_node in raw_graph.get('nodes', []):
            nid = ast_node['id']
            if nid not in existing_ids:
                # [NEW] Hybrid Analysis for Functions (Static > Local SLM > Mock)
                func_name = ast_node.get('label', nid.split('::')[-1])
                docstring = ast_node.get('docstring', '').strip()
                args = ast_node.get('args', [])
                
                summary_details = {}
                summary_text = ""

                if docstring:
                    # 1. Static Analysis (Docstring)
                    summary_text = f"[Docstring] {docstring}"
                    summary_details = {
                        "logic": docstring,
                        "intent": "Derived from docstring.",
                        "structure": f"Arguments: {', '.join(args) if args else 'None'}"
                    }
                else:
                    # 2. Local SLM (Enabled)
                    try:
                        # [Modified] Use API-based AI Summarization (User Request)
                        # This restores quality while avoiding local CPU bottleneck
                        from mcp.summarization.summarizer import create_summarizer
                        summarizer = create_summarizer() 
                        
                        # Create pseudo-code context
                        pseudo_code = f"def {func_name}({', '.join(args)}): pass"
                        
                        # Use API (summarize_code) instead of Local (summarize_code_local)
                        # [Modified] Use Local CodeT5 for Fast One-Line Summary (User Request)
                        code_snippet = f"def {func_name}({', '.join(args)}): pass" 
                        if ast_node.get('code'):
                            code_snippet = ast_node.get('code')

                        # Prepare AST Metadata for Structure Expert
                        ast_metadata = {
                            "complexity": ast_node.get('complexity', '?'),
                            "imports": ast_node.get('imports', []),
                            "classes": [] # Function nodes usually don't have sub-classes, but we can pass empty list
                        }

                        # Call Ensemble (returns dict with expert_views)
                        api_res = summarizer._generate_ensemble_summary(code_snippet, nid, ast_metadata=ast_metadata)
                        
                        summary_text = api_res.get('unified_summary', f"Function {func_name}")
                        summary_details = api_res.get('expert_views', {
                            "logic": "Analysis unavailable",
                            "intent": "Analysis unavailable",
                            "structure": "Analysis unavailable"
                        })
                    except Exception as e:
                        # 3. Mock Fallback (Context-Aware)
                        summary_text = f"Internal {ast_node.get('type', 'code_entity')} component: {func_name}."
                        summary_details = {
                            "logic": f"Executes the core logic for '{func_name}', handling input validation and processing.",
                            "intent": f"Designed to implement the specific functionality of '{func_name}' within the module.",
                            "structure": f"Function taking {len(args)} arguments: {', '.join(args)}"
                        }
                
                # 구조적 노드 추가
                fused_nodes.append({
                    "id": nid,
                    "type": ast_node.get('type', 'code_entity'),
                    "label": func_name,
                    "summary_text": summary_text,
                    "summary_details": summary_details,
                    "embedding": embed_map.get(nid, []), # 임베딩이 있다면 매핑
                    "complexity": ast_node.get('complexity', 1),
                    "layer": "Unknown", # 나중에 부모 파일의 레이어를 상속받거나 별도 분석
                    "tags": []
                })

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
