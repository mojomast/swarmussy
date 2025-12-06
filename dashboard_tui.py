"""
Textual-based Dashboard for Multi-Agent Chatroom.

Full-featured TUI with scrollable panels, per-agent status, token tracking, and devplan.
"""

import asyncio
import logging
import sys
import os
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

from config.settings import validate_config, ARCHITECT_MODEL, AVAILABLE_MODELS, get_scratch_dir
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
        max-width: 280;
        height: 85%;
        max-height: 50;
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
                            yield Label("Architect Model:")
                            yield Select([(m, m) for m in AVAILABLE_MODELS], value=settings.get("architect_model", AVAILABLE_MODELS[0]), id="architect-model-select")
                            yield Label("Worker Model:")
                            yield Select([(m, m) for m in AVAILABLE_MODELS], value=settings.get("swarm_model", AVAILABLE_MODELS[0]), id="swarm-model-select")
                    
                    with TabPane("Advanced", id="advanced-tab"):
                        with Vertical():
                            with Horizontal(classes="settings-row"):
                                yield Label("Max Tokens:", classes="settings-label")
                                yield Input(value=str(settings.get("max_tokens", 100000)), id="max-tokens-input", classes="settings-input")
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
        settings.set("username", self.query_one("#username-input", Input).value, auto_save=False)
        settings.set("auto_chat", self.query_one("#auto-chat-switch", Switch).value, auto_save=False)
        settings.set("tools_enabled", self.query_one("#tools-switch", Switch).value, auto_save=False)
        settings.set("architect_model", self.query_one("#architect-model-select", Select).value, auto_save=False)
        settings.set("swarm_model", self.query_one("#swarm-model-select", Select).value, auto_save=False)
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
        """Toggle expanded/collapsed view for this agent card."""
        # Stop event so parent containers don't also handle the click
        try:
            event.stop()
        except Exception:
            pass
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
        
        # Tokens
        content.append(f"Tokens: {self.tokens_used:,}\n", style="dim")
        
        # Current Action (Granular)
        if self.current_action:
            content.append(f"Action: {self.current_action}\n", style="bold cyan")
        
        # Task
        task = getattr(self.agent, 'current_task_description', '')
        content.append("\nTask:\n", style="bold yellow")
        if task:
            content.append(f"{task}\n")
        else:
            content.append("No task assigned\n", style="dim")
        
        # Accomplishments
        if self.accomplishments:
            content.append("\nLatest:\n", style="bold white")
            if self.expanded:
                items = self.accomplishments[-self._max_history:]
            else:
                items = self.accomplishments[-3:]
            for acc in items:
                content.append(f"✓ {acc}\n", style="green")
        
        # Update with a panel
        self.update(Panel(content, title=title, border_style=border_style))


class DevPlanPanel(Static):
    """Panel displaying the master plan and todo list."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.plan_content = "Loading..."
    
    def refresh_plan(self):
        """Load the master plan from file."""
        try:
            devplan_path = get_scratch_dir() / "shared" / "devplan.md"
            plan_path = get_scratch_dir() / "shared" / "master_plan.md"
            todo_path = get_scratch_dir() / "shared" / "todo.md"
            
            content_parts = []
            
            # Prefer live devplan dashboard if present
            if devplan_path.exists():
                content = devplan_path.read_text(encoding='utf-8')
                content_parts.append(content)
            elif plan_path.exists():
                content = plan_path.read_text(encoding='utf-8')
                content_parts.append(content)
            else:
                content_parts.append(
                    "No devplan.md or master_plan.md yet.\n\n"
                    "Ask the Architect:\n"
                    "  'Create a plan and devplan dashboard for [your project]'\n\n"
                    "The plan and dashboard will appear here."
                )
            
            if todo_path.exists():
                todo_content = todo_path.read_text(encoding='utf-8')
                content_parts.append("\n\n════════════════════════════════════════════════════════════\n")
                content_parts.append("TODO LIST (scratch/shared/todo.md)\n")
                content_parts.append("════════════════════════════════════════════════════════════\n")
                content_parts.append(todo_content)
            
            self.plan_content = "\n".join(content_parts)
            
        except Exception as e:
            self.plan_content = f"Error loading plan: {e}"
        
        self.update(self.plan_content)


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
        toggle = "[-]" if self.expanded else "[+]"
        
        self.header_text = f"{toggle} [{timestamp}] {status_icon} {short_name} {elapsed:.1f}s [{total:,} tok]"
        if preview:
            self.header_text += f'\n    ← "{preview}..."'
        
        self._update_display()
    
    def _update_display(self):
        """Update the display."""
        lines = [self.header_text]
        
        if self.expanded and self.has_response:
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
            
            # Show messages (full content when expanded)
            messages = self.request_data.get("messages", [])
            lines.append("")
            lines.append(f"  Messages ({len(messages)}):")
            for i, msg in enumerate(messages):
                role = msg.get("role", "?")
                content = msg.get("content") or ""
                lines.append(f"  ┌─[{i+1}] {role.upper()}")
                # Show full content, wrapped
                content_lines = content.split('\n')
                for cl in content_lines:  # Show all lines
                    lines.append(f"  │ {cl}")
                lines.append(f"  └─────")
            
            lines.append("")
            lines.append("═══ RESPONSE ═══")
            
            usage = self.response_data.get("usage", {})
            elapsed = self.response_data.get("elapsed", 0)
            lines.append(f"  Time: {elapsed:.2f}s")
            lines.append(f"  Prompt Tokens: {usage.get('prompt_tokens', 0):,}")
            lines.append(f"  Completion Tokens: {usage.get('completion_tokens', 0):,}")
            lines.append(f"  Total Tokens: {usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0):,}")
            
            # Show response content (full when expanded)
            full_response = self.response_data.get("full_response", "")
            if full_response:
                lines.append("")
                lines.append("  Content:")
                lines.append("  ┌─────")
                response_lines = full_response.split('\n')
                for rl in response_lines:  # Show all lines
                    lines.append(f"  │ {rl}")
                lines.append("  └─────")
            
            # Show tool calls (full details when expanded)
            tool_calls = self.response_data.get("tool_calls", [])
            if tool_calls:
                lines.append("")
                lines.append(f"  Tool Calls ({len(tool_calls)}):")
                for tc in tool_calls:
                    func = tc.get("function", {})
                    name = func.get("name", "?")
                    args = func.get("arguments", "")
                    lines.append(f"  ┌─ {name}")
                    # Parse and show args nicely
                    try:
                        import json
                        args_dict = json.loads(args) if args else {}
                        for k, v in args_dict.items():
                            v_str = str(v)
                            # Show full argument value
                            lines.append(f"  │   {k}: {v_str}")
                    except:
                        # Show full args string
                        lines.append(f"  │   {args}")
                    lines.append(f"  └─────")
            
            lines.append("═════════════════")
        
        self.update("\n".join(lines))
    
    def toggle_expand(self):
        """Toggle expanded state."""
        if self.has_response:
            self.expanded = not self.expanded
            # Update header toggle indicator
            if self.expanded:
                self.header_text = self.header_text.replace("[+]", "[-]", 1)
            else:
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
        grid-columns: 1.8fr 3.2fr 2.0fr;  /* Wider sidebars */
    }

    /* LEFT SIDEBAR - Agent Cards (full height) */
    #left-sidebar {
        height: 100%;
        layout: vertical;
        border: solid $primary;
        padding: 0;
    }
    
    #agents-scroll {
        height: 1fr;
        border-bottom: solid $primary-darken-2;
        overflow: auto;
    }
    
    #agents-container {
        width: 100%;
        padding: 1;
    }
    
    .agent-card {
        width: 100%;
        height: auto;
        min-height: 8;  /* Increased height for details */
        margin-bottom: 1;
        padding: 0;
        overflow: hidden;
    }
    
    ApiLogEntry {
        width: 100%;
        height: auto;
        padding: 0;
        margin-bottom: 1;
        border: solid $primary-darken-3;
    }
    
    ApiLogEntry:hover {
        background: $primary-darken-2;
    }

    /* CENTER - Chat */
    #center {
        height: 100%;
        layout: vertical;
    }

    #chat-log {
        height: 1fr;
        border: solid $success;
        padding: 1;
        width: 100%;
        overflow: auto;
    }
    
    RichLog {
        width: 100%;
        overflow: auto;
        scrollbar-gutter: stable;
    }
    
    #chat-log > * {
        width: 100%;
    }

    #input-box {
        height: 3;
        padding: 0 1;
    }

    /* RIGHT SIDEBAR - Tokens+Tools (top), Plan + API Log (bottom) */
    #right-sidebar {
        height: 100%;
        layout: vertical;
        border: solid $warning;
        padding: 0;
    }

    #tokens-tools-row {
        height: 16;
        layout: horizontal;
        border-bottom: solid $warning-darken-2;
    }

    #tokens-scroll {
        width: 34;  /* Fixed width for tokens */
        height: 100%;
        border-right: solid $warning-darken-2;
        padding: 0 1;
        overflow: auto;
    }

    #tools-scroll {
        width: 1fr;  /* Remaining space for tools */
        height: 100%;
        padding: 0 1;
        overflow: auto;
    }

    #plan-scroll {
        height: 0.7fr;  /* Majority of remaining height for DevPlan */
        padding: 1;
        overflow: auto;
    }

    #api-log-scroll {
        height: 0.3fr;  /* Lower portion of right sidebar under DevPlan */
        padding: 1;
        overflow-y: auto;
        overflow-x: auto;
    }

    #api-log-container {
        width: 100%;
        height: auto;
        padding: 0;
    }

    .section-title {
        text-style: bold;
        background: $primary-darken-2;
        padding: 0 1;
        width: 100%;
    }

    Input {
        width: 100%;
    }
    
    ScrollableContainer {
        scrollbar-gutter: stable;
    }
    
    #stop-btn {
        dock: bottom;
        width: 100%;
        margin: 1;
    }
    
    /* Ensure text doesn't get cut off */
    Static {
        width: 100%;
    }
    
    TokenDetailPanel {
        width: 100%;
    }
    
    DevPlanPanel {
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+s", "open_settings", "Settings"),
        Binding("ctrl+t", "open_tasks", "Tasks"),
        Binding("ctrl+x", "stop_current", "Stop"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+p", "refresh_plan", "Plan"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+a", "focus_agents", "Agents"),
        Binding("ctrl+up", "scroll_agents_up", "Agents ▲"),
        Binding("ctrl+down", "scroll_agents_down", "Agents ▼"),
    ]

    api_status = reactive("idle")

    def __init__(self, project: Project, username: str = "You", load_history: bool = True):
        super().__init__()
        self.project = project
        self.username = username
        # Whether to load prior chat history from disk on startup
        self.load_history = load_history
        self.chatroom: Optional[Chatroom] = None
        self.agents = []
        self.agent_cards: Dict[str, AgentCard] = {}
        self.is_processing = False

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

        # LEFT - Agent cards (full column)
        with Vertical(id="left-sidebar"):
            with ScrollableContainer(id="agents-scroll"):
                yield Label("🤖 AGENTS", classes="section-title")
                with Vertical(id="agents-container"):
                    yield Static("Loading agents...", id="agents-placeholder")

        # CENTER - Chat
        with Vertical(id="center"):
            yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
            with Container(id="input-box"):
                yield Input(placeholder="Type message or /help...", id="chat-input")

        # RIGHT - Tokens+Tools (side by side), DevPlan + API Log below
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
            with ScrollableContainer(id="api-log-scroll"):
                yield Label("📡 API LOG (click to expand)", classes="section-title")
                yield Vertical(id="api-log-container")
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
        self.api_log_container = self.query_one("#api-log-container", Vertical)
        self.api_log_entries: Dict[str, ApiLogEntry] = {}
        self.api_entry_counter = 0
        self.current_request_id = None
        
        # Set up API logging callback
        set_api_log_callback(self.on_api_call)

        self.query_one("#chat-input", Input).focus()
        await self.init_chatroom()
        self.set_interval(3.0, self.refresh_panels)

    async def init_chatroom(self):
        settings = get_settings()
        # Respect user preference for loading previous history
        self.chatroom = Chatroom(load_history=self.load_history)
        set_chatroom(self.chatroom)
        self.chatroom.on_tool_call = self.on_tool_call

        model = settings.get("architect_model", ARCHITECT_MODEL)
        architect = create_agent("architect", model=model)
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

        # Create agent card
        self.create_agent_card(architect)

        self.chat_log.write(Text("🏗️ Bossy McArchitect joined the swarm", style="green"))
        self.chat_log.write(Text("Ctrl+S: Settings | Ctrl+T: Tasks | Ctrl+X: Stop | Ctrl+P: Refresh Plan", style="dim"))
        self.refresh_panels()

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
        
        if event_type == "request":
            self.api_status = "request"
            self.set_timer(0.7, lambda: setattr(self, "api_status", "idle"))
            # Create new entry for this request
            self.api_entry_counter += 1
            entry_id = f"api-entry-{self.api_entry_counter}"
            self.current_request_id = entry_id
            
            entry = ApiLogEntry(entry_id)
            entry.set_request(timestamp, agent_name, data)
            self.api_log_entries[entry_id] = entry
            self.api_log_container.mount(entry)
            
            # Keep only last 50 entries to prevent memory issues
            if len(self.api_log_entries) > 50:
                oldest_id = list(self.api_log_entries.keys())[0]
                oldest_entry = self.api_log_entries.pop(oldest_id)
                oldest_entry.remove()
                
        elif event_type == "response":
            self.api_status = "response"
            self.set_timer(0.9, lambda: setattr(self, "api_status", "idle"))
            # Update the current request entry with response
            if self.current_request_id and self.current_request_id in self.api_log_entries:
                entry = self.api_log_entries[self.current_request_id]
                entry.set_response(timestamp, agent_name, data)
                
                # Update agent card tokens
                status = data.get("status", "?")
                usage = data.get("usage", {})
                total = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
                
                if status == 200 and total > 0:
                    for card in self.agent_cards.values():
                        if agent_name and agent_name in card.agent.name:
                            card.add_tokens(total)
                            break
            
            self.current_request_id = None
                
        elif event_type == "error":
            self.api_status = "error"
            self.set_timer(1.2, lambda: setattr(self, "api_status", "idle"))
            # Update current entry with error
            if self.current_request_id and self.current_request_id in self.api_log_entries:
                entry = self.api_log_entries[self.current_request_id]
                error_data = {
                    "status": "error",
                    "usage": {},
                    "elapsed": data.get("elapsed", 0),
                    "preview": data.get("error", "Unknown error"),
                    "full_response": data.get("error", "Unknown error"),
                    "tool_calls": []
                }
                entry.set_response(timestamp, agent_name, error_data)
            
            self.current_request_id = None

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
                    self.on_tool_call(agent_name, action)
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
        # Don't write here - on_chat_message callback handles display
        await self.chatroom.add_human_message(content=content, username=self.username, user_id="dashboard_user")
        self.is_processing = True
        self.run_conversation()

    @work(exclusive=True)
    async def run_conversation(self):
        try:
            await self.chatroom.run_conversation_round()
        finally:
            self.is_processing = False
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
            self.chat_log.write(Text("  /stop     - Stop current (Ctrl+X)", style="dim"))
            self.chat_log.write(Text("  /plan     - Refresh devplan (Ctrl+P)", style="dim"))
            self.chat_log.write(Text("  /spawn <role> - Spawn agent", style="dim"))
            self.chat_log.write(Text("  /status   - Show status", style="dim"))
            self.chat_log.write(Text("  /clear    - Clear chat", style="dim"))
            self.chat_log.write(Text("  /fix <reason> - Stop & request fix", style="dim"))
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
        elif cmd == "/status":
            status = self.chatroom.get_status()
            tracker = get_token_tracker()
            stats = tracker.get_stats()
            self.chat_log.write(Text(f"Agents: {len(status['active_agents'])} | Msgs: {status['message_count']} | Tokens: {stats['total_tokens']:,}", style="cyan"))
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

def select_project_cli() -> tuple[Project, str, bool]:
    """CLI project selection before launching TUI."""
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    pm = get_project_manager()
    projects = pm.list_projects()
    last_project = pm.get_last_project()
    settings = get_settings()

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

    console.print()
    console.print("[dim]Starting dashboard... (Ctrl+Q to quit)[/dim]")
    console.print()

    return project, username[:20], load_history


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

    is_valid, errors = validate_config()
    if not is_valid:
        for error in errors:
            print(f"Error: {error}")
        return

    project, username, load_history = select_project_cli()
    app = SwarmDashboard(project=project, username=username, load_history=load_history)
    app.run()


if __name__ == "__main__":
    main()
