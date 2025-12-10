import sys
import shutil
import asyncio
import time
import uuid
import subprocess
from pathlib import Path
import json

from agent.workflow import get_workflow
from agent.state import AgentState

TEMP_BASE = Path("temp_repos")

def clone_repo(url: str, dest: Path):
    """Clone a git repository to a destination path."""
    if dest.exists():
        print(f"🧹 Clearing existing directory: {dest}")
        shutil.rmtree(dest)
    
    print(f"⬇️ Cloning {url}...")
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])
        print("✅ Clone successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Clone failed: {e}")
        sys.exit(1)

async def analyze_repo(repo_url: str):
    start_time = time.time()
    
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target_dir = TEMP_BASE / repo_name
    
    # 1. Clone
    clone_repo(repo_url, target_dir)
    
    # 2. Setup State
    run_id = str(uuid.uuid4())
    print(f"🚀 Starting analysis for: {repo_name} (RunID: {run_id})")
    
    initial_state: AgentState = {
        "run_id": run_id,
        "repo_input": {"repo_id": repo_name, "local_path": str(target_dir.resolve())},
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
        "repo_path": str(target_dir.resolve()) # Explicitly set repo_path
    }
    
    # 3. Run Workflow
    workflow = get_workflow()
    final_state = await workflow.ainvoke(initial_state)
    
    # 4. Save Result
    result = final_state.get("final_artifact")
    if result:
        output_dir = Path("results")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{repo_name}_result.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis Complete! Result saved to: {output_path}")
        
        # Stats
        coverage = result.get("metrics", {}).get("coverage", {})
        print(f"📊 Stats: {coverage.get('analyzed_files')} files analyzed ({coverage.get('percentage')}%)")
        
    else:
        print("❌ Analysis failed to produce an artifact.")

    # 5. Timing
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"⏱️ Total Execution Time: {elapsed:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_github.py <github_url>")
        print("Example: python analyze_github.py https://github.com/octocat/Hello-World")
        sys.exit(1)
        
    url = sys.argv[1]
    asyncio.run(analyze_repo(url))
