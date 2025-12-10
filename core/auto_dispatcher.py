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


# Complexity-based batch limits
COMPLEXITY_BATCH_LIMITS = {
    "trivial": 5,   # Batch up to 5 trivial tasks
    "simple": 3,    # Batch up to 3 simple tasks  
    "medium": 1,    # Don't batch medium tasks
    "complex": 1,   # Don't batch complex tasks
}


class AutoDispatcher:
    """
    Local task dispatcher that replaces the Architect for task orchestration.
    
    Benefits:
    - Zero API calls for task dispatch
    - Instant response (no LLM latency)
    - No token consumption
    - Deterministic behavior (no LLM hallucinations)
    - Parallel task dispatch for maximum throughput
    - Smart batching of trivial/simple tasks to reduce API calls
    """
    
    # Maximum number of DIFFERENT AGENTS to dispatch at once
    MAX_PARALLEL_AGENTS = 3
    
    def __init__(self):
        self._enabled = True
        self._dispatch_lock = asyncio.Lock()
        self._last_dispatch_time: Optional[datetime] = None
        self._dispatch_cooldown_seconds = 1.0  # Reduced from 2.0 for faster chaining
        self._on_status_callback: Optional[Callable[[str], Awaitable[None]]] = None
        self._enable_batching = True  # Batch trivial/simple tasks together
        self._watchdog_scheduled = False  # Prevent multiple watchdog tasks
        
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
    
    async def _watchdog_check(self, delay_seconds: float = 10):
        """
        Watchdog that checks for dispatchable work after a delay.
        
        This prevents stalls when:
        - All remaining tasks are for busy agents
        - An agent finishes but there was no task completion event
        - The conversation loop stops for any reason
        """
        if self._watchdog_scheduled:
            return  # Already have a watchdog running
        
        self._watchdog_scheduled = True
        try:
            await asyncio.sleep(delay_seconds)
            
            if not self._enabled:
                return
            
            from core.swarm_orchestrator import get_orchestrator
            from core.chatroom import get_chatroom
            
            orchestrator = get_orchestrator()
            chatroom = await get_chatroom()
            
            if not orchestrator or not orchestrator._initialized:
                return
            
            # Check if there's work to do
            summary = orchestrator.get_state_summary()
            if summary["completed_tasks"] == summary["total_tasks"]:
                return  # All done
            
            # Check if any agents are now idle
            idle_agents = []
            if chatroom:
                for agent in chatroom._agents.values():
                    if agent.status.value != "working":
                        role = getattr(agent, "role", "unknown")
                        if role in ("backend_dev", "frontend_dev", "qa_engineer", "devops", "tech_writer"):
                            idle_agents.append(agent)
            
            if idle_agents:
                # There are idle workers - try to dispatch
                logger.info(f"[AutoDispatcher] Watchdog: {len(idle_agents)} idle agents, attempting dispatch")
                await self.dispatch_next_task()
            else:
                # All workers still busy - schedule another check
                logger.debug("[AutoDispatcher] Watchdog: All workers still busy, will check again")
                self._watchdog_scheduled = False  # Allow new watchdog
                asyncio.create_task(self._watchdog_check(delay_seconds=15))
        except Exception as e:
            logger.warning(f"[AutoDispatcher] Watchdog error: {e}")
        finally:
            self._watchdog_scheduled = False
    
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
            
            # Count how many workers are currently busy (by agent role)
            busy_roles = set()
            if chatroom:
                for agent in chatroom._agents.values():
                    if agent.status.value == "working":
                        busy_roles.add(getattr(agent, "role", "unknown"))
            
            # Calculate how many agent slots are free
            free_slots = max(1, self.MAX_PARALLEL_AGENTS - len(busy_roles))
            
            # Get batched tasks (groups trivial/simple tasks by agent),
            # excluding roles that are already busy so we don't spam them
            next_tasks = self._get_batched_tasks(
                orchestrator,
                max_agents=free_slots,
                busy_roles=busy_roles,
            )
            
            if not next_tasks:
                # Check if all done
                summary = orchestrator.get_state_summary()
                if summary["completed_tasks"] == summary["total_tasks"]:
                    await self._log_status(f"🎉 All {summary['total_tasks']} tasks completed!")
                    return False
                elif len(busy_roles) > 0:
                    # Other workers still busy - schedule a watchdog check
                    logger.debug(f"No new tasks to dispatch, {len(busy_roles)} agents still busy")
                    # Schedule watchdog to check again in a few seconds
                    asyncio.create_task(self._watchdog_check(delay_seconds=10))
                    return False
                else:
                    await self._log_status("No more dispatchable tasks (waiting for dependencies)")
                    return False
            
            # Dispatch task batches (each batch goes to one agent)
            if len(next_tasks) == 1:
                batch = next_tasks[0]
                if isinstance(batch, list):
                    task_ids = ", ".join(t.id for t in batch)
                    await self._log_status(f"Dispatching batch [{task_ids}] to {batch[0].agent_name}")
                else:
                    await self._log_status(f"Dispatching Task {batch.id}: {batch.title[:40]}...")
            else:
                total_tasks = sum(len(b) if isinstance(b, list) else 1 for b in next_tasks)
                await self._log_status(f"Dispatching {total_tasks} tasks to {len(next_tasks)} agents in parallel")
            
            dispatched = 0
            for task_or_batch in next_tasks:
                if isinstance(task_or_batch, list):
                    # Batch dispatch
                    if await self._dispatch_batch(task_or_batch, run_round=False):
                        dispatched += len(task_or_batch)
                else:
                    if await self._dispatch_task(task_or_batch, run_round=False):
                        dispatched += 1
            
            # Run ONE conversation round for all newly assigned workers
            if dispatched > 0 and chatroom:
                try:
                    await asyncio.sleep(0.3)
                    await chatroom.run_conversation_round()
                except Exception as e:
                    logger.warning(f"AutoDispatcher: Error running round: {e}")
            
            return dispatched > 0
    
    def _get_batched_tasks(self, orchestrator, max_agents: int = 3, busy_roles: Optional[set] = None) -> list:
        """
        Get tasks grouped by agent, batching trivial/simple tasks together.
        
        Returns a list where each element is either:
        - A single SwarmTask (for medium/complex tasks)
        - A list of SwarmTasks (for batched trivial/simple tasks)
        """
        # Get all dispatchable tasks (more than we need for batching)
        all_tasks = orchestrator.get_next_dispatchable_tasks(max_count=max_agents * 5)

        # If certain agent roles are already busy, avoid queuing more work for them
        if busy_roles:
            all_tasks = [t for t in all_tasks if t.agent_role not in busy_roles]
        
        if not all_tasks or not self._enable_batching:
            return all_tasks[:max_agents]
        
        # Group by agent role for batching
        by_agent: Dict[str, list] = {}
        for task in all_tasks:
            key = task.batch_key or task.agent_role
            if key not in by_agent:
                by_agent[key] = []
            by_agent[key].append(task)
        
        result = []
        agents_used = 0
        
        for agent_key, agent_tasks in by_agent.items():
            if agents_used >= max_agents:
                break
            
            # Sort by complexity (trivial first for batching)
            complexity_order = {'trivial': 0, 'simple': 1, 'medium': 2, 'complex': 3}
            agent_tasks.sort(key=lambda t: complexity_order.get(t.complexity, 2))
            
            batch = []
            remaining = []
            
            for task in agent_tasks:
                batch_limit = COMPLEXITY_BATCH_LIMITS.get(task.complexity, 1)
                
                if task.complexity in ('trivial', 'simple') and len(batch) < batch_limit:
                    batch.append(task)
                elif task.complexity in ('trivial', 'simple') and batch:
                    # Batch is full, save remaining
                    remaining.append(task)
                else:
                    # Medium/complex task - dispatch solo
                    if batch:
                        # Flush current batch first
                        result.append(batch if len(batch) > 1 else batch[0])
                        batch = []
                        agents_used += 1
                        if agents_used >= max_agents:
                            break
                    result.append(task)
                    agents_used += 1
            
            # Flush any remaining batch
            if batch and agents_used < max_agents:
                result.append(batch if len(batch) > 1 else batch[0])
                agents_used += 1
        
        return result
    
    async def dispatch_next_task(self) -> bool:
        """
        Manually trigger dispatch of pending tasks.
        Called on "go" command or startup.
        """
        from core.swarm_orchestrator import get_orchestrator
        from core.chatroom import get_chatroom

        orchestrator = get_orchestrator()
        if not orchestrator or not orchestrator._initialized:
            logger.warning("AutoDispatcher: Cannot dispatch - orchestrator not ready")
            return False

        # Look at current workers so we don't try to pile more work onto
        # roles that are already busy.
        chatroom = await get_chatroom()
        busy_roles = set()
        if chatroom:
            for agent in chatroom._agents.values():
                if agent.status.value == "working":
                    busy_roles.add(getattr(agent, "role", "unknown"))

        # Get batched tasks (groups trivial/simple tasks), skipping busy roles
        next_tasks = self._get_batched_tasks(
            orchestrator,
            max_agents=self.MAX_PARALLEL_AGENTS,
            busy_roles=busy_roles,
        )
        
        if not next_tasks:
            summary = orchestrator.get_state_summary()
            if summary["completed_tasks"] == summary["total_tasks"]:
                await self._log_status(f"All {summary['total_tasks']} tasks already completed!")
            else:
                await self._log_status("No dispatchable tasks available")
            return False
        
        # Log what we're dispatching
        total_tasks = sum(len(b) if isinstance(b, list) else 1 for b in next_tasks)
        if total_tasks == 1:
            task = next_tasks[0][0] if isinstance(next_tasks[0], list) else next_tasks[0]
            await self._log_status(f"Starting Task {task.id}: {task.title[:40]}...")
        else:
            await self._log_status(f"Starting {total_tasks} tasks across {len(next_tasks)} agents")
        
        # Dispatch all task batches
        dispatched = 0
        for task_or_batch in next_tasks:
            if isinstance(task_or_batch, list):
                if await self._dispatch_batch(task_or_batch, run_round=False):
                    dispatched += len(task_or_batch)
            else:
                if await self._dispatch_task(task_or_batch, run_round=False):
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
    
    async def _dispatch_batch(self, tasks: list, run_round: bool = True) -> bool:
        """
        Dispatch multiple tasks as a single batch to one agent.
        
        This combines trivial/simple tasks into one assignment to reduce API calls.
        """
        if not tasks:
            return False
        
        from core.chatroom import get_chatroom
        chatroom = await get_chatroom()
        if not chatroom:
            logger.error("AutoDispatcher: No chatroom available")
            return False
        
        # All tasks go to the same agent
        agent_role = tasks[0].agent_role
        agent_name = tasks[0].agent_name
        
        # Ensure worker exists
        existing_agent = None
        for agent in chatroom._agents.values():
            if agent.name == agent_name:
                existing_agent = agent
                break
        
        if not existing_agent:
            await self._log_status(f"Spawning {agent_name}...")
            agent = await chatroom.spawn_agent(agent_role)
            if not agent:
                logger.error(f"AutoDispatcher: Failed to spawn {agent_role}")
                return False
        
        # Build combined task description
        task_ids = [t.id for t in tasks]
        combined = f"""# BATCH ASSIGNMENT: Tasks {', '.join(task_ids)}

You have been assigned {len(tasks)} related tasks. Complete them ALL before calling complete_my_task.

"""
        for i, task in enumerate(tasks, 1):
            combined += f"""---
## Task {task.id}: {task.title}

**GOAL:** {task.goal}

**FILES:** {', '.join(task.files) if task.files else '(see details)'}

**DONE_WHEN:** {task.done_when}

"""
        
        combined += f"""
---
# IMPORTANT
- Complete ALL {len(tasks)} tasks above
- When ALL are done, call: complete_my_task(result="Completed batch: {', '.join(task_ids)}")
"""
        
        # Assign the batch (use first task ID as reference)
        success = await chatroom.assign_task(agent_name, combined)
        
        if success:
            await self._log_status(f"✅ Batch dispatched [{', '.join(task_ids)}] to {agent_name}")
            
            # Mark all tasks as dispatched
            from core.swarm_orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            if orchestrator:
                for task in tasks:
                    orchestrator.mark_task_dispatched(task.id, agent_name)
            
            if run_round:
                try:
                    await asyncio.sleep(0.3)
                    await chatroom.run_conversation_round()
                except Exception as e:
                    logger.warning(f"AutoDispatcher: Error running round: {e}")
            
            return True
        else:
            logger.error(f"AutoDispatcher: Failed to assign batch to {agent_name}")
            return False
    
    async def _dispatch_task(self, task, run_round: bool = True) -> bool:
        """Actually dispatch a single task to a worker.
        
        Args:
            task: The task to dispatch
            run_round: If True, run a conversation round after dispatch.
                       Set to False when batch-dispatching multiple tasks.
        """
        from core.chatroom import get_chatroom
        from core.file_ownership import get_file_tracker
        
        chatroom = await get_chatroom()
        if not chatroom:
            logger.error("AutoDispatcher: No chatroom available")
            return False
        
        # Check for file conflicts before dispatch
        tracker = get_file_tracker()
        if tracker and task.files:
            conflicts = tracker.check_conflicts(task.files, task.agent_name)
            if conflicts:
                conflict_info = ", ".join(f"{p} (owned by {o})" for p, o, _ in conflicts[:3])
                await self._log_status(f"⚠️ Task {task.id} has file conflicts: {conflict_info}")
                # Mark task as blocked instead of failing
                from core.swarm_orchestrator import get_orchestrator
                orchestrator = get_orchestrator()
                if orchestrator:
                    t = orchestrator._find_task(task.id)
                    if t:
                        from core.swarm_orchestrator import TaskState
                        t.state = TaskState.BLOCKED
                return False
            
            # Reserve files for this task
            tracker.reserve_files(task.files, task.agent_name, task.id)
        
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
        
        # Build task description with complexity hint
        complexity_hint = ""
        if task.complexity in ('trivial', 'simple'):
            complexity_hint = f"\n\n**COMPLEXITY:** {task.complexity} - Complete quickly and call complete_my_task()"
        
        task_description = f"""Task {task.id}: {task.title}

GOAL: {task.goal}

FILES:
{chr(10).join('- ' + f for f in task.files) if task.files else '- (see task details)'}

REQUIREMENTS:
{chr(10).join('- ' + r for r in task.requirements) if task.requirements else '- (see task details)'}

DONE_WHEN: {task.done_when}{complexity_hint}
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
