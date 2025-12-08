"""
Main entry point for Multi-Agent Chatroom.

Interactive terminal chat with AI agents.
"""

import asyncio
import logging
import sys
import os
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import LOG_FORMAT, validate_config, AVAILABLE_MODELS
from core.chatroom import Chatroom
from core.models import Message, MessageRole
from core.project_manager import get_project_manager, Project
from agents import create_all_default_agents


# ANSI color codes for terminal
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Agent name colors (bright/bold)
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[38;5;213m"
    LIME = "\033[38;5;118m"
    
    # Message text color (dimmer)
    TEXT = "\033[37m"
    SYSTEM = "\033[90m"  # Gray for system messages


# Assign colors to agents
AGENT_COLORS = {
    "Bossy McArchitect": Colors.MAGENTA,
    "Codey McBackend": Colors.BLUE,
    "Pixel McFrontend": Colors.PINK,
    "Bugsy McTester": Colors.GREEN,
    "Deployo McOps": Colors.YELLOW,
    "Checky McManager": Colors.CYAN,
    "Docy McWriter": Colors.RED,
    "System": Colors.SYSTEM,
}


class ChatSettings:
    """Configurable chat settings with persistence."""
    def __init__(self):
        from core.settings_manager import get_settings
        self._manager = get_settings()
        
    @property
    def username(self):
        return self._manager.get("username", "You")
    
    @username.setter
    def username(self, value):
        self._manager.set("username", value)
    
    @property
    def round_delay(self):
        return self._manager.get("round_delay", 15.0)
    
    @round_delay.setter
    def round_delay(self, value):
        self._manager.set("round_delay", value)
    
    @property
    def response_delay_min(self):
        return self._manager.get("response_delay_min", 2.0)
    
    @response_delay_min.setter
    def response_delay_min(self, value):
        self._manager.set("response_delay_min", value)
    
    @property
    def response_delay_max(self):
        return self._manager.get("response_delay_max", 5.0)
    
    @response_delay_max.setter
    def response_delay_max(self, value):
        self._manager.set("response_delay_max", value)
    
    @property
    def max_responders(self):
        return self._manager.get("max_responders", 3)
    
    @max_responders.setter
    def max_responders(self, value):
        self._manager.set("max_responders", value)
    
    @property
    def auto_chat(self):
        return self._manager.get("auto_chat", False)
    
    @auto_chat.setter
    def auto_chat(self, value):
        self._manager.set("auto_chat", value)
    
    @property
    def verbose(self):
        return self._manager.get("verbose", False)
    
    @verbose.setter
    def verbose(self, value):
        self._manager.set("verbose", value)


class InteractiveChatroom:
    """Interactive terminal chatroom with colored output and user input."""
    
    def __init__(self):
        self.chatroom = None
        self.settings = ChatSettings()
        self.running = True
        self.log_file = None
        self.agents = []
        self.disabled_agents = set()  # Agent names that are disabled
        
    def setup_logging(self):
        """Configure logging to file only (console handled separately)."""
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = log_dir / f"chatroom_{timestamp}.log"
        
        # Root logger at DEBUG level
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # File handler - DEBUG level (verbose)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler - only if verbose mode
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.WARNING)  # Start quiet
        self.console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        root_logger.addHandler(self.console_handler)
        
        return self.log_file
    
    def toggle_verbose(self):
        """Toggle verbose console logging."""
        self.settings.verbose = not self.settings.verbose
        if self.settings.verbose:
            self.console_handler.setLevel(logging.DEBUG)
            self.print_system("Verbose mode ON - showing debug output")
        else:
            self.console_handler.setLevel(logging.WARNING)
            self.print_system("Verbose mode OFF")
    
    def get_color(self, name: str) -> str:
        """Get color for a sender name."""
        if name == self.settings.username:
            return Colors.LIME
        return AGENT_COLORS.get(name, Colors.WHITE)
    
    def print_message(self, message: Message):
        """Print a chat message with colors."""
        color = self.get_color(message.sender_name)
        timestamp = message.timestamp.strftime("%H:%M")
        
        # Format: [HH:MM] Name: message
        print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {color}{Colors.BOLD}{message.sender_name}{Colors.RESET}: {Colors.TEXT}{message.content}{Colors.RESET}")
    
    def print_system(self, text: str):
        """Print a system message."""
        print(f"{Colors.SYSTEM}>> {text}{Colors.RESET}")
    
    def print_header(self):
        """Print the chat header."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  MULTI-AGENT AI CHATROOM{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print()
        self.print_system("Commands: /help for all commands")
        self.print_system(f"Logging to: {self.log_file}")
        print()
    
    def show_help(self):
        """Show help menu."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}=== COMMANDS ==={Colors.RESET}")
        print(f"  {Colors.YELLOW}Chat:{Colors.RESET}")
        print(f"    {Colors.GREEN}/help{Colors.RESET}         - Show this help")
        print(f"    {Colors.GREEN}/clear{Colors.RESET}        - Clear chat history")
        print(f"    {Colors.GREEN}/topic{Colors.RESET} <t>    - Set discussion topic")
        print()
        print(f"  {Colors.YELLOW}Agents:{Colors.RESET}")
        print(f"    {Colors.GREEN}/agents{Colors.RESET}       - List active agents")
        print(f"    {Colors.GREEN}/spawn{Colors.RESET} <role> - Spawn new agent")
        print(f"    {Colors.GREEN}/kick{Colors.RESET} <name>  - Disable an agent")
        print(f"    {Colors.GREEN}/invite{Colors.RESET} <n>   - Re-enable an agent")
        print(f"    {Colors.GREEN}/roles{Colors.RESET}        - List available roles")
        print()
        print(f"  {Colors.YELLOW}Project:{Colors.RESET}")
        print(f"    {Colors.GREEN}/project{Colors.RESET}      - Show current project")
        print(f"    {Colors.GREEN}/projects{Colors.RESET}     - List/switch projects")
        print(f"    {Colors.GREEN}/status{Colors.RESET}       - Show swarm status")
        print(f"    {Colors.GREEN}/tasks{Colors.RESET}        - Show task list")
        print(f"    {Colors.GREEN}/files{Colors.RESET}        - Show project files")
        print(f"    {Colors.GREEN}/plan{Colors.RESET}         - Show master plan")
        print()
        print(f"  {Colors.YELLOW}Settings:{Colors.RESET}")
        print(f"    {Colors.GREEN}/settings{Colors.RESET}     - Open settings menu")
        print(f"    {Colors.GREEN}/name{Colors.RESET} <n>     - Set your display name")
        print(f"    {Colors.GREEN}/verbose{Colors.RESET}      - Toggle debug output")
        print(f"    {Colors.GREEN}/api{Colors.RESET} <url> <key> - Configure API base URL and key")
        print(f"    {Colors.GREEN}/quit{Colors.RESET}         - Exit chatroom")
        print()
    
    def show_settings_menu(self):
        """Show interactive settings menu."""
        while True:
            print()
            # Check tools status
            tools_on = all(a.tools_enabled for a in self.agents) if self.agents else False
            
            print(f"{Colors.BOLD}{Colors.CYAN}=== SETTINGS MENU ==={Colors.RESET}")
            print(f"  {Colors.YELLOW}1.{Colors.RESET} Bot Management (enable/disable bots)")
            print(f"  {Colors.YELLOW}2.{Colors.RESET} Round Delay: {Colors.GREEN}{self.settings.round_delay}s{Colors.RESET}")
            print(f"  {Colors.YELLOW}3.{Colors.RESET} Response Delay: {Colors.GREEN}{self.settings.response_delay_min}-{self.settings.response_delay_max}s{Colors.RESET}")
            print(f"  {Colors.YELLOW}4.{Colors.RESET} Max Responders/Round: {Colors.GREEN}{self.settings.max_responders}{Colors.RESET}")
            print(f"  {Colors.YELLOW}5.{Colors.RESET} Change Bot Models")
            print(f"  {Colors.YELLOW}6.{Colors.RESET} Your Name: {Colors.GREEN}{self.settings.username}{Colors.RESET}")
            print(f"  {Colors.YELLOW}7.{Colors.RESET} Auto-Chat: {Colors.GREEN}{'ON' if self.settings.auto_chat else 'OFF'}{Colors.RESET}")
            print(f"  {Colors.YELLOW}8.{Colors.RESET} Bot Tools: {Colors.GREEN}{'ON' if tools_on else 'OFF'}{Colors.RESET} (file read/write, code search)")
            print(f"  {Colors.YELLOW}9.{Colors.RESET} View Scratch Folder")
            print(f"  {Colors.YELLOW}0.{Colors.RESET} Back to chat")
            print()
            
            choice = input(f"{Colors.BOLD}Enter choice (0-9): {Colors.RESET}").strip()
            
            if choice == "0" or choice == "":
                break
            elif choice == "1":
                self.manage_bots()
            elif choice == "2":
                self.set_round_delay()
            elif choice == "3":
                self.set_response_delay()
            elif choice == "4":
                self.set_max_responders()
            elif choice == "5":
                self.change_bot_models()
            elif choice == "6":
                self.set_username()
            elif choice == "7":
                self.settings.auto_chat = not self.settings.auto_chat
                self.print_system(f"Auto-chat {'enabled' if self.settings.auto_chat else 'disabled'}")
            elif choice == "8":
                self.toggle_tools()
            elif choice == "9":
                self.view_scratch()
            else:
                self.print_system("Invalid choice")
    
    def manage_bots(self):
        """Enable/disable bots."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}=== BOT MANAGEMENT ==={Colors.RESET}")
        
        for i, agent in enumerate(self.agents, 1):
            status = f"{Colors.RED}[DISABLED]{Colors.RESET}" if agent.name in self.disabled_agents else f"{Colors.GREEN}[ENABLED]{Colors.RESET}"
            color = self.get_color(agent.name)
            print(f"  {Colors.YELLOW}{i}.{Colors.RESET} {color}{agent.name}{Colors.RESET} {status}")
        
        print(f"  {Colors.YELLOW}0.{Colors.RESET} Back")
        print()
        
        choice = input("Enter bot number to toggle (0 to go back): ").strip()
        
        if choice == "0" or choice == "":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.agents):
                agent = self.agents[idx]
                if agent.name in self.disabled_agents:
                    self.disabled_agents.remove(agent.name)
                    self.print_system(f"{agent.name} enabled")
                else:
                    self.disabled_agents.add(agent.name)
                    self.print_system(f"{agent.name} disabled")
        except ValueError:
            self.print_system("Invalid input")
    
    def set_round_delay(self):
        """Set delay between auto-rounds."""
        print(f"\nCurrent round delay: {self.settings.round_delay}s")
        try:
            new_delay = float(input("Enter new delay in seconds (5-120): ").strip())
            if 5 <= new_delay <= 120:
                self.settings.round_delay = new_delay
                self.print_system(f"Round delay set to {new_delay}s")
            else:
                self.print_system("Must be between 5-120 seconds")
        except ValueError:
            self.print_system("Invalid number")
    
    def set_response_delay(self):
        """Set delay between agent responses."""
        print(f"\nCurrent response delay: {self.settings.response_delay_min}-{self.settings.response_delay_max}s")
        try:
            min_d = float(input("Enter min delay in seconds (0-30): ").strip())
            max_d = float(input("Enter max delay in seconds (0-30): ").strip())
            if 0 <= min_d <= max_d <= 30:
                self.settings.response_delay_min = min_d
                self.settings.response_delay_max = max_d
                self.print_system(f"Response delay set to {min_d}-{max_d}s")
            else:
                self.print_system("Invalid range")
        except ValueError:
            self.print_system("Invalid number")
    
    def set_max_responders(self):
        """Set max agents per round."""
        print(f"\nCurrent max responders: {self.settings.max_responders}")
        try:
            new_max = int(input("Enter max responders per round (1-6): ").strip())
            if 1 <= new_max <= 6:
                self.settings.max_responders = new_max
                self.print_system(f"Max responders set to {new_max}")
            else:
                self.print_system("Must be between 1-6")
        except ValueError:
            self.print_system("Invalid number")
    
    def change_bot_models(self):
        """Change model for specific bots."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}=== CHANGE BOT MODELS ==={Colors.RESET}")
        print(f"Available models: {', '.join(AVAILABLE_MODELS)}")
        print()
        
        for i, agent in enumerate(self.agents, 1):
            color = self.get_color(agent.name)
            print(f"  {Colors.YELLOW}{i}.{Colors.RESET} {color}{agent.name}{Colors.RESET}: {Colors.DIM}{agent.model}{Colors.RESET}")
        
        print(f"  {Colors.YELLOW}0.{Colors.RESET} Back")
        print()
        
        choice = input("Enter bot number to change model (0 to go back): ").strip()
        
        if choice == "0" or choice == "":
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(self.agents):
                agent = self.agents[idx]
                print(f"\nAvailable models:")
                for i, model in enumerate(AVAILABLE_MODELS, 1):
                    print(f"  {i}. {model}")
                
                model_choice = input("Enter model number: ").strip()
                model_idx = int(model_choice) - 1
                if 0 <= model_idx < len(AVAILABLE_MODELS):
                    agent.model = AVAILABLE_MODELS[model_idx]
                    self.print_system(f"{agent.name} now using {agent.model}")
                else:
                    self.print_system("Invalid model choice")
        except ValueError:
            self.print_system("Invalid input")
    
    def set_username(self):
        """Set user's display name."""
        print(f"\nCurrent name: {self.settings.username}")
        new_name = input("Enter new name: ").strip()
        if new_name and len(new_name) <= 20:
            self.settings.username = new_name
            self.print_system(f"Name set to {new_name}")
        elif len(new_name) > 20:
            self.print_system("Name too long (max 20 chars)")
        else:
            self.print_system("Name cannot be empty")
    
    def show_agents(self):
        """Show list of agents."""
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}=== ACTIVE AGENTS ==={Colors.RESET}")
        for agent in self.agents:
            status = f"{Colors.RED}[OFF]{Colors.RESET}" if agent.name in self.disabled_agents else f"{Colors.GREEN}[ON]{Colors.RESET}"
            color = self.get_color(agent.name)
            print(f"  {color}•{Colors.RESET} {color}{agent.name}{Colors.RESET} {status}")
            print(f"    {Colors.DIM}Model: {agent.model} | Temp: {agent.temperature}{Colors.RESET}")
        print()
    
    def toggle_tools(self):
        """Toggle tools for all agents."""
        if not self.agents:
            self.print_system("No agents loaded")
            return
        
        # Toggle based on current state
        current = self.agents[0].tools_enabled
        new_state = not current
        
        for agent in self.agents:
            agent.tools_enabled = new_state
        
        self.print_system(f"Bot tools {'enabled' if new_state else 'disabled'} for all agents")
        if new_state:
            self.print_system("Agents can now read/write files in the scratch/ folder")
    
    def view_scratch(self):
        """View contents of scratch folder."""
        from pathlib import Path
        from config.settings import get_scratch_dir
        
        scratch_dir = get_scratch_dir()
        
        if not scratch_dir.exists():
            scratch_dir.mkdir(parents=True, exist_ok=True)
            self.print_system("Scratch folder created (was empty)")
            return
        
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}=== SCRATCH FOLDER ==={Colors.RESET}")
        print(f"{Colors.DIM}{scratch_dir}{Colors.RESET}")
        print()
        
        def print_tree(path, prefix=""):
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                
                if item.is_dir():
                    print(f"{prefix}{connector}{Colors.CYAN}{item.name}/{Colors.RESET}")
                    extension = "    " if is_last else "│   "
                    print_tree(item, prefix + extension)
                else:
                    size = item.stat().st_size
                    size_str = f"{size}B" if size < 1024 else f"{size//1024}KB"
                    print(f"{prefix}{connector}{item.name} {Colors.DIM}({size_str}){Colors.RESET}")
        
        if any(scratch_dir.iterdir()):
            print_tree(scratch_dir)
        else:
            print(f"  {Colors.DIM}(empty){Colors.RESET}")
        print()

    
    async def handle_user_input(self):
        """Handle user input using threading to avoid blocking."""
        import threading
        import queue
        
        input_queue = queue.Queue()
        
        def input_thread():
            """Thread that reads input and puts it in queue."""
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
        
        while self.running:
            try:
                # Check for input without blocking
                try:
                    line = input_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                # Handle commands
                if line.startswith("/"):
                    await self.handle_command(line)
                else:
                    # Send as chat message
                    await self.chatroom.add_human_message(
                        content=line,
                        username=self.settings.username,
                        user_id="local_user"
                    )
                    # Trigger responses
                    asyncio.create_task(self.trigger_staggered_responses())
                    
            except Exception as e:
                logging.error(f"Input error: {e}")
    
    async def handle_command(self, line: str):
        """Handle a / command."""
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["/quit", "/exit", "/q"]:
            self.running = False
            self.print_system("Shutting down...")
        elif cmd == "/help" or cmd == "/?":
            self.show_help()
        elif cmd == "/settings" or cmd == "/options" or cmd == "/config":
            self.show_settings_menu()
        elif cmd == "/verbose":
            self.toggle_verbose()
        elif cmd in ("/api", "/provider", "/command"):
            from core.settings_manager import get_settings
            from config.settings import REQUESTY_API_BASE_URL

            settings = get_settings()
            arg = arg.strip()

            if not arg:
                custom_base = (settings.get("api_base_url", "") or "").strip()
                custom_key = (settings.get("api_key", "") or "").strip()
                active_base = custom_base or REQUESTY_API_BASE_URL
                using_custom = bool(custom_base or custom_key)

                print()
                print(f"{Colors.BOLD}{Colors.CYAN}=== API PROVIDER ==={Colors.RESET}")
                print(f"  Active base URL: {active_base}")
                source = "Custom settings (api_base_url/api_key)" if using_custom else "Requesty (.env)"
                print(f"  Source: {source}")
                print()
                print("  Usage:")
                print("    /api <base_url> <api_key>")
                print("    /api reset            (switch back to Requesty/env)")
                print()
            else:
                lower = arg.lower()
                if lower in ("reset", "clear", "default"):
                    settings.set("api_base_url", "")
                    settings.set("api_key", "")
                    self.print_system("API provider reset to Requesty (.env)")
                else:
                    parts = arg.split()
                    if len(parts) < 2:
                        self.print_system("Usage: /api <base_url> <api_key>")
                    else:
                        base_url = parts[0].strip()
                        api_key = " ".join(parts[1:]).strip()
                        if not (base_url.startswith("http://") or base_url.startswith("https://")):
                            self.print_system("Base URL must start with http:// or https://")
                        else:
                            settings.set("api_base_url", base_url)
                            settings.set("api_key", api_key)
                            self.print_system("Custom API provider configured for future calls.")
        elif cmd == "/agents" or cmd == "/bots":
            self.show_agents()
        elif cmd == "/name":
            if arg:
                if len(arg) <= 20:
                    self.settings.username = arg
                    self.print_system(f"Name set to {arg}")
                else:
                    self.print_system("Name too long (max 20 chars)")
            else:
                self.print_system(f"Your name is: {self.settings.username}")
                self.print_system("Usage: /name <newname>")
        elif cmd == "/clear":
            self.chatroom.state.messages.clear()
            self.print_system("Chat history cleared")
        elif cmd == "/topic":
            if arg:
                # Set a conversation topic
                await self.chatroom.add_human_message(
                    content=f"Let's discuss: {arg}",
                    username="System",
                    user_id="system"
                )
                self.print_system(f"Topic set: {arg}")
                asyncio.create_task(self.trigger_staggered_responses())
            else:
                self.print_system("Usage: /topic <topic to discuss>")
        elif cmd == "/kick":
            # Temporarily disable a bot
            if arg:
                for agent in self.agents:
                    if agent.name.lower() == arg.lower():
                        self.disabled_agents.add(agent.name)
                        self.print_system(f"{agent.name} has been kicked")
                        return
                self.print_system(f"No agent named '{arg}'")
            else:
                self.print_system("Usage: /kick <agentname>")
        elif cmd == "/invite":
            # Re-enable a bot
            if arg:
                for agent in self.agents:
                    if agent.name.lower() == arg.lower():
                        self.disabled_agents.discard(agent.name)
                        self.print_system(f"{agent.name} has been invited back")
                        return
                self.print_system(f"No agent named '{arg}'")
            else:
                self.print_system("Usage: /invite <agentname>")
        elif cmd == "/spawn":
            if arg:
                from agents import AGENT_CLASSES
                if arg.lower() in AGENT_CLASSES:
                    agent = await self.chatroom.spawn_agent(arg.lower())
                    if agent:
                        self.agents.append(agent)
                        self.print_system(f"{agent.name} has joined the swarm!")
                    else:
                        self.print_system(f"Failed to spawn {arg}")
                else:
                    self.print_system(f"Unknown role: {arg}. Use /roles to see available roles.")
            else:
                self.print_system("Usage: /spawn <role>")
        
        elif cmd == "/roles":
            from agents import AGENT_CLASSES
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}=== AVAILABLE ROLES ==={Colors.RESET}")
            for role in AGENT_CLASSES.keys():
                print(f"  {Colors.GREEN}{role}{Colors.RESET}")
            print()
        
        elif cmd == "/status":
            status = self.chatroom.get_status()
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}=== SWARM STATUS ==={Colors.RESET}")
            print(f"  Running: {Colors.GREEN if status['is_running'] else Colors.RED}{status['is_running']}{Colors.RESET}")
            print(f"  Round: {status['round_number']}")
            print(f"  Messages: {status['message_count']}")
            print(f"  Agents: {len(status['active_agents'])}")
            print()
        
        elif cmd == "/tasks":
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            tasks = tm.get_all_tasks()
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}=== TASKS ==={Colors.RESET}")
            if not tasks:
                print(f"  {Colors.DIM}No tasks yet{Colors.RESET}")
            else:
                for task in tasks[-10:]:
                    status_colors = {"pending": Colors.YELLOW, "in_progress": Colors.BLUE, "completed": Colors.GREEN, "failed": Colors.RED}
                    color = status_colors.get(task.status.value, Colors.WHITE)
                    print(f"  {color}[{task.status.value}]{Colors.RESET} {task.description[:50]}...")
            print()
        
        elif cmd == "/files":
            self.view_scratch()
        
        elif cmd == "/plan":
            from config.settings import get_scratch_dir
            plan_path = get_scratch_dir() / "shared" / "master_plan.md"
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}=== MASTER PLAN ==={Colors.RESET}")
            if plan_path.exists():
                with open(plan_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(content[:2000])
                if len(content) > 2000:
                    print(f"\n{Colors.DIM}... (truncated, see scratch/shared/master_plan.md){Colors.RESET}")
            else:
                print(f"  {Colors.DIM}No master plan yet. Ask the Architect to create one!{Colors.RESET}")
            print()
        
        elif cmd == "/project":
            # Show current project info
            pm = get_project_manager()
            current = pm.current
            if current:
                info = current.get_info()
                print()
                print(f"{Colors.BOLD}{Colors.CYAN}=== CURRENT PROJECT ==={Colors.RESET}")
                print(f"  Name: {Colors.GREEN}{info['name']}{Colors.RESET}")
                print(f"  Path: {Colors.DIM}{info['path']}{Colors.RESET}")
                print(f"  Created: {Colors.DIM}{info['created_at']}{Colors.RESET}")
                if info['description']:
                    print(f"  Description: {info['description']}")
                print(f"  Has Master Plan: {'Yes' if info['has_master_plan'] else 'No'}")
                print()
            else:
                self.print_system("No project selected. Use /projects to select one.")
        
        elif cmd == "/projects":
            # List and switch projects
            pm = get_project_manager()
            projects = pm.list_projects()
            current = pm.current
            
            print()
            print(f"{Colors.BOLD}{Colors.CYAN}=== PROJECTS ==={Colors.RESET}")
            
            if projects:
                for i, proj in enumerate(projects, 1):
                    marker = f" {Colors.GREEN}(current){Colors.RESET}" if current and proj.name == current.name else ""
                    print(f"  {Colors.YELLOW}{i}.{Colors.RESET} {proj.name}{marker}")
            else:
                print(f"  {Colors.DIM}No projects yet{Colors.RESET}")
            
            print(f"  {Colors.GREEN}N.{Colors.RESET} Create new project")
            print()
            
            choice = input("Enter choice (or press Enter to cancel): ").strip()
            
            if not choice:
                return
            
            if choice.upper() == "N":
                name = input("Project name: ").strip()
                if name:
                    desc = input("Description (optional): ").strip()
                    project = pm.create_project(name, desc)
                    pm.set_current(project)
                    self.print_system(f"Created and switched to project: {project.name}")
                    self.print_system("Note: Restart the chatroom to use the new project's data.")
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(projects):
                        project = projects[idx]
                        pm.set_current(project)
                        self.print_system(f"Switched to project: {project.name}")
                        self.print_system("Note: Restart the chatroom to use the new project's data.")
                    else:
                        self.print_system("Invalid choice")
                except ValueError:
                    self.print_system("Invalid input")
        
        else:
            self.print_system(f"Unknown command: {cmd}. Type /help for commands")
    
    async def trigger_staggered_responses(self):
        """Trigger agent responses with current settings."""
        # Get active agents
        active_agents = [a for a in self.agents if a.name not in self.disabled_agents]
        random.shuffle(active_agents)
        
        # Limit to max responders
        agents_to_query = active_agents[:self.settings.max_responders]
        
        round_messages = []
        for agent in agents_to_query:
            # Stagger delay
            if round_messages:
                delay = random.uniform(
                    self.settings.response_delay_min,
                    self.settings.response_delay_max
                )
                await asyncio.sleep(delay)
            
            if agent.should_respond():
                response = await agent.respond(self.chatroom.state.messages)
                if response:
                    await self.chatroom._broadcast_message(response)
                    round_messages.append(response)
                    
                    # Notify other agents
                    for other in self.agents:
                        if other.agent_id != response.sender_id:
                            await other.process_incoming_message(response)
    
    async def run_background_conversation(self):
        """Run background conversation rounds if auto-chat enabled."""
        while self.running:
            await asyncio.sleep(self.settings.round_delay)
            if self.running and self.settings.auto_chat and self.chatroom.state.messages:
                await self.trigger_staggered_responses()
    
    def message_callback(self, message: Message):
        """Callback for new messages."""
        # Don't echo back user's own messages (they already see them)
        if message.sender_id == "local_user":
            return
        self.print_message(message)
    
    def select_project(self) -> Project:
        """Interactive project selection at startup."""
        pm = get_project_manager()
        projects = pm.list_projects()
        last_project = pm.get_last_project()
        
        print()
        print(f"{Colors.BOLD}{Colors.CYAN}=== SELECT PROJECT ==={Colors.RESET}")
        print()
        
        if projects:
            for i, proj in enumerate(projects, 1):
                marker = f" {Colors.GREEN}(last used){Colors.RESET}" if proj.name == last_project else ""
                print(f"  {Colors.YELLOW}{i}.{Colors.RESET} {proj.name}{marker}")
        else:
            print(f"  {Colors.DIM}No existing projects{Colors.RESET}")
        
        print(f"  {Colors.GREEN}N.{Colors.RESET} Create new project")
        print()
        
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
                    # Invalid index, use default
                    if last_project and pm.project_exists(last_project):
                        project = pm.load_project(last_project)
                    elif projects:
                        project = projects[0]
                    else:
                        project = pm.create_project("default")
            except ValueError:
                # Not a number, use default
                if last_project and pm.project_exists(last_project):
                    project = pm.load_project(last_project)
                elif projects:
                    project = projects[0]
                else:
                    project = pm.create_project("default")
        else:
            # Empty input - use last project or first available or create default
            if last_project and pm.project_exists(last_project):
                project = pm.load_project(last_project)
            elif projects:
                project = projects[0]
            else:
                project = pm.create_project("default")
        
        pm.set_current(project)
        print()
        self.print_system(f"Using project: {project.name}")
        return project
    
    async def run(self):
        """Run the interactive chatroom."""
        # Setup
        self.setup_logging()
        
        # Interactive setup if needed
        if not setup_env_interactive():
            return
        
        # Validate config
        is_valid, errors = validate_config()
        if not is_valid:
            for error in errors:
                self.print_system(f"Error: {error}")
            return
        
        # Project selection
        project = self.select_project()
        
        # Initialize chatroom
        self.chatroom = Chatroom()
        
        # Start with Architect and ensure Project Manager is available
        from agents import create_agent
        from config.settings import ARCHITECT_MODEL
        
        architect = create_agent("architect", model=ARCHITECT_MODEL)
        self.agents = [architect]
        await self.chatroom.initialize(self.agents)

        # Spawn Checky McManager (project_manager) for CLI sessions
        try:
            from core.settings_manager import get_settings
            settings = get_settings()
            swarm_model = settings.get("swarm_model", ARCHITECT_MODEL)
            checky = await self.chatroom.spawn_agent("project_manager", model=swarm_model)
        except Exception:
            checky = None

        if checky:
            self.agents.append(checky)
        
        # Start Traffic Control relay for visualization dashboard
        try:
            from core.traffic_relay import start_traffic_relay
            self.traffic_relay = await start_traffic_relay(self.chatroom)
            self.print_system("Traffic Control relay started on ws://localhost:8766")
        except Exception as e:
            self.print_system(f"Traffic Control relay failed: {e}")
            self.traffic_relay = None
        
        # Register message callback
        self.chatroom.on_message(self.message_callback)
        
        # Print header
        self.print_header()
        
        # Show project info
        self.print_system(f"Project: {project.name}")
        
        # Show agents
        self.print_system("Agents joined:")
        for agent in self.agents:
            color = self.get_color(agent.name)
            print(f"  {color}•{Colors.RESET} {color}{agent.name}{Colors.RESET}")
        print()
        
        # Prompt for username
        print(f"{Colors.BOLD}What's your name?{Colors.RESET} (press Enter for '{self.settings.username}')")
        name_input = input("> ").strip()
        if name_input:
            self.settings.username = name_input[:20]
        print()
        
        self.print_system(f"Welcome, {self.settings.username}! Type /help for commands.")
        print()
        
        # Run tasks
        try:
            input_task = asyncio.create_task(self.handle_user_input())
            background_task = asyncio.create_task(self.run_background_conversation())
            
            # Wait for input task (main loop)
            await input_task
            background_task.cancel()
            
        except KeyboardInterrupt:
            self.print_system("Interrupted...")
        finally:
            # Stop Traffic Control relay
            if hasattr(self, 'traffic_relay') and self.traffic_relay:
                await self.traffic_relay.stop()
            await self.chatroom.shutdown()
            self.print_system("Chatroom closed. Goodbye!")


def setup_env_interactive():
    """Interactive .env setup if needed."""
    from dotenv import load_dotenv
    from core.settings_manager import get_settings

    env_path = Path(__file__).parent / ".env"
    existing_key = os.getenv("REQUESTY_API_KEY", "")

    settings = get_settings()
    custom_base = (settings.get("api_base_url", "") or "").strip()
    custom_key = (settings.get("api_key", "") or "").strip()
    
    # Try loading .env first
    if env_path.exists():
        load_dotenv(env_path, override=True)
        existing_key = os.getenv("REQUESTY_API_KEY", "")
    
    if (env_path.exists() and existing_key) or (custom_base and custom_key):
        return True
    
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  FIRST TIME SETUP{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print()
    
    if not env_path.exists():
        print(f"{Colors.SYSTEM}No .env file found. Let's create one!{Colors.RESET}")
    else:
        print(f"{Colors.SYSTEM}API key not configured.{Colors.RESET}")
    print()
    
    print(f"Get your Requesty API key at: {Colors.CYAN}https://requesty.ai{Colors.RESET}")
    print()
    
    while True:
        api_key = input(f"{Colors.BOLD}Enter your Requesty API key (or 'q' to quit): {Colors.RESET}").strip()
        
        if api_key.lower() == 'q':
            print("Setup cancelled.")
            return False
        
        if not api_key:
            print("API key cannot be empty.")
            continue
        
        break
    
    # Write .env
    env_content = f"""# Multi-Agent Chatroom Configuration
REQUESTY_API_KEY={api_key}
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765
LOG_LEVEL=INFO
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"\n{Colors.GREEN}Configuration saved!{Colors.RESET}\n")
    load_dotenv(env_path, override=True)
    
    return True


def main():
    """Entry point - launches dashboard by default."""
    import argparse
    
    # Enable ANSI colors on Windows
    if sys.platform == "win32":
        os.system("color")
        # Also try to enable VT100 processing
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except:
            pass
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Multi-Agent AI Chatroom")
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="Use the basic CLI interface instead of the dashboard"
    )
    parser.add_argument(
        "--tui",
        action="store_true",
        help="Use the Textual TUI dashboard (recommended, requires: pip install textual)"
    )
    args = parser.parse_args()
    
    if args.cli:
        # Use the basic CLI interface
        chat = InteractiveChatroom()
        try:
            asyncio.run(chat.run())
        except KeyboardInterrupt:
            pass
    elif args.tui:
        # Use the new Textual TUI dashboard
        try:
            from dashboard_tui import main as tui_main
            tui_main()
        except ImportError as e:
            print(f"Textual not installed. Run: pip install textual")
            print(f"Error: {e}")
            print("Falling back to CLI mode...")
            chat = InteractiveChatroom()
            try:
                asyncio.run(chat.run())
            except KeyboardInterrupt:
                pass
    else:
        # Launch Rich dashboard by default
        from dashboard import DashboardUI, RICH_AVAILABLE
        
        if not RICH_AVAILABLE:
            print("Rich library not installed. Run: pip install rich")
            print("Falling back to CLI mode...")
            chat = InteractiveChatroom()
            try:
                asyncio.run(chat.run())
            except KeyboardInterrupt:
                pass
        else:
            dashboard = DashboardUI()
            try:
                asyncio.run(dashboard.run())
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
