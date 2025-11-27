# Fithub Agent Setup Guide 🚀

This guide will help you set up the Fithub Agent environment, configure API keys, and run the system.

## 1. Prerequisites

Ensure you have the following installed:
- **Python 3.10+**
- **Git**
- **pip** (Python package manager)

## 2. Environment Configuration

The agent relies on environment variables for API keys and paths.

1.  Copy the example configuration file:
    ```bash
    cp .env.example .env
    ```

2.  Open `.env` and fill in the required values:

    | Variable | Description | Required? |
    | :--- | :--- | :--- |
    | `LLM_PROVIDER` | `huggingface` (default) or `openai`. | No |
    | `HF_API_KEY` | **Hugging Face API Key**. Used for Embedding/Summarization. | **Yes** |
    | `OPENAI_API_KEY` | **OpenAI API Key**. Required if `LLM_PROVIDER=openai`. | Conditional |
    | `LOCAL_MODEL_DIR` | Absolute path to the `RepoGraph` model directory. | **Yes** |
    | `BACKEND_API_URL` | URL of the Fithub Backend API. Default: `http://localhost:4000/api` | No |
    | `TEMP_DIR` | Directory to store temporary repository files. Default: `./temp_repos` | No |

    ### Optional: LangSmith Tracing 🛠️
    To monitor agent execution steps and debug issues, configure LangSmith:
    | Variable | Description |
    | :--- | :--- |
    | `LANGCHAIN_TRACING_V2` | Set to `true` to enable tracing. |
    | `LANGCHAIN_API_KEY` | Your LangSmith API Key. Get it [here](https://smith.langchain.com/). |
    | `LANGCHAIN_PROJECT` | Project name (e.g., `fithub-agent`). |

## 3. Installation

Install the required Python dependencies:

```bash
# Create a virtual environment (Recommended)
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

> **Note**: If `requirements.txt` is missing, install the core packages manually:
> ```bash
> pip install fastapi uvicorn langgraph scikit-learn networkx numpy huggingface_hub python-dotenv grep_ast pygments tree-sitter tree-sitter-languages transformers torch
> ```

## 4. Running the Agent

### A. Verify Installation
Run the verification script to ensure everything is connected correctly:
```bash
python verify_pipeline.py
```
If successful, you should see `✅ Workflow Completed!` and a summary of the graph nodes.

### B. Start the Server
To start the agent API server:
```bash
uvicorn agent.main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`.

## 5. Troubleshooting

-   **`ModuleNotFoundError: tree_sitter`**: Ensure you installed `tree-sitter` and `tree-sitter-languages`.
-   **`HF_API_KEY is missing`**: Check your `.env` file and make sure `python-dotenv` is installed.
-   **`RepoGraph` import error**: Verify `LOCAL_MODEL_DIR` points to the correct folder containing `repograph`.
