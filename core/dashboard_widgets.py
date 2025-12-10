"""
Dashboard Widgets - Real-time swarm status display.

Provides:
- CollapsiblePhase: Phase with expandable task list
- TaskStatusRow: Individual task with emoji and progress
- SwarmDashboard: Complete dashboard with all phases
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Label, Rule, Collapsible, ProgressBar
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


# Agent emojis
AGENT_EMOJI = {
    "backend_dev": "⚙️",
    "frontend_dev": "🎨", 
    "qa_engineer": "🐛",
    "devops": "🚀",
    "tech_writer": "📝",
    "database_specialist": "🗄️",
    "api_designer": "🔌",
}

# Status emojis
STATUS_EMOJI = {
    "pending": "⏳",
    "dispatched": "📤",
    "in_progress": "🔄",
    "completed": "✅",
    "blocked": "❌",
    "skipped": "⏭️",
}

STATUS_STYLE = {
    "pending": "dim",
    "dispatched": "yellow",
    "in_progress": "cyan bold",
    "completed": "green",
    "blocked": "red",
    "skipped": "dim italic",
}


class TaskStatusRow(Static):
    """Single task row with emoji, title, and status."""
    
    DEFAULT_CSS = """
    TaskStatusRow {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    TaskStatusRow.pending { color: $text-muted; }
    TaskStatusRow.dispatched { color: yellow; }
    TaskStatusRow.in_progress { color: cyan; }
    TaskStatusRow.completed { color: green; }
    TaskStatusRow.blocked { color: red; }
    """
    
    def __init__(self, task_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.task_data = task_data
        self.add_class(task_data.get("state", "pending"))
    
    def render(self) -> Text:
        data = self.task_data
        state = data.get("state", "pending")
        
        text = Text()
        
        # Status emoji
        status_emoji = STATUS_EMOJI.get(state, "❓")
        text.append(f"{status_emoji} ", style=STATUS_STYLE.get(state, ""))
        
        # Agent emoji
        agent_emoji = data.get("emoji", "🤖")
        text.append(f"{agent_emoji} ", style="dim")
        
        # Task ID
        text.append(f"{data.get('id', '?')}: ", style="bold")
        
        # Task title (truncate if long)
        title = data.get("title", "Unknown")[:40]
        if len(data.get("title", "")) > 40:
            title += "..."
        text.append(title, style=STATUS_STYLE.get(state, ""))
        
        # Agent name if in progress
        if state in ("dispatched", "in_progress"):
            agent = data.get("agent_name", "")
            if agent:
                text.append(f" → {agent}", style="italic yellow")
        
        return text
    
    def update_state(self, new_state: str):
        """Update task state and refresh display."""
        old_state = self.task_data.get("state", "pending")
        self.remove_class(old_state)
        
        self.task_data["state"] = new_state
        self.add_class(new_state)
        self.refresh()


class PhaseHeader(Static):
    """Phase header with progress indicator."""
    
    DEFAULT_CSS = """
    PhaseHeader {
        width: 100%;
        height: auto;
        padding: 0 1;
        background: $surface;
    }
    """
    
    def __init__(self, phase_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.phase_data = phase_data
    
    def render(self) -> Text:
        data = self.phase_data
        state = data.get("state", "not_started")
        
        text = Text()
        
        # Phase state emoji
        if state == "completed":
            text.append("✅ ", style="green")
        elif state == "in_progress":
            text.append("🔄 ", style="cyan")
        else:
            text.append("⏳ ", style="dim")
        
        # Phase number and title
        text.append(f"Phase {data.get('number', '?')}: ", style="bold")
        text.append(data.get("title", "Unknown")[:30])
        
        # Progress
        total = data.get("total", 0)
        completed = data.get("completed", 0)
        pct = data.get("progress_pct", 0)
        
        text.append(f" [{completed}/{total}] ", style="dim")
        
        # Progress bar (text-based)
        bar_width = 10
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        if pct == 100:
            text.append(f"[{bar}]", style="green")
        elif pct > 0:
            text.append(f"[{bar}]", style="yellow")
        else:
            text.append(f"[{bar}]", style="dim")
        
        text.append(f" {pct}%", style="bold" if pct > 0 else "dim")
        
        return text


class CollapsiblePhase(Collapsible):
    """Collapsible phase section with tasks."""
    
    DEFAULT_CSS = """
    CollapsiblePhase {
        width: 100%;
        margin: 0 0 1 0;
        border: solid $primary-darken-2;
    }
    CollapsiblePhase > Contents {
        padding: 0;
    }
    """
    
    def __init__(self, phase_data: Dict[str, Any], **kwargs):
        self.phase_data = phase_data
        self.task_widgets: Dict[str, TaskStatusRow] = {}
        
        # Create title from phase header
        title = self._make_title()
        
        # Start collapsed if phase is complete or not started
        state = phase_data.get("state", "not_started")
        collapsed = state in ("completed", "not_started")
        
        super().__init__(title=title, collapsed=collapsed, **kwargs)
    
    def _make_title(self) -> str:
        data = self.phase_data
        state = data.get("state", "not_started")
        
        # State emoji
        if state == "completed":
            emoji = "✅"
        elif state == "in_progress":
            emoji = "🔄"
        else:
            emoji = "⏳"
        
        # Progress
        total = data.get("total", 0)
        completed = data.get("completed", 0)
        pct = data.get("progress_pct", 0)
        
        return f"{emoji} Phase {data.get('number', '?')}: {data.get('title', 'Unknown')[:25]} [{completed}/{total}] {pct}%"
    
    def compose(self) -> ComposeResult:
        with Vertical():
            for task_data in self.phase_data.get("tasks", []):
                task_widget = TaskStatusRow(task_data, id=f"task-{task_data.get('id', 'unknown')}")
                self.task_widgets[task_data.get("id", "")] = task_widget
                yield task_widget
    
    def update_task(self, task_id: str, new_state: str):
        """Update a specific task's state."""
        if task_id in self.task_widgets:
            self.task_widgets[task_id].update_state(new_state)
        
        # Update phase summary
        self._update_summary()
    
    def _update_summary(self):
        """Recalculate phase progress and update title."""
        tasks = self.phase_data.get("tasks", [])
        completed = sum(1 for t in tasks if t.get("state") == "completed")
        total = len(tasks)
        pct = int(100 * completed / total) if total else 0
        
        self.phase_data["completed"] = completed
        self.phase_data["progress_pct"] = pct
        
        if completed == total and total > 0:
            self.phase_data["state"] = "completed"
        elif completed > 0:
            self.phase_data["state"] = "in_progress"
        
        self.title = self._make_title()


class SwarmDashboard(ScrollableContainer):
    """Complete dashboard showing all phases with real-time updates."""
    
    DEFAULT_CSS = """
    SwarmDashboard {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #dashboard-header {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    #progress-summary {
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface;
        margin-bottom: 1;
    }
    """
    
    project_name = reactive("Project")
    total_progress = reactive(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.phase_widgets: Dict[int, CollapsiblePhase] = {}
        self._data: Dict[str, Any] = {}
    
    def compose(self) -> ComposeResult:
        yield Static(id="dashboard-header")
        yield Static(id="progress-summary")
        yield Vertical(id="phases-container")
    
    def on_mount(self):
        """Initialize with placeholder content."""
        self._update_header()
        self._update_summary()
    
    def load_data(self, data: Dict[str, Any]):
        """Load dashboard data from orchestrator."""
        self._data = data
        self.project_name = data.get("project_name", "Project")
        
        # Calculate total progress
        phases = data.get("phases", [])
        total_tasks = sum(p.get("total", 0) for p in phases)
        completed_tasks = sum(p.get("completed", 0) for p in phases)
        self.total_progress = int(100 * completed_tasks / total_tasks) if total_tasks else 0
        
        self._update_header()
        self._update_summary()
        self._rebuild_phases(phases)
    
    def _update_header(self):
        """Update header with project name."""
        header = self.query_one("#dashboard-header", Static)
        text = Text()
        text.append("📊 ", style="bold")
        text.append(f"{self.project_name}", style="bold cyan")
        text.append(" - Swarm Dashboard", style="dim")
        header.update(Panel(text, border_style="cyan"))
    
    def _update_summary(self):
        """Update progress summary."""
        summary = self.query_one("#progress-summary", Static)
        
        phases = self._data.get("phases", [])
        total_phases = len(phases)
        completed_phases = sum(1 for p in phases if p.get("state") == "completed")
        in_progress = sum(1 for p in phases if p.get("state") == "in_progress")
        total_tasks = sum(p.get("total", 0) for p in phases)
        completed_tasks = sum(p.get("completed", 0) for p in phases)
        
        text = Text()
        text.append("Progress: ", style="bold")
        
        # Visual progress bar
        bar_width = 20
        filled = int(bar_width * self.total_progress / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        if self.total_progress == 100:
            text.append(f"[{bar}]", style="green bold")
        elif self.total_progress > 50:
            text.append(f"[{bar}]", style="yellow")
        else:
            text.append(f"[{bar}]", style="cyan")
        
        text.append(f" {self.total_progress}%\n", style="bold")
        
        # Stats
        text.append(f"Phases: {completed_phases}/{total_phases} complete", style="dim")
        if in_progress:
            text.append(f" ({in_progress} in progress)", style="yellow")
        text.append(f"\nTasks: {completed_tasks}/{total_tasks}", style="dim")
        
        summary.update(text)
    
    def _rebuild_phases(self, phases: List[Dict[str, Any]]):
        """Rebuild phase widgets from data."""
        container = self.query_one("#phases-container", Vertical)
        container.remove_children()
        self.phase_widgets.clear()
        
        for phase_data in phases:
            phase_num = phase_data.get("number", 0)
            phase_widget = CollapsiblePhase(
                phase_data, 
                id=f"phase-{phase_num}"
            )
            self.phase_widgets[phase_num] = phase_widget
            container.mount(phase_widget)
    
    def update_task_state(self, task_id: str, new_state: str):
        """Update a specific task's state in real-time."""
        # Parse phase number from task_id (e.g., "1.3" -> 1)
        try:
            phase_num = int(task_id.split(".")[0])
        except (ValueError, IndexError):
            return
        
        if phase_num in self.phase_widgets:
            self.phase_widgets[phase_num].update_task(task_id, new_state)
            
            # Update summary
            self._recalculate_progress()
    
    def _recalculate_progress(self):
        """Recalculate total progress after task updates."""
        total_tasks = 0
        completed_tasks = 0
        
        for phase_widget in self.phase_widgets.values():
            phase_data = phase_widget.phase_data
            total_tasks += phase_data.get("total", 0)
            completed_tasks += phase_data.get("completed", 0)
        
        self.total_progress = int(100 * completed_tasks / total_tasks) if total_tasks else 0
        self._update_summary()


class SimpleDashboardPanel(Static):
    """
    Simpler dashboard panel for embedding in existing TUI.
    
    Shows collapsible phases with task status and agent emojis.
    Falls back to reading markdown files if orchestrator not available.
    """
    
    DEFAULT_CSS = """
    SimpleDashboardPanel {
        width: 100%;
        height: 100%;
        overflow: auto;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._orchestrator = None
    
    def set_orchestrator(self, orch):
        """Set orchestrator for real-time data."""
        self._orchestrator = orch
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh dashboard display."""
        if self._orchestrator and self._orchestrator._initialized:
            content = self._render_from_orchestrator()
        else:
            content = self._render_from_files()
        
        self.update(content)
    
    def _render_from_orchestrator(self) -> Text:
        """Render dashboard from orchestrator state."""
        data = self._orchestrator.get_dashboard_data()
        
        text = Text()
        text.append(f"📊 {data.get('project_name', 'Project')}\n", style="bold cyan")
        text.append("─" * 40 + "\n", style="dim")
        
        # Progress summary
        phases = data.get("phases", [])
        total_tasks = sum(p.get("total", 0) for p in phases)
        completed_tasks = sum(p.get("completed", 0) for p in phases)
        pct = int(100 * completed_tasks / total_tasks) if total_tasks else 0
        
        # Progress bar
        bar_width = 20
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        text.append(f"[{bar}] {pct}%\n", style="green" if pct == 100 else "yellow")
        text.append(f"{completed_tasks}/{total_tasks} tasks complete\n\n", style="dim")
        
        # Phases
        for phase_data in phases:
            text.append(self._render_phase(phase_data))
            text.append("\n")
        
        return text
    
    def _render_phase(self, phase_data: Dict[str, Any]) -> Text:
        """Render a single phase section."""
        text = Text()
        state = phase_data.get("state", "not_started")
        
        # Phase header
        if state == "completed":
            text.append("✅ ", style="green")
        elif state == "in_progress":
            text.append("🔄 ", style="cyan")
        else:
            text.append("⏳ ", style="dim")
        
        text.append(f"Phase {phase_data.get('number', '?')}: ", style="bold")
        text.append(f"{phase_data.get('title', 'Unknown')[:25]}\n")
        
        # Progress
        total = phase_data.get("total", 0)
        completed = phase_data.get("completed", 0)
        text.append(f"   [{completed}/{total}] ", style="dim")
        
        pct = phase_data.get("progress_pct", 0)
        bar_width = 10
        filled = int(bar_width * pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        text.append(f"[{bar}] {pct}%\n", style="green" if pct == 100 else "yellow" if pct > 0 else "dim")
        
        # Tasks (only show for in-progress phase or if few tasks)
        if state == "in_progress" or total <= 5:
            for task in phase_data.get("tasks", [])[:10]:  # Limit display
                text.append(self._render_task(task))
        
        return text
    
    def _render_task(self, task_data: Dict[str, Any]) -> Text:
        """Render a single task row."""
        text = Text()
        state = task_data.get("state", "pending")
        
        # Indent
        text.append("   ")
        
        # Status emoji
        status_emoji = STATUS_EMOJI.get(state, "❓")
        text.append(f"{status_emoji} ", style=STATUS_STYLE.get(state, ""))
        
        # Agent emoji
        agent_emoji = task_data.get("emoji", "🤖")
        text.append(f"{agent_emoji} ")
        
        # Task ID and title
        text.append(f"{task_data.get('id', '?')}: ", style="bold" if state == "in_progress" else "")
        title = task_data.get("title", "Unknown")[:30]
        text.append(f"{title}\n", style=STATUS_STYLE.get(state, ""))
        
        return text
    
    def _render_from_files(self) -> Text:
        """Fallback: render from markdown files."""
        text = Text()
        text.append("📊 Dashboard\n", style="bold cyan")
        text.append("─" * 40 + "\n", style="dim")
        text.append("(Orchestrator not initialized)\n\n", style="dim")
        text.append("Start the swarm with 'go' to see\n", style="dim")
        text.append("real-time task progress here.\n", style="dim")
        return text
