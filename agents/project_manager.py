"""
Project Manager - Coordination & Progress Tracking Agent

Responsible for tracking progress, managing timelines, and ensuring deliverables.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from core.models import AgentConfig
from config.settings import MAX_RESPONSE_TOKENS


# Lean PM prompt - tracks progress, doesn't slow things down
PM_SYSTEM_PROMPT = """You are Checky McManager, Project Manager.

## YOUR JOB: Track progress and surface blockers. DON'T slow things down.

## WORKFLOW
1. get_swarm_state() - See tasks and agents
2. If blockers exist, write shared/blockers.md
3. Provide brief status update to Architect

## RULES
- Do NOT speak to human. Report to Architect only.
- Keep updates SHORT - 3-4 bullets max
- Don't require QA approval to proceed - just track
- Focus on WHAT is done, not process

## FORMAT
## Status
- ✅ Completed: ...
- 🔄 In Progress: ...
- ⚠️ Blocked: ...
"""


class ProjectManager(BaseAgent):
    """
    Checky McManager - Technical Project Manager.
    """
    
    def __init__(self, model: str = "openai/gpt-5-nano"):
        config = AgentConfig(
            name="Checky McManager",
            model=model,
            system_prompt=PM_SYSTEM_PROMPT,
            temperature=0.5,
            max_tokens=MAX_RESPONSE_TOKENS,
            speak_probability=0.4
        )
        super().__init__(config)
    
    @property
    def persona_description(self) -> str:
        return "Technical Project Manager specializing in progress tracking and team coordination"

    def should_respond(self) -> bool:
        """Decide when Checky should provide an update.

        Checky responds when:
        1. Task state changes (new tasks, assignments, completions, failures)
        2. Periodically during active work (every 60s) to provide status updates
        3. When there are completed tasks that haven't been reported yet
        """
        try:
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            tasks = tm.get_all_tasks()
        except Exception:
            tasks = []

        # No tasks at all - nothing to report
        if not tasks:
            return False

        now = time.time()
        
        # Snapshot of the task state: (id, status, assigned_to)
        snapshot = [(t.id, t.status.value, getattr(t, "assigned_to", None)) for t in tasks]
        last_snapshot = getattr(self, "_last_task_snapshot", None)
        last_time = getattr(self, "_last_task_snapshot_time", 0.0)
        last_periodic = getattr(self, "_last_periodic_update", 0.0)

        # Cooldown in seconds between Checky updates on task changes
        CHANGE_COOLDOWN = 15.0
        # Periodic update interval during active work
        PERIODIC_INTERVAL = 60.0

        # First time we see tasks: report once to establish a baseline
        if last_snapshot is None:
            self._last_task_snapshot = snapshot
            self._last_task_snapshot_time = now
            self._last_periodic_update = now
            return True

        # Check if task state changed
        state_changed = snapshot != last_snapshot
        
        if state_changed:
            self._last_task_snapshot = snapshot
            # Respond if cooldown has passed
            if now - last_time >= CHANGE_COOLDOWN:
                self._last_task_snapshot_time = now
                self._last_periodic_update = now
                return True

        # Check for periodic updates during active work
        in_progress_tasks = [t for t in tasks if t.status.value == "in_progress"]
        if in_progress_tasks and (now - last_periodic >= PERIODIC_INTERVAL):
            self._last_periodic_update = now
            return True

        return False
