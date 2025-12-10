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
    
    NOTE: In Devussy mode with AutoDispatcher enabled, the Architect is mostly
    passive. The AutoDispatcher handles task dispatch locally without LLM calls.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Bossy McArchitect",
            model=model,
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.1  # Very low - AutoDispatcher handles most work
        )
        super().__init__(config)
    
    def should_respond(self, message) -> bool:
        """
        Override to disable Architect when AutoDispatcher is active.
        
        The Architect only responds to:
        - Direct mentions of "Architect" or "Bossy"
        - Explicit requests for design/planning help
        - NOT "go" commands (AutoDispatcher handles those)
        """
        from core.auto_dispatcher import get_auto_dispatcher
        
        content = message.content.lower() if message.content else ""
        
        # Never respond to "go" - AutoDispatcher handles it
        if content.strip() == "go":
            return False
        
        # Never respond to auto-orchestrator messages (AutoDispatcher handles continuation)
        if message.sender_name == "Auto Orchestrator":
            return False
        
        # Only respond if explicitly mentioned
        if "architect" in content or "bossy" in content:
            return True
        
        # Or if asking for design/planning help
        if any(kw in content for kw in ["design", "plan", "architect", "structure", "breakdown"]):
            return True
        
        # Otherwise stay quiet - let workers do their thing
        return False
    
    @property
    def persona_description(self) -> str:
        return "Lead Architect & Swarm Orchestrator responsible for system design and task assignment"
