"""
Architect - Lead Architect & Swarm Orchestrator Agent

Responsible for high-level system design, task breakdown, and orchestrating
the work of other agents.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.lean_prompts import LEAN_ARCHITECT_PROMPT
from core.models import AgentConfig
from core.settings_manager import get_settings
from config.settings import MAX_RESPONSE_TOKENS


# Lean prompt is now the default - much more token efficient
ARCHITECT_SYSTEM_PROMPT = LEAN_ARCHITECT_PROMPT


class Architect(BaseAgent):
    """
    Bossy McArchitect - Lead Architect & Swarm Orchestrator.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Bossy McArchitect",
            model=model,
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.5  # Moderate - waits for user input
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Lead Architect & Swarm Orchestrator responsible for system design and task assignment"
