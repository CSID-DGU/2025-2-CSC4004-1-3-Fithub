"""
mcp/repository_analysis/analyzer.py
Context Analysis & Tagging using LLM (Mistral-7B) with Rule-based Fallback.
Also implements RepoCoder-like Context Retrieval using Vector Similarity.
"""
import logging
import re
import json
import numpy as np
from typing import Dict, Any, List
from huggingface_hub import InferenceClient
from sklearn.metrics.pairwise import cosine_similarity
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from agent.config import Config

logger = logging.getLogger(__name__)

class RepositoryAnalyzer:
    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.client = None
        self.model_id = None
        
        if self.provider == "openai":
            api_key = Config.OPENAI_API_KEY
            if api_key and OpenAI:
                self.client = OpenAI(api_key=api_key)
                self.model_id = Config.MODEL_LLM_OPENAI
                logger.info(f"Initialized OpenAI client with model {self.model_id}")
            else:
                logger.warning("OpenAI API Key missing or openai package not installed. OpenAI features will be disabled.")
                self.client = None
        else:
            # Default: Hugging Face
            token = Config.HF_API_KEY
            if token:
                self.client = InferenceClient(token=token)
                self.model_id = Config.MODEL_LLM # "mistralai/Mistral-7B-Instruct-v0.3"
                logger.info(f"Initialized HF client with model {self.model_id}")
            else:
                logger.warning("HF_API_KEY is missing. LLM features will be disabled.")
                self.client = None

    def analyze(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        융합된 데이터를 분석하여 메타데이터와 논리적 연결을 생성합니다.
        1. LLM/Rule-based 분석 (Tagging & Layering)
        2. Vector Similarity 분석 (RepoCoder - Context Retrieval)
        """
        nodes = fused_data.get("nodes", [])
        if not nodes:
            return {"file_metadata": {}, "logical_edges": []}

        # 1. LLM 분석 시도
        result = None
        if self.client:
            try:
                result = self._analyze_with_llm(nodes)
                if result:
                    logger.info("LLM analysis successful.")
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}. Falling back to rule-based.")
        
        # 2. 폴백: 규칙 기반 분석 (LLM 실패 시)
        if not result:
            result = self._analyze_rule_based(nodes)

        # 3. [New] Vector Similarity 기반 논리적 엣지 추가 (RepoCoder Logic)
        vector_edges = self._detect_vector_edges(nodes)
        
        # 기존 엣지와 병합 (중복 제거는 추후 그래프 단계에서 처리되지만 여기서도 간단히 체크 가능)
        result["logical_edges"].extend(vector_edges)
        
        return result

    def _analyze_with_llm(self, nodes: List[Dict]) -> Dict[str, Any]:
        """
        Mistral-7B를 사용하여 파일들의 역할(Domain, Layer)과 논리적 관계를 분석합니다.
        """
        if self.provider == "openai":
            return self._analyze_with_openai(nodes)
        
        # 프롬프트 구성을 위한 요약 정보 추출 (최대 20개 파일만 - 토큰 제한 고려)
        file_summaries = []
        for node in nodes[:20]:
            fid = node['id']
            summary = node.get('summary_text', 'No summary')[:100] # 요약도 짧게 자름
            file_summaries.append(f"- {fid}: {summary}")
        
        context_str = "\n".join(file_summaries)
        
        prompt = f"""
You are a software architect analyzing a codebase.
Analyze the following files and their summaries to identify:
1. Domain (e.g., Security, User, Commerce, Database, Common)
2. Layer (e.g., ServiceLayer, RepositoryLayer, PresentationLayer, DomainLayer)
3. Logical dependencies between files (e.g., Auth uses User).

Files:
{context_str}

Return ONLY a JSON object with this structure:
{{
  "file_metadata": {{
    "filename": {{ "domain_tag": "...", "layer": "...", "importance_hint": "High/Medium/Low" }}
  }},
  "logical_edges": [
    {{ "source": "filename", "target": "filename", "type": "logical", "relation": "reason" }}
  ]
}}
"""
        response = self.client.text_generation(
            prompt,
            model=self.model_id,
            max_new_tokens=1000,
            temperature=0.1, # 정형화된 출력을 위해 낮음
            do_sample=False,
            return_full_text=False
        )
        
        # JSON 파싱 시도 (Markdown 코드 블록 제거)
        clean_json = response.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.replace("```json", "").replace("```", "")
        
        return json.loads(clean_json)

    def _analyze_with_openai(self, nodes: List[Dict]) -> Dict[str, Any]:
        file_summaries = []
        for node in nodes[:30]: # OpenAI can handle more context
            fid = node['id']
            summary = node.get('summary_text', 'No summary')[:200]
            file_summaries.append(f"- {fid}: {summary}")
        
        context_str = "\n".join(file_summaries)
        
        system_prompt = "You are a software architect. Analyze the codebase structure and return a JSON object."
        user_prompt = f"""
Analyze the following files to identify Domains, Layers, and Logical Dependencies.

Files:
{context_str}

Return JSON format:
{{
  "file_metadata": {{
    "filename": {{ "domain_tag": "String", "layer": "String", "importance_hint": "High/Medium/Low" }}
  }},
  "logical_edges": [
    {{ "source": "filename", "target": "filename", "type": "logical", "relation": "reason" }}
  ]
}}
"""
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        return json.loads(content)

    def _analyze_rule_based(self, nodes: List[Dict]) -> Dict[str, Any]:
        """
        기존의 규칙 기반 분석 로직 (Fallback용)
        """
        context_metadata = {
            "file_metadata": {},
            "logical_edges": []
        }
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
                "stem": self._extract_stem(node['id']),
                "layer": layer,
                "domain": domain
            })

        # 논리적 엣지 탐지
        context_metadata["logical_edges"] = self._detect_logical_edges(processed_nodes)
        return context_metadata

    def _detect_vector_edges(self, nodes: List[Dict]) -> List[Dict]:
        """
        [RepoCoder Logic]
        임베딩 벡터 유사도를 기반으로 암묵적 연결(Implicit Edges)을 찾습니다.
        """
        edges = []
        
        # [Validation] 노드 리스트 확인
        if not nodes or not isinstance(nodes, list):
            logger.warning("No valid nodes provided for vector analysis.")
            return []

        # 벡터가 있는 노드만 필터링
        valid_nodes = [n for n in nodes if n.get("embedding") is not None]
        
        if len(valid_nodes) < 2:
            return []

        try:
            # 1. 벡터 추출 (타입 안전성 확보)
            ids = [n['id'] for n in valid_nodes]
            
            # 리스트인지 numpy array인지 확인 후 변환
            vectors_list = []
            for n in valid_nodes:
                vec = n['embedding']
                if isinstance(vec, list):
                    vectors_list.append(vec)
                elif isinstance(vec, np.ndarray):
                    vectors_list.append(vec.tolist())
                else:
                    logger.warning(f"Invalid vector type for node {n['id']}: {type(vec)}")
                    return [] # 하나라도 이상하면 중단 (차원 불일치 위험)

            vectors = np.array(vectors_list)
            
            # 차원 확인
            if len(vectors.shape) != 2:
                logger.error(f"Invalid vector shape: {vectors.shape}")
                return []

            # 2. 코사인 유사도 계산 (N x N)
            sim_matrix = cosine_similarity(vectors)

            # 3. 임계값 기반 엣지 생성
            threshold = 0.85
            
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)): # 상삼각행렬만 순회 (중복 방지)
                    sim = sim_matrix[i][j]
                    if sim >= threshold:
                        edges.append({
                            "source": ids[i],
                            "target": ids[j],
                            "type": "logical",
                            "relation": "semantic_similarity", # RepoCoder가 찾은 연결
                            "weight": float(sim)
                        })
            
            logger.info(f"RepoCoder detected {len(edges)} semantic edges.")
            return edges

        except Exception as e:
            logger.error(f"Vector analysis failed: {e}")
            return []

    def _extract_stem(self, filename: str) -> str:
        base = filename.split('/')[-1].replace('.py', '').lower()
        suffixes = ['_service', '_controller', '_repository', '_repo', '_model', '_dto', '_view', 'service', 'controller']
        for suffix in suffixes:
            if base.endswith(suffix):
                return base.replace(suffix, '')
        return base

    def _detect_logical_edges(self, nodes: List[Dict]) -> List[Dict]:
        edges = []
        for i, src in enumerate(nodes):
            for j, tgt in enumerate(nodes):
                if i == j: continue

                # 규칙 1: 아키텍처 계층 연결
                if src['stem'] == tgt['stem'] and len(src['stem']) > 2:
                    if src['layer'] == "PresentationLayer" and tgt['layer'] == "ServiceLayer":
                        edges.append(self._create_edge(src['id'], tgt['id'], "architectural_flow"))
                    elif src['layer'] == "ServiceLayer" and tgt['layer'] == "RepositoryLayer":
                        edges.append(self._create_edge(src['id'], tgt['id'], "data_access"))
                    elif src['layer'] == "ServiceLayer" and tgt['layer'] == "DomainLayer":
                        edges.append(self._create_edge(src['id'], tgt['id'], "uses_model"))

        return edges

    def _create_edge(self, src: str, tgt: str, reason: str) -> Dict:
        return {
            "source": src,
            "target": tgt,
            "type": "logical",
            "relation": reason
        }

def create_analyzer(device=None) -> RepositoryAnalyzer:
    return RepositoryAnalyzer()
