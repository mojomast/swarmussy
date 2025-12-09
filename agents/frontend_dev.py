"""
Frontend Dev - Frontend Engineering Agent

Responsible for user interfaces, client-side logic, and user experience.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.lean_prompts import LEAN_FRONTEND_PROMPT, LEAN_WORKER_SUFFIX
from core.models import AgentConfig
from config.settings import MAX_RESPONSE_TOKENS


# Lean prompt is now the default - much more token efficient
FRONTEND_SYSTEM_PROMPT = LEAN_FRONTEND_PROMPT + LEAN_WORKER_SUFFIX


class FrontendDev(BaseAgent):
    """
    Pixel McFrontend - Senior Frontend Engineer.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Pixel McFrontend",
            model=model,
            system_prompt=FRONTEND_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.6
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Senior Frontend Engineer specializing in UI/UX and client-side logic"
