"""
mcp/task_recommender/recommender.py
Generate actionable tasks based on analysis results.
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class TaskRecommender:
    def __init__(self, device=None):
        pass

    def recommend(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        분석 결과를 기반으로 작업 추천 생성
        input: { "graph": ..., "context": ..., "metrics": ... }
        """
        recommendations = []

        try:
            graph = analysis_results.get("graph", {})
            context = analysis_results.get("context", {}).get("file_metadata", {})

            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])

            # 1. 아키텍처 위반 감지 (Layer Violation)
            # 규칙: Repository Layer는 Controller Layer를 호출하면 안 됨
            for edge in edges:
                src = edge['source']
                tgt = edge['target']

                src_layer = context.get(src, {}).get('layer', 'Unknown')
                tgt_layer = context.get(tgt, {}).get('layer', 'Unknown')

                if src_layer == "RepositoryLayer" and tgt_layer == "PresentationLayer":
                    recommendations.append({
                        "type": "architecture_violation",
                        "file": src,
                        "severity": "High",
                        "description": f"Repository layer '{src}' should not depend on Presentation layer '{tgt}'."
                    })

            # 2. 복잡도 및 중요도 기반 리팩토링 추천
            for node in nodes:
                # GNN 사이즈(중요도)가 큰데 복잡도(AST)가 높으면 리팩토링 대상
                importance = node.get("size", 10)
                complexity = node.get("complexity", 0)

                if importance > 50 and complexity > 20:
                    recommendations.append({
                        "type": "refactor_needed",
                        "file": node['id'],
                        "severity": "Medium",
                        "description": "Critical file with high complexity. Consider splitting."
                    })

            return recommendations

        except Exception as e:
            logger.error(f"Task recommendation failed: {e}")
            return []

def create_recommender(device=None) -> TaskRecommender:
    return TaskRecommender(device=device)
