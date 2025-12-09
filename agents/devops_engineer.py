"""
DevOps Engineer - Infrastructure & Deployment Agent

Responsible for CI/CD, containerization, cloud infrastructure, and deployment automation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.lean_prompts import LEAN_DEVOPS_PROMPT, LEAN_WORKER_SUFFIX
from core.models import AgentConfig
from config.settings import MAX_RESPONSE_TOKENS


# Lean prompt is now the default - much more token efficient
DEVOPS_SYSTEM_PROMPT = LEAN_DEVOPS_PROMPT + LEAN_WORKER_SUFFIX


class DevOpsEngineer(BaseAgent):
    """
    Deployo McOps - Senior DevOps Engineer.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Deployo McOps",
            model=model,
            system_prompt=DEVOPS_SYSTEM_PROMPT,
            temperature=0.4,  # Lower temperature for precise configs
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.5
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Senior DevOps Engineer specializing in CI/CD, containers, and cloud infrastructure"
