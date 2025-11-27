import asyncio
import time
import os
import sys
import logging
from agent.state import AgentState
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent.workflow import get_workflow
from agent.config import Config

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock InferenceClient to avoid API calls
mock_client = MagicMock()
mock_client.text_generation.return_value = "This is a dummy summary."
mock_client.feature_extraction.return_value = [0.1] * 768 # Dummy embedding

# Mock OpenAI Client
mock_openai = MagicMock()
mock_openai.chat.completions.create.return_value.choices[0].message.content = '{"file_metadata": {}, "logical_edges": []}'

# Patching modules
patch('huggingface_hub.InferenceClient', return_value=mock_client).start()
patch('mcp.summarization.summarizer.InferenceClient', return_value=mock_client).start()
patch('mcp.semantic_embedding.embedder.InferenceClient', return_value=mock_client).start()
patch('mcp.repository_analysis.analyzer.InferenceClient', return_value=mock_client).start()
patch('mcp.repository_analysis.analyzer.OpenAI', return_value=mock_openai).start()

# Force OpenAI Provider
Config.LLM_PROVIDER = "openai"
Config.OPENAI_API_KEY = "sk-dummy"

async def run_verification():
    print("🚀 Starting Verification Pipeline...")
    
    # 1. 초기 상태 설정
    initial_state: AgentState = {
        "run_id": "verify_test_run",
        "repo_input": {"repo_id": "test_repo", "branch": "main"},
        "options": {},
        "thresholds": {},
        "retry_count": 0,
        "initial_summaries": [],
        "embeddings": [],
        "code_graph_raw": {},
        "fused_data_package": {},
        "context_metadata": {},
        "final_graph_json": {},
        "metrics": {},
        "recommendations": [],
        "node_execution_log": []
    }

    # 2. 분석 실행 (직접 호출)
    # _run_analysis는 비동기 함수이므로 await 필요
    # execution_store는 main.py에 전역으로 있지만, 여기서는 직접 state를 확인
    
    from agent.workflow import get_workflow
    workflow = get_workflow()
    
    print("🔄 Invoking Workflow...")
    final_state = await workflow.ainvoke(initial_state)
    
    print("✅ Workflow Completed!")
    
    # 3. 결과 검증
    print("\n📊 Verification Results:")
    
    # A. RepoGraph & GNN Check
    graph_json = final_state.get("final_graph_json", {})
    nodes = graph_json.get("nodes", [])
    edges = graph_json.get("edges", [])
    
    print(f" - Nodes: {len(nodes)}")
    print(f" - Edges: {len(edges)}")
    
    # 중요도(Size)가 반영되었는지 확인
    sizes = [n['size'] for n in nodes]
    if sizes:
        print(f" - Node Sizes: {sizes}")
        if max(sizes) > 30: # 기본값이 30이므로, 중요도가 반영되면 더 커야 함
            print("   ✅ RepoGraph Importance Reflected (Size > 30)")
        else:
            print("   ⚠️ RepoGraph Importance NOT Reflected (All default size)")
            
    # B. RepoCoder Check
    # 논리적 엣지가 있는지 확인
    logical_edges = [e for e in edges if e.get('type') == 'logical']
    print(f" - Logical Edges: {len(logical_edges)}")
    if logical_edges:
         print("   ✅ RepoCoder Logic Reflected (Logical edges found)")
    else:
         print("   ⚠️ RepoCoder Logic NOT Reflected (No logical edges)")

    # C. LLM Check
    # 도메인 태그 확인
    domains = set(n.get('color') for n in nodes)
    print(f" - Domains (Colors): {domains}")

if __name__ == "__main__":
    asyncio.run(run_verification())
