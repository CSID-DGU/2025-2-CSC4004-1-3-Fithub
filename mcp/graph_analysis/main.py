"""FastAPI server for Graph Analysis MCP."""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from .visualizer import create_visualizer

app = FastAPI(title="Graph Analysis MCP")
builder = create_visualizer()

class GraphRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    context_metadata: Dict[str, Any]

@app.post("/build-graph")
async def build_graph(request: GraphRequest):
    return builder.build_graph(
        request.nodes,
        request.edges,
        request.context_metadata
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9005)
