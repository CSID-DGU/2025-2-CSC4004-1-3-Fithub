import asyncio
import json
import uuid
from pathlib import Path
import time # [Modified]
from agent.workflow import get_workflow
from agent.schemas import RepoInput
from agent.state import AgentState

async def regenerate():
    print("🔄 Regenerating verification_result.json...")
    start_time = time.time() # [Modified]
    
    repo_path = str(Path(".").resolve())
    run_id = str(uuid.uuid4())
    
    # 1. Initialize State
    initial_state: AgentState = {
        "run_id": run_id,
        "repo_input": {"repo_id": "restore-local", "local_path": repo_path},
        "options": {"force_refresh": True},
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
    
    # 2. Run Workflow
    print(f"📂 Analyzing: {repo_path}")
    workflow = get_workflow()
    final_state = await workflow.ainvoke(initial_state)
    
    # 3. Extract Result
    result = final_state.get("final_artifact")
    
    if result:
        output_path = Path("verification_result.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Restored: {output_path.resolve()}")
    else:
        print("❌ Regeneration failed: No artifact produced.")
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"⏱️ Total Analysis Time: {elapsed:.2f}s") # [Modified]

if __name__ == "__main__":
    asyncio.run(regenerate())
