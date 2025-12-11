
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(".").resolve()))

from mcp.graph_analysis.visualizer import GraphBuilder

class CodeVisualizer:
    def __init__(self):
        self.builder = GraphBuilder()
        
    def generate(self, fused_data, context_metadata):
        return self.builder.build_graph(fused_data['nodes'], fused_data['edges'], context_metadata)
from mcp.repository_analysis.analyzer import RepositoryAnalyzer

def generate_graph_from_intermediate(result_dir_path):
    result_dir = Path(result_dir_path)
    
    print(f"📂 Loading intermediate files from: {result_dir}")
    
    # Load intermediate files
    try:
        with open(result_dir / "structural.json", "r") as f:
            structural_data = json.load(f)
        with open(result_dir / "summarization.json", "r") as f:
            summarization_data = json.load(f)
        with open(result_dir / "embedding.json", "r") as f:
            embedding_data = json.load(f)
            
        print("✅ Metadata loaded successfully.")
    except FileNotFoundError as e:
        print(f"❌ Missing file: {e}")
        return

    # Mock Fused Data Structure
    # Fusion node logic usually combines these, we'll do a simple merge
    nodes_map = {}
    
    # 1. Base from structure
    for node in structural_data.get("nodes", []):
        nodes_map[node["id"]] = node
        
    # 2. Add Summaries
    for sum_item in summarization_data: # List of dicts
        fid = sum_item.get("code_id") # Fix: Matches summarization.json schema
        if fid in nodes_map:
            nodes_map[fid]["summary_text"] = sum_item.get("text", "") # Fix: Matches summarization.json schema
    
    # 3. Add Embeddings
    for emb_item in embedding_data:
        fid = emb_item.get("id")
        if fid in nodes_map:
            nodes_map[fid]["embedding"] = emb_item.get("vector")
            
    fused_data = {
        "nodes": list(nodes_map.values()),
        "edges": structural_data.get("edges", [])
    }
    
    print("🧩 Data fused internally.")
    
    # 4. Context Analysis (Repo MCP)
    print("🏗️ Running Repository Analysis (Context)...")
    repo_analyzer = RepositoryAnalyzer()
    context_metadata = repo_analyzer.analyze(fused_data)
    
    # 5. Graph Visualization (Visual MCP)
    print("🎨 Running Graph Visualization...")
    visualizer = CodeVisualizer()
    final_json = visualizer.generate(fused_data, context_metadata)
    
    # 6. Save Result
    output_path = result_dir / "visualization_data.json"
    with open(output_path, "w") as f:
        json.dump(final_json, f, indent=2)
        
    print(f"🎉 Final Graph JSON saved to: {output_path.resolve()}")

if __name__ == "__main__":
    # Target the Latest Directory found previously: e4cfeebf-c57a-4bae-af8a-fd3f1dd3229c
    TARGET_DIR = "results/e4cfeebf-c57a-4bae-af8a-fd3f1dd3229c"
    generate_graph_from_intermediate(TARGET_DIR)
