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
    
    def should_respond(self) -> bool:
        """
        Override to disable Architect when AutoDispatcher is active.
        
        The Architect ONLY responds to:
        - Direct mentions of "Architect" or "Bossy" by a HUMAN
        - NOT task completions, not system messages, not worker messages
        
        AutoDispatcher handles ALL orchestration now.
        """
        # Find the last message in memory to check content
        last_message = None
        for msg in reversed(self._short_term_memory):
            if msg.content:
                last_message = msg
                break
        
        if not last_message:
            return False
        
        content = last_message.content.lower() if last_message.content else ""
        sender_name = getattr(last_message, 'sender_name', '') or ''
        role = getattr(last_message, 'role', None)
        
        # NEVER respond to system messages, auto-orchestrator, or agent messages
        if sender_name in ("System", "Auto Orchestrator", "AutoDispatch"):
            return False
        if role and role.value in ("system", "assistant"):
            return False
        
        # NEVER respond to task completions or status updates
        if "task complete" in content or "✅" in content:
            return False
        
        # NEVER respond to "go" commands
        if content.strip() == "go":
            return False
        
        # NEVER respond to get_next_task results or dispatch messages
        if any(kw in content for kw in ["dispatching", "dispatched", "assigned to", "next task"]):
            return False
        
        # ONLY respond if a HUMAN explicitly mentions the Architect
        # Check if this looks like a human message (not from an agent)
        agent_names = ["codey", "pixel", "bugsy", "deployo", "docy", "checky"]
        sender_lower = sender_name.lower()
        is_agent_message = any(name in sender_lower for name in agent_names)
        
        if is_agent_message:
            return False
        
        # Only respond to direct human mentions
        if "architect" in content or "bossy" in content:
            return True
        
        # Otherwise stay completely quiet
        return False
    
    @property
    def persona_description(self) -> str:
        return "Lead Architect & Swarm Orchestrator responsible for system design and task assignment"
