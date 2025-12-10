"""
Swarm Orchestrator - State machine for efficient swarm execution.

This module provides:
1. Orchestration state tracking (current phase, task, assignments)
2. Pre-computed dispatch queue with agent assignments
3. Prevention of repeated tool calls and stalling
4. Real-time status for dashboard display
"""

import re
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskState(Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"  # Assigned to agent, waiting for work
    IN_PROGRESS = "in_progress"  # Agent actively working
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class PhaseState(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Agent emojis for dashboard
AGENT_EMOJI = {
    "backend_dev": "⚙️",
    "frontend_dev": "🎨",
    "qa_engineer": "🐛",
    "devops": "🚀",
    "tech_writer": "📝",
    "database_specialist": "🗄️",
    "api_designer": "🔌",
}

AGENT_NAMES = {
    "backend_dev": "Codey McBackend",
    "frontend_dev": "Pixel McFrontend",
    "qa_engineer": "Bugsy McTester",
    "devops": "Deployo McOps",
    "tech_writer": "Docy McWriter",
}


@dataclass
class SwarmTask:
    """Individual task with pre-computed dispatch info."""
    id: str  # e.g., "1.1"
    phase: int
    number: int
    title: str
    state: TaskState = TaskState.PENDING
    agent_role: str = "backend_dev"
    agent_name: str = ""
    priority: str = "medium"
    depends: List[str] = field(default_factory=list)
    goal: str = ""
    files: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    done_when: str = ""
    dispatch_command: str = ""  # Pre-formatted assign_task() call
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def emoji(self) -> str:
        return AGENT_EMOJI.get(self.agent_role, "🤖")
    
    def to_dispatch_command(self) -> str:
        """Generate ready-to-use dispatch command."""
        if self.dispatch_command:
            return self.dispatch_command
        
        files_str = "\n".join(f"- {f}" for f in self.files) if self.files else "- (see task details)"
        reqs_str = "\n".join(f"- {r}" for r in self.requirements) if self.requirements else "- (see task details)"
        
        return f'''assign_task("{self.agent_name}", """Task {self.id}: {self.title}

GOAL: {self.goal}

FILES:
{files_str}

REQUIREMENTS:
{reqs_str}

DONE_WHEN: {self.done_when}
""")'''


@dataclass
class SwarmPhase:
    """Phase containing multiple tasks."""
    number: int
    title: str
    state: PhaseState = PhaseState.NOT_STARTED
    tasks: Dict[str, SwarmTask] = field(default_factory=dict)
    
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)
    
    @property
    def completed_tasks(self) -> int:
        return sum(1 for t in self.tasks.values() if t.state == TaskState.COMPLETED)
    
    @property
    def pending_tasks(self) -> List[SwarmTask]:
        return [t for t in self.tasks.values() if t.state == TaskState.PENDING]
    
    @property
    def in_progress_tasks(self) -> List[SwarmTask]:
        return [t for t in self.tasks.values() if t.state in (TaskState.DISPATCHED, TaskState.IN_PROGRESS)]
    
    @property
    def is_complete(self) -> bool:
        return all(t.state == TaskState.COMPLETED for t in self.tasks.values())
    
    @property
    def progress_pct(self) -> int:
        if not self.tasks:
            return 0
        return int(100 * self.completed_tasks / self.total_tasks)


class SwarmOrchestrator:
    """
    Central orchestration state machine.
    
    Key Features:
    - Parses devplan/phases ONCE at startup
    - Pre-computes all task assignments and dispatch commands
    - Tracks state so Architect doesn't need to re-read files
    - Provides next_dispatch() for simple orchestration
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.shared_dir = self.project_path / "scratch" / "shared"
        
        # State
        self.phases: Dict[int, SwarmPhase] = {}
        self.current_phase: int = 1
        self.project_name: str = ""
        self.tech_stack: str = ""
        
        # Callbacks
        self._on_task_complete: Optional[Callable[[SwarmTask], None]] = None
        self._on_phase_complete: Optional[Callable[[SwarmPhase], None]] = None
        
        # Tracking
        self._initialized = False
        self._last_dispatch_time: Optional[datetime] = None
    
    async def initialize(self) -> bool:
        """Load and parse devplan/phases, pre-compute all dispatch commands."""
        try:
            devplan_path = self.shared_dir / "devplan.md"
            
            if not devplan_path.exists():
                logger.warning(f"No devplan.md found at {devplan_path}")
                return False
            
            # Parse devplan for project overview
            devplan_content = devplan_path.read_text(encoding="utf-8")
            self._parse_devplan(devplan_content)
            
            # Load design for tech stack detection
            design_path = self.shared_dir / "project_design.md"
            if design_path.exists():
                self._detect_tech_stack(design_path.read_text(encoding="utf-8"))
            
            # Parse all phase files
            phases_dir = self.shared_dir / "phases"
            if phases_dir.exists():
                for phase_file in sorted(phases_dir.glob("phase*.md")):
                    phase_content = phase_file.read_text(encoding="utf-8")
                    phase_num = self._extract_phase_number(phase_file.name)
                    if phase_num:
                        self._parse_phase(phase_num, phase_content)
            
            # Pre-compute dispatch commands for all tasks
            self._compute_dispatch_commands()
            
            # Find current phase (first incomplete)
            for num in sorted(self.phases.keys()):
                if not self.phases[num].is_complete:
                    self.current_phase = num
                    break
            
            # Load persisted task states (from previous sessions)
            self._load_task_state()
            
            self._initialized = True
            logger.info(f"Orchestrator initialized: {len(self.phases)} phases, "
                       f"{sum(p.total_tasks for p in self.phases.values())} tasks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            return False
    
    def _parse_devplan(self, content: str):
        """Parse devplan.md for project overview and phase list."""
        # Extract project name from title
        title_match = re.search(r'^#\s+(.+?)(?:\n|$)', content, re.MULTILINE)
        if title_match:
            self.project_name = title_match.group(1).strip()
        
        # Parse phase overview table
        # Format: | 1 | Phase Title | Status | Steps | [file](link) |
        phase_pattern = re.compile(
            r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(\d+)\s*\|',
            re.MULTILINE
        )
        
        for match in phase_pattern.finditer(content):
            phase_num = int(match.group(1))
            phase_title = match.group(2).strip()
            status_text = match.group(3).strip().lower()
            
            state = PhaseState.NOT_STARTED
            if "progress" in status_text or "working" in status_text:
                state = PhaseState.IN_PROGRESS
            elif "complete" in status_text or "done" in status_text:
                state = PhaseState.COMPLETED
            
            self.phases[phase_num] = SwarmPhase(
                number=phase_num,
                title=phase_title,
                state=state
            )
    
    def _detect_tech_stack(self, design_content: str):
        """Detect tech stack from project design."""
        content_lower = design_content.lower()
        
        if "godot" in content_lower or "gdscript" in content_lower:
            self.tech_stack = "godot"
        elif "unity" in content_lower or "c#" in content_lower:
            self.tech_stack = "unity"
        elif "react" in content_lower or "typescript" in content_lower:
            self.tech_stack = "react-ts"
        elif "fastapi" in content_lower or "python" in content_lower:
            self.tech_stack = "python"
        else:
            self.tech_stack = "generic"
    
    def _extract_phase_number(self, filename: str) -> Optional[int]:
        """Extract phase number from filename like 'phase1.md'."""
        match = re.search(r'phase(\d+)', filename.lower())
        return int(match.group(1)) if match else None
    
    def _parse_phase(self, phase_num: int, content: str):
        """Parse a phase file for tasks."""
        if phase_num not in self.phases:
            self.phases[phase_num] = SwarmPhase(number=phase_num, title=f"Phase {phase_num}")
        
        phase = self.phases[phase_num]
        
        # Multiple patterns to match different task formats
        patterns = [
            # Format: ### Task 1.1: Title
            r'###?\s*Task\s+(\d+)\.(\d+)[:\s]+(.+?)(?=\n###|\n##|\Z)',
            # Format: ## 1.1: Title
            r'##\s*(\d+)\.(\d+)[:\s]+(.+?)(?=\n##|\Z)',
            # Format: ### Step 1.1: Title  
            r'###?\s*Step\s+(\d+)\.(\d+)[:\s]+(.+?)(?=\n###|\n##|\Z)',
            # Format: 1.1: Title (at line start)
            r'^(\d+)\.(\d+)[:\s]+(.+?)(?=\n\d+\.\d+:|\Z)',
            # Format: - [ ] 1.1: Title (checklist - new Devussy format)
            r'^\s*-\s*\[[ xX]\]\s*(\d+)\.(\d+):\s*(.+?)(?=^\s*-\s*\[[ xX]\]\s*\d+\.\d+:|\Z)',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, content, re.DOTALL | re.MULTILINE))
            if matches:
                for match in matches:
                    task_phase = int(match.group(1))
                    task_num = int(match.group(2))
                    task_content = match.group(3).strip()
                    
                    # Only add if matches current phase
                    if task_phase == phase_num:
                        task = self._parse_task_content(phase_num, task_num, task_content)
                        phase.tasks[task.id] = task
                break
        
        logger.debug(f"Phase {phase_num}: parsed {len(phase.tasks)} tasks")
    
    def _parse_task_content(self, phase: int, num: int, content: str) -> SwarmTask:
        """Parse task content to extract metadata."""
        lines = content.split("\n")
        title = lines[0].strip() if lines else f"Task {phase}.{num}"
        
        # Remove any trailing header markers from title
        title = re.sub(r'\s*#+\s*$', '', title)
        
        task = SwarmTask(
            id=f"{phase}.{num}",
            phase=phase,
            number=num,
            title=title
        )
        
        # Extract @agent: tag
        agent_match = re.search(r'@agent:\s*(\w+)', content, re.IGNORECASE)
        if agent_match:
            task.agent_role = agent_match.group(1).lower()
        else:
            task.agent_role = self._infer_agent(content)
        
        task.agent_name = AGENT_NAMES.get(task.agent_role, task.agent_role)
        
        # Extract @priority:
        priority_match = re.search(r'@priority:\s*(high|medium|low)', content, re.IGNORECASE)
        task.priority = priority_match.group(1).lower() if priority_match else "medium"
        
        # Extract @depends:
        depends_match = re.search(r'@depends:\s*([^\n]+)', content, re.IGNORECASE)
        if depends_match:
            deps_text = depends_match.group(1).strip()
            if deps_text.lower() != "none":
                task.depends = [d.strip() for d in deps_text.split(",") if d.strip()]
        
        # Extract @done_when:
        done_match = re.search(r'@done_when:\s*([^\n]+)', content, re.IGNORECASE)
        task.done_when = done_match.group(1).strip() if done_match else "Task completed as specified"
        
        # Extract goal from **Goal:** or first paragraph
        goal_match = re.search(r'\*\*Goal:\*\*\s*(.+?)(?:\n\n|\n\*\*|$)', content, re.DOTALL)
        if goal_match:
            task.goal = goal_match.group(1).strip()
        else:
            # Use title as goal
            task.goal = title
        
        # Extract files mentioned
        task.files = self._extract_files(content)
        
        # Extract requirements
        task.requirements = self._extract_requirements(content)
        
        return task
    
    def _infer_agent(self, content: str) -> str:
        """Infer agent role from task content."""
        content_lower = content.lower()
        
        # Game-specific: everything goes to backend for GDScript/Unity
        if self.tech_stack in ("godot", "unity"):
            if any(kw in content_lower for kw in ["test", "pytest", "gut", "gdunit"]):
                return "qa_engineer"
            if any(kw in content_lower for kw in ["doc", "readme", "guide"]):
                return "tech_writer"
            if any(kw in content_lower for kw in ["docker", "deploy", "ci/cd", "export"]):
                return "devops"
            return "backend_dev"  # All game code
        
        # Web projects
        if any(kw in content_lower for kw in ["component", "react", "vue", "css", "ui", "frontend", "html"]):
            return "frontend_dev"
        if any(kw in content_lower for kw in ["api", "endpoint", "server", "database", "model", "backend", "python"]):
            return "backend_dev"
        if any(kw in content_lower for kw in ["test", "pytest", "jest", "coverage"]):
            return "qa_engineer"
        if any(kw in content_lower for kw in ["docker", "deploy", "ci/cd", "pipeline"]):
            return "devops"
        if any(kw in content_lower for kw in ["documentation", "readme", "docs"]):
            return "tech_writer"
        
        return "backend_dev"  # Default
    
    def _extract_files(self, content: str) -> List[str]:
        """Extract file paths from task content."""
        files = []
        
        # Look for @files: section or file paths in content
        files_section = re.search(r'@files:\s*(.*?)(?=@|\*\*|$)', content, re.DOTALL | re.IGNORECASE)
        if files_section:
            file_lines = files_section.group(1).strip().split("\n")
            for line in file_lines:
                line = line.strip().lstrip("-").strip()
                if line and ("/" in line or "." in line):
                    files.append(line)
        
        # Also look for paths like shared/src/file.ts
        path_pattern = re.compile(r'shared/[\w/.-]+\.\w+')
        files.extend(path_pattern.findall(content))
        
        return list(set(files))  # Dedupe
    
    def _extract_requirements(self, content: str) -> List[str]:
        """Extract requirements from task content."""
        reqs = []
        
        # Look for **Requirements:** or bullet points
        req_section = re.search(r'\*\*Requirements?:\*\*\s*(.*?)(?=\*\*|$)', content, re.DOTALL | re.IGNORECASE)
        if req_section:
            req_lines = req_section.group(1).strip().split("\n")
            for line in req_lines:
                line = line.strip().lstrip("-").lstrip("*").strip()
                if line and len(line) > 5:
                    reqs.append(line)
        
        # If no requirements section, use implementation steps
        if not reqs:
            steps_section = re.search(r'\*\*Implementation Steps?:\*\*\s*(.*?)(?=\*\*|$)', content, re.DOTALL)
            if steps_section:
                step_lines = steps_section.group(1).strip().split("\n")
                for line in step_lines:
                    line = line.strip().lstrip("-").lstrip("*").lstrip("0123456789.").strip()
                    if line and len(line) > 5:
                        reqs.append(line)
        
        return reqs[:5]  # Limit to 5
    
    def _compute_dispatch_commands(self):
        """Pre-compute dispatch commands for all tasks."""
        for phase in self.phases.values():
            for task in phase.tasks.values():
                task.dispatch_command = task.to_dispatch_command()
    
    # =========================================================================
    # TASK STATE PERSISTENCE
    # =========================================================================
    
    def _get_state_file(self) -> Path:
        """Get path to task state file."""
        return self.shared_dir / "task_state.json"
    
    def _save_task_state(self):
        """Persist task states to JSON file for session recovery."""
        try:
            state_data = {
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "tasks": {}
            }
            
            for phase in self.phases.values():
                for task in phase.tasks.values():
                    state_data["tasks"][task.id] = {
                        "state": task.state.value,
                        "agent_name": task.agent_name,
                        "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    }
            
            state_file = self._get_state_file()
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
            logger.debug(f"Saved task state: {len(state_data['tasks'])} tasks")
            
        except Exception as e:
            logger.warning(f"Failed to save task state: {e}")
    
    def _load_task_state(self):
        """Load task states from JSON file (from previous sessions)."""
        state_file = self._get_state_file()
        if not state_file.exists():
            logger.debug("No task state file found - starting fresh")
            return
        
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            tasks_loaded = 0
            
            for task_id, task_state in state_data.get("tasks", {}).items():
                task = self._find_task(task_id)
                if task:
                    saved_state = task_state.get("state", "pending")
                    try:
                        task.state = TaskState(saved_state)
                    except ValueError:
                        task.state = TaskState.PENDING
                    
                    task.agent_name = task_state.get("agent_name", "")
                    
                    if task_state.get("assigned_at"):
                        try:
                            task.assigned_at = datetime.fromisoformat(task_state["assigned_at"])
                        except:
                            pass
                    
                    if task_state.get("completed_at"):
                        try:
                            task.completed_at = datetime.fromisoformat(task_state["completed_at"])
                        except:
                            pass
                    
                    tasks_loaded += 1
            
            # Update phase states based on loaded task states
            for phase in self.phases.values():
                if phase.is_complete:
                    phase.state = PhaseState.COMPLETED
                elif any(t.state in (TaskState.DISPATCHED, TaskState.IN_PROGRESS, TaskState.COMPLETED) 
                        for t in phase.tasks.values()):
                    phase.state = PhaseState.IN_PROGRESS
            
            # Update current phase
            for num in sorted(self.phases.keys()):
                if not self.phases[num].is_complete:
                    self.current_phase = num
                    break
            
            logger.info(f"Loaded task state: {tasks_loaded} tasks restored")
            
        except Exception as e:
            logger.warning(f"Failed to load task state: {e}")
    
    def _update_task_queue_file(self):
        """Update task_queue.md with current task states."""
        try:
            task_queue_path = self.shared_dir / "task_queue.md"
            if not task_queue_path.exists():
                return
            
            content = task_queue_path.read_text(encoding="utf-8")
            
            # Update status for each task
            for phase in self.phases.values():
                for task in phase.tasks.values():
                    # Replace status in the markdown
                    # Pattern: **Status:** `pending` -> **Status:** `completed`
                    old_pattern = f"**Status:** `pending`"
                    
                    if task.state == TaskState.COMPLETED:
                        new_status = "**Status:** `✅ completed`"
                    elif task.state == TaskState.DISPATCHED:
                        new_status = "**Status:** `📤 dispatched`"
                    elif task.state == TaskState.IN_PROGRESS:
                        new_status = "**Status:** `🔄 in_progress`"
                    else:
                        continue  # Don't update pending tasks
                    
                    # Find the task section and update its status
                    task_header = f"### ⚙️ Task {task.id}:"
                    if task_header not in content:
                        task_header = f"### 🎨 Task {task.id}:"
                    if task_header not in content:
                        task_header = f"### 🐛 Task {task.id}:"
                    if task_header not in content:
                        task_header = f"### 🚀 Task {task.id}:"
                    if task_header not in content:
                        task_header = f"### 📝 Task {task.id}:"
                    
                    if task_header in content:
                        # Find the section and update status
                        import re
                        pattern = rf"({re.escape(task_header)}.*?)\*\*Status:\*\* `[^`]+`"
                        replacement = rf"\1{new_status}"
                        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            task_queue_path.write_text(content, encoding="utf-8")
            logger.debug("Updated task_queue.md with current states")
            
        except Exception as e:
            logger.warning(f"Failed to update task_queue.md: {e}")
    
    # =========================================================================
    # ORCHESTRATION API
    # =========================================================================
    
    def get_next_dispatchable_tasks(self, max_count: int = 3) -> List[SwarmTask]:
        """
        Get next tasks that can be dispatched.
        
        Considers:
        - Dependencies (blocked tasks excluded)
        - Current phase priority
        - Max concurrent tasks
        """
        if not self._initialized:
            return []
        
        dispatchable = []
        
        # Focus on current phase first
        for phase_num in sorted(self.phases.keys()):
            phase = self.phases[phase_num]
            
            if phase.state == PhaseState.COMPLETED:
                continue
            
            for task in phase.tasks.values():
                if task.state != TaskState.PENDING:
                    continue
                
                # Check dependencies
                deps_met = True
                for dep_id in task.depends:
                    dep_task = self._find_task(dep_id)
                    if dep_task and dep_task.state != TaskState.COMPLETED:
                        deps_met = False
                        break
                
                if deps_met:
                    dispatchable.append(task)
                    
                    if len(dispatchable) >= max_count:
                        return dispatchable
        
        return dispatchable
    
    def _find_task(self, task_id: str) -> Optional[SwarmTask]:
        """Find task by ID."""
        for phase in self.phases.values():
            if task_id in phase.tasks:
                return phase.tasks[task_id]
        return None
    
    def mark_task_dispatched(self, task_id: str, agent_name: str):
        """Mark task as dispatched to agent."""
        task = self._find_task(task_id)
        if task:
            task.state = TaskState.DISPATCHED
            task.assigned_at = datetime.now()
            task.agent_name = agent_name
            
            # Update phase state
            phase = self.phases.get(task.phase)
            if phase and phase.state == PhaseState.NOT_STARTED:
                phase.state = PhaseState.IN_PROGRESS
            
            # Persist state
            self._save_task_state()
            
            # Update task_queue.md
            self._update_task_queue_file()
    
    def mark_task_in_progress(self, task_id: str):
        """Mark task as actively being worked on."""
        task = self._find_task(task_id)
        if task:
            task.state = TaskState.IN_PROGRESS
    
    def mark_task_completed(self, task_id: str):
        """Mark task as completed."""
        task = self._find_task(task_id)
        if task:
            task.state = TaskState.COMPLETED
            task.completed_at = datetime.now()
            
            # Persist state immediately
            self._save_task_state()
            
            # Update task_queue.md
            self._update_task_queue_file()
            
            # Check if phase is complete
            phase = self.phases.get(task.phase)
            if phase and phase.is_complete:
                phase.state = PhaseState.COMPLETED
                logger.info(f"Phase {task.phase} completed!")
                
                if self._on_phase_complete:
                    self._on_phase_complete(phase)
            
            if self._on_task_complete:
                self._on_task_complete(task)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get orchestration state for Architect context."""
        completed_phases = [p for p in self.phases.values() if p.is_complete]
        in_progress = [p for p in self.phases.values() if p.state == PhaseState.IN_PROGRESS]
        
        total_tasks = sum(p.total_tasks for p in self.phases.values())
        completed_tasks = sum(p.completed_tasks for p in self.phases.values())
        
        next_tasks = self.get_next_dispatchable_tasks(3)
        
        return {
            "project_name": self.project_name,
            "tech_stack": self.tech_stack,
            "total_phases": len(self.phases),
            "completed_phases": len(completed_phases),
            "current_phase": self.current_phase,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress_pct": int(100 * completed_tasks / total_tasks) if total_tasks else 0,
            "next_dispatchable": [
                {
                    "id": t.id,
                    "title": t.title,
                    "agent_role": t.agent_role,
                    "agent_name": t.agent_name,
                    "dispatch_command": t.dispatch_command,
                }
                for t in next_tasks
            ],
        }
    
    def get_dispatch_instructions(self) -> str:
        """
        Get ready-to-use dispatch instructions for the Architect.
        
        This replaces the need for Architect to read files and figure out
        what to do - it's all pre-computed.
        """
        summary = self.get_state_summary()
        next_tasks = summary["next_dispatchable"]
        
        if not next_tasks:
            if summary["completed_tasks"] == summary["total_tasks"]:
                return "ALL_DONE: All tasks completed! Summarize deliverables for the human."
            return "WAITING: No dispatchable tasks - waiting for dependencies."
        
        lines = [
            f"# Phase {self.current_phase} - {summary['progress_pct']}% Complete",
            "",
            "## DISPATCH THESE TASKS:",
            "",
        ]
        
        for task_info in next_tasks:
            lines.extend([
                f"### {task_info['id']}: {task_info['title']}",
                f"Agent: {task_info['agent_name']} ({task_info['agent_role']})",
                "",
                "```python",
                task_info['dispatch_command'],
                "```",
                "",
            ])
        
        lines.extend([
            "---",
            "1. `spawn_worker(role)` for each needed agent",
            "2. Copy-paste the dispatch commands above",
            "3. Say 'Dispatched N tasks.' then STOP",
        ])
        
        return "\n".join(lines)
    
    # =========================================================================
    # DASHBOARD DATA
    # =========================================================================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for real-time dashboard display."""
        phases_data = []
        
        for phase_num in sorted(self.phases.keys()):
            phase = self.phases[phase_num]
            tasks_data = []
            
            for task_id in sorted(phase.tasks.keys()):
                task = phase.tasks[task_id]
                tasks_data.append({
                    "id": task.id,
                    "title": task.title,
                    "state": task.state.value,
                    "emoji": task.emoji,
                    "agent_role": task.agent_role,
                    "agent_name": task.agent_name,
                    "priority": task.priority,
                })
            
            phases_data.append({
                "number": phase.number,
                "title": phase.title,
                "state": phase.state.value,
                "total": phase.total_tasks,
                "completed": phase.completed_tasks,
                "progress_pct": phase.progress_pct,
                "tasks": tasks_data,
            })
        
        return {
            "project_name": self.project_name,
            "phases": phases_data,
        }


# Singleton instance
_orchestrator: Optional[SwarmOrchestrator] = None


def get_orchestrator() -> Optional[SwarmOrchestrator]:
    """Get the global orchestrator instance."""
    return _orchestrator


def set_orchestrator(orch: SwarmOrchestrator):
    """Set the global orchestrator instance."""
    global _orchestrator
    _orchestrator = orch


async def init_orchestrator(project_path: Path) -> SwarmOrchestrator:
    """Initialize and return the global orchestrator."""
    global _orchestrator
    _orchestrator = SwarmOrchestrator(project_path)
    await _orchestrator.initialize()
    return _orchestrator
