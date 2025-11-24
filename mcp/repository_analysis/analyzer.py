"""
mcp/repository_analysis/analyzer.py
Context Analysis & Tagging (Lite Version) with Logical Edge Detection.
"""
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RepositoryAnalyzer:
    def __init__(self, device=None):
        pass

    def analyze(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        융합된 데이터를 분석하여 메타데이터와 논리적 연결을 생성합니다.
        """
        nodes = fused_data.get("nodes", [])
        context_metadata = {
            "file_metadata": {},
            "logical_edges": []
        }

        try:
            # 1. & 2. 태깅 및 계층 분석 (기존 로직 유지 + 데이터 준비)
            processed_nodes = []

            for node in nodes:
                node_id = node['id'].lower()
                summary = node.get('summary_text', '').lower()

                # --- Domain Tagging ---
                domain = "Common"
                if any(k in node_id or k in summary for k in ['auth', 'login', 'security', 'jwt']):
                    domain = "Security"
                elif any(k in node_id or k in summary for k in ['user', 'member', 'profile']):
                    domain = "User"
                elif any(k in node_id or k in summary for k in ['order', 'cart', 'pay']):
                    domain = "Commerce"
                elif any(k in node_id or k in summary for k in ['db', 'model', 'entity', 'schema']):
                    domain = "Database"

                # --- Layer Analysis ---
                layer = "Other"
                if any(k in node_id for k in ["service", "manager", "business"]):
                    layer = "ServiceLayer"
                elif any(k in node_id for k in ["repo", "dao", "store", "db"]):
                    layer = "RepositoryLayer"
                elif any(k in node_id for k in ["controller", "route", "view", "api"]):
                    layer = "PresentationLayer"
                elif any(k in node_id for k in ["model", "dto", "schema"]):
                    layer = "DomainLayer"

                # --- Importance Hint ---
                importance = "Medium"
                if layer in ["ServiceLayer", "DomainLayer"]: importance = "High"

                # 메타데이터 저장
                context_metadata["file_metadata"][node['id']] = {
                    "domain_tag": domain,
                    "layer": layer,
                    "importance_hint": importance
                }

                # 논리적 엣지 계산을 위해 정보 모으기
                processed_nodes.append({
                    "id": node['id'],
                    "stem": self._extract_stem(node['id']), # 파일명에서 핵심 단어 추출 (auth_service.py -> auth)
                    "layer": layer,
                    "domain": domain
                })

            # 3. [New] 논리적 엣지 탐지 (Logical Edge Detection)
            logical_edges = self._detect_logical_edges(processed_nodes)
            context_metadata["logical_edges"] = logical_edges

            return context_metadata

        except Exception as e:
            logger.error(f"Repo analysis failed: {e}")
            return {"file_metadata": {}, "logical_edges": []}

    def _extract_stem(self, filename: str) -> str:
        """
        파일명에서 핵심 어간(Stem)을 추출합니다.
        예: 'auth_service.py' -> 'auth', 'user_controller.py' -> 'user'
        """
        # 확장자 제거
        base = filename.split('/')[-1].replace('.py', '').lower()
        # 접미사 제거 (service, controller, repository, etc.)
        suffixes = ['_service', '_controller', '_repository', '_repo', '_model', '_dto', '_view', 'service', 'controller']

        for suffix in suffixes:
            if base.endswith(suffix):
                return base.replace(suffix, '')
        return base

    def _detect_logical_edges(self, nodes: List[Dict]) -> List[Dict]:
        """
        노드 간의 이름 및 계층 규칙을 기반으로 암묵적 연결을 찾습니다.
        """
        edges = []

        # O(N^2) 비교지만, 파일 수가 적으므로(수백 개 이내) Lite 모드에서 허용 가능
        for i, src in enumerate(nodes):
            for j, tgt in enumerate(nodes):
                if i == j: continue

                # 규칙 1: 아키텍처 계층 연결 (같은 주제끼리)
                # Controller(User) -> Service(User) -> Repository(User)
                if src['stem'] == tgt['stem'] and len(src['stem']) > 2:

                    # Presentation -> Service
                    if src['layer'] == "PresentationLayer" and tgt['layer'] == "ServiceLayer":
                        edges.append(self._create_edge(src['id'], tgt['id'], "architectural_flow"))

                    # Service -> Repository
                    elif src['layer'] == "ServiceLayer" and tgt['layer'] == "RepositoryLayer":
                        edges.append(self._create_edge(src['id'], tgt['id'], "data_access"))

                    # Service -> Domain/Model
                    elif src['layer'] == "ServiceLayer" and tgt['layer'] == "DomainLayer":
                        edges.append(self._create_edge(src['id'], tgt['id'], "uses_model"))

                # 규칙 2: 도메인 횡단 관심사 (Cross-cutting)
                # 'Auth'나 'Security'는 모든 Controller와 연결될 가능성 높음
                if tgt['domain'] == "Security" and src['layer'] == "PresentationLayer":
                    # 단, 너무 많이 연결되면 그래프가 지저분하므로 확률적으로/조건부로 추가 가능
                    # 여기서는 예시로 추가
                    # edges.append(self._create_edge(src['id'], tgt['id'], "secured_by"))
                    pass

        return edges

    def _create_edge(self, src: str, tgt: str, reason: str) -> Dict:
        return {
            "source": src,
            "target": tgt,
            "type": "logical",  # Graph에서 점선으로 표현됨
            "relation": reason
        }

def create_analyzer(device=None) -> RepositoryAnalyzer:
    return RepositoryAnalyzer(device=device)
