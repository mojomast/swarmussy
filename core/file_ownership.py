"""
File Ownership Tracking - Prevent agent collisions during parallel work.

This module tracks which agent "owns" which files during task execution.
When tasks are dispatched, files are reserved for the assigned agent.
Other agents can read but not write to reserved files.

Key Features:
1. Automatic file reservation based on task @files: declarations
2. Directory-level ownership for new file creation
3. Conflict detection before dispatch
4. Ownership release on task completion
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Set, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FileOwnership:
    """Tracks ownership of a file or directory."""
    path: str  # Relative to shared/
    owner_agent: str  # Agent name
    task_id: str  # Task that owns the file
    ownership_type: str  # "file" or "directory"
    reserved_at: datetime = field(default_factory=datetime.now)
    read_only: bool = False  # If True, others can read but not write


class FileOwnershipTracker:
    """
    Tracks file ownership to prevent write collisions.
    
    Usage:
        tracker = get_file_tracker()
        
        # Before dispatching task
        conflicts = tracker.check_conflicts(task_files, agent_name)
        if conflicts:
            # Handle conflicts
        
        # Reserve files for task
        tracker.reserve_files(task_files, agent_name, task_id)
        
        # After task completes
        tracker.release_task(task_id)
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.shared_dir = self.project_path / "scratch" / "shared"
        self._ownership: Dict[str, FileOwnership] = {}  # path -> ownership
        self._task_files: Dict[str, Set[str]] = {}  # task_id -> set of paths
        self._agent_files: Dict[str, Set[str]] = {}  # agent_name -> set of paths
        
        # Load persisted state
        self._load_state()
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path to be relative to shared/."""
        path = path.replace("\\", "/")
        
        # Remove shared/ prefix if present
        if path.startswith("shared/"):
            path = path[7:]
        
        # Remove leading slashes
        path = path.lstrip("/")
        
        return path
    
    def reserve_files(self, files: List[str], agent_name: str, task_id: str) -> List[str]:
        """
        Reserve files for an agent's task.
        
        Args:
            files: List of file paths to reserve
            agent_name: Name of agent claiming the files
            task_id: Task ID for tracking
            
        Returns:
            List of successfully reserved paths
        """
        reserved = []
        
        for file_path in files:
            norm_path = self._normalize_path(file_path)
            
            # Skip if already owned by this agent
            if norm_path in self._ownership:
                owner = self._ownership[norm_path]
                if owner.owner_agent == agent_name:
                    continue
            
            # Create ownership record
            ownership = FileOwnership(
                path=norm_path,
                owner_agent=agent_name,
                task_id=task_id,
                ownership_type="file" if "." in os.path.basename(norm_path) else "directory",
            )
            
            self._ownership[norm_path] = ownership
            reserved.append(norm_path)
            
            # Track by task
            if task_id not in self._task_files:
                self._task_files[task_id] = set()
            self._task_files[task_id].add(norm_path)
            
            # Track by agent
            if agent_name not in self._agent_files:
                self._agent_files[agent_name] = set()
            self._agent_files[agent_name].add(norm_path)
        
        if reserved:
            logger.debug(f"Reserved {len(reserved)} files for {agent_name} (task {task_id})")
            self._save_state()
        
        return reserved
    
    def check_conflicts(self, files: List[str], agent_name: str) -> List[Tuple[str, str, str]]:
        """
        Check if any files conflict with existing ownership.
        
        Args:
            files: Files the agent wants to claim
            agent_name: Agent requesting the files
            
        Returns:
            List of (path, current_owner, task_id) tuples for conflicts
        """
        conflicts = []
        
        for file_path in files:
            norm_path = self._normalize_path(file_path)
            
            if norm_path in self._ownership:
                owner = self._ownership[norm_path]
                if owner.owner_agent != agent_name:
                    conflicts.append((norm_path, owner.owner_agent, owner.task_id))
            
            # Also check parent directory ownership
            parent = str(Path(norm_path).parent)
            if parent and parent != "." and parent in self._ownership:
                owner = self._ownership[parent]
                if owner.owner_agent != agent_name:
                    conflicts.append((parent + "/", owner.owner_agent, owner.task_id))
        
        return conflicts
    
    def can_write(self, file_path: str, agent_name: str) -> bool:
        """Check if agent can write to file."""
        norm_path = self._normalize_path(file_path)
        
        if norm_path not in self._ownership:
            return True  # Unowned files can be written
        
        owner = self._ownership[norm_path]
        return owner.owner_agent == agent_name
    
    def release_task(self, task_id: str):
        """Release all files owned by a completed task."""
        if task_id not in self._task_files:
            return
        
        released = []
        for path in self._task_files[task_id]:
            if path in self._ownership:
                owner = self._ownership[path]
                
                # Remove from agent tracking
                if owner.owner_agent in self._agent_files:
                    self._agent_files[owner.owner_agent].discard(path)
                
                del self._ownership[path]
                released.append(path)
        
        del self._task_files[task_id]
        
        if released:
            logger.debug(f"Released {len(released)} files from task {task_id}")
            self._save_state()
    
    def release_agent(self, agent_name: str):
        """Release all files owned by an agent."""
        if agent_name not in self._agent_files:
            return
        
        released = []
        for path in list(self._agent_files[agent_name]):
            if path in self._ownership:
                del self._ownership[path]
                released.append(path)
        
        del self._agent_files[agent_name]
        
        if released:
            logger.debug(f"Released {len(released)} files from agent {agent_name}")
            self._save_state()
    
    def get_agent_files(self, agent_name: str) -> Set[str]:
        """Get all files currently owned by an agent."""
        return self._agent_files.get(agent_name, set())
    
    def get_ownership_summary(self) -> Dict[str, List[str]]:
        """Get summary of current file ownership by agent."""
        summary = {}
        for path, ownership in self._ownership.items():
            agent = ownership.owner_agent
            if agent not in summary:
                summary[agent] = []
            summary[agent].append(path)
        return summary
    
    def clear_all(self):
        """Clear all ownership (e.g., on project reset)."""
        self._ownership.clear()
        self._task_files.clear()
        self._agent_files.clear()
        self._save_state()
        logger.info("Cleared all file ownership")
    
    # Persistence
    
    def _get_state_file(self) -> Path:
        """Get path to ownership state file."""
        return self.shared_dir / ".file_ownership.json"
    
    def _save_state(self):
        """Persist ownership state to disk."""
        try:
            state = {
                "version": 1,
                "saved_at": datetime.now().isoformat(),
                "ownership": {
                    path: {
                        "owner_agent": o.owner_agent,
                        "task_id": o.task_id,
                        "ownership_type": o.ownership_type,
                        "reserved_at": o.reserved_at.isoformat(),
                    }
                    for path, o in self._ownership.items()
                }
            }
            
            state_file = self._get_state_file()
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.warning(f"Failed to save ownership state: {e}")
    
    def _load_state(self):
        """Load ownership state from disk."""
        state_file = self._get_state_file()
        if not state_file.exists():
            return
        
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            
            for path, data in state.get("ownership", {}).items():
                ownership = FileOwnership(
                    path=path,
                    owner_agent=data["owner_agent"],
                    task_id=data["task_id"],
                    ownership_type=data["ownership_type"],
                    reserved_at=datetime.fromisoformat(data["reserved_at"]),
                )
                self._ownership[path] = ownership
                
                # Rebuild indexes
                if ownership.task_id not in self._task_files:
                    self._task_files[ownership.task_id] = set()
                self._task_files[ownership.task_id].add(path)
                
                if ownership.owner_agent not in self._agent_files:
                    self._agent_files[ownership.owner_agent] = set()
                self._agent_files[ownership.owner_agent].add(path)
            
            logger.debug(f"Loaded {len(self._ownership)} file ownership records")
            
        except Exception as e:
            logger.warning(f"Failed to load ownership state: {e}")


# Global instance
_tracker: Optional[FileOwnershipTracker] = None


def get_file_tracker() -> Optional[FileOwnershipTracker]:
    """Get the global file tracker instance."""
    return _tracker


def init_file_tracker(project_path: Path) -> FileOwnershipTracker:
    """Initialize and return the global file tracker."""
    global _tracker
    _tracker = FileOwnershipTracker(project_path)
    return _tracker
