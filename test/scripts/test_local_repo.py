import asyncio
import shutil
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent.workflow import get_workflow
from agent.config import Config

# Setup Mock Environment
Config.LLM_PROVIDER = "openai"
Config.OPENAI_API_KEY = "sk-dummy" # Mocked in real test, but here we rely on the mock patches if running verify_pipeline logic, 
# BUT this script is intended to run with REAL files. 
# If the user has a real key in .env, it will work. If not, we might need to mock.
# For now, let's assume we want to test the INGESTION logic primarily.

async def test_local_repo():
    print("🚀 Testing Local Repo Ingestion...")
    
    # 1. Create a dummy local repo
    # Define path relative to this script (test/scripts/test_local_repo.py -> test/repos/sample_repo)
    base_dir = Path(__file__).parent.parent / "repos"
    base_dir.mkdir(parents=True, exist_ok=True)
    local_repo_path = base_dir / "sample_repo"
    
    if local_repo_path.exists():
        shutil.rmtree(local_repo_path)
    local_repo_path.mkdir()
    
    # Add some files
    (local_repo_path / "main.py").write_text("def main():\n    print('Hello World')")
    (local_repo_path / "utils.py").write_text("def helper():\n    return True")
    (local_repo_path / "service").mkdir()
    (local_repo_path / "service" / "auth.py").write_text("def login():\n    pass")

    print(f"✅ Created sample repo at {local_repo_path.resolve()}")

    # 2. Prepare Agent State with local_path
    initial_state = {
        "run_id": "test_local_run",
        "repo_input": {
            "repo_id": "local-sample",
            "local_path": str(local_repo_path.resolve())
        },
        "retry_count": 0,
        "initial_summaries": [],
        "embeddings": [],
        "code_graph_raw": {},
        "fused_data_package": {},
        "context_metadata": {},
        "final_graph_json": {},
        "metrics": {},
        "recommendations": []
    }

    # 3. Run Workflow
    # We need to mock the LLM/Embedder parts if we don't have real keys, 
    # but let's try to run it and see if it at least ingests correctly.
    # To avoid API errors, we can mock the expensive nodes or just check if 'ingest' worked.
    
    # For this test, let's just run the 'ingest' node directly to verify the logic,
    # OR run the full workflow with mocks. Let's run full workflow with mocks to be safe.
    
    from unittest.mock import MagicMock, patch
    
    mock_client = MagicMock()
    mock_client.text_generation.return_value = "Summary"
    mock_client.feature_extraction.return_value = [0.1] * 768
    
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value.choices[0].message.content = '{"decision": "pass", "file_metadata": {}, "logical_edges": []}'

    with patch('huggingface_hub.InferenceClient', return_value=mock_client), \
         patch('mcp.summarization.summarizer.InferenceClient', return_value=mock_client), \
         patch('mcp.semantic_embedding.embedder.InferenceClient', return_value=mock_client), \
         patch('mcp.repository_analysis.analyzer.InferenceClient', return_value=mock_client), \
         patch('agent.router.OpenAI', return_value=mock_openai), \
         patch('mcp.repository_analysis.analyzer.OpenAI', return_value=mock_openai):

        workflow = get_workflow()
        final_state = await workflow.ainvoke(initial_state)
        
        # 4. Verify
        repo_path = final_state.get("repo_path")
        print(f"Agent Repo Path: {repo_path}")
        
        if repo_path and os.path.exists(repo_path):
            copied_files = list(Path(repo_path).rglob("*.py"))
            print(f"Found {len(copied_files)} files in agent workspace.")
            assert len(copied_files) == 3
            assert (Path(repo_path) / "service" / "auth.py").exists()
            print("✅ Local Ingestion Verified! Files copied successfully.")
        else:
            print("❌ Local Ingestion Failed.")

    # Cleanup
    # shutil.rmtree(local_repo_path)

if __name__ == "__main__":
    asyncio.run(test_local_repo())
