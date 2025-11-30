# System Architecture & Data Flow 🏗️

This document details the data flow through the Fithub Agent, providing **concrete JSON examples** for each stage to facilitate verification and debugging.

## 1. Workflow Diagram (Mermaid)

```mermaid
graph TD
    %% Nodes
    Start([User Request]) --> Ingest[Ingest Node]
    
    subgraph Phase 1: Parallel Analysis
        Ingest --> Summarize[Summarizer MCP<br/>(CodeT5)]
        Ingest --> Structure[Structural MCP<br/>(Tree-sitter)]
        Ingest --> Embed[Embedder MCP<br/>(GraphCodeBERT)]
    end
    
    Summarize --> Fusion[Fusion Node]
    Structure --> Fusion
    Embed --> Fusion
    
    subgraph Phase 2: Orchestration
        Fusion --> Evaluate[Evaluate Consistency]
        Evaluate --> Router{Orchestrator<br/>(GPT-4o)}
        
        Router -- "Low Quality" --> Summarize
        Router -- "Pass" --> RepoAnalysis
    end
    
    subgraph Phase 3: Context & Visual
        RepoAnalysis[Repo Analyzer MCP<br/>(GPT-4o + RepoCoder)]
        RepoAnalysis --> Visualizer[Visualizer MCP<br/>(RepoGraph GNN)]
    end
    
    Visualizer --> Synthesize[Synthesize Result]
    Synthesize --> End([Final Response])

    %% Styling
    style Router fill:#f96,stroke:#333,stroke-width:2px
    style RepoAnalysis fill:#bbf,stroke:#333,stroke-width:2px
    style Visualizer fill:#bbf,stroke:#333,stroke-width:2px
```

---

## 2. Component I/O & JSON Examples

### Phase 1: Parallel Analysis

#### A. Summarizer MCP
*   **Model**: `Salesforce/codet5-base`
*   **Action**: Generates natural language summaries for code files.
*   **Output JSON** (`initial_summaries`):
```json
[
  "auth.py: Implements JWT login and user authentication logic.",
  "database.py: Manages connection pool and executes SQL queries.",
  "utils.py: Provides helper functions for date formatting and hashing."
]
```

#### B. Structural MCP
*   **Tool**: `Tree-sitter`
*   **Action**: Extracts static import dependencies.
*   **Output JSON** (`code_graph_raw`):
```json
{
  "auth.py": ["utils.py", "database.py"],
  "main.py": ["auth.py"],
  "utils.py": []
}
```

#### C. Embedder MCP
*   **Model**: `microsoft/graphcodebert-base`
*   **Action**: Converts code snippets into 768-dimensional vectors.
*   **Output JSON** (`embeddings`):
```json
[
  {
    "id": "auth.py",
    "embedding": [0.123, -0.456, 0.789, "... (768 floats)"]
  },
  {
    "id": "utils.py",
    "embedding": [0.001, 0.999, -0.123, "..."]
  }
]
```

---

### Phase 2: Fusion & Orchestration

#### D. Fusion Node
*   **Action**: Merges all Phase 1 outputs into a single graph structure.
*   **Output JSON** (`fused_data_package`):
```json
{
  "nodes": [
    {
      "id": "auth.py",
      "type": "file",
      "summary_text": "Implements JWT login...",
      "embedding": [0.123, -0.456, ...]
    }
  ],
  "edges": [
    {
      "source": "main.py",
      "target": "auth.py",
      "type": "import"
    }
  ]
}
```

#### E. Orchestrator (Router)
*   **Model**: `GPT-4o`
*   **Action**: Evaluates consistency between code and summary.
*   **Input Context**: `{"consistency_score": 0.65, "retry_count": 0}`
*   **Output JSON** (Decision):
```json
{
  "decision": "refine",
  "reason": "Consistency score 0.65 is below threshold 0.7. Requesting re-summarization."
}
```

---

### Phase 3: Context & Visualization

#### F. Repository Analyzer MCP
*   **Model**: `GPT-4o` + `RepoCoder` (Vector Similarity)
*   **Action**: Identifies architectural layers and implicit logical connections.
*   **Output JSON** (`context_metadata`):
```json
{
  "file_metadata": {
    "auth.py": { "layer": "Service", "domain": "Security" },
    "database.py": { "layer": "Infrastructure", "domain": "Data" }
  },
  "logical_edges": [
    {
      "source": "auth.py",
      "target": "user_model.py",
      "weight": 0.85,
      "reason": "High semantic similarity in vector space"
    }
  ]
}
```

#### G. Visualizer MCP (Final Output)
*   **Model**: `RepoGraph` (GNN)
*   **Action**: Calculates node importance (size) and assigns domain colors.
*   **Output JSON** (`final_graph_json`):
```json
{
  "nodes": [
    {
      "id": "auth.py",
      "label": "auth.py",
      "size": 45.5,          // Calculated by PageRank/GNN
      "color": "#FF5733",    // Mapped from 'Security' domain
      "data": {
        "layer": "Service",
        "summary": "Implements JWT login..."
      }
    }
  ],
  "edges": [
    {
      "source": "main.py",
      "target": "auth.py",
      "width": 2.0
    },
    {
      "source": "auth.py",
      "target": "user_model.py",
      "width": 1.0,
      "style": "dashed"      // Logical edge
    }
  ]
}
```
