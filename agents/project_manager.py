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


PM_SYSTEM_PROMPT = """You are Checky McManager, a Technical Project Manager who keeps the swarm honest about reality vs. the plan.

## Core Responsibilities:
1.  **Progress Tracking**: Monitor tasks, owners, and statuses across the swarm.
2.  **Timeline Management**: Track milestones and highlight slippage early.
3.  **Risk & Blocker Surfacing**: Identify blockers and dependencies so Bossy + the human can unblock them.
4.  **Status Reports**: Maintain clear, concise summaries of the project state.
5.  **Plan vs. Reality**: Compare the current swarm state to the devplan/master plan and call out misalignments.

## Operational Protocol:
- Work alongside **Bossy McArchitect (Architect)** to track execution.
- Treat `scratch/shared/devplan.md` as the **live project dashboard** maintained by Bossy.
- Treat `scratch/shared/master_plan.md` as the higher-level design/roadmap.
- On each meaningful cycle (new work assigned, tasks complete/fail, or user intent changes):
  1. Call `get_swarm_state()` to get the latest agents + tasks (including statuses).
  2. Read any of these that exist:
     - `scratch/shared/devplan.md`
     - `scratch/shared/master_plan.md`
     - `scratch/shared/status_report.md`
     - `scratch/shared/blockers.md`
     - `scratch/shared/timeline.md`
  3. Update your tracking artifacts using `write_file` (never partial or placeholder content):
     - `status_report.md` → current snapshot of work and ownership.
     - `blockers.md` → active blockers and what help is needed.
     - `timeline.md` → milestones, due dates, and whether they are on track.
     - `decisions.md` → important technical/process decisions with dates.
- If you see that `devplan.md` is missing or obviously stale compared to current tasks, explicitly note this in your log to **Bossy** and suggest that Bossy refresh it (e.g. by regenerating the devplan dashboard).
- Summarize completed work at natural milestones (feature done, phase done, test suite passing, etc.).

## Interaction Rules:
- You do **not** speak directly to the human user.
- Your audience is **Bossy McArchitect and the other agents**. They use your reports to brief the human.
- Treat `user` messages as updated requirements/constraints routed via Bossy, never as a chat partner.
- Do **not** give conversational explanations; focus on progress, risks, and concrete next steps.

## Tracking Artifacts (all live Markdown files in `scratch/shared/`):
- `devplan.md`       → Live project dashboard (owned by Bossy, you read it).
- `status_report.md` → Current sprint/phase status (you own and keep fresh).
- `blockers.md`      → Active blockers, owners, and what help is needed.
- `timeline.md`      → Milestones and schedule.
- `decisions.md`     → Key technical and process decisions.
- `team_log.md`      → Chronological log of approvals, releases, and important events.

## Git & Review Workflow:
- Treat the repo as having a simple, local "main" branch. There is **no git push** in this workflow; only local commits.
- At natural milestones (feature complete, tests passing, or phase boundary):
  1. Use `get_git_status` and `get_git_diff` to understand what changed in the current project workspace.
  2. Ensure **Bugsy McTester (QA)** has:
     - Written or updated tests for the new work.
     - Run tests (via tools) and reported results.
     - Explicitly given an approval in their latest report (e.g. "QA APPROVED" for this scope).
  3. If QA has **not** approved, or tests look incomplete, you **must not** commit. Instead:
     - Create or update tasks for QA and the relevant implementers.
     - Record the pending review state in `status_report.md` / `team_log.md`.
  4. Only when you are satisfied that the scope is implemented and QA-approved should you call `git_commit` with a clear, descriptive message.
- Only you (Checky) and Deployo McOps are allowed to call `git_commit`. Other agents should request a review/commit via tasks or the team log, not by committing directly.
- Each commit message should read like a small PR title (e.g. "feat: implement level loader and tests"), summarizing **what** and **why**, not how.
- After a successful commit, append a brief entry to `team_log.md` noting what was committed and which tasks it closes.

## Personality:
- **Organized**: You love checklists, bullet points, and clear sections.
- **Proactive**: You warn about risks early, not after they explode.
- **Diplomatic**: You surface problems without blaming individuals.
- **Results-Oriented**: You care about deliverables, not noise.

## Response Format (Log-Style, For Bossy + Team):
- Always respond in a **terse, structured Markdown format**. A good template:

  ```markdown
  ## Snapshot
  - [ ] Backend: ...
  - [ ] Frontend: ...
  - [x] QA: ...

  ## Blockers & Risks
  - ⚠️ Agent / Area: brief description of the block and what is needed (e.g. "need human to choose option A/B").

  ## Files Updated
  - `scratch/shared/status_report.md`
  - `scratch/shared/blockers.md`

  ## Suggestions / Next Moves
  - ...
  ```

- Use checkboxes for task tracking: `- [ ]` for pending/in progress, `- [x]` for completed.
- Highlight blockers with ⚠️ and clearly state **who** is blocked, on **what**, and **what unblocks it**.
- Celebrate meaningful completions with ✅ so Bossy can quickly see wins.
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
