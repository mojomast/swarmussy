"""
Enhanced Dashboard for Multi-Agent Chatroom.

Rich terminal UI with agent status, tasks, and chat.
Fullscreen layout with segmented panels for each bot.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.markdown import Markdown
    from rich.style import Style
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.columns import Columns
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not installed. Run: pip install rich")
    print("Falling back to basic mode...")

from config.settings import validate_config, AVAILABLE_MODELS
from core.chatroom import Chatroom
from core.models import Message, MessageRole, AgentStatus
from core.task_manager import get_task_manager
from core.token_tracker import get_token_tracker
from core.project_manager import get_project_manager, Project
from agents import create_agent, AGENT_CLASSES


# User style for messages (lime green)
USER_STYLE = "bold bright_green"

# Agent colors for Rich
AGENT_STYLES = {
    "Bossy McArchitect": "bold magenta",
    "Codey McBackend": "bold blue",
    "Codey McBackend 2": "bold blue",
    "Pixel McFrontend": "bold bright_magenta",
    "Pixel McFrontend 2": "bold bright_magenta",
    "Bugsy McTester": "bold green",
    "Bugsy McTester 2": "bold green",
    "Deployo McOps": "bold yellow",
    "Deployo McOps 2": "bold yellow",
    "Checky McManager": "bold cyan",
    "Docy McWriter": "bold red",
    "System": "dim white",
}

AGENT_ICONS = {
    "Bossy McArchitect": "🏗️",
    "Codey McBackend": "⚙️",
    "Codey McBackend 2": "⚙️",
    "Pixel McFrontend": "🎨",
    "Pixel McFrontend 2": "🎨",
    "Bugsy McTester": "🐛",
    "Bugsy McTester 2": "🐛",
    "Deployo McOps": "🚀",
    "Deployo McOps 2": "🚀",
    "Checky McManager": "📊",
    "Docy McWriter": "📝",
}


class DashboardUI:
    """Rich terminal dashboard for the agent swarm."""

    def __init__(self):
        self.console = Console()
        self.chatroom = None
        self.agents = []
        self.messages: List[Message] = []
        self.status_messages: List[str] = []  # Ephemeral status updates
        self.running = True
        self.username = "You"
        self.current_project = None
        self.live: Optional[Live] = None
        self.layout: Optional[Layout] = None
        self.use_live_display = True  # Toggle for live vs simple mode

    def setup_logging(self):
        """Configure logging to file only."""
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"dashboard_{timestamp}.log"

        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file, encoding="utf-8")],
        )
        return log_file

    def select_project(self) -> Project:
        """Interactive project selection at startup."""
        pm = get_project_manager()
        projects = pm.list_projects()
        last_project = pm.get_last_project()

        self.console.print()
        self.console.print(
            Panel("[bold cyan]SELECT PROJECT[/bold cyan]", style="cyan")
        )
        self.console.print()

        if projects:
            for i, proj in enumerate(projects, 1):
                marker = (
                    " [green](last used)[/green]" if proj.name == last_project else ""
                )
                self.console.print(f"  [yellow]{i}.[/yellow] {proj.name}{marker}")
        else:
            self.console.print("  [dim]No existing projects[/dim]")

        self.console.print(f"  [green]N.[/green] Create new project")
        self.console.print()

        choice = input("Enter choice (or press Enter for default): ").strip()

        if choice.upper() == "N":
            name = input("Project name: ").strip()
            if not name:
                name = "default"
            desc = input("Description (optional): ").strip()
            project = pm.create_project(name, desc)
        elif choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    project = projects[idx]
                else:
                    if last_project and pm.project_exists(last_project):
                        project = pm.load_project(last_project)
                    elif projects:
                        project = projects[0]
                    else:
                        project = pm.create_project("default")
            except ValueError:
                if last_project and pm.project_exists(last_project):
                    project = pm.load_project(last_project)
                elif projects:
                    project = projects[0]
                else:
                    project = pm.create_project("default")
        else:
            if last_project and pm.project_exists(last_project):
                project = pm.load_project(last_project)
            elif projects:
                project = projects[0]
            else:
                project = pm.create_project("default")

        pm.set_current(project)
        self.current_project = project
        self.console.print()
        self.console.print(f"[green]Using project: {project.name}[/green]")
        return project

    # ─────────────────────────────────────────────────────────────────────
    # LAYOUT CREATION
    # ─────────────────────────────────────────────────────────────────────

    def create_layout(self) -> Layout:
        """Create the fullscreen dashboard layout with fixed sizes."""
        layout = Layout(name="root", minimum_size=5)

        # Main vertical split: header, body, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1, minimum_size=20),
            Layout(name="footer", size=3),
        )

        # Body: left sidebar | main chat | right sidebar
        layout["body"].split_row(
            Layout(name="left_sidebar", size=28, minimum_size=25),
            Layout(name="main", ratio=2, minimum_size=40),
            Layout(name="right_sidebar", size=38, minimum_size=35),
        )

        # Left sidebar: orchestrator panel + agent cards (fixed heights)
        layout["left_sidebar"].split_column(
            Layout(name="orchestrator", size=10),
            Layout(name="agents_list", ratio=1, minimum_size=10),
        )

        # Right sidebar: tokens + tasks + activity log (fixed heights)
        layout["right_sidebar"].split_column(
            Layout(name="tokens", size=7),
            Layout(name="tasks", size=12),
            Layout(name="activity", ratio=1, minimum_size=8),
        )

        return layout

    def create_header(self) -> Panel:
        """Create the header panel."""
        proj_name = self.current_project.name if self.current_project else "No Project"
        tracker = get_token_tracker()
        stats = tracker.get_stats()
        
        header_text = Text()
        header_text.append("🚀 ", style="bold")
        header_text.append("AGENT SWARM DASHBOARD", style="bold white")
        header_text.append("  │  ", style="dim")
        header_text.append(f"📁 {proj_name}", style="cyan")
        header_text.append("  │  ", style="dim")
        header_text.append(f"👤 {self.username}", style="green")
        header_text.append("  │  ", style="dim")
        header_text.append(f"🪙 {stats['total_tokens']:,} tokens", style="yellow")
        header_text.append("  │  ", style="dim")
        header_text.append(f"📞 {stats['call_count']} calls", style="dim")

        return Panel(header_text, style="blue", box=box.DOUBLE)

    def create_orchestrator_panel(self) -> Panel:
        """Create the orchestrator (Architect) status panel with fixed height."""
        agents = list(self.chatroom._agents.values()) if self.chatroom else []
        architect = next((a for a in agents if "Architect" in a.name), None)

        lines = []
        if architect:
            icon = AGENT_ICONS.get(architect.name, "🏗️")
            status = "🟢 ACTIVE" if architect.status == AgentStatus.WORKING else "⚪ IDLE"
            lines.append(f"{icon} Bossy McArchitect")
            lines.append(f"Status: {status}")
            
            # Get latest architect activity
            arch_activity = [s for s in self.status_messages if "Architect" in s or "Bossy" in s][-2:]
            for s in arch_activity:
                lines.append(f"  {s[:22]}...")
        else:
            lines.append("No orchestrator")
        
        # Pad to exactly 6 lines for consistent height
        while len(lines) < 6:
            lines.append("")
        lines = lines[:6]  # Trim if too many
        
        content = Text("\n".join(lines), style="dim")
        return Panel(content, title="🎯 ORCHESTRATOR", border_style="magenta", box=box.ROUNDED, height=10)

    def create_agents_panel(self) -> Panel:
        """Create the swarm agents panel - simple list format for stability."""
        agents = list(self.chatroom._agents.values()) if self.chatroom else []
        workers = [a for a in agents if "Architect" not in a.name]

        lines = []
        if workers:
            for agent in workers[:8]:  # Max 8 workers shown
                icon = AGENT_ICONS.get(agent.name, "🤖")
                # Get first name only, truncate if needed
                name = agent.name.split()[0][:10]
                status = "🟢" if agent.status == AgentStatus.WORKING else "⚪"
                lines.append(f"{icon} {name:<10} {status}")
        else:
            lines.append("No workers yet")
            lines.append("Architect will spawn")
            lines.append("workers as needed")
        
        content = Text("\n".join(lines), style="dim")
        return Panel(content, title=f"🤖 WORKERS ({len(workers)})", border_style="blue", box=box.ROUNDED)

    def create_tokens_panel(self) -> Panel:
        """Create the token usage panel - fixed 5 lines."""
        tracker = get_token_tracker()
        stats = tracker.get_stats()

        lines = [
            f"Prompt:     {stats['prompt_tokens']:>10,}",
            f"Completion: {stats['completion_tokens']:>10,}",
            f"{'─' * 24}",
            f"Total:      {stats['total_tokens']:>10,}",
            f"API Calls:  {stats['call_count']:>10}",
        ]
        
        content = Text("\n".join(lines), style="dim")
        return Panel(content, title="📊 TOKENS", border_style="cyan", box=box.ROUNDED, height=7)

    def create_tasks_panel(self) -> Panel:
        """Create the tasks panel - fixed 8 lines."""
        tm = get_task_manager()
        tasks = tm.get_all_tasks()

        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄", 
            "completed": "✅",
            "failed": "❌",
        }

        lines = []
        if tasks:
            for task in tasks[-8:]:  # Show last 8 tasks
                icon = status_icons.get(task.status.value, "?")
                desc = task.description[:28]
                if len(task.description) > 28:
                    desc += "..."
                lines.append(f"{icon} {desc}")
        else:
            lines.append("No tasks yet")
            lines.append("Tasks appear when")
            lines.append("assigned by orchestrator")
        
        # Pad to 8 lines
        while len(lines) < 8:
            lines.append("")
        lines = lines[:8]
        
        content = Text("\n".join(lines), style="dim")
        return Panel(content, title="📋 TASKS", border_style="yellow", box=box.ROUNDED, height=12)

    def create_activity_panel(self) -> Panel:
        """Create the activity/status log panel - fixed lines."""
        lines = []
        
        # Show last 10 status messages
        recent = self.status_messages[-10:] if self.status_messages else []
        
        if recent:
            for msg in recent:
                # Let Rich handle wrapping; avoid manual truncation
                lines.append(msg)
        else:
            lines.append("Activity will appear here")
            lines.append("as agents work...")
        
        # Pad to consistent height
        while len(lines) < 12:
            lines.append("")
        
        content = Text("\n".join(lines), style="dim")
        return Panel(content, title="⚡ ACTIVITY", border_style="dim", box=box.ROUNDED)

    def create_chat_panel(self) -> Panel:
        """Create the main chat panel with consistent formatting."""
        lines = []

        # Show last 12 messages for live mode (fewer = more stable)
        display_messages = [m for m in self.messages if m.sender_id not in ("auto_summary", "status")][-12:]
        
        for msg in display_messages:
            timestamp = msg.timestamp.strftime("%H:%M")
            # Let Rich handle wrapping; avoid manual truncation here
            content = msg.content

            if msg.role == MessageRole.SYSTEM:
                lines.append(f"[{timestamp}] ⚙️ {content}")
            elif msg.role == MessageRole.HUMAN:
                lines.append(f"[{timestamp}] 👤 {msg.sender_name}: {content}")
            else:
                icon = AGENT_ICONS.get(msg.sender_name, "🤖")
                # Shorten agent name
                name = msg.sender_name.split()[0][:8]
                lines.append(f"[{timestamp}] {icon} {name}: {content}")

        if not display_messages:
            lines.append("💬 Chat will appear here...")
            lines.append("Type your message and press Enter.")
            lines.append("Use /help for commands.")

        chat_content = "\n".join(lines)
        return Panel(chat_content, title="💬 CHAT", border_style="green", box=box.ROUNDED)

    def create_footer(self) -> Panel:
        """Create the footer with input hint."""
        footer_text = Text()
        footer_text.append("  Type message + Enter", style="dim")
        footer_text.append("  │  ", style="dim")
        footer_text.append("/help", style="green")
        footer_text.append("  │  ", style="dim")
        footer_text.append("/settings", style="green")
        footer_text.append("  │  ", style="dim")
        footer_text.append("/status", style="green")
        footer_text.append("  │  ", style="dim")
        footer_text.append("/quit", style="red")

        return Panel(footer_text, style="dim", box=box.SIMPLE)

    def update_layout(self):
        """Update all panels in the layout."""
        if not self.layout:
            return

        self.layout["header"].update(self.create_header())
        self.layout["orchestrator"].update(self.create_orchestrator_panel())
        self.layout["agents_list"].update(self.create_agents_panel())
        self.layout["tokens"].update(self.create_tokens_panel())
        self.layout["tasks"].update(self.create_tasks_panel())
        self.layout["activity"].update(self.create_activity_panel())
        self.layout["main"].update(self.create_chat_panel())
        self.layout["footer"].update(self.create_footer())

    # ─────────────────────────────────────────────────────────────────────
    # MESSAGE HANDLING
    # ─────────────────────────────────────────────────────────────────────

    def message_callback(self, message: Message):
        """Callback for new messages."""
        # Skip auto-summary requests
        if message.sender_id == "auto_summary":
            return
            
        # Handle status messages separately
        if message.sender_id == "status":
            self.status_messages.append(message.content)
            # Keep only last 50 status messages
            if len(self.status_messages) > 50:
                self.status_messages = self.status_messages[-50:]
            if not self.use_live_display:
                self.console.print(f"[dim]{message.content}[/dim]")
            return

        self.messages.append(message)
        
        # In simple mode, print directly
        if not self.use_live_display:
            self.print_message(message)

    def print_message(self, message: Message):
        """Print a single message to the console (simple mode)."""
        timestamp = message.timestamp.strftime("%H:%M")

        if message.role == MessageRole.SYSTEM:
            self.console.print(f"[dim][{timestamp}][/dim] [yellow]{message.content}[/yellow]")
        elif message.role == MessageRole.HUMAN:
            self.console.print(f"[dim][{timestamp}][/dim] [{USER_STYLE}]{message.sender_name}:[/{USER_STYLE}] {message.content}")
        else:
            name_style = AGENT_STYLES.get(message.sender_name, "white")
            icon = AGENT_ICONS.get(message.sender_name, "🤖")
            self.console.print(f"[dim][{timestamp}][/dim] [{name_style}]{icon} {message.sender_name}:[/{name_style}] {message.content}")

    # ─────────────────────────────────────────────────────────────────────
    # COMMANDS
    # ─────────────────────────────────────────────────────────────────────

    async def handle_command(self, cmd: str, arg: str):
        """Handle slash commands."""
        if cmd in ["/quit", "/exit", "/q"]:
            self.running = False
            self.console.print("[yellow]Shutting down...[/yellow]")

        elif cmd == "/help":
            self.console.print(
                Panel(
                    "Commands:\n"
                    "/help      - Show this help\n"
                    "/dashboard - Show dashboard snapshot (agents, tokens, tasks)\n"
                    "/agents    - List all available agent roles\n"
                    "/spawn <role> - Spawn agent (backend_dev, frontend_dev, qa_engineer, devops, project_manager, tech_writer)\n"
                    "/status    - Show swarm status\n"
                    "/settings  - Open settings menu\n"
                    "/clear     - Clear chat history\n"
                    "/mode      - Toggle live/simple display mode\n"
                    "/quit      - Exit",
                    title="Help",
                )
            )

        elif cmd == "/agents":
            table = Table(title="Available Agent Roles")
            table.add_column("Role", style="cyan")
            table.add_column("Description")
            for role, cls in AGENT_CLASSES.items():
                agent = cls()
                table.add_row(role, agent.persona_description)
                await agent.close()
            self.console.print(table)

        elif cmd == "/spawn":
            if arg and arg in AGENT_CLASSES:
                agent = await self.chatroom.spawn_agent(arg)
                if agent:
                    self.agents.append(agent)
                    self.console.print(f"[green]Spawned {agent.name}[/green]")
                else:
                    self.console.print(f"[red]Failed to spawn {arg}[/red]")
            else:
                self.console.print(f"[yellow]Usage: /spawn <role>[/yellow]")
                self.console.print(f"Available roles: {', '.join(AGENT_CLASSES.keys())}")

        elif cmd == "/status":
            status = self.chatroom.get_status()
            tracker = get_token_tracker()
            stats = tracker.get_stats()
            self.console.print(
                Panel(
                    f"Running: {status['is_running']}\n"
                    f"Round: {status['round_number']}\n"
                    f"Messages: {status['message_count']}\n"
                    f"Agents: {len(status['active_agents'])}\n"
                    f"Tokens: {stats['total_tokens']:,}\n"
                    f"API Calls: {stats['call_count']}",
                    title="Swarm Status",
                )
            )

        elif cmd == "/clear":
            self.messages.clear()
            self.status_messages.clear()
            self.console.print("[dim]Chat cleared[/dim]")

        elif cmd == "/mode":
            self.use_live_display = not self.use_live_display
            mode = "Live" if self.use_live_display else "Simple"
            self.console.print(f"[cyan]Switched to {mode} display mode[/cyan]")

        elif cmd == "/dashboard" or cmd == "/dash":
            # Show a one-time dashboard snapshot
            self.show_dashboard_snapshot()

        elif cmd == "/settings":
            # For settings, we need to exit live mode temporarily
            was_live = self.use_live_display
            if was_live:
                self.use_live_display = False
                self.console.print("[dim]Entering settings (live display paused)...[/dim]")
            await self.show_settings_menu()
            if was_live:
                self.use_live_display = True
                self.console.print("[dim]Settings closed. Live display will resume.[/dim]")

        else:
            self.console.print(f"[red]Unknown command: {cmd}[/red]")


    def show_dashboard_snapshot(self):
        """Show a one-time snapshot of the dashboard status."""
        tracker = get_token_tracker()
        stats = tracker.get_stats()
        tm = get_task_manager()
        tasks = tm.get_all_tasks()
        agents = list(self.chatroom._agents.values()) if self.chatroom else []
        
        # Header
        self.console.print()
        self.console.print("=" * 70, style="blue")
        self.console.print("🚀 DASHBOARD SNAPSHOT", style="bold cyan", justify="center")
        self.console.print("=" * 70, style="blue")
        
        # Token stats
        self.console.print(f"\n📊 [bold]TOKENS:[/bold] {stats['total_tokens']:,} total ({stats['prompt_tokens']:,} prompt + {stats['completion_tokens']:,} completion) | {stats['call_count']} API calls")
        
        # Agents
        self.console.print(f"\n🤖 [bold]AGENTS ({len(agents)}):[/bold]")
        for agent in agents:
            icon = AGENT_ICONS.get(agent.name, "🤖")
            status = "🟢 Working" if agent.status == AgentStatus.WORKING else "⚪ Idle"
            style = AGENT_STYLES.get(agent.name, "white")
            self.console.print(f"   {icon} [{style}]{agent.name}[/{style}] - {status}")
        
        # Tasks
        pending = len([t for t in tasks if t.status.value == "pending"])
        in_progress = len([t for t in tasks if t.status.value == "in_progress"])
        completed = len([t for t in tasks if t.status.value == "completed"])
        self.console.print(f"\n📋 [bold]TASKS:[/bold] {pending} pending | {in_progress} in progress | {completed} completed")
        
        # Recent activity
        if self.status_messages:
            self.console.print(f"\n⚡ [bold]RECENT ACTIVITY:[/bold]")
            for msg in self.status_messages[-5:]:
                self.console.print(f"   [dim]{msg}[/dim]")
        
        self.console.print("\n" + "=" * 70, style="blue")
        self.console.print()

    # ─────────────────────────────────────────────────────────────────────
    # SETTINGS MENUS
    # ─────────────────────────────────────────────────────────────────────

    async def show_settings_menu(self):
        """Show interactive settings menu."""
        from core.settings_manager import get_settings

        while True:
            pm = get_project_manager()
            settings = get_settings()
            current_proj = pm.current
            proj_name = current_proj.name if current_proj else "None"

            self.console.print(
                Panel(
                    "Settings Menu\n\n"
                    "1. Change username\n"
                    "2. Bot Management (enable/disable agents)\n"
                    "3. Model Selection (per agent)\n"
                    "4. Toggle Tools\n"
                    "5. Delay Settings\n"
                    "6. View scratch folder\n"
                    f"7. Project Management (current: {proj_name})\n"
                    "0. Back",
                    title="⚙️ Settings",
                )
            )

            choice = input("Enter choice: ").strip()

            if choice == "0" or choice == "":
                break
            elif choice == "1":
                await self.show_username_settings()
            elif choice == "2":
                await self.show_bot_management()
            elif choice == "3":
                await self.show_model_selection()
            elif choice == "4":
                await self.show_tools_toggle()
            elif choice == "5":
                await self.show_delay_settings()
            elif choice == "6":
                scratch_dir = Path(__file__).parent / "scratch"
                if scratch_dir.exists():
                    self.console.print(f"[cyan]Scratch folder: {scratch_dir}[/cyan]")
                    for item in scratch_dir.iterdir():
                        icon = "📁" if item.is_dir() else "📄"
                        self.console.print(f"  {icon} {item.name}")
                else:
                    self.console.print("[yellow]Scratch folder does not exist yet[/yellow]")
            elif choice == "7":
                await self.show_project_menu()
            else:
                self.console.print("[red]Invalid choice[/red]")

    async def show_username_settings(self):
        """Show username change settings."""
        from core.settings_manager import get_settings
        settings = get_settings()

        self.console.print(
            Panel(
                f"[bold]Current username:[/bold] {self.username}\n\n"
                "Enter a new username (max 20 characters)",
                title="👤 Username Settings",
            )
        )

        new_name = input("Enter new username (or press Enter to cancel): ").strip()
        if new_name:
            self.username = new_name[:20]
            settings.set("username", self.username)
            self.console.print(f"[green]Username set to {self.username}[/green]")
        else:
            self.console.print("[dim]Username unchanged[/dim]")

    async def show_bot_management(self):
        """Show bot management menu for enabling/disabling agents."""
        from core.settings_manager import get_settings
        settings = get_settings()
        disabled_agents = settings.get("disabled_agents", [])

        self.console.print(
            Panel(
                "[bold cyan]BOT MANAGEMENT[/bold cyan]\n\n"
                "Enable or disable individual agents in the swarm.",
                title="🤖 Bot Management",
            )
        )

        self.console.print("\n[bold]Available Agents:[/bold]")
        agent_roles = list(AGENT_CLASSES.keys())

        for i, role in enumerate(agent_roles, 1):
            agent_class = AGENT_CLASSES[role]
            temp_agent = agent_class()
            display_name = temp_agent.name
            is_enabled = role not in disabled_agents
            status = "[green]✓ Enabled[/green]" if is_enabled else "[red]✗ Disabled[/red]"
            self.console.print(f"  [yellow]{i}.[/yellow] {display_name} ({role}) - {status}")

        self.console.print(f"\n  [green]A.[/green] Enable all agents")
        self.console.print(f"  [red]D.[/red] Disable all agents")
        self.console.print(f"  [yellow]0.[/yellow] Back to settings")
        self.console.print()

        choice = input("Enter agent number to toggle, or A/D/0: ").strip()

        if choice == "0" or choice == "":
            return
        elif choice.upper() == "A":
            settings.set("disabled_agents", [])
            self.console.print("[green]All agents enabled[/green]")
        elif choice.upper() == "D":
            all_except_architect = [r for r in agent_roles if r != "architect"]
            settings.set("disabled_agents", all_except_architect)
            self.console.print("[yellow]All agents disabled except Architect[/yellow]")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(agent_roles):
                    role = agent_roles[idx]
                    if role in disabled_agents:
                        disabled_agents.remove(role)
                        settings.set("disabled_agents", disabled_agents)
                        self.console.print(f"[green]{role} enabled[/green]")
                    else:
                        if role == "architect":
                            self.console.print("[yellow]Cannot disable the Architect[/yellow]")
                        else:
                            disabled_agents.append(role)
                            settings.set("disabled_agents", disabled_agents)
                            self.console.print(f"[red]{role} disabled[/red]")
                else:
                    self.console.print("[red]Invalid choice[/red]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")

    async def show_model_selection(self):
        """Show model selection menu for each agent."""
        from core.settings_manager import get_settings
        settings = get_settings()

        self.console.print(
            Panel(
                "[bold cyan]MODEL SELECTION[/bold cyan]\n\n"
                "Select AI model for each agent or set a default for all.",
                title="🧠 Model Selection",
            )
        )

        self.console.print("\n[bold]Current Model Settings:[/bold]")
        default_model = settings.get("default_model", "openai/gpt-5-nano")
        architect_model = settings.get("architect_model", default_model)
        swarm_model = settings.get("swarm_model", default_model)
        default_provider = settings.get("default_provider", "requesty")
        architect_provider = settings.get("architect_provider", default_provider)
        swarm_provider = settings.get("swarm_provider", default_provider)

        self.console.print(f"  Default Provider: [cyan]{default_provider}[/cyan]")
        self.console.print(f"  Default Model: [cyan]{default_model}[/cyan]")
        self.console.print(f"  Architect: [cyan]{architect_provider} / {architect_model}[/cyan]")
        self.console.print(f"  Swarm: [cyan]{swarm_provider} / {swarm_model}[/cyan]")

        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("  [yellow]1.[/yellow] Change default model (for all agents)")
        self.console.print("  [yellow]2.[/yellow] Change architect model")
        self.console.print("  [yellow]3.[/yellow] Change swarm model (other agents)")
        self.console.print("  [yellow]0.[/yellow] Back to settings")
        self.console.print()

        choice = input("Enter choice: ").strip()

        if choice == "0" or choice == "":
            return

        if choice in ["1", "2", "3"]:
            # Choose provider first
            providers = [
                ("1", "requesty", "Requesty (router.requesty.ai)"),
                ("2", "zai", "Z.AI (api.z.ai)"),
                ("3", "custom", "Custom (/api override)"),
            ]

            self.console.print("\n[bold]Providers:[/bold]")
            for code, key, label in providers:
                self.console.print(f"  [yellow]{code}.[/yellow] {label}")

            provider_choice = input("\nEnter provider number: ").strip()
            provider_map = {code: key for code, key, _ in providers}
            provider = provider_map.get(provider_choice)
            if not provider:
                self.console.print("[red]Invalid provider selection[/red]")
                return

            # Heuristic: use GLM models for Z.AI, non-GLM for Requesty, all for custom
            if provider == "zai":
                model_list = [m for m in AVAILABLE_MODELS if m.startswith("glm-")]
            elif provider == "requesty":
                model_list = [m for m in AVAILABLE_MODELS if not m.startswith("glm-")]
            else:  # custom
                model_list = AVAILABLE_MODELS

            if not model_list:
                self.console.print("[red]No models available for selected provider[/red]")
                return

            self.console.print("\n[bold]Available Models for provider:[/bold]")
            for i, model in enumerate(model_list, 1):
                self.console.print(f"  [yellow]{i}.[/yellow] {model}")

            model_choice = input("\nEnter model number: ").strip()
            try:
                model_idx = int(model_choice) - 1
                if 0 <= model_idx < len(model_list):
                    selected_model = model_list[model_idx]

                    if choice == "1":
                        settings.set("default_model", selected_model)
                        settings.set("architect_model", selected_model)
                        settings.set("swarm_model", selected_model)
                        settings.set("default_provider", provider)
                        settings.set("architect_provider", provider)
                        settings.set("swarm_provider", provider)
                        self.console.print(f"[green]Default model set to {selected_model} on provider {provider}[/green]")
                    elif choice == "2":
                        settings.set("architect_model", selected_model)
                        settings.set("architect_provider", provider)
                        self.console.print(f"[green]Architect model set to {selected_model} on provider {provider}[/green]")
                    elif choice == "3":
                        settings.set("swarm_model", selected_model)
                        settings.set("swarm_provider", provider)
                        self.console.print(f"[green]Swarm model set to {selected_model} on provider {provider}[/green]")
                else:
                    self.console.print("[red]Invalid model number[/red]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")

    async def show_tools_toggle(self):
        """Show tools toggle menu."""
        from core.settings_manager import get_settings
        settings = get_settings()
        tools_enabled = settings.get("tools_enabled", True)

        self.console.print(
            Panel(
                f"[bold cyan]TOOLS TOGGLE[/bold cyan]\n\n"
                f"Current status: {'[green]Enabled[/green]' if tools_enabled else '[red]Disabled[/red]'}\n\n"
                "Tools allow agents to perform actions like:\n"
                "- Spawning new agents\n"
                "- Creating/managing tasks\n"
                "- File operations in scratch folder",
                title="🔧 Tools Toggle",
            )
        )

        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("  [yellow]1.[/yellow] Enable tools for all agents")
        self.console.print("  [yellow]2.[/yellow] Disable tools for all agents")
        self.console.print("  [yellow]0.[/yellow] Back to settings")
        self.console.print()

        choice = input("Enter choice: ").strip()

        if choice == "1":
            settings.set("tools_enabled", True)
            agents = list(self.chatroom._agents.values()) if self.chatroom else []
            for agent in agents:
                agent.tools_enabled = True
            self.console.print("[green]Tools enabled for all agents[/green]")
        elif choice == "2":
            settings.set("tools_enabled", False)
            agents = list(self.chatroom._agents.values()) if self.chatroom else []
            for agent in agents:
                agent.tools_enabled = False
            self.console.print("[red]Tools disabled for all agents[/red]")

    async def show_delay_settings(self):
        """Show delay settings menu."""
        from core.settings_manager import get_settings
        settings = get_settings()

        round_delay = settings.get("round_delay", 15.0)
        response_min = settings.get("response_delay_min", 2.0)
        response_max = settings.get("response_delay_max", 5.0)

        self.console.print(
            Panel(
                f"[bold cyan]DELAY SETTINGS[/bold cyan]\n\n"
                f"Round Delay: [cyan]{round_delay}s[/cyan]\n"
                f"Response Delay: [cyan]{response_min}s - {response_max}s[/cyan]",
                title="⏱️ Delay Settings",
            )
        )

        self.console.print("\n[bold]Options:[/bold]")
        self.console.print("  [yellow]1.[/yellow] Change round delay")
        self.console.print("  [yellow]2.[/yellow] Change response delay range")
        self.console.print("  [yellow]3.[/yellow] Use fast mode (minimal delays)")
        self.console.print("  [yellow]4.[/yellow] Use normal mode (default delays)")
        self.console.print("  [yellow]0.[/yellow] Back to settings")
        self.console.print()

        choice = input("Enter choice: ").strip()

        if choice == "1":
            try:
                new_delay = float(input("Enter round delay in seconds: ").strip())
                if new_delay >= 0:
                    settings.set("round_delay", new_delay)
                    self.console.print(f"[green]Round delay set to {new_delay}s[/green]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")
        elif choice == "2":
            try:
                min_delay = float(input("Enter minimum response delay: ").strip())
                max_delay = float(input("Enter maximum response delay: ").strip())
                if min_delay >= 0 and max_delay >= min_delay:
                    settings.set("response_delay_min", min_delay)
                    settings.set("response_delay_max", max_delay)
                    self.console.print(f"[green]Response delay set to {min_delay}s - {max_delay}s[/green]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")
        elif choice == "3":
            settings.set("round_delay", 1.0)
            settings.set("response_delay_min", 0.5)
            settings.set("response_delay_max", 1.0)
            self.console.print("[green]Fast mode enabled[/green]")
        elif choice == "4":
            settings.set("round_delay", 15.0)
            settings.set("response_delay_min", 2.0)
            settings.set("response_delay_max", 5.0)
            self.console.print("[green]Normal mode enabled[/green]")

    async def show_project_menu(self):
        """Show project management menu."""
        pm = get_project_manager()
        projects = pm.list_projects()
        current = pm.current

        self.console.print()
        self.console.print(Panel("[bold cyan]PROJECT MANAGEMENT[/bold cyan]", style="cyan"))

        if current:
            info = current.get_info()
            self.console.print(f"\n[bold]Current Project:[/bold] [green]{info['name']}[/green]")
            self.console.print(f"  Path: [dim]{info['path']}[/dim]")
            if info["description"]:
                self.console.print(f"  Description: {info['description']}")

        self.console.print("\n[bold]Available Projects:[/bold]")
        if projects:
            for i, proj in enumerate(projects, 1):
                marker = " [green](current)[/green]" if current and proj.name == current.name else ""
                self.console.print(f"  [yellow]{i}.[/yellow] {proj.name}{marker}")
        else:
            self.console.print("  [dim]No projects yet[/dim]")

        self.console.print(f"\n  [green]N.[/green] Create new project")
        self.console.print(f"  [green]S.[/green] Switch to another project")
        self.console.print(f"  [yellow]0.[/yellow] Back to settings")
        self.console.print()

        choice = input("Enter choice: ").strip()

        if choice == "0" or choice == "":
            return
        elif choice.upper() == "N":
            name = input("Project name: ").strip()
            if name:
                desc = input("Description (optional): ").strip()
                project = pm.create_project(name, desc)
                pm.set_current(project)
                self.current_project = project
                self.console.print(f"[green]Created and switched to project: {project.name}[/green]")
        elif choice.upper() == "S":
            if not projects:
                self.console.print("[yellow]No projects to switch to[/yellow]")
                return
            self.console.print("\nSelect project to switch to:")
            for i, proj in enumerate(projects, 1):
                self.console.print(f"  [yellow]{i}.[/yellow] {proj.name}")
            proj_choice = input("Enter project number: ").strip()
            try:
                idx = int(proj_choice) - 1
                if 0 <= idx < len(projects):
                    project = projects[idx]
                    pm.set_current(project)
                    self.current_project = project
                    self.console.print(f"[green]Switched to project: {project.name}[/green]")
            except ValueError:
                self.console.print("[red]Invalid input[/red]")


    # ─────────────────────────────────────────────────────────────────────
    # PROJECT SUMMARY & MAIN LOOP
    # ─────────────────────────────────────────────────────────────────────

    async def trigger_project_summary(self, project: Project):
        """Trigger the architect to give a project summary and suggest next steps."""
        has_master_plan = project.master_plan_path.exists()

        if has_master_plan:
            try:
                with open(project.master_plan_path, "r", encoding="utf-8") as f:
                    plan_content = f.read()[:2000]
                summary_prompt = (
                    f"[AUTO-SUMMARY REQUEST] Project '{project.name}' loaded. "
                    f"Master plan exists. Give a quick 2-3 sentence summary of where we are, "
                    f"what's been done, what's next, and suggest the best course of action. "
                    f"Be concise and actionable. Here's the plan context:\n{plan_content[:500]}..."
                )
            except Exception:
                summary_prompt = (
                    f"[AUTO-SUMMARY REQUEST] Project '{project.name}' loaded. "
                    f"Give a quick summary of the project status and suggest next steps."
                )
        else:
            summary_prompt = (
                f"[AUTO-SUMMARY REQUEST] Project '{project.name}' loaded (new or no master plan yet). "
                f"Briefly introduce yourself and ask what the user wants to build. "
                f"Keep it to 2-3 sentences max."
            )

        self.status_messages.append("🔍 Architect is reviewing the project...")

        await self.chatroom.add_human_message(
            content=summary_prompt, username="System", user_id="auto_summary"
        )

        await self.chatroom.run_conversation_round()

    async def handle_input(self):
        """Handle user input in a separate thread."""
        import threading
        import queue

        input_queue = queue.Queue()

        def input_thread():
            while self.running:
                try:
                    line = input()
                    input_queue.put(line)
                except EOFError:
                    break

        thread = threading.Thread(target=input_thread, daemon=True)
        thread.start()

        while self.running:
            try:
                line = input_queue.get_nowait()
                line = line.strip()

                if not line:
                    continue

                if line.startswith("/"):
                    parts = line.split(maxsplit=1)
                    cmd = parts[0].lower()
                    arg = parts[1] if len(parts) > 1 else ""
                    await self.handle_command(cmd, arg)
                else:
                    # Send as chat message
                    await self.chatroom.add_human_message(
                        content=line, username=self.username, user_id="dashboard_user"
                    )
                    # Trigger agent responses
                    asyncio.create_task(self.chatroom.run_conversation_round())

            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                logging.error(f"Input error: {e}")

    async def handle_input_refresh_mode(self):
        """Handle input with periodic dashboard refresh.
        
        Uses clear-and-redraw approach instead of Rich Live to avoid
        input conflicts on Windows. Dashboard refreshes after each
        interaction or on /dash command.
        """
        import threading
        import queue
        import time
        
        input_queue = queue.Queue()
        
        def input_thread():
            """Background thread to collect input."""
            while self.running:
                try:
                    line = input()
                    input_queue.put(line)
                except EOFError:
                    break
                except Exception:
                    break
        
        # Start input thread
        thread = threading.Thread(target=input_thread, daemon=True)
        thread.start()
        
        # Show initial dashboard
        self._draw_dashboard()
        
        last_activity = time.time()
        auto_refresh_interval = 5.0  # Auto-refresh every 5 seconds during activity
        
        while self.running:
            current_time = time.time()
            
            # Check for input (non-blocking)
            try:
                line = input_queue.get_nowait()
                line = line.strip()
                
                if line:
                    if line.startswith("/"):
                        parts = line.split(maxsplit=1)
                        cmd = parts[0].lower()
                        arg = parts[1] if len(parts) > 1 else ""
                        
                        # /dash or /dashboard redraws the full dashboard
                        if cmd in ["/dash", "/dashboard"]:
                            self._draw_dashboard()
                        else:
                            await self.handle_command(cmd, arg)
                    else:
                        # Show user message inline
                        timestamp = datetime.now().strftime("%H:%M")
                        self.console.print(f"[dim][{timestamp}][/dim] [{USER_STYLE}]👤 {self.username}:[/{USER_STYLE}] {line}")
                        
                        await self.chatroom.add_human_message(
                            content=line, username=self.username, user_id="dashboard_user"
                        )
                        asyncio.create_task(self.chatroom.run_conversation_round())
                    
                    last_activity = current_time
                    
            except queue.Empty:
                pass
            
            # Auto-refresh dashboard if there's been recent activity
            if current_time - last_activity < 30.0:  # Within 30 sec of activity
                if current_time - last_activity >= auto_refresh_interval:
                    # Only refresh if we have new status messages
                    if self.status_messages:
                        self._draw_dashboard()
                        last_activity = current_time
            
            await asyncio.sleep(0.1)
    
    def _draw_dashboard(self):
        """Clear screen and draw the dashboard layout once."""
        # Clear screen
        if sys.platform == "win32":
            os.system("cls")
        else:
            os.system("clear")
        
        # Update and print layout
        if self.layout:
            self.update_layout()
            self.console.print(self.layout)
        
        # Print input prompt
        self.console.print("\n[dim]Type message or /help for commands:[/dim]")

    async def run(self):
        """Run the dashboard."""
        log_file = self.setup_logging()

        # Validate config
        is_valid, errors = validate_config()
        if not is_valid:
            for error in errors:
                self.console.print(f"[red]Error: {error}[/red]")
            return

        # Welcome
        self.console.print(
            Panel(
                "[bold cyan]🚀 Agent Swarm Dashboard[/bold cyan]\n\n"
                "A multi-agent AI development system.\n"
                "The Architect will help you plan and build software projects.",
                title="Welcome",
            )
        )

        # Project selection
        project = self.select_project()

        # Get username
        self.username = input("Enter your name (or press Enter for 'You'): ").strip() or "You"
        self.username = self.username[:20]

        # Ask about display mode
        self.console.print("\n[bold]Display Mode:[/bold]")
        self.console.print("  [yellow]1.[/yellow] Live Dashboard (auto-updating panels - experimental)")
        self.console.print("  [yellow]2.[/yellow] Simple Mode (scrolling chat - recommended)")
        mode_choice = input("Enter choice (default: 2 for Simple): ").strip()
        self.use_live_display = mode_choice == "1"
        
        if self.use_live_display:
            self.console.print("[yellow]Live mode enabled. Use /mode to switch if you experience issues.[/yellow]")

        # Initialize chatroom with the Architect (use singleton so tools work)
        from core.chatroom import set_chatroom
        from config.settings import ARCHITECT_MODEL

        self.chatroom = Chatroom()
        set_chatroom(self.chatroom)

        architect = create_agent("architect", model=ARCHITECT_MODEL)
        self.agents = [architect]
        await self.chatroom.initialize(self.agents)

        # Ensure Checky McManager (project_manager) is available in dashboard sessions
        try:
            from core.settings_manager import get_settings
            settings = get_settings()
            swarm_model = settings.get("swarm_model", ARCHITECT_MODEL)
            checky = await self.chatroom.spawn_agent("project_manager", model=swarm_model)
        except Exception:
            checky = None

        if checky:
            self.agents.append(checky)
            style = AGENT_STYLES.get(checky.name, "white")
            icon = AGENT_ICONS.get(checky.name, "🤖")
            self.console.print(f"[{style}]{icon} {checky.name}[/{style}] joined the swarm")

        # Register message callback
        self.chatroom.on_message(self.message_callback)

        self.console.print(f"\n[green]Welcome, {self.username}![/green]")
        self.console.print(f"[dim]Project: {project.name}[/dim]")
        self.console.print("[dim]Type /help for commands. Start by describing your project to the Architect.[/dim]\n")

        # Show initial agents
        for agent in self.agents:
            style = AGENT_STYLES.get(agent.name, "white")
            icon = AGENT_ICONS.get(agent.name, "🤖")
            self.console.print(f"[{style}]{icon} {agent.name}[/{style}] joined the swarm")

        self.console.print()

        # Auto-trigger architect to give project summary
        await self.trigger_project_summary(project)

        try:
            if self.use_live_display:
                # Create layout for live display
                self.layout = self.create_layout()
                self.update_layout()
                
                # Use auto-refresh mode: periodically clear and redraw
                # This avoids Rich Live conflicts with input on Windows
                await self.handle_input_refresh_mode()
            else:
                # Simple scrolling mode
                await self.handle_input()
                
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted...[/yellow]")
        finally:
            if self.chatroom:
                await self.chatroom.shutdown()
            self.console.print("[dim]Dashboard closed. Goodbye![/dim]")


def main():
    """Entry point."""
    if sys.platform == "win32":
        os.system("color")
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass

    if not RICH_AVAILABLE:
        print("Please install rich: pip install rich")
        print("Then run: python dashboard.py")
        return

    dashboard = DashboardUI()
    asyncio.run(dashboard.run())


if __name__ == "__main__":
    main()
