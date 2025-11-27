"""
agent/router.py
Dynamic Workflow Router (The Orchestrator).
Decides the next step based on analysis quality and context using LLM.
"""
import logging
import json
from typing import Literal, Dict, Any
from huggingface_hub import InferenceClient
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .config import Config

logger = logging.getLogger(__name__)

class WorkflowRouter:
    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.client = None
        self.model_id = None

        if self.provider == "openai":
            api_key = Config.OPENAI_API_KEY
            if api_key and OpenAI:
                self.client = OpenAI(api_key=api_key)
                self.model_id = Config.MODEL_LLM_OPENAI # Use the smart model for routing
            else:
                logger.warning("OpenAI API Key missing. Router disabled.")
        else:
            token = Config.HF_API_KEY
            if token:
                self.client = InferenceClient(token=token)
                self.model_id = Config.MODEL_LLM
            else:
                logger.warning("HF_API_KEY missing. Router disabled.")

    def route(self, state: Dict[str, Any]) -> Literal["pass", "refine"]:
        """
        Decides whether to pass to the next phase or refine the current analysis.
        """
        # 1. Check hard limits first (Safety Net)
        retry_count = state.get("retry_count", 0)
        if retry_count >= Config.MAX_RETRIES:
            logger.info(f"Max retries ({Config.MAX_RETRIES}) reached. Forcing pass.")
            return "pass"

        # 2. If no client, fall back to rule-based
        if not self.client:
            return self._rule_based_route(state)

        # 3. LLM Decision
        try:
            metrics = state.get("metrics", {})
            score = metrics.get("consistency_score", 0.0)
            
            # Context for the LLM
            context = f"""
Current Analysis Status:
- Consistency Score: {score:.2f} (Target: > 0.7)
- Retry Count: {retry_count}
- Number of Files Analyzed: {len(state.get("initial_summaries", []))}
"""
            if self.provider == "openai":
                return self._route_with_openai(context)
            else:
                return self._route_with_hf(context)

        except Exception as e:
            logger.error(f"Routing failed: {e}. Falling back to rule-based.")
            return self._rule_based_route(state)

    def _rule_based_route(self, state: Dict[str, Any]) -> Literal["pass", "refine"]:
        metrics = state.get("metrics", {})
        score = metrics.get("consistency_score", 0.0)
        if score >= 0.7:
            return "pass"
        return "refine"

    def _route_with_openai(self, context: str) -> Literal["pass", "refine"]:
        system_prompt = """You are the Orchestrator of a code analysis agent.
Your goal is to ensure high-quality analysis by strictly following these rules:

[DECISION RUBRIC]
1. **CRITICAL FAILURE**: If 'Consistency Score' is 0.0 or 'Number of Files Analyzed' is 0 -> MUST 'refine'.
2. **LOW QUALITY**: If 'Consistency Score' < 0.7 -> SHOULD 'refine' (unless Retry Count >= 2).
3. **ACCEPTABLE**: If 'Consistency Score' >= 0.7 -> MUST 'pass'.
4. **MAX RETRIES**: If 'Retry Count' >= 2 -> MUST 'pass' (stop infinite loops).

Analyze the provided status against these rules.
Return ONLY a JSON object: {"decision": "pass" or "refine", "reason": "Brief explanation referencing the rule applied"}"""

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        content = response.choices[0].message.content
        decision_json = json.loads(content)
        decision = decision_json.get("decision", "pass")
        logger.info(f"Orchestrator Decision: {decision} (Reason: {decision_json.get('reason')})")
        
        return decision if decision in ["pass", "refine"] else "pass"

    def _route_with_hf(self, context: str) -> Literal["pass", "refine"]:
        # Simplified prompt for weaker models
        prompt = f"""
[Role] Orchestrator
[Task] Decide next step: 'pass' or 'refine'.
[Context] {context}
[Rule] Score < 0.7 -> refine. Else -> pass.
[Output] JSON {{ "decision": "..." }}
"""
        response = self.client.text_generation(
            prompt,
            model=self.model_id,
            max_new_tokens=50,
            temperature=0.1,
            return_full_text=False
        )
        
        try:
            # Try parsing JSON, handle potential markdown wrapping
            clean = response.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean)
            return data.get("decision", "pass")
        except:
            # Fallback heuristic if JSON fails
            if "refine" in response.lower(): return "refine"
            return "pass"

def create_router() -> WorkflowRouter:
    return WorkflowRouter()
