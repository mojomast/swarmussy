"""
Textual-based Dashboard for Multi-Agent Chatroom.

Full-featured TUI with scrollable panels, per-agent status, token tracking, and devplan.
"""

import asyncio
import logging
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Input, RichLog, Label,
    Button, Select, Switch, Rule, DataTable, OptionList,
    TabbedContent, TabPane, Collapsible
)
from textual.widgets.option_list import Option
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
from textual.binding import Binding
from textual import work, on
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from config.settings import validate_config, ARCHITECT_MODEL, AVAILABLE_MODELS, get_scratch_dir, REQUESTY_API_BASE_URL
from core.chatroom import Chatroom, set_chatroom
from core.models import Message as ChatMessage, MessageRole, AgentStatus
from core.task_manager import get_task_manager
from core.token_tracker import get_token_tracker
from core.project_manager import get_project_manager, Project
from core.settings_manager import get_settings, DEFAULT_SETTINGS
from agents import create_agent, AGENT_CLASSES
from agents.base_agent import set_api_log_callback

logger = logging.getLogger(__name__)

AGENT_ICONS = {
    "Bossy McArchitect": "🏗️", "Codey McBackend": "⚙️", "Codey McBackend 2": "⚙️",
    "Pixel McFrontend": "🎨", "Pixel McFrontend 2": "🎨", "Bugsy McTester": "🐛",
    "Bugsy McTester 2": "🐛", "Deployo McOps": "🚀", "Deployo McOps 2": "🚀",
    "Checky McManager": "📊", "Docy McWriter": "📝",
}


# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class SettingsScreen(ModalScreen):
    """Modal screen for settings."""
    BINDINGS = [Binding("escape", "dismiss", "Close")]
    CSS = """
    SettingsScreen {
        align: center middle;
    }
    
    #settings-container {
        width: 95%;
        max-width: 320;
        height: 90%;
        max-height: 55;
        border: thick $primary;
        background: $surface;
        padding: 2;
        layout: vertical;
    }
    
    #settings-header {
        height: auto;
        margin-bottom: 1;
    }
    
    #settings-content {
        height: 1fr;
        overflow: auto;
    }
    
    #settings-buttons {
        height: auto;
        margin-top: 1;
    }
    
    .settings-row {
        height: auto;
        min-height: 3;
        margin-bottom: 1;
        width: 100%;
    }
    
    .settings-label {
        width: 20;
        min-width: 20;
    }
    
    .settings-input {
        width: 1fr;
        min-width: 25;
    }
    
    #settings-container Button {
        margin: 0 1;
        min-width: 12;
    }
    
    #settings-container Select {
        width: 100%;
        margin-bottom: 1;
    }
    
    #settings-container TabbedContent {
        height: 1fr;
        border: solid $primary-darken-2;
    }
    
    #settings-container TabPane {
        padding: 1;
        height: 1fr;
        overflow: auto;
    }
    """

    def compose(self) -> ComposeResult:
        settings = get_settings()
        provider_options = [
            ("Requesty (router.requesty.ai)", "requesty"),
            ("Z.AI (api.z.ai)", "zai"),
            ("OpenAI (api.openai.com)", "openai"),
            ("Custom Endpoint", "custom"),
        ]
        # Tool identifier options for API spoofing
        tool_id_options = [
            ("Default (Swarm Agent)", "swarm"),
            ("Claude Code", "claude-code"),
            ("Cursor", "cursor"),
            ("Windsurf", "windsurf"),
            ("Aider", "aider"),
            ("Continue", "continue"),
            ("Custom", "custom"),
        ]
        with Vertical(id="settings-container"):
            with Container(id="settings-header"):
                yield Label("⚙️ SETTINGS", classes="section-title")
                yield Rule()
            
            with ScrollableContainer(id="settings-content"):
                with TabbedContent():
                    with TabPane("General", id="general-tab"):
                        with Vertical():
                            with Horizontal(classes="settings-row"):
                                yield Label("Username:", classes="settings-label")
                                yield Input(value=settings.get("username", "You"), id="username-input", classes="settings-input")
                            with Horizontal(classes="settings-row"):
                                yield Label("Auto Chat:", classes="settings-label")
                                yield Switch(value=settings.get("auto_chat", True), id="auto-chat-switch")
                            with Horizontal(classes="settings-row"):
                                yield Label("Tools Enabled:", classes="settings-label")
                                yield Switch(value=settings.get("tools_enabled", True), id="tools-switch")
                    
                    with TabPane("Models", id="models-tab"):
                        with Vertical():
                            yield Label("Architect Provider:")
                            yield Select(
                                provider_options,
                                value=settings.get("architect_provider", settings.get("default_provider", "requesty")),
                                id="architect-provider-select",
                            )
                            yield Label("Architect Model:")
                            yield Select(
                                [(m, m) for m in AVAILABLE_MODELS],
                                value=settings.get("architect_model", AVAILABLE_MODELS[0]),
                                id="architect-model-select",
                            )
                            yield Label("Worker Provider:")
                            yield Select(
                                provider_options,
                                value=settings.get("swarm_provider", settings.get("default_provider", "requesty")),
                                id="swarm-provider-select",
                            )
                            yield Label("Worker Model:")
                            yield Select(
                                [(m, m) for m in AVAILABLE_MODELS],
                                value=settings.get("swarm_model", AVAILABLE_MODELS[0]),
                                id="swarm-model-select",
                            )
                    
                    with TabPane("API", id="api-tab"):
                        with Vertical():
                            yield Label("Custom API Base URL:")
                            yield Input(
                                value=settings.get("api_base_url", ""),
                                placeholder="https://api.openai.com/v1/chat/completions",
                                id="api-base-url-input",
                                classes="settings-input"
                            )
                            yield Label("Custom API Key:")
                            yield Input(
                                value=settings.get("api_key", ""),
                                placeholder="sk-...",
                                password=True,
                                id="api-key-input",
                                classes="settings-input"
                            )
                            yield Rule()
                            yield Label("Z.AI API Key (for Z.AI provider):")
                            yield Input(
                                value=settings.get("zai_api_key", ""),
                                placeholder="Your Z.AI API key",
                                password=True,
                                id="zai-api-key-input",
                                classes="settings-input"
                            )
                            yield Rule()
                            yield Label("Tool Identifier (for API headers):")
                            yield Select(
                                tool_id_options,
                                value=settings.get("tool_identifier", "swarm"),
                                id="tool-identifier-select",
                            )
                            yield Label("Custom Tool ID (if 'Custom' selected):")
                            yield Input(
                                value=settings.get("custom_tool_id", ""),
                                placeholder="my-custom-tool",
                                id="custom-tool-id-input",
                                classes="settings-input"
                            )
                    
                    with TabPane("Advanced", id="advanced-tab"):
                        with Vertical():
                            with Horizontal(classes="settings-row"):
                                yield Label("Max Tokens:", classes="settings-label")
                                yield Input(value=str(settings.get("max_tokens", 16000)), id="max-tokens-input", classes="settings-input")
                            with Horizontal(classes="settings-row"):
                                yield Label("Temperature:", classes="settings-label")
                                yield Input(value=str(settings.get("temperature", 0.8)), id="temperature-input", classes="settings-input")
                            with Horizontal(classes="settings-row"):
                                yield Label("Max Tool Depth:", classes="settings-label")
                                yield Input(value=str(settings.get("max_tool_depth", 15)), id="tool-depth-input", classes="settings-input")
            
            yield Rule()
            with Horizontal(id="settings-buttons"):
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    @on(Button.Pressed, "#save-btn")
    def save_settings(self):
        settings = get_settings()
        # General tab
        settings.set("username", self.query_one("#username-input", Input).value, auto_save=False)
        settings.set("auto_chat", self.query_one("#auto-chat-switch", Switch).value, auto_save=False)
        settings.set("tools_enabled", self.query_one("#tools-switch", Switch).value, auto_save=False)
        # Models tab
        settings.set("architect_provider", self.query_one("#architect-provider-select", Select).value, auto_save=False)
        settings.set("swarm_provider", self.query_one("#swarm-provider-select", Select).value, auto_save=False)
        settings.set("architect_model", self.query_one("#architect-model-select", Select).value, auto_save=False)
        settings.set("swarm_model", self.query_one("#swarm-model-select", Select).value, auto_save=False)
        # API tab
        settings.set("api_base_url", self.query_one("#api-base-url-input", Input).value.strip(), auto_save=False)
        settings.set("api_key", self.query_one("#api-key-input", Input).value.strip(), auto_save=False)
        settings.set("zai_api_key", self.query_one("#zai-api-key-input", Input).value.strip(), auto_save=False)
        settings.set("tool_identifier", self.query_one("#tool-identifier-select", Select).value, auto_save=False)
        settings.set("custom_tool_id", self.query_one("#custom-tool-id-input", Input).value.strip(), auto_save=False)
        # Advanced tab
        try: settings.set("max_tokens", int(self.query_one("#max-tokens-input", Input).value), auto_save=False)
        except: pass
        try: settings.set("temperature", float(self.query_one("#temperature-input", Input).value), auto_save=False)
        except: pass
        # Allow deeper tool chains (up to 250) so agents can work more autonomously
        try: settings.set("max_tool_depth", max(5, min(250, int(self.query_one("#tool-depth-input", Input).value))), auto_save=False)
        except: pass
        settings.save()
        self.dismiss(True)

    @on(Button.Pressed, "#cancel-btn")
    def cancel(self): self.dismiss(False)


class FileBrowserScreen(ModalScreen):
    """Modal screen for browsing project files and viewing contents."""

    BINDINGS = [Binding("escape", "dismiss", "Close")]

    CSS = """
    FileBrowserScreen {
        align: center middle;
    }

    #file-browser-container {
        width: 95%;
        max-width: 320;
        height: 85%;
        max-height: 60;
        border: thick $primary;
        background: $surface;
        padding: 2;
        layout: vertical;
    }

    #file-browser-header {
        height: auto;
        margin-bottom: 1;
    }

    #file-browser-body {
        height: 1fr;
        layout: horizontal;
    }

    #file-list-panel {
        width: 1fr;
        border-right: solid $primary-darken-2;
        padding-right: 1;
    }

    #file-viewer-panel {
        width: 1.4fr;
        padding-left: 1;
    }

    #file-list {
        height: 1fr;
        overflow: auto;
    }

    #file-viewer {
        height: 1fr;
        overflow: auto;
    }

    #file-browser-buttons {
        height: auto;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        from core.project_manager import get_project_manager

        pm = get_project_manager()
        project = pm.current

        title = "📁 PROJECT FILES"
        if project is not None:
            title = f"📁 FILES — {project.name}"

        with Vertical(id="file-browser-container"):
            with Container(id="file-browser-header"):
                yield Label(title, classes="section-title")
                yield Rule()

            with Container(id="file-browser-body"):
                with Vertical(id="file-list-panel"):
                    yield Label("Structure", classes="section-title")
                    yield OptionList(id="file-list")
                with Vertical(id="file-viewer-panel"):
                    yield Label("Preview", id="file-viewer-title", classes="section-title")
                    yield Static("Select a file on the left to preview its contents.", id="file-viewer")

            yield Rule()
            with Horizontal(id="file-browser-buttons"):
                yield Button("Close", variant="primary", id="file-browser-close")

    async def on_mount(self):
        await self._load_files()

    async def _load_files(self):
        """Populate the file list from the current project's root."""
        from core.project_manager import get_project_manager

        pm = get_project_manager()
        project = pm.current
        option_list = self.query_one("#file-list", OptionList)
        option_list.clear_options()

        # Prefer the shared scratch workspace where agents actually write
        # project files (scratch/shared). Fall back to the project root if
        # the shared dir doesn't exist yet.
        if project is None or not project.root.exists():
            option_list.add_option(Option("(no active project)", ""))
            return

        root = project.shared_dir if getattr(project, "shared_dir", None) and project.shared_dir.exists() else project.root

        paths = []
        try:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(root)
                # Skip hidden and internal folders, but **do** include scratch/
                if any(part.startswith(".") for part in rel.parts):
                    continue
                if any(part in {"data", "__pycache__", "node_modules"} for part in rel.parts):
                    continue
                paths.append(rel)
        except Exception:
            paths = []

        paths.sort()

        for rel in paths:
            depth = len(rel.parts) - 1
            indent = "  " * depth
            label = f"{indent}{rel.name}"
            option_list.add_option(Option(label, str(rel)))

    @on(OptionList.OptionSelected, "#file-list")
    def on_file_selected(self, event: OptionList.OptionSelected):
        """Load and display the selected file in the preview pane."""
        from core.project_manager import get_project_manager

        # Textual's Option instances don't expose a generic `.value`; we
        # stored the relative path in the option's ID, which is available on
        # the event as `option_id`.
        rel_value = event.option_id or ""
        if not rel_value:
            return

        pm = get_project_manager()
        project = pm.current
        if project is None:
            return

        # Use the same root that was used to list files (shared_dir if it exists)
        root = project.shared_dir if getattr(project, "shared_dir", None) and project.shared_dir.exists() else project.root
        full_path = root / rel_value

        viewer = self.query_one("#file-viewer", Static)
        title = self.query_one("#file-viewer-title", Label)
        title.update(f"📄 {rel_value}")

        try:
            if not full_path.exists():
                viewer.update(f"File not found: {full_path}")
                return
            # Try to read as UTF-8 text; fall back to binary summary
            text = full_path.read_text(encoding="utf-8")
            if len(text) > 8000:
                text = text[:8000] + "\n… (truncated)"
            viewer.update(text)
        except UnicodeDecodeError:
            size = full_path.stat().st_size
            viewer.update(f"(binary file, {size} bytes)")
        except Exception as e:
            viewer.update(f"Error reading file: {e}")

    @on(Button.Pressed, "#file-browser-close")
    def close_browser(self):
        self.dismiss()


# ─────────────────────────────────────────────────────────────────────────────
# SCROLLABLE WIDGET PANELS
# ─────────────────────────────────────────────────────────────────────────────

class TokenDetailPanel(Static):
    """Panel showing token usage details."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tracker = get_token_tracker()
    
    def refresh_display(self):
        """Refresh the token display."""
        stats = self.tracker.get_stats()
        
        content = Text()
        content.append("Session Totals:\n", style="bold")
        # TokenTracker exposes prompt_tokens, completion_tokens, total_tokens, call_count
        content.append(f"  Input:  {stats.get('prompt_tokens', 0):,}\n")
        content.append(f"  Output: {stats.get('completion_tokens', 0):,}\n")
        content.append(f"  Total:  {stats.get('total_tokens', 0):,}\n")
        content.append(f"  Calls:  {stats.get('call_count', 0):,}\n")
        
        # Per-agent breakdown
        by_agent = stats.get('by_agent', {})
        if by_agent:
            content.append("\nBy Agent:\n", style="bold")
            for agent, agent_stats in by_agent.items():
                short_name = agent.split()[0] if agent else "?"
                total_agent_tokens = agent_stats.get("prompt", 0) + agent_stats.get("completion", 0)
                content.append(f"  {short_name}: {total_agent_tokens:,}\n")
        
        self.update(content)


class AgentCard(Static):
    """Individual agent status card."""
    def __init__(self, agent, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self.accomplishments = []
        self.tokens_used = 0
        self.current_action = ""  # Granular progress
        self.expanded = False
        self._max_history = 50

    def add_accomplishment(self, text: str):
        self.accomplishments.append(text)
        if len(self.accomplishments) > self._max_history:
            self.accomplishments = self.accomplishments[-self._max_history:]
        self.refresh_display()

    def add_tokens(self, count: int):
        self.tokens_used += count
        self.refresh_display()
        
    def set_action(self, action: str):
        """Set current granular action."""
        self.current_action = action
        self.refresh_display()

    async def on_click(self, event):
        """Handle clicks for expand/collapse and per-agent halt.

        - Left click toggles expanded/collapsed view.
        - Right click halts this agent's current work via the dashboard.
        """
        # Stop event so parent containers don't also handle the click
        try:
            event.stop()
        except Exception:
            pass

        button = getattr(event, "button", 1)

        # Right-click: request halt for this agent
        if button == 3:
            try:
                dashboard = self.app  # type: ignore[assignment]
                # Halt this agent's current work (fire and forget)
                import asyncio as _asyncio
                _asyncio.create_task(dashboard.halt_agent(self.agent))
            except Exception:
                pass
            return

        # Left-click (or default): toggle expanded/collapsed
        self.expanded = not self.expanded
        self.refresh_display()

    def refresh_display(self):
        icon = AGENT_ICONS.get(self.agent.name, "🤖")
        
        # Status color
        if self.agent.status == AgentStatus.WORKING:
            border_style = "green"
            title = f"{icon} {self.agent.name} (WORKING{' ▾' if self.expanded else ' ▸'})"
        else:
            border_style = "dim"
            title = f"{icon} {self.agent.name} (IDLE{' ▾' if self.expanded else ' ▸'})"
            
        # Content construction
        content = Text()

        # Compact collapsed view: ~2 lines with tokens, action, task, latest
        if not self.expanded:
            action = (self.current_action or "Idle").replace("\n", " ")
            action_short = action[:60]
            task = getattr(self.agent, 'current_task_description', '') or "No task"
            task_short = task.replace("\n", " ")[:40]
            latest = self.accomplishments[-1] if self.accomplishments else ""
            latest_short = latest.replace("\n", " ")[:30]

            line1 = f"T:{self.tokens_used:,} | {action_short}"
            line2 = f"Task: {task_short}"
            if latest_short:
                line2 = f"{line2} | {latest_short}"

            content.append(line1 + "\n", style="dim")
            content.append(line2, style="yellow")

            self.update(Panel(content, title=title, border_style=border_style))
            return

        # Expanded view: detailed layout (tokens, full action, task, latest list)
        content.append(f"Tokens: {self.tokens_used:,}\n", style="dim")

        if self.current_action:
            content.append(f"Action: {self.current_action}\n", style="bold cyan")

        task = getattr(self.agent, 'current_task_description', '')
        content.append("\nTask:\n", style="bold yellow")
        if task:
            content.append(f"{task}\n")
        else:
            content.append("No task assigned\n", style="dim")

        if self.accomplishments:
            content.append("\nLatest:\n", style="bold white")
            items = self.accomplishments[-self._max_history:]
            for acc in items:
                content.append(f"[x] {acc}\n", style="green")

        self.update(Panel(content, title=title, border_style=border_style))


def _sanitize_for_display(text: str) -> str:
    """Remove problematic Unicode characters for Windows terminal compatibility."""
    import re
    # Replace common problematic characters
    replacements = {
        '█': '#', '░': '-', '▓': '=',
        '─': '-', '│': '|', '┌': '+', '┐': '+', '└': '+', '┘': '+',
        '├': '+', '┤': '+', '┬': '+', '┴': '+', '┼': '+',
        '▶': '>', '▼': 'v', '◀': '<', '▲': '^',
        '→': '->', '←': '<-', '↑': '^', '↓': 'v',
        '✓': '[x]', '✗': '[!]', '✔': '[x]', '✘': '[!]',
        '⏳': '[ ]', '🔄': '[~]', '✅': '[x]', '❌': '[!]', '📤': '[>]',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove other problematic emoji ranges
    text = re.sub(r'[\U0001F300-\U0001F9FF]', '', text)  # Misc symbols
    return text


class DevPlanPanel(Static):
    """Panel displaying real-time swarm progress with phases and tasks."""
    
    # Agent markers for task display
    AGENT_EMOJI = {
        "backend_dev": "[BE]",
        "frontend_dev": "[FE]",
        "qa_engineer": "[QA]",
        "devops": "[DO]",
        "tech_writer": "[TW]",
    }
    
    STATUS_EMOJI = {
        "pending": "[ ]",
        "dispatched": "[>]",
        "in_progress": "[~]",
        "completed": "[x]",
        "blocked": "[!]",
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_content = "Loading..."
        self._orchestrator = None
        self._collapsed_phases = set()  # Track collapsed phases
    
    def set_orchestrator(self, orch):
        """Set the orchestrator for real-time updates."""
        self._orchestrator = orch
    
    def toggle_phase(self, phase_num: int):
        """Toggle phase collapsed state."""
        if phase_num in self._collapsed_phases:
            self._collapsed_phases.discard(phase_num)
        else:
            self._collapsed_phases.add(phase_num)
        self.refresh_plan()
    
    def refresh_plan(self):
        """Refresh the dashboard - prefer orchestrator data, fallback to files."""
        try:
            # Try orchestrator first for real-time data
            if self._orchestrator and self._orchestrator._initialized:
                self.plan_content = self._render_from_orchestrator()
            else:
                self.plan_content = self._render_from_files()
        except Exception as e:
            self.plan_content = f"Error loading dashboard: {e}"
        
        self.update(self.plan_content)
    
    def _render_from_orchestrator(self) -> str:
        """Render real-time dashboard from orchestrator state."""
        data = self._orchestrator.get_dashboard_data()
        lines = []
        
        # Header
        project_name = data.get('project_name', 'Project')
        lines.append(f"[P] {project_name}")
        lines.append("-" * 35)
        
        # Overall progress
        phases = data.get('phases', [])
        total_tasks = sum(p.get('total', 0) for p in phases)
        completed_tasks = sum(p.get('completed', 0) for p in phases)
        pct = int(100 * completed_tasks / total_tasks) if total_tasks else 0
        
        bar_width = 20
        filled = int(bar_width * pct / 100)
        bar = "#" * filled + "-" * (bar_width - filled)
        
        lines.append(f"Progress: [{bar}] {pct}%")
        lines.append(f"Tasks: {completed_tasks}/{total_tasks}")
        lines.append("")
        
        # Phases with tasks
        for phase_data in phases:
            phase_num = phase_data.get('number', 0)
            state = phase_data.get('state', 'not_started')
            is_collapsed = phase_num in self._collapsed_phases
            
            # Phase state indicator
            if state == 'completed':
                state_emoji = "[DONE]"
            elif state == 'in_progress':
                state_emoji = "[....]"
            else:
                state_emoji = "[    ]"
            
            # Phase header
            total = phase_data.get('total', 0)
            completed = phase_data.get('completed', 0)
            phase_pct = phase_data.get('progress_pct', 0)
            collapse_icon = ">" if is_collapsed else "v"
            
            phase_title = phase_data.get('title', '')[:40]  # Longer titles
            lines.append(f"{collapse_icon} {state_emoji} Phase {phase_num}: {phase_title}")
            lines.append(f"   [{completed}/{total}] {phase_pct}%")
            
            # Tasks (if not collapsed and phase is active)
            if not is_collapsed and (state == 'in_progress' or total <= 8):
                for task in phase_data.get('tasks', [])[:15]:
                    task_state = task.get('state', 'pending')
                    status_emoji = self.STATUS_EMOJI.get(task_state, "[?]")
                    agent_emoji = task.get('emoji', '[A]')
                    
                    task_id = task.get('id', '?')
                    title = task.get('title', 'Unknown')[:50]  # Longer task titles
                    
                    # Highlight in-progress tasks
                    if task_state in ('dispatched', 'in_progress'):
                        agent_name = task.get('agent_name', '')
                        lines.append(f"   {status_emoji}{agent_emoji} {task_id}: {title}")
                        if agent_name:
                            lines.append(f"      -> {agent_name}")
                    else:
                        lines.append(f"   {status_emoji}{agent_emoji} {task_id}: {title}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _render_from_files(self) -> str:
        """Fallback: render from markdown files."""
        dashboard_path = get_scratch_dir() / "shared" / "dashboard.md"
        devplan_path = get_scratch_dir() / "shared" / "devplan.md"
        task_queue_path = get_scratch_dir() / "shared" / "task_queue.md"
        plan_path = get_scratch_dir() / "shared" / "master_plan.md"
        
        # Prefer task_queue.md for task-level visibility
        if task_queue_path.exists():
            content = task_queue_path.read_text(encoding='utf-8')
            # Truncate if too long
            if len(content) > 3000:
                content = content[:3000] + "\n\n... (truncated)"
            return _sanitize_for_display(content)
        
        if dashboard_path.exists():
            return _sanitize_for_display(dashboard_path.read_text(encoding='utf-8'))
        
        if devplan_path.exists():
            content = devplan_path.read_text(encoding='utf-8')
            if len(content) > 3000:
                content = content[:3000] + "\n\n... (truncated)"
            return _sanitize_for_display(content)
        
        if plan_path.exists():
            return _sanitize_for_display(plan_path.read_text(encoding='utf-8'))
        
        return (
            "No project dashboard yet.\n\n"
            "Start by telling the Architect what you want to build:\n"
            "  'Create a [description of your project]'\n\n"
            "The dashboard will appear here once work begins."
        )


class ToolCallsLog(RichLog):
    """Scrollable log of tool calls."""
    pass


class ApiLogEntry(Static):
    """Single expandable API log entry."""
    
    DEFAULT_CSS = """
    ApiLogEntry {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    ApiLogEntry .api-header {
        width: 100%;
        height: auto;
    }
    
    ApiLogEntry .api-details {
        width: 100%;
        height: auto;
        padding-left: 2;
        display: none;
    }
    
    ApiLogEntry.expanded .api-details {
        display: block;
    }
    
    ApiLogEntry .api-section {
        width: 100%;
        height: auto;
        margin-top: 1;
        padding: 1;
        border: solid $primary-darken-2;
    }
    
    ApiLogEntry .api-section-title {
        text-style: bold;
        color: $text-muted;
    }
    
    ApiLogEntry .api-content {
        width: 100%;
        height: auto;
        overflow: auto;
    }
    """
    
    def __init__(self, entry_id: str, **kwargs):
        super().__init__(**kwargs)
        self.entry_id = entry_id
        self.expanded = False
        # 0 = collapsed, 1 = summary, 2 = full details
        self.detail_level = 0
        self.request_data = {}
        self.response_data = {}
        self.header_text = ""
        self.has_response = False
    
    def set_request(self, timestamp: str, agent_name: str, data: dict):
        """Set request data."""
        self.request_data = data
        short_name = agent_name.split()[0] if agent_name else "?"
        msg_count = data.get("msg_count", "?")
        tools = "🔧" if data.get("tools") else ""
        preview = data.get("preview", "")[:40]
        
        self.header_text = f"[+] [{timestamp}] {short_name} ({msg_count} msgs) {tools}"
        if preview:
            self.header_text += f'\n    → "{preview}..."'
        
        self._update_display()
    
    def set_response(self, timestamp: str, agent_name: str, data: dict):
        """Set response data."""
        self.response_data = data
        self.has_response = True
        
        short_name = agent_name.split()[0] if agent_name else "?"
        elapsed = data.get("elapsed", 0)
        status = data.get("status", "?")
        usage = data.get("usage", {})
        total = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
        preview = data.get("preview", "")[:40]
        
        status_icon = "✓" if status == 200 else "✗"
        toggle = "[-]" if self.detail_level > 0 else "[+]"
        
        self.header_text = f"{toggle} [{timestamp}] {status_icon} {short_name} {elapsed:.1f}s [{total:,} tok]"
        if preview:
            self.header_text += f'\n    ← "{preview}..."'
        
        self._update_display()
    
    def _update_display(self):
        """Update the display."""
        lines = [self.header_text]
        
        # Level 1: compact summary view (no full message bodies)
        if self.detail_level == 1:
            lines.append("")
            lines.append("═══ SUMMARY ═══")

            model = self.request_data.get("model", "?")
            max_tokens = self.request_data.get("max_tokens", "?")
            msg_count = self.request_data.get("msg_count", "?")
            lines.append(f"  Model: {model}")
            lines.append(f"  Max Tokens: {max_tokens}")
            lines.append(f"  Messages: {msg_count}")

            temperature = self.request_data.get("temperature")
            if temperature is not None:
                lines.append(f"  Temperature: {temperature}")

            task = (self.request_data.get("task") or "").strip()
            if task:
                short_task = task[:120]
                lines.append(f"  Task: {short_task}{'...' if len(task) > 120 else ''}")

            tool_names = self.request_data.get("tool_names", [])
            if tool_names:
                lines.append(f"  Tools: {', '.join(tool_names[:5])}")
                if len(tool_names) > 5:
                    lines.append(f"         +{len(tool_names) - 5} more")

            if self.has_response:
                usage = self.response_data.get("usage", {})
                elapsed = self.response_data.get("elapsed", 0)
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total = prompt_tokens + completion_tokens
                lines.append(f"  Time: {elapsed:.2f}s")
                lines.append(f"  Tokens: P {prompt_tokens:,} | C {completion_tokens:,} | T {total:,}")
                preview = self.response_data.get("preview") or self.response_data.get("full_response", "")
                if preview:
                    lines.append("")
                    lines.append(f"  Preview: {preview[:120]}...")
                    lines.append("")
                    lines.append("  (click again for full request/response details)")
            else:
                lines.append("  Status: waiting for response…")

        # Level 2+: full details (request always, response when available)
        elif self.detail_level >= 2:
            lines.append("")
            lines.append("═══ REQUEST ═══")
            
            # Show model info
            model = self.request_data.get("model", "?")
            max_tokens = self.request_data.get("max_tokens", "?")
            lines.append(f"  Model: {model}")
            lines.append(f"  Max Tokens: {max_tokens}")
            
            # Show tools if any
            tool_names = self.request_data.get("tool_names", [])
            if tool_names:
                lines.append(f"  Tools ({len(tool_names)}): {', '.join(tool_names[:8])}")
                if len(tool_names) > 8:
                    lines.append(f"         {', '.join(tool_names[8:])}")
            
            # Show messages (TRUNCATED to save space)
            messages = self.request_data.get("messages", [])
            lines.append("")
            lines.append(f"  Messages ({len(messages)}):")
            for i, msg in enumerate(messages):
                role = msg.get("role", "?")
                content = msg.get("content") or ""
                # Truncate long content
                if len(content) > 200:
                    content = content[:200] + f"... [{len(content)} chars total]"
                lines.append(f"  ┌─[{i+1}] {role.upper()}")
                content_lines = content.split('\n')[:5]  # Max 5 lines
                for cl in content_lines:
                    lines.append(f"  │ {cl[:100]}")  # Max 100 chars per line
                if len(content.split('\n')) > 5:
                    lines.append(f"  │ ... ({len(content.split(chr(10)))} lines total)")
                lines.append("  └─────")
            
            if self.has_response:
                lines.append("")
                lines.append("═══ RESPONSE ═══")
                
                usage = self.response_data.get("usage", {})
                elapsed = self.response_data.get("elapsed", 0)
                lines.append(f"  Time: {elapsed:.2f}s")
                lines.append(f"  Prompt Tokens: {usage.get('prompt_tokens', 0):,}")
                lines.append(f"  Completion Tokens: {usage.get('completion_tokens', 0):,}")
                lines.append(f"  Total Tokens: {usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0):,}")
                
                full_response = self.response_data.get("full_response", "")
                if full_response:
                    lines.append("")
                    lines.append("  Content:")
                    lines.append("  ┌─────")
                    # Truncate response
                    response_lines = full_response.split('\n')[:10]  # Max 10 lines
                    for rl in response_lines:
                        lines.append(f"  │ {rl[:100]}")  # Max 100 chars
                    if len(full_response.split('\n')) > 10:
                        lines.append(f"  │ ... ({len(full_response)} chars total)")
                    lines.append("  └─────")
                
                tool_calls = self.response_data.get("tool_calls", [])
                if tool_calls:
                    lines.append("")
                    lines.append(f"  Tool Calls ({len(tool_calls)}):")
                    for tc in tool_calls[:5]:  # Max 5 tool calls shown
                        func = tc.get("function", {})
                        name = func.get("name", "?")
                        args = func.get("arguments", "")
                        lines.append(f"  ┌─ {name}")
                        try:
                            import json
                            args_dict = json.loads(args) if args else {}
                            for k, v in list(args_dict.items())[:3]:  # Max 3 args
                                v_str = str(v)[:100]  # Truncate values
                                lines.append(f"  │   {k}: {v_str}")
                            if len(args_dict) > 3:
                                lines.append(f"  │   ... +{len(args_dict) - 3} more args")
                        except:
                            lines.append(f"  │   {args[:100]}")
                        lines.append("  └─────")
                    if len(tool_calls) > 5:
                        lines.append(f"  ... +{len(tool_calls) - 5} more tool calls")
            
            lines.append("═════════════════")
        
        self.update("\n".join(lines))
    
    def toggle_expand(self):
        """Toggle expanded state.

        Cycles through: collapsed → summary → full → collapsed.
        """
        if not self.has_response and not self.request_data:
            return

        if self.detail_level == 0:
            self.detail_level = 1
            self.expanded = True
        elif self.detail_level == 1:
            self.detail_level = 2
            self.expanded = True
        else:
            self.detail_level = 0
            self.expanded = False

        if "[+]" in self.header_text and self.detail_level > 0:
            self.header_text = self.header_text.replace("[+]", "[-]", 1)
        elif "[-]" in self.header_text and self.detail_level == 0:
            self.header_text = self.header_text.replace("[-]", "[+]", 1)

        self._update_display()
    
    async def on_click(self, event):
        """Handle click to toggle expansion."""
        # Stop event so the click doesn't bubble further up the tree
        try:
            event.stop()
        except Exception:
            pass
        self.toggle_expand()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN DASHBOARD APP
# ─────────────────────────────────────────────────────────────────────────────

class SwarmDashboard(App):
    """Textual app for the agent swarm dashboard."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1.5fr 3.5fr 2.0fr;
    }

    /* LEFT SIDEBAR - Agent Cards (full height, scrollable) */
    #left-sidebar {
        height: 100%;
        layout: vertical;
        border: solid $primary;
        padding: 0;
        overflow: hidden;
    }
    
    #agents-scroll {
        height: 1fr;
        min-height: 10;
        overflow-y: auto;
        overflow-x: hidden;
    }
    
    #agents-container {
        width: 100%;
        height: auto;
        padding: 1;
    }
    
    .agent-card {
        width: 100%;
        height: auto;
        min-height: 4;
        margin-bottom: 1;
        padding: 0;
        overflow: hidden;
    }
    
    ApiLogEntry {
        width: 100%;
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        border: solid $primary-darken-3;
    }
    
    ApiLogEntry:hover {
        background: $primary-darken-2;
    }

    /* CENTER - Inflight (collapsible top) + Chat + Input */
    #center {
        height: 100%;
        layout: vertical;
        overflow: hidden;
    }

    #inflight-collapsible {
        height: auto;
        max-height: 33%;
        border: solid $warning;
        margin-bottom: 1;
    }
    
    #inflight-scroll {
        height: auto;
        max-height: 20;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0 1;
    }
    
    #inflight-container {
        width: 100%;
        height: auto;
    }
    
    #inflight-empty {
        color: $text-muted;
        text-style: italic;
        padding: 1;
    }

    #chat-log {
        height: 1fr;
        min-height: 10;
        border: solid $success;
        padding: 1;
        width: 100%;
        overflow-y: auto;
        overflow-x: hidden;
    }
    
    RichLog {
        width: 100%;
        overflow-y: auto;
        overflow-x: hidden;
        scrollbar-gutter: stable;
    }

    #input-box {
        height: 3;
        padding: 0 1;
    }

    /* RIGHT SIDEBAR - Tokens+Tools (top), Plan (middle), API History (bottom) */
    #right-sidebar {
        height: 100%;
        layout: vertical;
        border: solid $warning;
        padding: 0;
        overflow: hidden;
    }

    #tokens-tools-row {
        height: 14;
        layout: horizontal;
        border-bottom: solid $warning-darken-2;
    }

    #tokens-scroll {
        width: 32;
        height: 100%;
        border-right: solid $warning-darken-2;
        padding: 0 1;
        overflow-y: auto;
        overflow-x: hidden;
    }

    #tools-scroll {
        width: 1fr;
        height: 100%;
        padding: 0 1;
        overflow-y: auto;
        overflow-x: hidden;
    }

    #plan-scroll {
        /* Take ~2/3 of the remaining right-sidebar height */
        height: 2fr;
        padding: 1;
        overflow-y: auto;
        overflow-x: hidden;
    }

    #api-history-collapsible {
        /* Take ~1/3 of the remaining right-sidebar height */
        height: 1fr;
        border-top: solid $warning-darken-2;
    }
    
    #api-history-scroll {
        height: 1fr;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0 1;
    }
    
    #api-history-container {
        width: 100%;
        height: auto;
    }

    .section-title {
        text-style: bold;
        background: $primary-darken-2;
        padding: 0 1;
        width: 100%;
        height: auto;
    }

    Input {
        width: 100%;
    }
    
    ScrollableContainer {
        scrollbar-gutter: stable;
    }
    
    Collapsible {
        padding: 0;
    }
    
    #files-btn {
        dock: bottom;
        width: 100%;
        margin: 0 1;
    }

    #stop-btn {
        dock: bottom;
        width: 100%;
        margin: 1;
    }
    
    Static {
        width: 100%;
        height: auto;
    }
    
    TokenDetailPanel {
        width: 100%;
        height: auto;
    }
    
    DevPlanPanel {
        width: 100%;
        height: auto;
    }
    
    ToolCallsLog {
        height: auto;
        max-height: 100%;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "open_settings", "Settings"),
        Binding("ctrl+t", "open_tasks", "Tasks"),
        Binding("ctrl+x", "stop_current", "Stop"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+p", "refresh_plan", "Plan"),
        Binding("ctrl+f", "open_files", "Files"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+a", "focus_agents", "Agents"),
        Binding("ctrl+up", "scroll_agents_up", "Agents ▲"),
        Binding("ctrl+down", "scroll_agents_down", "Agents ▼"),
    ]

    api_status = reactive("idle")

    def __init__(self, project: Project, username: str = "You", load_history: bool = True, devussy_mode: bool = False):
        super().__init__()
        self.project = project
        self.username = username
        # Whether to load prior chat history from disk on startup
        self.load_history = load_history
        # Whether devussy pipeline was run - Architect follows devplan strictly
        self.devussy_mode = devussy_mode
        self.chatroom: Optional[Chatroom] = None
        self.agents = []
        self.agent_cards: Dict[str, AgentCard] = {}
        self.is_processing = False
        # Set when a synthetic Auto Orchestrator message is injected to nudge Bossy/Checky
        self.auto_orchestrator_pending: bool = False
        self.auto_orchestrator_retries: int = 0  # Retry counter to prevent infinite loops

    def update_status_line(self):
        status_map = {
            "idle": "○ idle",
            "request": "↑ req",
            "response": "↓ resp",
            "error": "× err",
        }
        label = status_map.get(self.api_status, "○ idle")
        self.sub_title = f"User: {self.username} | API {label}"

    def watch_api_status(self, old, new):
        self.update_status_line()

    def action_focus_agents(self):
        try:
            container = self.query_one("#agents-scroll", ScrollableContainer)
            container.focus()
        except Exception:
            pass

    def action_scroll_agents_up(self):
        try:
            container = self.query_one("#agents-scroll", ScrollableContainer)
            container.scroll_up(4)
        except Exception:
            pass

    def action_scroll_agents_down(self):
        try:
            container = self.query_one("#agents-scroll", ScrollableContainer)
            container.scroll_down(4)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Header()

        # LEFT - Agent cards (scrollable)
        with Vertical(id="left-sidebar"):
            yield Label("🤖 AGENTS", classes="section-title")
            with ScrollableContainer(id="agents-scroll"):
                with Vertical(id="agents-container"):
                    yield Static("Loading agents...", id="agents-placeholder")

        # CENTER - Inflight requests (top, collapsible) + Chat + Input
        with Vertical(id="center"):
            with Collapsible(title="⏳ In-Flight Requests", id="inflight-collapsible", collapsed=False):
                with ScrollableContainer(id="inflight-scroll"):
                    with Vertical(id="inflight-container"):
                        yield Static("(no requests)", id="inflight-empty")
            yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
            with Container(id="input-box"):
                yield Input(placeholder="Type message or /help...", id="chat-input")

        # RIGHT - Tokens+Tools (top), DevPlan (middle), API History (bottom collapsible)
        with Vertical(id="right-sidebar"):
            with Horizontal(id="tokens-tools-row"):
                with ScrollableContainer(id="tokens-scroll"):
                    yield Label("📊 TOKENS", classes="section-title")
                    yield TokenDetailPanel(id="tokens")
                with ScrollableContainer(id="tools-scroll"):
                    yield Label("🔧 TOOLS", classes="section-title")
                    yield ToolCallsLog(id="tools-log", wrap=True)
            with ScrollableContainer(id="plan-scroll"):
                yield Label("📋 DEVPLAN", classes="section-title")
                yield DevPlanPanel(id="devplan")
            with Collapsible(title="📡 API History (click to expand)", id="api-history-collapsible", collapsed=True):
                with ScrollableContainer(id="api-history-scroll"):
                    with Vertical(id="api-history-container"):
                        yield Static("(no completed requests yet)", id="api-history-empty")
            yield Button("📁 FILES", variant="primary", id="files-btn")
            yield Button("⏹ STOP", variant="error", id="stop-btn")

        yield Footer()

    async def on_mount(self):
        self.title = f"Agent Swarm - {self.project.name}"
        self.sub_title = f"User: {self.username}"
        self.update_status_line()

        self.chat_log = self.query_one("#chat-log", RichLog)
        self.token_panel = self.query_one("#tokens", TokenDetailPanel)
        self.devplan_panel = self.query_one("#devplan", DevPlanPanel)
        self.tools_log = self.query_one("#tools-log", ToolCallsLog)
        # Inflight requests now in center top
        self.api_log_inflight = self.query_one("#inflight-container", Vertical)
        # API history now in right sidebar collapsible
        self.api_log_history = self.query_one("#api-history-container", Vertical)
        self.api_log_entries: Dict[str, ApiLogEntry] = {}
        self.api_inflight_entries: Dict[str, ApiLogEntry] = {}
        self.api_entry_counter = 0
        self.current_request_id = None
        
        # Set up API logging callback
        set_api_log_callback(self.on_api_call)
        
        # Start memory profiler to debug memory leaks
        try:
            from core.memory_profiler import start_memory_monitor
            start_memory_monitor(interval=15.0)  # Log every 15 seconds
            logger.info("Memory profiler started - check logs/memory_*.log")
        except Exception as e:
            logger.warning(f"Could not start memory profiler: {e}")

        self.query_one("#chat-input", Input).focus()
        await self.init_chatroom()
        self.set_interval(3.0, self.refresh_panels)
        # Periodically advance the swarm when auto_chat is enabled
        self.set_interval(1.0, self.auto_chat_tick)

    async def init_chatroom(self):
        settings = get_settings()
        # Respect user preference for loading previous history
        self.chatroom = Chatroom(load_history=self.load_history)
        set_chatroom(self.chatroom)
        self.chatroom.on_tool_call = self.on_tool_call

        model = settings.get("architect_model", ARCHITECT_MODEL)
        architect = create_agent("architect", model=model)
        
        # If devussy mode, inject devplan-following instructions
        if self.devussy_mode:
            devussy_prompt = self._get_devussy_architect_prompt()
            if devussy_prompt:
                # Prepend devussy instructions to the architect's system prompt
                # Must modify architect.system_prompt directly (not config - already copied during __init__)
                architect.system_prompt = devussy_prompt + "\n\n" + architect.system_prompt
        
        self.agents = [architect]
        await self.chatroom.initialize(self.agents)

        # Ensure Checky McManager (project_manager) is present in dashboard sessions
        try:
            swarm_model = settings.get("swarm_model", ARCHITECT_MODEL)
            checky = await self.chatroom.spawn_agent("project_manager", model=swarm_model)
        except Exception:
            checky = None

        if checky:
            self.agents.append(checky)
            self.create_agent_card(checky)
            self.chat_log.write(Text("📊 Checky McManager joined the swarm", style="green"))
        self.chatroom.on_message(self.on_chat_message)
        
        # Start Traffic Control relay for visualization dashboard
        try:
            from core.traffic_relay import start_traffic_relay
            self.traffic_relay = await start_traffic_relay(self.chatroom)
            self.chat_log.write(Text("📡 Traffic Control relay started on ws://localhost:8766", style="blue"))
        except Exception as e:
            self.chat_log.write(Text(f"⚠️ Traffic Control relay failed: {e}", style="yellow"))
            self.traffic_relay = None
        
        # Initialize orchestrator for real-time task tracking (devussy mode)
        self.orchestrator = None
        if self.devussy_mode:
            try:
                from core.swarm_orchestrator import SwarmOrchestrator, set_orchestrator
                self.orchestrator = SwarmOrchestrator(Path(self.project.root))
                if await self.orchestrator.initialize():
                    set_orchestrator(self.orchestrator)  # Make globally accessible
                    self.devplan_panel.set_orchestrator(self.orchestrator)
                    self.chat_log.write(Text("📊 Orchestrator initialized - real-time task tracking enabled", style="cyan"))
                else:
                    self.orchestrator = None
            except Exception as e:
                logger.warning(f"Orchestrator init failed: {e}")
                self.orchestrator = None

        # Create agent card
        self.create_agent_card(architect)

        self.chat_log.write(Text("🏗️ Bossy McArchitect joined the swarm", style="green"))
        
        # Show devussy mode info
        if self.devussy_mode:
            self.chat_log.write(Text("🔮 DEVUSSY MODE - Following generated devplan", style="magenta bold"))
            self._show_devplan_summary()
        
        self.chat_log.write(Text("Ctrl+S: Settings | Ctrl+T: Tasks | Ctrl+X: Stop | Ctrl+P: Refresh Plan", style="dim"))
        self.refresh_panels()
    
    def _get_devussy_architect_prompt(self) -> Optional[str]:
        """Get the devussy-specific architect prompt that enforces plan-following."""
        try:
            from core.devussy_integration import load_devplan_for_swarm
            from agents.lean_prompts import LEAN_DEVUSSY_ARCHITECT_PROMPT
            
            devplan_data = load_devplan_for_swarm(Path(self.project.root))
            
            if not devplan_data or not devplan_data.get("has_devplan"):
                return None
            
            # Use the lean devussy prompt - it's optimized for dispatch
            return LEAN_DEVUSSY_ARCHITECT_PROMPT
        except Exception as e:
            logger.warning(f"Failed to load devussy prompt: {e}")
            return None
    
    def _show_devplan_summary(self):
        """Show a summary of the devplan in chat and recover if needed."""
        try:
            from core.devussy_integration import (
                load_devplan_for_swarm,
                SWARM_AGENTS,
                recover_project_state,
                regenerate_task_queue_from_devplan,
                generate_swarm_task_queue,
            )
            
            project_root = Path(self.project.root)
            devplan_data = load_devplan_for_swarm(project_root)
            
            if devplan_data and devplan_data.get("has_devplan"):
                self.chat_log.write(Text("📋 Devplan loaded:", style="cyan"))
                
                # Check project state for recovery needs
                state = recover_project_state(project_root)
                
                # Show existing files if resuming
                if state.get("existing_files"):
                    file_count = len(state["existing_files"])
                    self.chat_log.write(Text(f"   📂 Found {file_count} existing source files (resuming project)", style="yellow"))
                
                # Show phase progress
                if state.get("phases"):
                    completed = state.get("completed_tasks", 0)
                    total = state.get("total_tasks", 0)
                    current = state.get("current_phase", 1)
                    self.chat_log.write(Text(f"   📊 Progress: {completed}/{total} tasks, currently on Phase {current}", style="dim"))
                
                # Check for task queue
                task_queue_file = project_root / "scratch" / "shared" / "task_queue.md"
                needs_recovery = False
                regen_from_phases = False

                queue_content = ""
                if task_queue_file.exists():
                    queue_content = task_queue_file.read_text(encoding="utf-8")

                # Determine if phase files look valid (new or old formats)
                phase_files = devplan_data.get("phase_files", [])
                has_valid_tasks = False
                if phase_files:
                    for pf in phase_files:
                        content = pf.get("content", "")
                        if (
                            "@agent:" in content
                            or "### Task" in content
                            or "## Task" in content
                            or "- [ ] 1.1:" in content
                            or "PHASE_TASKS_START" in content and "TASK_1_1_START" in content
                        ):
                            has_valid_tasks = True
                            break

                # Decide how to handle the current task_queue
                if not queue_content:
                    # No queue yet
                    if has_valid_tasks:
                        regen_from_phases = True
                    else:
                        needs_recovery = True
                else:
                    # We have some queue content; check if it's the rich swarm format
                    has_rich_markers = any(
                        marker in queue_content
                        for marker in [
                            "# 🚀 Swarm Task Queue",
                            "## Agent Summary",
                            "## Phase 1",
                            "## Task Queue",  # legacy format
                        ]
                    )

                    if not has_rich_markers and has_valid_tasks:
                        # We have good phase tasks but only a minimal/recovery queue
                        regen_from_phases = True
                    elif not has_rich_markers:
                        needs_recovery = True

                # Prefer generating a rich swarm task queue from phase files
                if regen_from_phases:
                    self.chat_log.write(Text("   🔧 Generating swarm task queue from phase files...", style="yellow"))
                    try:
                        generate_swarm_task_queue(project_root)
                        self.chat_log.write(Text("   ✅ Swarm task queue generated from phases", style="green"))
                        task_queue_file = project_root / "scratch" / "shared" / "task_queue.md"
                        queue_content = task_queue_file.read_text(encoding="utf-8") if task_queue_file.exists() else ""
                        needs_recovery = False
                    except Exception as e:
                        self.chat_log.write(Text(f"   ❌ Failed to generate swarm task queue: {e}", style="red"))
                        needs_recovery = True

                # Fallback: regenerate a minimal recovery queue from devplan table
                if needs_recovery:
                    self.chat_log.write(Text("   🔧 Regenerating minimal task queue from devplan...", style="yellow"))
                    if regenerate_task_queue_from_devplan(project_root):
                        self.chat_log.write(Text("   ✅ Task queue recovered from devplan", style="green"))
                    else:
                        self.chat_log.write(Text("   ❌ Could not recover task queue", style="red"))
                else:
                    self.chat_log.write(Text("   🚀 Task queue ready", style="green"))
                    
                    # Count tasks per agent
                    queue_content = task_queue_file.read_text(encoding="utf-8")
                    agent_counts = {}
                    for agent_key in SWARM_AGENTS:
                        count = queue_content.lower().count(f"`{agent_key}`")
                        if count > 0:
                            agent_counts[agent_key] = count
                    
                    if agent_counts:
                        agents_str = ", ".join([
                            f"{SWARM_AGENTS[k]['name'].split()[0]}:{v}" 
                            for k, v in sorted(agent_counts.items())
                        ])
                        self.chat_log.write(Text(f"   🤖 {agents_str}", style="dim"))
                
                self.chat_log.write(Text("   Type 'Go' to start/resume executing the devplan", style="yellow"))
        except Exception as e:
            self.chat_log.write(Text(f"⚠️ Could not load devplan summary: {e}", style="yellow"))

    def create_agent_card(self, agent):
        """Create a card widget for an agent."""
        card = AgentCard(agent, classes="agent-card")
        self.agent_cards[agent.agent_id] = card
        
        # Add to container
        container = self.query_one("#agents-container", Vertical)
        # Remove placeholder if exists
        try:
            placeholder = self.query_one("#agents-placeholder")
            placeholder.remove()
        except:
            pass
        container.mount(card)
        card.refresh_display()

    def on_tool_call(self, agent_name: str, tool_name: str, result: str = ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        text.append(f"{agent_name.split()[0]}: ", style="cyan")
        # Show full tool action; let the panel's wrapping/scrolling handle length
        text.append(tool_name, style="white")
        self.tools_log.write(text)
        
        # Update agent card accomplishments for write operations
        if "Writing" in tool_name or "Creating" in tool_name:
            for card in self.agent_cards.values():
                if agent_name in card.agent.name:
                    card.add_accomplishment(tool_name)
                    break

    def on_api_call(self, event_type: str, agent_name: str, data: dict):
        """Handle API request/response logging with expandable entries."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        request_id = data.get("request_id")

        if event_type == "request":
            self.api_status = "request"
            self.set_timer(0.7, lambda: setattr(self, "api_status", "idle"))

            if not request_id:
                self.api_entry_counter += 1
                request_id = f"api-entry-{self.api_entry_counter}"
            self.current_request_id = request_id

            entry = ApiLogEntry(request_id)
            entry.set_request(timestamp, agent_name, data)
            self.api_log_entries[request_id] = entry
            self.api_inflight_entries[request_id] = entry
            
            # Remove empty placeholder if present
            try:
                empty = self.query_one("#inflight-empty", Static)
                empty.remove()
            except Exception:
                pass
            
            try:
                self.api_log_inflight.mount(entry)
            except Exception:
                pass

            self._trim_api_history()

        elif event_type == "response":
            self.api_status = "response"
            self.set_timer(0.9, lambda: setattr(self, "api_status", "idle"))

            if not request_id:
                request_id = self.current_request_id

            if request_id and request_id in self.api_log_entries:
                entry = self.api_log_entries[request_id]
                entry.set_response(timestamp, agent_name, data)

                usage = data.get("usage", {})
                status = data.get("status", "?")
                total = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

                if status == 200 and total > 0:
                    for card in self.agent_cards.values():
                        if agent_name and agent_name in card.agent.name:
                            card.add_tokens(total)
                            break

                if request_id in self.api_inflight_entries:
                    # Remove the inflight entry
                    try:
                        entry.remove()
                    except Exception:
                        pass
                    
                    # Remove history empty placeholder if present
                    try:
                        empty = self.query_one("#api-history-empty", Static)
                        empty.remove()
                    except Exception:
                        pass
                    
                    # Create a NEW entry for history (can't remount removed widget in Textual)
                    try:
                        history_entry = ApiLogEntry(request_id)
                        history_entry.request_data = entry.request_data
                        history_entry.response_data = entry.response_data
                        history_entry.has_response = True
                        history_entry.set_response(timestamp, agent_name, data)
                        self.api_log_history.mount(history_entry)
                        # Update the reference in api_log_entries to point to new widget
                        self.api_log_entries[request_id] = history_entry
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"Failed to mount API history entry: {e}")
                    self.api_inflight_entries.pop(request_id, None)
                    
                    # Restore inflight empty if no more inflight
                    if not self.api_inflight_entries:
                        try:
                            self.api_log_inflight.mount(Static("(no requests)", id="inflight-empty"))
                        except Exception:
                            pass

                self._trim_api_history()

            self.current_request_id = None

        elif event_type == "error":
            self.api_status = "error"
            self.set_timer(1.2, lambda: setattr(self, "api_status", "idle"))

            if not request_id:
                request_id = self.current_request_id

            if request_id and request_id in self.api_log_entries:
                entry = self.api_log_entries[request_id]
                error_data = {
                    "status": "error",
                    "usage": {},
                    "elapsed": data.get("elapsed", 0),
                    "preview": data.get("error", "Unknown error"),
                    "full_response": data.get("error", "Unknown error"),
                    "tool_calls": []
                }
                entry.set_response(timestamp, agent_name, error_data)

                if request_id in self.api_inflight_entries:
                    # Remove the inflight entry
                    try:
                        entry.remove()
                    except Exception:
                        pass
                    
                    # Remove history empty placeholder if present
                    try:
                        empty = self.query_one("#api-history-empty", Static)
                        empty.remove()
                    except Exception:
                        pass
                    
                    # Create a NEW entry for history (can't remount removed widget in Textual)
                    try:
                        history_entry = ApiLogEntry(request_id)
                        history_entry.request_data = entry.request_data
                        history_entry.response_data = entry.response_data
                        history_entry.has_response = True
                        history_entry.set_response(timestamp, agent_name, error_data)
                        self.api_log_history.mount(history_entry)
                        # Update the reference in api_log_entries to point to new widget
                        self.api_log_entries[request_id] = history_entry
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).debug(f"Failed to mount API history error entry: {e}")
                    self.api_inflight_entries.pop(request_id, None)
                    
                    # Restore inflight empty if no more inflight
                    if not self.api_inflight_entries:
                        try:
                            self.api_log_inflight.mount(Static("(no requests)", id="inflight-empty"))
                        except Exception:
                            pass

                self._trim_api_history()

            self.current_request_id = None

    def _trim_api_history(self):
        """Keep API log history bounded while preserving in-flight entries."""
        max_entries = 50
        if len(self.api_log_entries) <= max_entries:
            return

        # Only prune from history (leave in-flight entries alone)
        while len(self.api_log_entries) > max_entries and self.api_log_history.children:
            oldest_widget = self.api_log_history.children[0]
            oldest_id = getattr(oldest_widget, "entry_id", None)
            try:
                oldest_widget.remove()
            except Exception:
                pass
            if oldest_id and oldest_id in self.api_log_entries and oldest_id not in self.api_inflight_entries:
                self.api_log_entries.pop(oldest_id, None)

    def on_chat_message(self, message: ChatMessage):
        if message.sender_id == "auto_summary":
            return

        if message.sender_id == "status":
            content = message.content
            
            # Tool Call
            if "🔧" in content:
                parts = content.replace("🔧 ", "").split(": ", 1)
                if len(parts) == 2:
                    agent_name, action = parts[0], parts[1]
                    # Update granular status
                    for card in self.agent_cards.values():
                        if agent_name in card.agent.name:
                            card.set_action(f"Tool: {action[:25]}...")
                            break
            
            # Thinking / Working
            elif "⏳" in content:
                # Format: "⏳ AgentName is thinking..."
                parts = content.replace("⏳ ", "").split(" is ", 1)
                if len(parts) > 0:
                    agent_name = parts[0]
                    for card in self.agent_cards.values():
                        if agent_name in card.agent.name:
                            card.set_action("Thinking...")
                            break
                            
            # Task Assignment
            elif "📋" in content:
                # Format: "📋 Assigning task to AgentName..."
                if "Assigning task to " in content:
                    agent_name = content.split("Assigning task to ")[1].replace("...", "").strip()
                    for card in self.agent_cards.values():
                        if agent_name in card.agent.name:
                            card.set_action("Receiving Task...")
                            break

            # Tool Result / Success
            elif "✅" in content:
                # Format: "✅ AgentName: Result"
                parts = content.replace("✅ ", "").split(": ", 1)
                if len(parts) == 2:
                    agent_name = parts[0]
                    for card in self.agent_cards.values():
                        if agent_name in card.agent.name:
                            card.set_action("Idle") 
                            break
            return

        # Track synthetic auto-orchestration prompts as human messages
        if (
            message.role == MessageRole.HUMAN
            and message.sender_id == "auto_orchestrator"
        ):
            self.auto_orchestrator_pending = True
            self.auto_orchestrator_retries = 0  # Reset retry counter for new trigger

        timestamp = message.timestamp.strftime("%H:%M")
        icon = AGENT_ICONS.get(message.sender_name, "🤖")

        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        
        if message.role == MessageRole.SYSTEM:
            text.append(f"⚙️ {message.content}", style="yellow")
        elif message.role == MessageRole.HUMAN:
            text.append(f"👤 {message.sender_name}: ", style="bold green")
            text.append(message.content)
        else:
            text.append(f"{icon} {message.sender_name}: ", style="cyan")
            text.append(message.content)
        
        self.chat_log.write(text)

    def refresh_panels(self):
        # Refresh token panel
        self.token_panel.refresh_display()
        
        # Refresh devplan
        self.devplan_panel.refresh_plan()
        
        # Refresh agent cards
        if self.chatroom:
            for agent in self.chatroom._agents.values():
                if agent.agent_id not in self.agent_cards:
                    self.create_agent_card(agent)
                else:
                    self.agent_cards[agent.agent_id].refresh_display()


    def auto_chat_tick(self):
        """Background tick to keep the swarm moving when auto_chat is enabled.

        This lets Checky McManager update status/devplan and Bossy McArchitect
        hand out fresh tasks once workers finish, without manual user prompts.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        from core.settings_manager import get_settings
        settings = get_settings()

        # Respect user preference
        if not settings.get("auto_chat", True):
            return

        # Don't overlap with an in-flight round - use an atomic guard
        if self.is_processing or not self.chatroom:
            return
        
        # Additional guard: check if we're already in a tick to prevent race conditions
        if getattr(self, '_tick_in_progress', False):
            return
        self._tick_in_progress = True

        try:
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            tasks = tm.get_all_tasks()
        except Exception:
            tasks = []

        has_open = any(t.status.value in ("pending", "in_progress") for t in tasks)
        has_working_agents = any(
            a.status.value == "working" 
            for a in self.chatroom._agents.values()
        )
        has_completed_tasks = any(t.status.value == "completed" for t in tasks)

        # Run when there is active work
        should_run = has_open or has_working_agents
        
        # Also run when auto-orchestrator prompt is pending
        if self.auto_orchestrator_pending and tasks:
            should_run = True
            logger.info(f"[auto_chat_tick] Auto-orchestrator pending, triggering round (retry {self.auto_orchestrator_retries})")
        
        # FALLBACK: If all tasks completed but swarm is idle, manually trigger
        # This handles cases where the Auto Orchestrator message wasn't received
        if not should_run and has_completed_tasks and not has_open and not has_working_agents:
            # Check if we recently completed work and haven't triggered yet
            if not hasattr(self, '_idle_ticks_after_complete'):
                self._idle_ticks_after_complete = 0
            
            self._idle_ticks_after_complete += 1
            
            # After 3 idle ticks (~3 seconds), manually inject a nudge
            if self._idle_ticks_after_complete >= 3 and self._idle_ticks_after_complete <= 5:
                logger.info("[auto_chat_tick] Fallback: All tasks done but idle, nudging Architect")
                self.auto_orchestrator_pending = True
                self.auto_orchestrator_retries = 0
                should_run = True
                
                # Manually inject the Auto Orchestrator message if not already present
                self._inject_auto_orchestrator_message()
            elif self._idle_ticks_after_complete > 5:
                # Reset after giving up to prevent spam
                self._idle_ticks_after_complete = 0
        else:
            # Reset counter when there's activity
            self._idle_ticks_after_complete = 0

        if not should_run:
            self._tick_in_progress = False
            return

        # Kick off another conversation round; @work(exclusive=True) prevents
        # overlapping runs.
        self.is_processing = True

        # Note: auto_orchestrator_pending is cleared in run_conversation after
        # the round completes successfully, not here (prevents losing the flag
        # if something goes wrong)
        # The _tick_in_progress flag is cleared in run_conversation's finally block

        self.run_conversation()
    
    def _inject_auto_orchestrator_message(self):
        """Manually inject an Auto Orchestrator message to nudge the Architect."""
        import asyncio
        from core.models import Message, MessageRole, MessageType
        
        async def _inject():
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            completed = len([t for t in tm.get_all_tasks() if t.status.value == "completed"])
            
            auto_msg = Message(
                content=(
                    f"Phase milestone: {completed} task(s) completed. "
                    "Bossy McArchitect: Check the master plan and assign next batch of tasks. "
                    "If all work is done, summarize deliverables for the human."
                ),
                sender_name="Auto Orchestrator",
                sender_id="auto_orchestrator",
                role=MessageRole.HUMAN,
                message_type=MessageType.CHAT
            )
            await self.chatroom._broadcast_message(auto_msg)
            
            # Also add to Architect's memory directly
            for agent in self.chatroom._agents.values():
                await agent.process_incoming_message(auto_msg)
        
        # Run in the event loop
        try:
            asyncio.create_task(_inject())
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to inject auto-orchestrator message: {e}")


    # ─────────────────────────────────────────────────────────────────────────
    # INPUT & COMMANDS
    # ─────────────────────────────────────────────────────────────────────────

    async def on_input_submitted(self, event: Input.Submitted):
        line = event.value.strip()
        event.input.value = ""
        if not line:
            return
        if line.startswith("/"):
            await self.handle_command(line)
        else:
            await self.send_message(line)

    async def send_message(self, content: str):
        # Check for "go" command - use AutoDispatcher instead of LLM
        if content.strip().lower() == "go":
            await self._handle_go_command()
            return
        
        # Don't write here - on_chat_message callback handles display
        await self.chatroom.add_human_message(content=content, username=self.username, user_id="dashboard_user")
        self.is_processing = True
        self.run_conversation()
    
    async def _handle_go_command(self):
        """Handle 'go' command using local AutoDispatcher instead of LLM."""
        from core.auto_dispatcher import get_auto_dispatcher
        from rich.text import Text
        
        self.chat_log.write(Text("🚀 AutoDispatcher: Starting task dispatch (no LLM needed)...", style="cyan bold"))
        
        try:
            dispatcher = get_auto_dispatcher()
            
            # Set status callback for UI updates
            async def status_callback(msg: str):
                self.chat_log.write(Text(f"  {msg}", style="cyan"))
            
            dispatcher.set_status_callback(status_callback)
            
            # Dispatch the next task
            dispatched = await dispatcher.dispatch_next_task()
            
            if dispatched:
                self.chat_log.write(Text("✅ Task dispatched! Worker will start automatically.", style="green"))
                # Trigger conversation round for the worker
                self.is_processing = True
                self.run_conversation()
            else:
                self.chat_log.write(Text("ℹ️ No tasks to dispatch right now.", style="yellow"))
            
            self.refresh_panels()
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AutoDispatcher error: {e}")
            self.chat_log.write(Text(f"❌ AutoDispatcher error: {e}", style="red"))
            # Fall back to sending to Architect
            self.chat_log.write(Text("Falling back to Architect...", style="yellow"))
            await self.chatroom.add_human_message(content="go", username=self.username, user_id="dashboard_user")
            self.is_processing = True
            self.run_conversation()

    @work(exclusive=True)
    async def run_conversation(self):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            messages = await self.chatroom.run_conversation_round()
            
            logger.info(f"[run_conversation] Round complete: {len(messages)} messages, auto_pending={self.auto_orchestrator_pending}")
            
            # If the round produced messages and auto_orchestrator was pending,
            # clear the flag since we successfully processed it
            if self.auto_orchestrator_pending:
                if messages:
                    # Architect (or someone) responded - success!
                    logger.info("[run_conversation] Auto-orchestrator handled successfully")
                    self.auto_orchestrator_pending = False
                    self.auto_orchestrator_retries = 0
                else:
                    # No response this round, increment retry counter
                    self.auto_orchestrator_retries += 1
                    logger.warning(f"[run_conversation] No response to auto-orchestrator, retry {self.auto_orchestrator_retries}")
                    if self.auto_orchestrator_retries >= 5:
                        # Give up after 5 retries to prevent infinite loops
                        logger.error("[run_conversation] Giving up on auto-orchestrator after 5 retries")
                        self.auto_orchestrator_pending = False
                        self.auto_orchestrator_retries = 0
        except Exception as e:
            logger.error(f"[run_conversation] Error: {e}")
        finally:
            self.is_processing = False
            self._tick_in_progress = False  # Clear tick guard to allow next tick
            self.refresh_panels()

    async def handle_command(self, line: str):
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ["/quit", "/exit", "/q"]:
            self.exit()
        elif cmd == "/help":
            self.chat_log.write(Text("─" * 50, style="dim"))
            self.chat_log.write(Text("COMMANDS:", style="yellow bold"))
            self.chat_log.write(Text("  /help     - Show this help", style="dim"))
            self.chat_log.write(Text("  /settings - Open settings (Ctrl+S)", style="dim"))
            self.chat_log.write(Text("  /tasks    - View tasks (Ctrl+T)", style="dim"))
            self.chat_log.write(Text("  /files    - Browse project files (Ctrl+F)", style="dim"))
            self.chat_log.write(Text("  /stop     - Stop current (Ctrl+X)", style="dim"))
            self.chat_log.write(Text("  /plan     - Refresh dashboard (Ctrl+P)", style="dim"))
            self.chat_log.write(Text("  /devplan  - Show raw devplan.md", style="dim"))
            self.chat_log.write(Text("  /spawn <role> - Spawn agent", style="dim"))
            self.chat_log.write(Text("  /model    - View/change agent models", style="dim"))
            self.chat_log.write(Text("  /status   - Show status", style="dim"))
            self.chat_log.write(Text("  /clear    - Clear chat", style="dim"))
            self.chat_log.write(Text("  /fix <reason> - Stop & request fix", style="dim"))
            self.chat_log.write(Text("  /snapshot - Snapshot current project folder", style="dim"))
            self.chat_log.write(Text("  /api      - View or change API provider", style="dim"))
            self.chat_log.write(Text("  /memdump  - Debug memory usage (leak detection)", style="dim"))
            self.chat_log.write(Text("─" * 50, style="dim"))
            self.chat_log.write(Text(f"Roles: {', '.join(AGENT_CLASSES.keys())}", style="dim"))
        elif cmd == "/settings":
            self.action_open_settings()
        elif cmd == "/tasks":
            self.action_open_tasks()
        elif cmd == "/stop":
            await self.action_stop_current()
        elif cmd == "/plan":
            self.action_refresh_plan()
        elif cmd == "/devplan":
            # Show the raw devplan.md content in chat
            try:
                devplan_path = get_scratch_dir() / "shared" / "devplan.md"
                if devplan_path.exists():
                    content = devplan_path.read_text(encoding='utf-8')
                    self.chat_log.write(Text("─" * 50, style="dim"))
                    self.chat_log.write(Text("📋 DEVPLAN.MD (Architect's Internal Tracker):", style="yellow bold"))
                    self.chat_log.write(Text("─" * 50, style="dim"))
                    # Show first 2000 chars to avoid flooding
                    if len(content) > 2000:
                        self.chat_log.write(Text(content[:2000] + "\n... (truncated)", style="dim"))
                    else:
                        self.chat_log.write(Text(content, style="dim"))
                    self.chat_log.write(Text("─" * 50, style="dim"))
                else:
                    self.chat_log.write(Text("No devplan.md found yet.", style="yellow"))
            except Exception as e:
                self.chat_log.write(Text(f"Error reading devplan: {e}", style="red"))
        elif cmd == "/files":
            self.action_open_files()
        elif cmd == "/status":
            status = self.chatroom.get_status()
            tracker = get_token_tracker()
            stats = tracker.get_stats()
            self.chat_log.write(Text(f"Agents: {len(status['active_agents'])} | Msgs: {status['message_count']} | Tokens: {stats['total_tokens']:,}", style="cyan"))
        elif cmd == "/memdump":
            # Immediate memory dump for debugging leaks
            try:
                from core.memory_profiler import dump_memory_report, get_memory_mb
                self.chat_log.write(Text(f"🧠 Memory: {get_memory_mb():.1f} MB - generating full dump...", style="yellow"))
                report = dump_memory_report()
                # Write to log file
                from pathlib import Path
                log_path = Path("logs") / f"memdump_{datetime.now().strftime('%H%M%S')}.log"
                log_path.parent.mkdir(exist_ok=True)
                log_path.write_text(report, encoding='utf-8')
                self.chat_log.write(Text(f"📝 Memory dump saved to {log_path}", style="green"))
                # Show summary in chat
                for line in report.split('\n')[:20]:
                    self.chat_log.write(Text(line, style="dim"))
                self.chat_log.write(Text("... (see full dump in log file)", style="dim"))
            except Exception as e:
                self.chat_log.write(Text(f"Error: {e}", style="red"))
        elif cmd == "/spawn":
            if arg and arg in AGENT_CLASSES:
                settings = get_settings()
                model = settings.get("swarm_model", ARCHITECT_MODEL)
                agent = await self.chatroom.spawn_agent(arg, model=model)
                if agent:
                    self.agents.append(agent)
                    self.create_agent_card(agent)
                    icon = AGENT_ICONS.get(agent.name, "🤖")
                    self.chat_log.write(Text(f"{icon} {agent.name} joined!", style="green"))
            else:
                self.chat_log.write(Text(f"Usage: /spawn <role>", style="yellow"))
        elif cmd == "/model":
            await self.action_model(arg)
        elif cmd == "/snapshot":
            await self.action_snapshot(arg)
        elif cmd in ("/api", "/command"):
            await self.action_api(arg)
        elif cmd == "/clear":
            self.chat_log.clear()
        elif cmd == "/fix":
            reason = arg if arg else "I need to make changes to the current approach."
            await self.send_message(f"STOP! {reason} Please pause and let me clarify.")
            self.notify("Fix requested", severity="warning")
        else:
            self.chat_log.write(Text(f"Unknown: {cmd}. Try /help", style="red"))

    # ─────────────────────────────────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────────────────────────────────

    def action_open_settings(self):
        def on_dismiss(result):
            if result:
                self.notify("Settings saved")
                settings = get_settings()
                self.username = settings.get("username", "You")
                self.update_status_line()
        self.push_screen(SettingsScreen(), on_dismiss)

    def action_open_files(self):
        self.push_screen(FileBrowserScreen())

    def action_open_tasks(self):
        # Simple task display in chat for now
        tm = get_task_manager()
        tasks = tm.get_all_tasks()
        self.chat_log.write(Text("─" * 50, style="dim"))
        self.chat_log.write(Text("TASKS:", style="yellow bold"))
        icons = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}
        for task in tasks[-10:]:
            icon = icons.get(task.status.value, "?")
            self.chat_log.write(Text(f"  {icon} {task.description[:50]}...", style="dim"))
        self.chat_log.write(Text("─" * 50, style="dim"))

    async def action_stop_current(self):
        if self.is_processing:
            tm = get_task_manager()
            for task in tm.get_all_tasks():
                if task.status.value == "in_progress":
                    tm.update_task_status(task.id, "failed")
            self.notify("Stop requested", severity="warning")
            self.chat_log.write(Text("⏹ Stop requested", style="red"))
        else:
            self.notify("Nothing processing")

    def action_refresh_plan(self):
        self.devplan_panel.refresh_plan()
        self.notify("Plan refreshed")

    def action_refresh(self):
        self.refresh_panels()

    def action_show_help(self):
        self.chat_log.write(Text("F1:Help | Ctrl+S:Settings | Ctrl+T:Tasks | Ctrl+X:Stop | Ctrl+P:Plan | Ctrl+Q:Quit", style="yellow"))

    @on(Button.Pressed, "#stop-btn")
    async def on_stop_button(self):
        await self.action_stop_current()

    @on(Button.Pressed, "#files-btn")
    def on_files_button(self):
        self.action_open_files()

    async def action_snapshot(self, label: str = ""):
        """Create a snapshot of the current project folder.

        Copies the entire contents of the project's root folder into a
        timestamped directory under a shared "snapshots" folder located in
        the parent of the project root (sibling to all project folders).
        """
        try:
            project_root: Path = self.project.root
            projects_parent = project_root.parent

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_label = "".join(c if c.isalnum() or c in "-_" else "_" for c in label).strip("_")
            suffix = f"_{safe_label}" if safe_label else ""

            snapshots_root = projects_parent / "snapshots"
            dest = snapshots_root / f"{self.project.name}{suffix}_{ts}"

            snapshots_root.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                self.chat_log.write(Text(f"❌ Snapshot path already exists: {dest}", style="red"))
                return

            self.chat_log.write(Text(f"🗂️ Creating snapshot at {dest} ...", style="dim"))

            # Run copytree in a background thread to avoid blocking the UI
            await asyncio.to_thread(shutil.copytree, project_root, dest)

            self.chat_log.write(Text("✅ Snapshot created", style="green"))
        except Exception as e:
            self.chat_log.write(Text(f"❌ Snapshot failed: {e}", style="red"))

    async def action_api(self, arg: str):
        from core.settings_manager import get_settings

        settings = get_settings()
        arg = arg.strip()

        if not arg:
            custom_base = (settings.get("api_base_url", "") or "").strip()
            custom_key = (settings.get("api_key", "") or "").strip()
            active_base = custom_base or REQUESTY_API_BASE_URL
            using_custom = bool(custom_base or custom_key)

            self.chat_log.write(Text("─" * 50, style="dim"))
            self.chat_log.write(Text("API PROVIDER:", style="yellow bold"))
            self.chat_log.write(Text(f"  Active base URL: {active_base}", style="dim"))
            source = "Custom settings (api_base_url/api_key)" if using_custom else "Requesty (.env)"
            self.chat_log.write(Text(f"  Source: {source}", style="dim"))
            self.chat_log.write(Text("Usage:", style="yellow"))
            self.chat_log.write(Text("  /api <base_url> <api_key>", style="dim"))
            self.chat_log.write(Text("  /api reset            (switch back to Requesty/env)", style="dim"))
            self.chat_log.write(Text("─" * 50, style="dim"))
            return

        lower = arg.lower()
        if lower in ("reset", "clear", "default"):
            settings.set("api_base_url", "")
            settings.set("api_key", "")
            self.chat_log.write(Text("API provider reset to Requesty (.env)", style="green"))
            return

        parts = arg.split()
        if len(parts) < 2:
            self.chat_log.write(Text("Usage: /api <base_url> <api_key>", style="yellow"))
            return

        base_url = parts[0].strip()
        api_key = " ".join(parts[1:]).strip()

        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            self.chat_log.write(Text("Base URL must start with http:// or https://", style="red"))
            return

        settings.set("api_base_url", base_url)
        settings.set("api_key", api_key)
        self.chat_log.write(Text("Custom API provider configured for future calls.", style="green"))

    async def action_model(self, arg: str):
        """View or change per-agent models.

        Usage:
          /model                      - list agents and their models
          /model <agent> <model>      - set model for a specific agent

        <agent> can be the full name ("Codey McBackend") or a case-insensitive
        prefix. <model> must be one of AVAILABLE_MODELS.
        """
        agents = list(self.chatroom._agents.values()) if self.chatroom else []
        if not agents:
            self.chat_log.write(Text("No agents are active yet.", style="yellow"))
            return

        from core.settings_manager import get_settings
        settings = get_settings()

        if not arg:
            # List current models
            self.chat_log.write(Text("─" * 50, style="dim"))
            self.chat_log.write(Text("AGENT MODELS:", style="yellow bold"))
            for a in agents:
                self.chat_log.write(Text(f"  {a.name}: {a.model}", style="dim"))
            self.chat_log.write(Text("Available:", style="yellow"))
            for m in AVAILABLE_MODELS:
                self.chat_log.write(Text(f"  - {m}", style="dim"))
            self.chat_log.write(Text("Usage: /model <agent> <model>", style="dim"))
            self.chat_log.write(Text("─" * 50, style="dim"))
            return

        # Parse "agent model" using rsplit so agent names may contain spaces
        try:
            agent_spec, model_spec = arg.rsplit(maxsplit=1)
        except ValueError:
            self.chat_log.write(Text("Usage: /model <agent> <model>", style="yellow"))
            return

        agent_spec = agent_spec.strip()
        model_spec = model_spec.strip()

        if model_spec not in AVAILABLE_MODELS:
            self.chat_log.write(Text(f"Unknown model: {model_spec}", style="red"))
            self.chat_log.write(Text("Available models:", style="yellow"))
            for m in AVAILABLE_MODELS:
                self.chat_log.write(Text(f"  - {m}", style="dim"))
            return

        # Find matching agent (exact name or prefix, case-insensitive)
        target = None
        agent_spec_lower = agent_spec.lower()
        for a in agents:
            name_lower = a.name.lower()
            if name_lower == agent_spec_lower or name_lower.startswith(agent_spec_lower):
                target = a
                break

        if not target:
            self.chat_log.write(Text(f"Agent not found for spec: {agent_spec}", style="red"))
            self.chat_log.write(Text("Active agents:", style="yellow"))
            for a in agents:
                self.chat_log.write(Text(f"  - {a.name}", style="dim"))
            return

        # Apply override in-memory
        old_model = target.model
        target.model = model_spec

        # Persist override in settings
        agent_models = settings.get("agent_models", {}) or {}
        agent_models[target.name] = model_spec
        settings.set("agent_models", agent_models)

        self.chat_log.write(Text(f"🧠 Model for {target.name} changed from {old_model} to {model_spec}", style="green"))

    async def halt_agent(self, agent):
        """Halt a specific agent's current work and prompt the Architect to adjust.

        This is invoked from AgentCard via right-click. It marks any of the
        agent's in-progress tasks as failed and injects a human message asking
        Bossy McArchitect to respond to why the user stopped this worker.
        """
        try:
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            halted = 0
            for task in tm.get_all_tasks():
                if task.assigned_to == agent.agent_id and task.status.value == "in_progress":
                    tm.update_task_status(task.id, "failed", result="Stopped by user via dashboard")
                    halted += 1

            reason = f"I just halted {agent.name}'s current work in the dashboard. Please briefly explain what they were doing, whether anything needs to be rolled back, and then adjust the devplan/tasks accordingly."
            await self.chatroom.add_human_message(
                content=reason,
                username=self.username,
                user_id="dashboard_user",
            )
            self.is_processing = True
            self.run_conversation()

            msg = f"⏹ Halt requested for {agent.name} ({halted} task(s) marked failed)."
            self.chat_log.write(Text(msg, style="yellow"))
        except Exception as e:
            self.chat_log.write(Text(f"⚠️ Failed to halt {agent.name}: {e}", style="red"))

    async def action_quit(self):
        # Stop Traffic Control relay
        if hasattr(self, 'traffic_relay') and self.traffic_relay:
            await self.traffic_relay.stop()
        if self.chatroom:
            await self.chatroom.shutdown()
        self.exit()


# ─────────────────────────────────────────────────────────────────────────────
# PROJECT SELECTION & MAIN
# ─────────────────────────────────────────────────────────────────────────────

def select_project_cli() -> tuple[Project, str, bool, bool]:
    """CLI project selection before launching TUI.
    
    Returns:
        Tuple of (project, username, load_history, devussy_mode)
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    pm = get_project_manager()
    projects = pm.list_projects()
    last_project = pm.get_last_project()
    settings = get_settings()
    devussy_mode = False

    console.print()
    console.print(Panel("[bold cyan]🚀 AGENT SWARM DASHBOARD[/bold cyan]", style="cyan"))
    console.print()

    console.print("[bold]Select Project:[/bold]")
    if projects:
        for i, proj in enumerate(projects, 1):
            marker = " [green](last)[/green]" if proj.name == last_project else ""
            console.print(f"  [yellow]{i}.[/yellow] {proj.name}{marker}")
    else:
        console.print("  [dim]No existing projects[/dim]")
    console.print(f"  [green]N.[/green] Create new project")
    console.print()

    choice = input("Choice (Enter for default): ").strip()

    if choice.upper() == "N":
        name = input("Project name: ").strip() or "default"
        desc = input("Description (optional): ").strip()
        project = pm.create_project(name, desc)
    elif choice.isdigit() and 0 < int(choice) <= len(projects):
        project = projects[int(choice) - 1]
    elif last_project and pm.project_exists(last_project):
        project = pm.load_project(last_project)
    elif projects:
        project = projects[0]
    else:
        project = pm.create_project("default")

    pm.set_current(project)
    console.print(f"[green]✓ Using project: {project.name}[/green]")
    console.print()

    # Ask about Devussy pipeline
    console.print()
    console.print(Panel(
        "[bold magenta]🔮 DEVUSSY PIPELINE[/bold magenta]\n"
        "[dim]Generate a structured development plan before starting the swarm.\n"
        "The swarm will execute the generated plan phase by phase.[/dim]",
        style="magenta"
    ))
    
    # Check if devussy is available
    try:
        from core.devussy_integration import (
            check_devussy_available, 
            run_devussy_pipeline_sync,
            run_devussy_with_resume_option,
            load_devplan_for_swarm,
            select_devussy_model,
        )
        devussy_available = check_devussy_available()
    except ImportError:
        devussy_available = False
    
    if devussy_available:
        # Check if project already has a devplan
        existing_devplan = load_devplan_for_swarm(Path(project.root))
        
        if existing_devplan and existing_devplan.get("has_devplan"):
            console.print("[green]✓ Existing devplan found in project[/green]")
            devussy_choice = input("Run Devussy pipeline? [y/N/use existing=Enter]: ").strip().lower()
            if devussy_choice in ("y", "yes"):
                # Let user select model for pipeline
                devussy_model = select_devussy_model()
                saved_model = devussy_model or settings.get("devussy_model")
                if devussy_model:
                    settings.set("devussy_model", devussy_model)
                
                console.print("\n[magenta]Starting Devussy pipeline...[/magenta]\n")
                success, message = run_devussy_with_resume_option(
                    Path(project.root), 
                    verbose=False,
                    model=saved_model,
                )
                if success:
                    console.print(f"[green]✓ {message}[/green]")
                    devussy_mode = True
                else:
                    console.print(f"[red]✗ {message}[/red]")
                    console.print("[yellow]Continuing without devussy...[/yellow]")
            elif devussy_choice in ("n", "no"):
                console.print("[dim]Skipping devussy, starting normal swarm mode[/dim]")
            else:
                # Use existing devplan
                console.print("[green]✓ Using existing devplan[/green]")
                devussy_mode = True
        else:
            devussy_choice = input("Run Devussy pipeline to create a development plan? [y/N]: ").strip().lower()
            if devussy_choice in ("y", "yes"):
                # Let user select model for pipeline
                devussy_model = select_devussy_model()
                saved_model = devussy_model or settings.get("devussy_model")
                if devussy_model:
                    settings.set("devussy_model", devussy_model)
                
                console.print("\n[magenta]Starting Devussy pipeline...[/magenta]\n")
                success, message = run_devussy_with_resume_option(
                    Path(project.root), 
                    verbose=False,
                    model=saved_model,
                )
                if success:
                    console.print(f"[green]✓ {message}[/green]")
                    devussy_mode = True
                else:
                    console.print(f"[red]✗ {message}[/red]")
                    console.print("[yellow]Continuing without devussy...[/yellow]")
            else:
                console.print("[dim]Skipping devussy, starting normal swarm mode[/dim]")
    else:
        console.print("[yellow]Devussy not available (missing dependencies)[/yellow]")
    
    console.print()

    saved_username = settings.get("username", "You")
    username = input(f"Your name [{saved_username}]: ").strip()
    if username:
        settings.set("username", username[:20])
    else:
        username = saved_username

    # Ask whether to load previous chat history for this project
    default_load = settings.get("load_previous_history", True)
    default_label = "Y/n" if default_load else "y/N"
    choice = input(f"Load previous messages? [{default_label}]: ").strip().lower()
    if choice in ("y", "yes"):
        load_history = True
    elif choice in ("n", "no"):
        load_history = False
    else:
        load_history = default_load

    settings.set("load_previous_history", load_history)
    
    # Store devussy mode in settings for the session
    settings.set("devussy_mode", devussy_mode)

    console.print()
    if devussy_mode:
        console.print("[magenta]Starting in DEVUSSY MODE - Architect will follow the devplan[/magenta]")
    console.print("[dim]Starting dashboard... (Ctrl+Q to quit)[/dim]")
    console.print()

    return project, username[:20], load_history, devussy_mode


def main():
    """Entry point."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_dir / f"tui_{timestamp}.log", encoding="utf-8")],
    )
    
    # Silence verbose third-party libraries that spam DEBUG logs
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    is_valid, errors = validate_config()
    if not is_valid:
        for error in errors:
            print(f"Error: {error}")
        return

    project, username, load_history, devussy_mode = select_project_cli()
    app = SwarmDashboard(
        project=project, 
        username=username, 
        load_history=load_history,
        devussy_mode=devussy_mode
    )
    app.run()


if __name__ == "__main__":
    main()
