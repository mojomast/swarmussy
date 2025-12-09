"""
Technical Writer - Documentation & API Docs Agent

Responsible for creating comprehensive documentation, API references, and user guides.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.lean_prompts import LEAN_TECH_WRITER_PROMPT, LEAN_WORKER_SUFFIX
from core.models import AgentConfig
from config.settings import MAX_RESPONSE_TOKENS


# Lean prompt is now the default - much more token efficient
TECH_WRITER_SYSTEM_PROMPT = LEAN_TECH_WRITER_PROMPT + LEAN_WORKER_SUFFIX


class TechWriter(BaseAgent):
    """
    Docy McWriter - Senior Technical Writer.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Docy McWriter",
            model=model,
            system_prompt=TECH_WRITER_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.4
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Senior Technical Writer specializing in API docs, guides, and developer documentation"
