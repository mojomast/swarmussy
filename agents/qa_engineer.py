"""
QA Engineer - Quality Assurance & Security Agent

Responsible for testing, code review, security auditing, and ensuring quality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.lean_prompts import LEAN_QA_PROMPT, LEAN_WORKER_SUFFIX
from core.models import AgentConfig
from config.settings import MAX_RESPONSE_TOKENS


# Lean prompt is now the default - much more token efficient
QA_SYSTEM_PROMPT = LEAN_QA_PROMPT + LEAN_WORKER_SUFFIX


class QAEngineer(BaseAgent):
    """
    Bugsy McTester - Lead QA & Security Engineer.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Bugsy McTester",
            model=model,
            system_prompt=QA_SYSTEM_PROMPT,
            temperature=0.4,  # Low temperature for rigorous testing
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.5
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Lead QA & Security Engineer specializing in testing, code review, and security auditing"
