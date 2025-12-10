"""
Session Controller - Shared core logic for TUI and CLI modes.

This module provides a unified interface for managing swarm sessions,
abstracting away the chatroom, orchestrator, and task management
so that both TUI and CLI frontends can use the same core logic.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime

from core.chatroom import Chatroom, set_chatroom
from core.models import Message, MessageRole, MessageType, AgentStatus
from core.project_manager import Project, get_project_manager
from core.settings_manager import get_settings
from core.task_manager import get_task_manager, TaskStatus
from core.token_tracker import get_token_tracker
from agents import create_agent, AGENT_CLASSES
from config.settings import ARCHITECT_MODEL, get_scratch_dir

logger = logging.getLogger(__name__)


class SessionController:
    """
    Shared controller for TUI and CLI modes.
    
    Encapsulates all swarm session logic including:
    - Chatroom initialization and management
    - Agent spawning and orchestration
    - Task management and dispatch
    - Devussy integration
    - Message routing with callbacks
    
    Both TUI and CLI modes should use this controller instead of
    directly manipulating the Chatroom.
    """
    
    def __init__(self):
        self._project: Optional[Project] = None
        self._username: str = "You"
        self._chatroom: Optional[Chatroom] = None
        self._orchestrator = None
        self._auto_dispatcher = None
        self._traffic_relay = None
        self._devussy_mode: bool = False
        self._is_processing: bool = False
        self._running: bool = False
        
        # Callbacks for UI
        self.on_message: Optional[Callable[[Message], None]] = None
        self.on_status: Optional[Callable[[str], None]] = None
        self.on_agent_update: Optional[Callable[[str, Dict], None]] = None
        self.on_api_event: Optional[Callable[[str, str, Dict], None]] = None
        self.on_tool_call: Optional[Callable[[str, str, str], None]] = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # PROPERTIES
    # ─────────────────────────────────────────────────────────────────────────
    
    @property
    def project(self) -> Optional[Project]:
        return self._project
    
    @property
    def username(self) -> str:
        return self._username
    
    @property
    def chatroom(self) -> Optional[Chatroom]:
        return self._chatroom
    
    @property
    def is_devussy_mode(self) -> bool:
        return self._devussy_mode
    
    @property
    def is_processing(self) -> bool:
        return self._is_processing
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def agents(self) -> List:
        """Get list of active agents."""
        if self._chatroom:
            return list(self._chatroom._agents.values())
        return []
    
    # ─────────────────────────────────────────────────────────────────────────
    # INITIALIZATION
    # ─────────────────────────────────────────────────────────────────────────
    
    async def initialize(
        self,
        project: Project,
        username: str,
        load_history: bool = True,
        devussy_mode: bool = False
    ) -> bool:
        """
        Initialize the session with project, user, and mode settings.
        
        Args:
            project: The project to use
            username: User's display name
            load_history: Whether to load previous chat history
            devussy_mode: Whether to use devussy orchestration
            
        Returns:
            True if initialization succeeded
        """
        self._project = project
        self._username = username
        self._devussy_mode = devussy_mode
        self._running = True
        
        settings = get_settings()
        
        # Store devussy_mode in settings so other components can check it
        settings.set("devussy_mode", devussy_mode)
        
        # Create chatroom
        self._chatroom = Chatroom(load_history=load_history)
        set_chatroom(self._chatroom)
        
        # Set up tool call callback
        if self.on_tool_call:
            self._chatroom.on_tool_call = self.on_tool_call
        
        # Create architect
        model = settings.get("architect_model", ARCHITECT_MODEL)
        architect = create_agent("architect", model=model)
        
        # If devussy mode, inject devplan-following prompt
        if devussy_mode:
            devussy_prompt = self._get_devussy_architect_prompt()
            if devussy_prompt:
                architect.system_prompt = devussy_prompt + "\n\n" + architect.system_prompt
        
        await self._chatroom.initialize([architect])
        
        # Spawn project manager
        try:
            swarm_model = settings.get("swarm_model", ARCHITECT_MODEL)
            await self._chatroom.spawn_agent("project_manager", model=swarm_model)
        except Exception as e:
            logger.warning(f"Could not spawn project manager: {e}")
        
        # Register message callback
        if self.on_message:
            self._chatroom.on_message(self._message_callback)
        
        # Start traffic relay (optional)
        await self._start_traffic_relay()
        
        # Initialize orchestrator (devussy mode)
        if devussy_mode:
            await self._init_orchestrator()
        
        await self._broadcast_status(f"Session initialized for project: {project.name}")
        
        return True
    
    async def _start_traffic_relay(self):
        """Start the WebSocket traffic relay for visualization."""
        try:
            from core.traffic_relay import start_traffic_relay
            self._traffic_relay = await start_traffic_relay(self._chatroom)
            await self._broadcast_status("Traffic Control relay started on ws://localhost:8766")
        except Exception as e:
            logger.warning(f"Traffic relay failed: {e}")
            self._traffic_relay = None
    
    async def _init_orchestrator(self):
        """Initialize the swarm orchestrator for devussy mode."""
        try:
            from core.swarm_orchestrator import SwarmOrchestrator, set_orchestrator
            self._orchestrator = SwarmOrchestrator(Path(self._project.root))
            if await self._orchestrator.initialize():
                set_orchestrator(self._orchestrator)
                await self._broadcast_status("Orchestrator initialized - real-time task tracking enabled")
            else:
                self._orchestrator = None
        except Exception as e:
            logger.warning(f"Orchestrator init failed: {e}")
            self._orchestrator = None
        
        # Initialize file ownership tracker for collision prevention
        try:
            from core.file_ownership import init_file_tracker
            init_file_tracker(Path(self._project.root))
            logger.debug("File ownership tracker initialized")
        except Exception as e:
            logger.warning(f"File tracker init failed: {e}")
    
    def _get_devussy_architect_prompt(self) -> Optional[str]:
        """Get the devussy-specific architect prompt."""
        try:
            from core.devussy_integration import load_devplan_for_swarm
            from agents.lean_prompts import LEAN_DEVUSSY_ARCHITECT_PROMPT
            
            devplan_data = load_devplan_for_swarm(Path(self._project.root))
            if not devplan_data or not devplan_data.get("has_devplan"):
                return None
            
            return LEAN_DEVUSSY_ARCHITECT_PROMPT
        except Exception as e:
            logger.warning(f"Failed to load devussy prompt: {e}")
            return None
    
    async def shutdown(self):
        """Gracefully shut down the session."""
        self._running = False
        
        # Stop traffic relay
        if self._traffic_relay:
            try:
                await self._traffic_relay.stop()
            except Exception:
                pass
        
        # Shutdown chatroom
        if self._chatroom:
            await self._chatroom.shutdown()
        
        await self._broadcast_status("Session closed")
    
    # ─────────────────────────────────────────────────────────────────────────
    # CALLBACKS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _message_callback(self, message: Message):
        """Internal message callback that forwards to UI."""
        if self.on_message:
            try:
                self.on_message(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
    
    async def _broadcast_status(self, text: str):
        """Broadcast a status message."""
        if self.on_status:
            try:
                self.on_status(text)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # USER ACTIONS
    # ─────────────────────────────────────────────────────────────────────────
    
    async def send_message(self, text: str) -> List[Message]:
        """
        Send a user message and trigger agent responses.
        
        Args:
            text: The message text
            
        Returns:
            List of response messages from agents
        """
        if not self._chatroom:
            return []
        
        # Check for special "go" command
        if text.strip().lower() == "go":
            await self.handle_go_command()
            return []
        
        # Add human message
        await self._chatroom.add_human_message(
            content=text,
            username=self._username,
            user_id="session_user"
        )
        
        # Run conversation round
        return await self.run_round()
    
    async def run_round(self) -> List[Message]:
        """
        Run a single conversation round.
        
        Returns:
            List of messages generated this round
        """
        if not self._chatroom:
            return []
        
        if self._is_processing:
            return []
        
        self._is_processing = True
        try:
            messages = await self._chatroom.run_conversation_round()
            return messages
        finally:
            self._is_processing = False
    
    async def handle_go_command(self) -> bool:
        """
        Handle the 'go' command using AutoDispatcher (zero tokens).
        
        Returns:
            True if a task was dispatched
        """
        # Try AutoDispatcher first (devussy mode)
        if self._devussy_mode:
            try:
                from core.auto_dispatcher import get_auto_dispatcher
                dispatcher = get_auto_dispatcher()
                
                async def status_cb(msg: str):
                    await self._broadcast_status(msg)
                
                dispatcher.set_status_callback(status_cb)
                
                dispatched = await dispatcher.dispatch_next_task()
                
                if dispatched:
                    await self._broadcast_status("Task dispatched! Worker will start automatically.")
                    # Run round for the worker to respond
                    await self.run_round()
                    return True
                else:
                    await self._broadcast_status("No tasks to dispatch right now.")
                    return False
                    
            except Exception as e:
                logger.warning(f"AutoDispatcher failed, falling back to Architect: {e}")
        
        # Fallback: send "go" to Architect
        if self._chatroom:
            await self._chatroom.add_human_message(
                content="go",
                username=self._username,
                user_id="session_user"
            )
            await self.run_round()
        
        return False
    
    async def spawn_agent(self, role: str) -> Optional[Any]:
        """
        Spawn a new agent by role.
        
        Args:
            role: The agent role (e.g., 'backend_dev')
            
        Returns:
            The spawned agent or None
        """
        if not self._chatroom:
            return None
        
        if role not in AGENT_CLASSES:
            await self._broadcast_status(f"Unknown role: {role}")
            return None
        
        settings = get_settings()
        model = settings.get("swarm_model", ARCHITECT_MODEL)
        
        agent = await self._chatroom.spawn_agent(role, model=model)
        if agent:
            await self._broadcast_status(f"{agent.name} joined the swarm!")
        
        return agent
    
    async def stop_current(self) -> int:
        """
        Stop all in-progress tasks.
        
        Returns:
            Number of tasks stopped
        """
        tm = get_task_manager()
        stopped = 0
        
        for task in tm.get_all_tasks():
            if task.status == TaskStatus.IN_PROGRESS:
                tm.update_task_status(task.id, "failed", result="Stopped by user")
                stopped += 1
        
        if stopped:
            await self._broadcast_status(f"Stopped {stopped} task(s)")
        
        return stopped
    
    async def halt_agent(self, agent_name: str) -> bool:
        """
        Halt a specific agent's work.
        
        Args:
            agent_name: Name of the agent to halt
            
        Returns:
            True if successful
        """
        if not self._chatroom:
            return False
        
        # Find the agent
        target = None
        for agent in self._chatroom._agents.values():
            if agent.name.lower() == agent_name.lower():
                target = agent
                break
        
        if not target:
            await self._broadcast_status(f"Agent not found: {agent_name}")
            return False
        
        # Stop their tasks
        tm = get_task_manager()
        halted = 0
        
        for task in tm.get_all_tasks():
            if task.assigned_to == target.agent_id and task.status == TaskStatus.IN_PROGRESS:
                tm.update_task_status(task.id, "failed", result="Halted by user")
                halted += 1
        
        # Reset agent status
        target.status = AgentStatus.IDLE
        target.current_task_id = None
        
        await self._broadcast_status(f"Halted {target.name} ({halted} task(s) stopped)")
        
        return True
    
    # ─────────────────────────────────────────────────────────────────────────
    # STATE QUERIES
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_status(self) -> Dict[str, Any]:
        """Get current session status."""
        if not self._chatroom:
            return {
                "is_running": False,
                "round_number": 0,
                "message_count": 0,
                "agent_count": 0,
                "devussy_mode": self._devussy_mode,
            }
        
        chatroom_status = self._chatroom.get_status()
        tracker = get_token_tracker()
        stats = tracker.get_stats()
        
        return {
            "is_running": chatroom_status["is_running"],
            "round_number": chatroom_status["round_number"],
            "message_count": chatroom_status["message_count"],
            "agent_count": len(chatroom_status["active_agents"]),
            "total_tokens": stats.get("total_tokens", 0),
            "api_calls": stats.get("call_count", 0),
            "devussy_mode": self._devussy_mode,
            "project_name": self._project.name if self._project else "None",
        }
    
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get information about all agents."""
        if not self._chatroom:
            return []
        
        result = []
        for agent in self._chatroom._agents.values():
            result.append({
                "name": agent.name,
                "agent_id": agent.agent_id,
                "status": agent.status.value,
                "model": agent.model,
                "current_task_id": getattr(agent, "current_task_id", None),
                "current_task_description": getattr(agent, "current_task_description", ""),
            })
        
        return result
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks with their status."""
        tm = get_task_manager()
        result = []
        
        for task in tm.get_all_tasks():
            result.append({
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "assigned_to": task.assigned_to,
                "result": getattr(task, "result", None),
                "created_at": task.created_at,
                "completed_at": getattr(task, "completed_at", None),
            })
        
        return result
    
    def get_token_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        tracker = get_token_tracker()
        return tracker.get_stats()
    
    def get_devplan_summary(self) -> str:
        """Get a summary of the devplan/master plan."""
        if not self._project:
            return "No project selected"
        
        # Try task_queue.md first (devussy mode)
        task_queue_path = get_scratch_dir() / "shared" / "task_queue.md"
        if task_queue_path.exists():
            content = task_queue_path.read_text(encoding='utf-8')
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            return content
        
        # Try devplan.md
        devplan_path = get_scratch_dir() / "shared" / "devplan.md"
        if devplan_path.exists():
            content = devplan_path.read_text(encoding='utf-8')
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            return content
        
        # Try master_plan.md
        plan_path = get_scratch_dir() / "shared" / "master_plan.md"
        if plan_path.exists():
            content = plan_path.read_text(encoding='utf-8')
            if len(content) > 2000:
                content = content[:2000] + "\n... (truncated)"
            return content
        
        return "No devplan or master plan found yet. Ask the Architect to create one!"
    
    def get_available_roles(self) -> List[str]:
        """Get list of available agent roles."""
        return list(AGENT_CLASSES.keys())


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_controller: Optional[SessionController] = None


def get_session_controller() -> SessionController:
    """Get or create the global session controller."""
    global _controller
    if _controller is None:
        _controller = SessionController()
    return _controller


def reset_session_controller():
    """Reset the global session controller (for testing)."""
    global _controller
    _controller = None
