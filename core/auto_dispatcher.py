"""
Auto Dispatcher - Local task dispatch without LLM.

Replaces the Architect for basic task orchestration:
1. Watches for task completion events
2. Automatically dispatches the next pending task
3. No API calls, no tokens, no delays

This is a deterministic state machine that does what the Architect
was supposed to do, but without the LLM overhead.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoDispatcher:
    """
    Local task dispatcher that replaces the Architect for task orchestration.
    
    Benefits:
    - Zero API calls for task dispatch
    - Instant response (no LLM latency)
    - No token consumption
    - Deterministic behavior (no LLM hallucinations)
    - Parallel task dispatch for maximum throughput
    """
    
    # Maximum number of tasks to dispatch at once
    MAX_PARALLEL_TASKS = 3
    
    def __init__(self):
        self._enabled = True
        self._dispatch_lock = asyncio.Lock()
        self._last_dispatch_time: Optional[datetime] = None
        self._dispatch_cooldown_seconds = 1.0  # Reduced from 2.0 for faster chaining
        self._on_status_callback: Optional[Callable[[str], Awaitable[None]]] = None
        
    def set_status_callback(self, callback: Callable[[str], Awaitable[None]]):
        """Set callback for status messages."""
        self._on_status_callback = callback
    
    async def _log_status(self, message: str):
        """Log status and call callback if set."""
        logger.info(f"[AutoDispatcher] {message}")
        if self._on_status_callback:
            try:
                await self._on_status_callback(f"🤖 AutoDispatch: {message}")
            except Exception:
                pass
    
    async def on_task_completed(self, task_id: str, agent_name: str) -> bool:
        """
        Called when a task is completed. Dispatches new tasks to fill available slots.
        
        Returns True if at least one new task was dispatched, False otherwise.
        """
        if not self._enabled:
            return False
        
        async with self._dispatch_lock:
            # Cooldown to prevent rapid-fire dispatching
            now = datetime.now()
            if self._last_dispatch_time:
                elapsed = (now - self._last_dispatch_time).total_seconds()
                if elapsed < self._dispatch_cooldown_seconds:
                    await asyncio.sleep(self._dispatch_cooldown_seconds - elapsed)
            
            self._last_dispatch_time = datetime.now()
            
            # Get orchestrator and chatroom
            from core.swarm_orchestrator import get_orchestrator
            from core.chatroom import get_chatroom
            
            orchestrator = get_orchestrator()
            chatroom = await get_chatroom()
            
            if not orchestrator or not orchestrator._initialized:
                logger.debug("AutoDispatcher: Orchestrator not ready")
                return False
            
            # Count how many workers are currently busy
            busy_count = 0
            if chatroom:
                for agent in chatroom._agents.values():
                    if agent.status.value == "working":
                        busy_count += 1
            
            # Calculate how many slots are free
            free_slots = max(1, self.MAX_PARALLEL_TASKS - busy_count)
            
            # Get tasks to fill the free slots
            next_tasks = orchestrator.get_next_dispatchable_tasks(max_count=free_slots)
            
            if not next_tasks:
                # Check if all done
                summary = orchestrator.get_state_summary()
                if summary["completed_tasks"] == summary["total_tasks"]:
                    await self._log_status(f"🎉 All {summary['total_tasks']} tasks completed!")
                    return False
                elif busy_count > 0:
                    # Other workers still busy, no message needed
                    logger.debug(f"No new tasks to dispatch, {busy_count} workers still busy")
                    return False
                else:
                    await self._log_status("No more dispatchable tasks (waiting for dependencies)")
                    return False
            
            # Dispatch all available tasks
            if len(next_tasks) == 1:
                await self._log_status(f"Dispatching Task {next_tasks[0].id}: {next_tasks[0].title[:40]}...")
            else:
                task_ids = ", ".join(t.id for t in next_tasks)
                await self._log_status(f"Dispatching {len(next_tasks)} tasks in parallel: {task_ids}")
            
            dispatched = 0
            for task in next_tasks:
                if await self._dispatch_task(task, run_round=False):
                    dispatched += 1
            
            # Run ONE conversation round for all newly assigned workers
            if dispatched > 0 and chatroom:
                try:
                    await asyncio.sleep(0.3)
                    await chatroom.run_conversation_round()
                except Exception as e:
                    logger.warning(f"AutoDispatcher: Error running round: {e}")
            
            return dispatched > 0
    
    async def dispatch_next_task(self) -> bool:
        """
        Manually trigger dispatch of pending tasks (up to MAX_PARALLEL_TASKS).
        Called on "go" command or startup.
        """
        from core.swarm_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        if not orchestrator or not orchestrator._initialized:
            logger.warning("AutoDispatcher: Cannot dispatch - orchestrator not ready")
            return False
        
        # Get multiple dispatchable tasks for parallel execution
        next_tasks = orchestrator.get_next_dispatchable_tasks(max_count=self.MAX_PARALLEL_TASKS)
        
        if not next_tasks:
            summary = orchestrator.get_state_summary()
            if summary["completed_tasks"] == summary["total_tasks"]:
                await self._log_status(f"All {summary['total_tasks']} tasks already completed!")
            else:
                await self._log_status("No dispatchable tasks available")
            return False
        
        # Log what we're dispatching
        if len(next_tasks) == 1:
            await self._log_status(f"Starting Task {next_tasks[0].id}: {next_tasks[0].title[:40]}...")
        else:
            task_ids = ", ".join(t.id for t in next_tasks)
            await self._log_status(f"Starting {len(next_tasks)} tasks in parallel: {task_ids}")
        
        # Dispatch all tasks
        dispatched = 0
        for task in next_tasks:
            if await self._dispatch_task(task, run_round=False):
                dispatched += 1
        
        # Run ONE conversation round for all workers to start in parallel
        if dispatched > 0:
            from core.chatroom import get_chatroom
            chatroom = await get_chatroom()
            if chatroom:
                try:
                    await asyncio.sleep(0.3)
                    await chatroom.run_conversation_round()
                except Exception as e:
                    logger.warning(f"AutoDispatcher: Error running round: {e}")
        
        return dispatched > 0
    
    async def _dispatch_task(self, task, run_round: bool = True) -> bool:
        """Actually dispatch a task to a worker.
        
        Args:
            task: The task to dispatch
            run_round: If True, run a conversation round after dispatch.
                       Set to False when batch-dispatching multiple tasks.
        """
        from core.chatroom import get_chatroom
        
        chatroom = await get_chatroom()
        if not chatroom:
            logger.error("AutoDispatcher: No chatroom available")
            return False
        
        # Spawn worker if needed
        agent_role = task.agent_role
        agent_name = task.agent_name
        
        # Check if worker exists
        existing_agent = None
        for agent in chatroom._agents.values():
            if agent.name == agent_name:
                existing_agent = agent
                break
        
        if not existing_agent:
            # Spawn the worker using spawn_agent (not spawn_worker)
            await self._log_status(f"Spawning {agent_name}...")
            agent = await chatroom.spawn_agent(agent_role)
            if not agent:
                logger.error(f"AutoDispatcher: Failed to spawn {agent_role}")
                return False
        
        # Build task description
        task_description = f"""Task {task.id}: {task.title}

GOAL: {task.goal}

FILES:
{chr(10).join('- ' + f for f in task.files) if task.files else '- (see task details)'}

REQUIREMENTS:
{chr(10).join('- ' + r for r in task.requirements) if task.requirements else '- (see task details)'}

DONE_WHEN: {task.done_when}
"""
        
        # Assign the task
        success = await chatroom.assign_task(agent_name, task_description)
        
        if success:
            await self._log_status(f"✅ Dispatched Task {task.id} to {agent_name}")
            
            # Run a conversation round if requested (skip when batch-dispatching)
            if run_round:
                try:
                    await asyncio.sleep(0.3)
                    await chatroom.run_conversation_round()
                except Exception as e:
                    logger.warning(f"AutoDispatcher: Error running round after dispatch: {e}")
            
            return True
        else:
            logger.error(f"AutoDispatcher: Failed to assign task to {agent_name}")
            return False
    
    def enable(self):
        """Enable auto-dispatching."""
        self._enabled = True
        logger.info("AutoDispatcher enabled")
    
    def disable(self):
        """Disable auto-dispatching (for manual control)."""
        self._enabled = False
        logger.info("AutoDispatcher disabled")


# Global instance
_dispatcher: Optional[AutoDispatcher] = None


def get_auto_dispatcher() -> AutoDispatcher:
    """Get or create the global auto dispatcher."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = AutoDispatcher()
    return _dispatcher
