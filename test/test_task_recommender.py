import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock huggingface_hub and dotenv before importing recommender
sys.modules['huggingface_hub'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from mcp.task_recommender.recommender import create_recommender

class TestTaskRecommender(unittest.TestCase):
    def setUp(self):
        # Mock Config
        with patch('agent.config.Config') as MockConfig:
            MockConfig.LLM_PROVIDER = "huggingface"
            MockConfig.HF_API_KEY = "mock_token"
            MockConfig.MODEL_LLM = "mock_model"
            
            self.recommender = create_recommender()
            self.recommender.client = MagicMock()

        # Create mock nodes
        nodes = []
        for i in range(25):
            nodes.append({
                "id": f"file_{i}.py",
                "size": 100 - i,
                "complexity": 10,
                "summary_text": f"Summary for file {i}"
            })
        
        self.mock_analysis_results = {
            "graph": {
                "nodes": nodes,
                "edges": []
            },
            "context": {
                "file_metadata": {f"file_{i}.py": {"layer": "Common"} for i in range(25)}
            }
        }

    def test_reliability_features(self):
        # Scenario: AI returns 3 tasks:
        # 1. Valid task (Confidence 90, Exists)
        # 2. Low confidence task (Confidence 50, Exists) -> Should be filtered
        # 3. Hallucinated task (Confidence 90, Not Exists) -> Should be filtered
        
        mock_ai_recs = [
            {
                "target": "file_0.py",
                "reason": "Valid",
                "priority": "High",
                "type": "refactor",
                "category": "Backend",
                "confidence": 90
            },
            {
                "target": "file_1.py",
                "reason": "Low Confidence",
                "priority": "High",
                "type": "refactor",
                "category": "Backend",
                "confidence": 50 # Should be filtered (< 70)
            },
            {
                "target": "ghost_file.py", # Does not exist in nodes
                "reason": "Hallucination",
                "priority": "High",
                "type": "refactor",
                "category": "Backend",
                "confidence": 90
            }
        ]
        
        with patch.object(self.recommender, '_recommend_with_llm', return_value=mock_ai_recs):
            # Mock Rule-based to return nothing to isolate AI testing
            with patch.object(self.recommender, '_get_rule_based_recommendations', return_value=[]):
                
                # Mock Filtering LLM to select all candidates passed to it
                # We expect only file_0.py to be passed
                filter_response = json.dumps({"selected_ids": [0]})
                self.recommender.client.text_generation.return_value = filter_response
                
                final_tasks = self.recommender.recommend_tasks(self.mock_analysis_results, top_k=10)
                
                # Verify only 1 task remains
                self.assertEqual(len(final_tasks), 1)
                self.assertEqual(final_tasks[0]['target'], "file_0.py")
                
                # Verify confidence is preserved (if we kept it in output, but currently we don't strictly need to assert it in final output unless we added it)
                # The key is that others are gone.

if __name__ == '__main__':
    unittest.main()
