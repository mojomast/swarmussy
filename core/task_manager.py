"""
Task Manager for Multi-Agent Swarm.

Acts as the central registry for all tasks, tracking their status and results.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging

from core.models import Task, TaskStatus

logger = logging.getLogger(__name__)


class TaskManager:
    """
    Central registry for swarm tasks.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks: Dict[str, Task] = {}
        return cls._instance
    
    def create_task(self, description: str) -> Task:
        """
        Create a new pending task.
        
        Args:
            description: Description of the work to be done
            
        Returns:
            The created Task object
        """
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            description=description,
            created_at=datetime.now().isoformat(),
            status=TaskStatus.PENDING
        )
        self._tasks[task_id] = task
        logger.info(f"Task created: {task_id} - {description[:50]}...")
        return task
    
    def update_task_status(self, task_id: str, status: str, result: Optional[str] = None) -> Optional[Task]:
        """Update the status (and optional result) of a task by ID.

        Args:
            task_id: ID of the task to update
            status: New status as a string (pending, in_progress, completed, failed)
            result: Optional result or error summary
        """
        if task_id not in self._tasks:
            logger.error(f"Task not found: {task_id}")
            return None
        
        try:
            new_status = TaskStatus(status)
        except ValueError:
            logger.error(f"Invalid task status '{status}' for task {task_id}")
            return None
        
        task = self._tasks[task_id]
        task.status = new_status
        if result is not None:
            task.result = result
        if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            task.completed_at = datetime.now().isoformat()
        logger.info(f"Task {task_id} status updated to {new_status.value}")
        return task
    
    def assign_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """
        Assign a task to an agent.
        
        Args:
            task_id: ID of the task
            agent_id: ID of the agent
            
        Returns:
            The updated Task or None if not found
        """
        if task_id not in self._tasks:
            logger.error(f"Task not found: {task_id}")
            return None
            
        task = self._tasks[task_id]
        task.assigned_to = agent_id
        task.status = TaskStatus.IN_PROGRESS
        logger.info(f"Task {task_id} assigned to agent {agent_id}")
        return task
    
    def complete_task(self, task_id: str, result: str) -> Optional[Task]:
        """
        Mark a task as completed with a result.
        
        Args:
            task_id: ID of the task
            result: Summary of the work done
            
        Returns:
            The updated Task or None if not found
        """
        if task_id not in self._tasks:
            logger.error(f"Task not found: {task_id}")
            return None
            
        task = self._tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now().isoformat()
        logger.info(f"Task {task_id} completed")
        return task
    
    def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        """
        Mark a task as failed.
        
        Args:
            task_id: ID of the task
            error: Error message
            
        Returns:
            The updated Task or None if not found
        """
        if task_id not in self._tasks:
            logger.error(f"Task not found: {task_id}")
            return None
            
        task = self._tasks[task_id]
        task.status = TaskStatus.FAILED
        task.result = error
        task.completed_at = datetime.now().isoformat()
        logger.warning(f"Task {task_id} failed: {error}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self._tasks.values())
    
    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Get all tasks assigned to a specific agent."""
        return [t for t in self._tasks.values() if t.assigned_to == agent_id]
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]


def get_task_manager() -> TaskManager:
    """Get the singleton task manager."""
    return TaskManager()
