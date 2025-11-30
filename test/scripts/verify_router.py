import asyncio
import logging
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent.router import create_router
from agent.config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_router():
    print("🚀 Testing Workflow Router...")

    # Mock OpenAI
    mock_openai = MagicMock()
    # Scenario 1: Low score -> Refine
    mock_openai.chat.completions.create.return_value.choices[0].message.content = '{"decision": "refine", "reason": "Score is too low"}'
    
    with patch('agent.router.OpenAI', return_value=mock_openai):
        Config.LLM_PROVIDER = "openai"
        Config.OPENAI_API_KEY = "sk-dummy"
        
        router = create_router()
        
        # Test Case 1: Low Score
        state_low = {"metrics": {"consistency_score": 0.5}, "retry_count": 0, "initial_summaries": ["file1", "file2"]}
        decision = router.route(state_low)
        print(f"Case 1 (Score 0.5): Expected 'refine', Got '{decision}'")
        assert decision == "refine"

        # Scenario 2: High score -> Pass
        mock_openai.chat.completions.create.return_value.choices[0].message.content = '{"decision": "pass", "reason": "Score is good"}'
        
        # Test Case 2: High Score
        state_high = {"metrics": {"consistency_score": 0.8}, "retry_count": 0, "initial_summaries": ["file1", "file2"]}
        decision = router.route(state_high)
        print(f"Case 2 (Score 0.8): Expected 'pass', Got '{decision}'")
        assert decision == "pass"

        # Test Case 3: Max Retries (Should pass regardless of LLM)
        state_max = {"metrics": {"consistency_score": 0.1}, "retry_count": 2, "initial_summaries": ["file1"]}
        decision = router.route(state_max)
        print(f"Case 3 (Max Retries): Expected 'pass', Got '{decision}'")
        assert decision == "pass"

    print("✅ Router Verification Passed!")

if __name__ == "__main__":
    test_router()
