"""
Chatroom orchestrator for Multi-Agent Chatroom.

This module manages the AI chatroom simulation, coordinating
multiple agents to have natural conversations together.
"""

import asyncio
import random
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
import logging

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    AGENT_RESPONSE_DELAY_MIN,
    AGENT_RESPONSE_DELAY_MAX,
    MAX_CONCURRENT_API_CALLS,
    get_chat_history_path,
    ensure_data_directory
)
from core.models import Message, MessageRole, MessageType, ChatroomState, AgentStatus, TaskStatus
from agents import BaseAgent, create_all_default_agents

logger = logging.getLogger(__name__)


class Chatroom:
    """
    Orchestrates multi-agent conversations.
    
    Manages:
    - Agent registration and lifecycle
    - Message routing and history
    - Conversation rounds with concurrent agent responses
    - Human participant integration
    - Message broadcasting to external listeners
    """
    
    def __init__(self, load_history: bool = True):
        """Initialize the chatroom.

        Args:
            load_history: Whether to load prior chat history from disk on init.
        """
        self.state = ChatroomState()
        self._agents: Dict[str, BaseAgent] = {}
        self._message_callbacks: List[Callable[[Message], None]] = []
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_API_CALLS)
        self._running = False
        self._conversation_task: Optional[asyncio.Task] = None
        # Optional callback for tool calls: (agent_name, tool_name, result_summary)
        self.on_tool_call: Optional[Callable[[str, str, str], None]] = None
        # Control whether history is loaded from disk during initialize
        self._load_history_on_init = load_history
    
    async def initialize(self, agents: Optional[List[BaseAgent]] = None):
        """
        Initialize the chatroom with agents.
        
        Args:
            agents: Optional list of agents. Uses defaults if not provided.
        """
        if agents is None:
            agents = create_all_default_agents()
        
        for agent in agents:
            await self.add_agent(agent)
        
        # Load previous history if requested and it exists
        if self._load_history_on_init:
            await self._load_history()
        
        logger.info(f"Chatroom initialized with {len(self._agents)} agents")
    
    async def add_agent(self, agent: BaseAgent):
        """
        Add an agent to the chatroom.
        
        Args:
            agent: The agent to add
        """
        self._agents[agent.agent_id] = agent
        self.state.active_agents.append(agent.agent_id)
        
        # Announce agent joining
        join_message = Message(
            content=f"{agent.name} has joined the chat.",
            sender_name="System",
            sender_id="system",
            role=MessageRole.SYSTEM,
            message_type=MessageType.JOIN
        )
        await self._broadcast_message(join_message)
        
        logger.info(f"Agent {agent.name} added to chatroom")
    
    async def spawn_agent(self, role: str, model: str = None) -> Optional[BaseAgent]:
        """
        Dynamically spawn a new agent.
        
        Args:
            role: The role/type of agent (e.g., 'backend_dev')
            model: Optional model override
            
        Returns:
            The created agent or None on failure
        """
        try:
            from agents import create_agent
            from config.settings import SWARM_MODEL
            from agents import AGENT_CLASSES

            # Use default swarm model if none provided
            if not model:
                model = SWARM_MODEL

            # Determine the target class for this role
            if role not in AGENT_CLASSES:
                logger.error(f"Unknown role: {role}")
                return None

            target_class = AGENT_CLASSES[role]
            existing_of_type = [a for a in self._agents.values() if isinstance(a, target_class)]

            singleton_roles = {"project_manager", "backend_dev", "frontend_dev", "qa_engineer", "devops", "tech_writer"}
            if role in singleton_roles and existing_of_type:
                logger.info(f"{role} already active; reusing existing instance")
                return existing_of_type[0]

            count = len(existing_of_type)

            name_suffix = None
            if count > 0:
                name_suffix = str(count + 1)
            
            # Announce spawning
            await self._broadcast_status(f"🚀 Spawning {role}...")
            
            agent = create_agent(role, model, name_suffix)
            await self.add_agent(agent)
            
            # Announce ready
            await self._broadcast_status(f"✅ {agent.name} is ready for work")
            
            return agent
        except Exception as e:
            logger.error(f"Failed to spawn agent {role}: {e}")
            return None

    async def assign_task(self, agent_name: str, task_description: str) -> bool:
        """Assign a task to an agent.

        If a *semantically identical* task (same normalized description) is
        already open (pending or in_progress), this will **reassign** that task
        to the new agent instead of creating a duplicate. This prevents multiple
        workers from racing on the same brief.

        Args:
            agent_name: Name of the agent (case-insensitive)
            task_description: Description of the task

        Returns:
            True if successful
        """
        from core.task_manager import get_task_manager

        # Find agent by display name (case-insensitive)
        target_agent = None
        for agent in self._agents.values():
            if agent.name.lower() == agent_name.lower():
                target_agent = agent
                break

        if not target_agent:
            logger.error(f"Agent not found: {agent_name}")
            return False

        task_manager = get_task_manager()

        # ENFORCE ONE-TASK-PER-AGENT: Block if agent is already WORKING on a different task
        if (
            target_agent.status == AgentStatus.WORKING
            and target_agent.current_task_id is not None
        ):
            existing_task = task_manager.get_task(target_agent.current_task_id)
            if existing_task and existing_task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                logger.warning(
                    f"Cannot assign new task to {agent_name}: already working on task {target_agent.current_task_id[:8]}"
                )
                await self._broadcast_status(
                    f"⚠️ {target_agent.name} is busy. Wait for them to call complete_my_task()."
                )
                return False

        # Normalize description to detect duplicates (collapse whitespace)
        def _norm(text: str) -> str:
            return " ".join((text or "").split()).strip().lower()

        normalized_new = _norm(task_description)
        existing_task = None

        for t in task_manager.get_all_tasks():
            if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                if _norm(getattr(t, "description", "")) == normalized_new:
                    existing_task = t
                    break

        reassigned = False
        previous_owner_name = None

        if existing_task is not None:
            # Reuse the existing task instead of creating a duplicate.
            task = existing_task

            # If it was previously assigned to someone else, release them.
            if getattr(task, "assigned_to", None):
                prev_agent = self._agents.get(task.assigned_to)
                if prev_agent and prev_agent.agent_id != target_agent.agent_id:
                    prev_agent.status = AgentStatus.IDLE
                    prev_agent.current_task_id = None
                    setattr(prev_agent, "current_task_description", "")
                    previous_owner_name = prev_agent.name

            # Assign task to the new agent in the TaskManager
            task_manager.assign_task(task.id, target_agent.agent_id)
            reassigned = True
        else:
            # Create a brand new task
            task = task_manager.create_task(task_description)
            task_manager.assign_task(task.id, target_agent.agent_id)

        # Update target agent state
        target_agent.status = AgentStatus.WORKING
        target_agent.current_task_id = task.id
        setattr(target_agent, "current_task_description", task_description)

        # Announce assignment or reassignment with status
        if reassigned and previous_owner_name:
            await self._broadcast_status(
                f"📋 Reassigning task from {previous_owner_name} to {target_agent.name}..."
            )
            msg_text = (
                f"📋 Task Reassigned from {previous_owner_name} to {target_agent.name}: "
                f"{task_description[:100]}{'...' if len(task_description) > 100 else ''}"
            )
        else:
            await self._broadcast_status(f"📋 Assigning task to {target_agent.name}...")
            msg_text = (
                f"📋 Task Assigned to {target_agent.name}: "
                f"{task_description[:100]}{'...' if len(task_description) > 100 else ''}"
            )

        assignment_msg = Message(
            content=msg_text,
            sender_name="System",
            sender_id="system",
            role=MessageRole.SYSTEM,
            message_type=MessageType.SYSTEM_NOTICE
        )
        await self._broadcast_message(assignment_msg)

        return True

    async def remove_agent(self, agent_id: str):
        """
        Remove an agent from the chatroom.
        
        Args:
            agent_id: ID of the agent to remove
        """
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            await agent.close()
            del self._agents[agent_id]
            self.state.active_agents.remove(agent_id)
            
            leave_message = Message(
                content=f"{agent.name} has left the chat.",
                sender_name="System",
                sender_id="system",
                role=MessageRole.SYSTEM,
                message_type=MessageType.LEAVE
            )
            await self._broadcast_message(leave_message)
            
            logger.info(f"Agent {agent.name} removed from chatroom")
    
    def on_message(self, callback: Callable[[Message], None]):
        """
        Register a callback for new messages.
        
        Used by websocket server and Discord bot to receive messages.
        
        Args:
            callback: Function to call with each new message
        """
        self._message_callbacks.append(callback)
    
    def remove_message_callback(self, callback: Callable[[Message], None]):
        """Remove a message callback."""
        if callback in self._message_callbacks:
            self._message_callbacks.remove(callback)
    
    async def _broadcast_message(self, message: Message):
        """
        Broadcast a message to all callbacks and add to history.
        
        Args:
            message: The message to broadcast
        """
        self.state.add_message(message)
        
        for callback in self._message_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
    
    async def add_human_message(self, content: str, username: str, user_id: str):
        """
        Add a message from a human participant.
        
        Args:
            content: Message content
            username: Display name
            user_id: Unique user identifier
        """
        message = Message(
            content=content,
            sender_name=username,
            sender_id=user_id,
            role=MessageRole.HUMAN,
            message_type=MessageType.CHAT
        )
        
        await self._broadcast_message(message)
        
        # Notify all agents about the new message
        # Use list() to create a copy of values to avoid "dictionary changed size during iteration"
        # if an agent spawns another agent while processing the message
        for agent in list(self._agents.values()):
            await agent.process_incoming_message(message)
        
        logger.debug(f"Human message added from {username}: {content[:50]}...")
        
        return message
    
    async def _get_agent_response(self, agent: BaseAgent) -> Optional[Message]:
        """
        Get a response from an agent with concurrency control.
        
        Args:
            agent: The agent to query
            
        Returns:
            Message from the agent or None
        """
        async with self._semaphore:
            try:
                return await agent.respond(self.state.messages, self._broadcast_status)
            except Exception as e:
                logger.error(f"Error getting response from {agent.name}: {e}")
                return None
    
    async def _broadcast_status(self, status_text: str):
        """Broadcast a status update (not stored in history, just for display)."""
        status_msg = Message(
            content=status_text,
            sender_name="System",
            sender_id="status",
            role=MessageRole.SYSTEM,
            message_type=MessageType.SYSTEM_NOTICE
        )
        # Only call callbacks, don't add to history
        for callback in self._message_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(status_msg)
                else:
                    callback(status_msg)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
        
        # Parse tool calls from status and forward to tool callback
        if self.on_tool_call and "🔧" in status_text:
            # Format: "🔧 AgentName: ToolAction"
            try:
                parts = status_text.replace("🔧 ", "").split(": ", 1)
                if len(parts) == 2:
                    agent_name = parts[0]
                    tool_action = parts[1]
                    self.on_tool_call(agent_name, tool_action, "")
            except Exception as e:
                logger.debug(f"Could not parse tool call from status: {e}")

    async def run_conversation_round(self) -> List[Message]:
        """
        Run a single conversation round.
        
        Strict Orchestration Logic:
        - Iterate through ALL agents.
        - Check if they want to speak (should_respond).
        - Architect always gets a chance.
        - Workers only speak if ASSIGNED (and have something to say).
        
        Returns:
            List of messages generated this round
        """
        self.state.round_number += 1
        logger.info(f"Starting conversation round {self.state.round_number}")
        
        # Get list of agents (Architect first, then Project Manager, then workers by status)
        agents = list(self._agents.values())
        architects = [a for a in agents if "Architect" in a.__class__.__name__]
        managers = [a for a in agents if "ProjectManager" in a.__class__.__name__ or "McManager" in a.name]
        workers = [a for a in agents if a not in architects and a not in managers]
        
        # Sort workers: WORKING agents first (they have active tasks), then IDLE
        workers.sort(key=lambda a: (0 if a.status.value == "working" else 1, a.name))
        
        ordered_agents = architects + managers + workers

        round_messages: List[Message] = []

        # Decide who actually wants to speak this round (strict orchestration still applies)
        speakers: List[BaseAgent] = []
        for agent in ordered_agents:
            try:
                if agent.should_respond():
                    speakers.append(agent)
            except Exception as e:
                logger.error(f"Error in should_respond for {agent.name}: {e}")

        if not speakers:
            # Log why each key agent didn't respond for debugging
            architect = next((a for a in architects), None)
            if architect:
                logger.info(f"Architect {architect.name} did not respond. Status: {architect.status.value}, "
                           f"Memory size: {len(architect._short_term_memory)}")
            logger.info("No agents chose to respond this round")
            
            # STILL check task completion even if no one responded!
            # This fixes the bug where swarm stalls after all tasks complete
            try:
                from core.task_manager import get_task_manager
                tm = get_task_manager()
                all_tasks = tm.get_all_tasks()
                open_tasks = [t for t in all_tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
                completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
                
                if not open_tasks and completed_tasks:
                    logger.info(f"All {len(completed_tasks)} tasks complete, sending Auto Orchestrator message")
                    await self._send_auto_orchestrator_message(len(completed_tasks))
            except Exception as e:
                logger.warning(f"Failed to check task completion: {e}")
            
            return []

        # Announce that these agents are thinking, so the UI shows activity immediately
        for agent in speakers:
            await self._broadcast_status(f"⏳ {agent.name} is thinking...")

        # Kick off API/tool work in parallel, bounded by MAX_CONCURRENT_API_CALLS via _get_agent_response
        tasks = {asyncio.create_task(self._get_agent_response(agent)): agent for agent in speakers}

        while tasks:
            done, _ = await asyncio.wait(
                set(tasks.keys()),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                agent = tasks.pop(task, None)
                if agent is None:
                    continue
                try:
                    response = task.result()
                except Exception as e:
                    logger.error(f"Error getting response from {agent.name}: {e}")
                    continue

                if response is not None:
                    await self._broadcast_message(response)
                    round_messages.append(response)

                    # Notify other agents about this message
                    for other_agent in list(self._agents.values()):
                        if other_agent.agent_id != response.sender_id:
                            await other_agent.process_incoming_message(response)
        
        # Log round summary
        agent_summary = ", ".join([f"{a.name}:{a.status.value}" for a in self._agents.values()])
        logger.info(f"Round {self.state.round_number} complete: {len(round_messages)} messages. Agents: {agent_summary}")
        
        # Check if any workers have pending tasks and need to respond
        workers_with_tasks = [
            a for a in self._agents.values() 
            if "Architect" not in a.__class__.__name__ and a.status.value == "working"
        ]
        
        if workers_with_tasks:
            worker_names = [w.name for w in workers_with_tasks]
            logger.info(f"Workers with tasks: {worker_names}")
            await self._broadcast_status(f"⚡ {len(workers_with_tasks)} worker(s) processing tasks...")
            # Run another round to let workers respond
            await asyncio.sleep(1.0)
            worker_messages = await self._run_worker_round(workers_with_tasks)
            round_messages.extend(worker_messages)
            logger.info(f"Worker round complete: {len(worker_messages)} messages")
        
        # Check if all tasks are now complete and send Auto Orchestrator message
        try:
            from core.task_manager import get_task_manager
            tm = get_task_manager()
            all_tasks = tm.get_all_tasks()
            open_tasks = [t for t in all_tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
            completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
            
            if not open_tasks and completed_tasks:
                logger.info(f"All {len(completed_tasks)} tasks complete, sending Auto Orchestrator message")
                await self._send_auto_orchestrator_message(len(completed_tasks))
        except Exception as e:
            logger.warning(f"Failed to check task completion: {e}")
        
        return round_messages
    
    async def _send_auto_orchestrator_message(self, completed_count: int):
        """Send an Auto Orchestrator message to trigger the Architect.
        
        Includes a cooldown to prevent spam if called multiple times.
        """
        import time
        from core.models import Message, MessageRole, MessageType
        
        # Cooldown: don't send if we sent one recently (within 10 seconds)
        now = time.time()
        last_sent = getattr(self, '_last_auto_orchestrator_time', 0)
        if now - last_sent < 10:
            logger.debug("Skipping Auto Orchestrator message (cooldown)")
            return
        self._last_auto_orchestrator_time = now
        
        auto_msg = Message(
            content=(
                f"Phase milestone: {completed_count} task(s) completed, 0 remaining. "
                "Bossy McArchitect: Review the master plan and assign the next batch of tasks. "
                "If all planned work is done, summarize the deliverables for the human."
            ),
            sender_name="Auto Orchestrator",
            sender_id="auto_orchestrator",
            role=MessageRole.HUMAN,
            message_type=MessageType.CHAT
        )
        
        await self._broadcast_message(auto_msg)
        
        # Also add to all agents' memory
        for agent in list(self._agents.values()):
            await agent.process_incoming_message(auto_msg)
        
        logger.info(f"Auto Orchestrator message sent ({completed_count} tasks completed)")
    
    async def _run_worker_round(self, workers: List[BaseAgent]) -> List[Message]:
        """Run a round specifically for workers with assigned tasks, in parallel."""
        worker_messages: List[Message] = []

        # Filter to workers that actually want to respond
        active_workers: List[BaseAgent] = []
        for worker in workers:
            try:
                if worker.should_respond():
                    active_workers.append(worker)
            except Exception as e:
                logger.error(f"Error in should_respond for {worker.name}: {e}")

        if not active_workers:
            return worker_messages

        # Broadcast that workers are actively processing tasks
        for worker in active_workers:
            await self._broadcast_status(f"⏳ {worker.name} is working on task...")

        tasks = {asyncio.create_task(self._get_agent_response(worker)): worker for worker in active_workers}

        while tasks:
            done, _ = await asyncio.wait(
                set(tasks.keys()),
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                worker = tasks.pop(task, None)
                if worker is None:
                    continue
                try:
                    response = task.result()
                except Exception as e:
                    logger.error(f"Error getting response from {worker.name}: {e}")
                    continue

                if response is not None:
                    await self._broadcast_message(response)
                    worker_messages.append(response)

                    # Notify other agents
                    for other_agent in list(self._agents.values()):
                        if other_agent.agent_id != response.sender_id:
                            await other_agent.process_incoming_message(response)

        return worker_messages
    
    async def start_conversation(
        self,
        initial_message: Optional[str] = None,
        rounds: Optional[int] = None
    ):
        """
        Start an ongoing conversation.
        
        Args:
            initial_message: Optional message to kick off the conversation
            rounds: Number of rounds to run (None = infinite)
        """
        self._running = True
        self.state.is_running = True
        
        if initial_message:
            await self.add_human_message(
                content=initial_message,
                username="Conversation Starter",
                user_id="starter"
            )
        
        round_count = 0
        while self._running:
            if rounds is not None and round_count >= rounds:
                break
            
            await self.run_conversation_round()
            round_count += 1
            
            # Pause between rounds (short delay to avoid tight loop)
            await asyncio.sleep(1.0)
        
        self.state.is_running = False
        logger.info("Conversation stopped")
    
    def stop_conversation(self):
        """Stop the ongoing conversation."""
        self._running = False
        if self._conversation_task and not self._conversation_task.done():
            self._conversation_task.cancel()
    
    async def trigger_response_to_human(self):
        """
        Trigger agents to respond to the latest human message.
        
        Called after a human sends a message in interactive mode.
        """
        await self.run_conversation_round()
    
    async def _load_history(self):
        """Load chat history from file if it exists."""
        try:
            chat_history_path = get_chat_history_path()
            if chat_history_path.exists():
                with open(chat_history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for msg_data in data.get('messages', [])[-50:]:  # Load last 50
                        msg = Message.from_dict(msg_data)
                        self.state.messages.append(msg)
                logger.info(f"Loaded {len(self.state.messages)} messages from history")
        except Exception as e:
            logger.warning(f"Could not load chat history: {e}")
    
    async def save_history(self):
        """Save chat history to file."""
        try:
            chat_history_path = get_chat_history_path()
            # Ensure parent directory exists
            chat_history_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "saved_at": datetime.now().isoformat(),
                "messages": [msg.to_dict() for msg in self.state.messages[-100:]]
            }
            with open(chat_history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Chat history saved")
        except Exception as e:
            logger.error(f"Could not save chat history: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current chatroom status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.state.is_running,
            "round_number": self.state.round_number,
            "message_count": len(self.state.messages),
            "active_agents": [
                self._agents[aid].get_info()
                for aid in self.state.active_agents
                if aid in self._agents
            ],
            "connected_humans": len(self.state.connected_humans)
        }
    
    async def shutdown(self):
        """
        Gracefully shut down the chatroom.
        
        Saves history and cleans up resources.
        """
        self.stop_conversation()
        await self.save_history()
        
        for agent in self._agents.values():
            await agent.close()
        
        logger.info("Chatroom shut down")


# Singleton chatroom instance
_chatroom: Optional[Chatroom] = None


def set_chatroom(chatroom: Chatroom):
    """Set the global chatroom instance (used by dashboard)."""
    global _chatroom
    _chatroom = chatroom


async def get_chatroom() -> Chatroom:
    """Get the global chatroom instance."""
    global _chatroom
    if _chatroom is None:
        _chatroom = Chatroom()
        await _chatroom.initialize()
    return _chatroom
