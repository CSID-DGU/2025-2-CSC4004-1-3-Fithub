"""Core task recommendation logic."""
import logging
from typing import Dict, List, Any, Optional
from .models_loader import get_model_pool

logger = logging.getLogger(__name__)


class TaskRecommender:
    """작업 추천 엔진."""

    def __init__(self, device: Optional[str] = None):
        self.model_pool = get_model_pool(device=device)
        self.device = device or "cpu"

    def recommend_tasks(
        self,
        analysis_results: Dict[str, Any],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        분석 결과에 따라 작업을 추천합니다.

        Args:
            analysis_results: 종합 분석 결과 (그래프, 요약, 메트릭 등)
            top_k: 상위 K개 추천

        Returns:
            추천 작업 목록
        """
        recommendations = []

        try:
            # 1. 복잡도 분석
            complexity_tasks = self._analyze_complexity(analysis_results)
            recommendations.extend(complexity_tasks)

            # 2. 의존성 분석
            dependency_tasks = self._analyze_dependencies(analysis_results)
            recommendations.extend(dependency_tasks)

            # 3. 코드 품질 분석
            quality_tasks = self._analyze_quality(analysis_results)
            recommendations.extend(quality_tasks)

            # 4. 구조 개선 제안
            structure_tasks = self._suggest_structure_improvements(analysis_results)
            recommendations.extend(structure_tasks)

            # 정렬 (우선순위 기반)
            recommendations = self._rank_recommendations(recommendations)

            # 상위 K개 반환
            return recommendations[:top_k]

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return []

    def _analyze_complexity(self, results: Dict) -> List[Dict[str, Any]]:
        """복잡도 기반 추천을 생성합니다."""
        tasks = []

        graph = results.get("graph", {})
        nodes = graph.get("nodes", [])

        # 진입도/출입도가 높은 노드 찾기
        node_degrees = {}
        for node in nodes:
            node_id = node.get("id")
            if node_id:
                node_degrees[node_id] = {"in": 0, "out": 0}

        edges = graph.get("edges", [])
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in node_degrees:
                node_degrees[source]["out"] += 1
            if target in node_degrees:
                node_degrees[target]["in"] += 1

        # 높은 차수의 노드 추천
        high_degree_nodes = sorted(
            node_degrees.items(),
            key=lambda x: x[1]["in"] + x[1]["out"],
            reverse=True
        )[:3]

        for idx, (node_id, degree) in enumerate(high_degree_nodes, 1):
            tasks.append({
                "rank": idx,
                "target": node_id,
                "reason": f"High complexity node with degree {degree['in'] + degree['out']}",
                "priority": "high",
                "category": "complexity",
            })

        return tasks

    def _analyze_dependencies(self, results: Dict) -> List[Dict[str, Any]]:
        """의존성 기반 추천을 생성합니다."""
        tasks = []

        graph = results.get("graph", {})
        edges = graph.get("edges", [])

        # 순환 의존성 찾기
        edges_by_type = {}
        for edge in edges:
            edge_type = edge.get("type", "UNKNOWN")
            if edge_type not in edges_by_type:
                edges_by_type[edge_type] = 0
            edges_by_type[edge_type] += 1

        for idx, (edge_type, count) in enumerate(
            sorted(edges_by_type.items(), key=lambda x: x[1], reverse=True)[:2],
            1
        ):
            tasks.append({
                "rank": 3 + idx,
                "target": f"Review {edge_type} edges",
                "reason": f"Found {count} {edge_type} relationships",
                "priority": "medium",
                "category": "dependency",
            })

        return tasks

    def _analyze_quality(self, results: Dict) -> List[Dict[str, Any]]:
        """코드 품질 기반 추천을 생성합니다."""
        tasks = []

        metrics = results.get("metrics", {})

        # 메트릭 점수 확인
        low_score_metrics = []

        for metric_name, threshold in [
            ("codebleu", 0.42),
            ("rougeL", 0.30),
        ]:
            if metric_name in metrics:
                score = metrics[metric_name]
                if score < threshold:
                    low_score_metrics.append(f"{metric_name} ({score:.2f})")

        if low_score_metrics:
            tasks.append({
                "rank": 5,
                "target": "Improve Code Quality",
                "reason": f"Low scores in: {', '.join(low_score_metrics)}",
                "priority": "high",
                "category": "quality",
            })

        return tasks

    def _suggest_structure_improvements(
        self,
        results: Dict
    ) -> List[Dict[str, Any]]:
        """구조 개선 제안을 생성합니다."""
        tasks = []

        summaries = results.get("summaries", [])

        if summaries:
            tasks.append({
                "rank": 6,
                "target": "Review Main Modules",
                "reason": f"Analyze {min(3, len(summaries))} key modules for architecture improvements",
                "priority": "medium",
                "category": "structure",
                "related_entities": [s.get("target_id") for s in summaries[:3]],
            })

        return tasks

    def _rank_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """추천을 우선순위별로 정렬합니다."""
        priority_order = {"high": 0, "medium": 1, "low": 2}

        return sorted(
            recommendations,
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 2),
                x.get("rank", float('inf'))
            )
        )


def create_recommender(device: Optional[str] = None) -> TaskRecommender:
    """추천기를 생성합니다."""
    return TaskRecommender(device=device)
