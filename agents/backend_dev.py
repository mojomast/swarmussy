"""
Backend Dev - Backend Engineering Agent

Responsible for server-side logic, APIs, databases, and system implementation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.lean_prompts import LEAN_BACKEND_PROMPT, LEAN_WORKER_SUFFIX
from core.models import AgentConfig
from config.settings import MAX_RESPONSE_TOKENS


# Lean prompt is now the default - much more token efficient
BACKEND_SYSTEM_PROMPT = LEAN_BACKEND_PROMPT + LEAN_WORKER_SUFFIX


class BackendDev(BaseAgent):
    """
    Codey McBackend - Senior Backend Engineer.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Codey McBackend",
            model=model,
            system_prompt=BACKEND_SYSTEM_PROMPT,
            temperature=0.5,  # Lower temperature for precise code
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.6
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Senior Backend Engineer specializing in APIs, databases, and server logic"
