import json
import os
import logging
from pathlib import Path
from typing import Any, Dict
from .config import Config

logger = logging.getLogger(__name__)

def save_mcp_result(run_id: str, component: str, data: Any) -> None:
    """
    Save intermediate MCP results to a structured directory.
    
    Args:
        run_id: The unique ID of the current analysis run.
        component: The name of the component (e.g., 'summarization', 'structural').
        data: The data to save (usually a dict or list).
    """
    try:
        # Define result directory: project_root/results/{run_id}
        # Assuming Config.TEMP_DIR or similar is available, or just use a 'results' dir in root
        result_dir = Path("results") / run_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = result_dir / f"{component}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved {component} result to {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save {component} result: {e}")
