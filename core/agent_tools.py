"""
Agent Tools System for Multi-Agent Chatroom.

Provides sandboxed file operations and development tools for AI agents.
All file operations are restricted to the scratch/ directory.
"""

import asyncio
import json
import os
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import aiofiles

from core.models import Message, MessageRole, MessageType, AgentStatus, TaskStatus

# Conditional import for file locking (Unix only)
try:
    import fcntl
except ImportError:
    fcntl = None

logger = logging.getLogger(__name__)


def get_scratch_dir() -> Path:
    """Get the current scratch directory (project-aware)."""
    from config.settings import get_scratch_dir as settings_get_scratch_dir
    return settings_get_scratch_dir()


# Legacy constant for backwards compatibility (use get_scratch_dir() instead)
SCRATCH_DIR = Path(__file__).parent.parent / "scratch"


class FileLockManager:
    """
    Manages file locks to prevent concurrent editing collisions.
    
    Each agent can claim exclusive access to a file while working on it.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._locks: Dict[str, str] = {}  # path -> agent_id
            cls._instance._lock = asyncio.Lock()
        return cls._instance
    
    async def claim_file(self, path: str, agent_id: str, agent_name: str) -> Tuple[bool, str]:
        """
        Claim exclusive access to a file.
        
        Returns:
            Tuple of (success, message)
        """
        async with self._lock:
            normalized = self._normalize_path(path)
            
            if normalized in self._locks:
                owner = self._locks[normalized]
                if owner == agent_id:
                    return True, f"You already have this file claimed"
                return False, f"File is currently claimed by another agent"
            
            self._locks[normalized] = agent_id
            logger.info(f"[{agent_name}] Claimed file: {normalized}")
            return True, f"Successfully claimed file: {path}"
    
    async def release_file(self, path: str, agent_id: str, agent_name: str) -> Tuple[bool, str]:
        """Release a file lock."""
        async with self._lock:
            normalized = self._normalize_path(path)
            
            if normalized not in self._locks:
                return True, "File was not locked"
            
            if self._locks[normalized] != agent_id:
                return False, "You don't own this lock"
            
            del self._locks[normalized]
            logger.info(f"[{agent_name}] Released file: {normalized}")
            return True, f"Released file: {path}"
    
    async def is_locked_by_other(self, path: str, agent_id: str) -> bool:
        """Check if file is locked by another agent."""
        async with self._lock:
            normalized = self._normalize_path(path)
            if normalized in self._locks:
                return self._locks[normalized] != agent_id
            return False
    
    async def get_all_locks(self) -> Dict[str, str]:
        """Get all current file locks."""
        async with self._lock:
            return dict(self._locks)
    
    async def release_all_by_agent(self, agent_id: str):
        """Release all locks held by an agent."""
        async with self._lock:
            to_remove = [p for p, a in self._locks.items() if a == agent_id]
            for path in to_remove:
                del self._locks[path]
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for consistent comparison."""
        return str(Path(path).resolve())


def get_lock_manager() -> FileLockManager:
    """Get the singleton lock manager."""
    return FileLockManager()


class AgentToolExecutor:
    """
    Executes tools on behalf of an agent.
    
    All file operations are sandboxed to the scratch directory.
    """
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        # Use dynamic scratch dir (project-aware)
        self.scratch_dir = get_scratch_dir()
        # FORCE SHARED WORKSPACE: All agents now work in scratch/shared by default
        self.agent_workspace = self.scratch_dir / "shared"
        self.lock_manager = get_lock_manager()
        
        # Ensure directories exist
        self.scratch_dir.mkdir(parents=True, exist_ok=True)
        self.agent_workspace.mkdir(parents=True, exist_ok=True)
    
    def _safe_name(self, name: str) -> str:
        """Convert agent name to safe folder name."""
        return re.sub(r'[^a-zA-Z0-9_-]', '_', name.lower())
    
    def _validate_path(self, path: str) -> Tuple[bool, Path, str]:
        """
        Validate that a path is within the scratch directory.
        
        Returns:
            Tuple of (is_valid, resolved_path, error_message)
        """
        try:
            # Handle relative paths
            path_obj = Path(path)
            if not path_obj.is_absolute():
                # Check for special prefixes to allow easier access to shared/root
                parts = path_obj.parts
                if parts and parts[0] == "shared":
                    # Treat 'shared/...' as relative to SCRATCH_DIR root
                    full_path = self.scratch_dir / path
                elif parts and parts[0] == "scratch":
                    # Treat 'scratch/...' as relative to SCRATCH_DIR root (strip 'scratch' prefix)
                    # path is "scratch/foo/bar", we want "foo/bar" relative to scratch_dir
                    relative_path = Path(*parts[1:])
                    full_path = self.scratch_dir / relative_path
                else:
                    # Default: relative to agent workspace
                    full_path = self.agent_workspace / path
            else:
                full_path = Path(path)
            
            resolved = full_path.resolve()
            
            # Check if within scratch directory
            try:
                resolved.relative_to(self.scratch_dir.resolve())
                return True, resolved, ""
            except ValueError:
                return False, resolved, f"Access denied: Path must be within scratch folder"
                
        except Exception as e:
            return False, Path(path), f"Invalid path: {str(e)}"
    
    def _is_protected_planning_file(self, resolved: Path) -> bool:
        """Return True if the resolved path points to a core planning file.

        Currently this includes devplan.md and master_plan.md in the shared
        scratch directory. Only the Architect is allowed to modify these.
        """
        try:
            shared = self.scratch_dir / "shared"
            protected = {
                (shared / "devplan.md").resolve(),
                (shared / "master_plan.md").resolve(),
            }
            return resolved.resolve() in protected
        except Exception:
            return False
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.
        
        Returns:
            Dict with 'success' bool and 'result' or 'error' string
        """
        tool_map = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "append_file": self._append_file,
            "edit_file": self._edit_file,
            "replace_in_file": self._replace_in_file,
            "list_files": self._list_files,
            "delete_file": self._delete_file,
            "create_folder": self._create_folder,
            "search_code": self._search_code,
            "get_git_status": self._get_git_status,
            "get_git_diff": self._get_git_diff,
            "git_commit": self._git_commit,
            "run_command": self._run_command,
            "claim_file": self._claim_file,
            "release_file": self._release_file,
            "get_file_locks": self._get_file_locks,
            "move_file": self._move_file,
            "scaffold_project": self._scaffold_project,
            "get_project_structure": self._get_project_structure,
            "spawn_worker": self._spawn_worker,
            "create_task": self._create_task,
            "assign_task": self._assign_task,
            "get_swarm_state": self._get_swarm_state,
            "update_devplan_dashboard": self._update_devplan_dashboard,
            "update_task_status": self._update_task_status,
            "append_decision_log": self._append_decision_log,
            "append_team_log": self._append_team_log,
            "complete_my_task": self._complete_my_task,
        }
        
        if tool_name not in tool_map:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            result = await tool_map[tool_name](arguments)
            logger.info(f"[{self.agent_name}] Tool {tool_name}: {'success' if result.get('success') else 'failed'}")
            return result
        except Exception as e:
            logger.error(f"[{self.agent_name}] Tool {tool_name} error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents."""
        path = args.get("path", "")
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        if not resolved.is_file():
            return {"success": False, "error": f"Not a file: {path}"}
        
        try:
            async with aiofiles.open(resolved, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Add line numbers for context
            lines = content.split('\n')
            numbered = '\n'.join(f"{i+1}: {line}" for i, line in enumerate(lines))
            
            return {
                "success": True,
                "result": {
                    "path": str(resolved.relative_to(self.scratch_dir)),
                    "content": content,
                    "numbered_content": numbered,
                    "line_count": len(lines)
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {e}"}
    
    async def _write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file (create or overwrite)."""
        path = args.get("path", "")
        content = args.get("content", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        # Check if locked by another agent
        if await self.lock_manager.is_locked_by_other(str(resolved), self.agent_id):
            return {"success": False, "error": "File is locked by another agent. Use claim_file first."}
        
        if self._is_protected_planning_file(resolved) and "Architect" not in self.agent_name:
            return {
                "success": False,
                "error": "Only Bossy McArchitect can modify devplan.md or master_plan.md. "
                         "Ask the Architect to adjust the plan/dashboard instead of editing directly.",
            }
        
        try:
            # Ensure parent directory exists
            resolved.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(resolved, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return {
                "success": True,
                "result": f"Successfully wrote {len(content)} bytes to {path}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {e}"}
    
    async def _edit_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Edit specific lines in a file."""
        path = args.get("path", "")
        start_line = args.get("start_line", 1)
        end_line = args.get("end_line")
        new_content = args.get("new_content", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        # Check if locked by another agent
        if await self.lock_manager.is_locked_by_other(str(resolved), self.agent_id):
            return {"success": False, "error": "File is locked by another agent"}
        
        if self._is_protected_planning_file(resolved) and "Architect" not in self.agent_name:
            return {
                "success": False,
                "error": "Only Bossy McArchitect can modify devplan.md or master_plan.md. "
                         "Ask the Architect to adjust the plan/dashboard instead of editing directly.",
            }
        
        try:
            async with aiofiles.open(resolved, 'r', encoding='utf-8') as f:
                lines = (await f.read()).split('\n')
            
            # Adjust for 1-indexed lines
            start_idx = max(0, start_line - 1)
            end_idx = end_line if end_line else start_idx + 1
            
            # Replace lines
            new_lines = new_content.split('\n') if new_content else []
            lines = lines[:start_idx] + new_lines + lines[end_idx:]
            
            async with aiofiles.open(resolved, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(lines))
            
            return {
                "success": True,
                "result": f"Edited lines {start_line}-{end_line} in {path}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to edit file: {e}"}

    async def _replace_in_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Replace string in a file."""
        path = args.get("path", "")
        old_string = args.get("old_string", "")
        new_string = args.get("new_string", "")
        
        if not path or not old_string:
            return {"success": False, "error": "path and old_string are required"}
            
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}

        if self._is_protected_planning_file(resolved) and "Architect" not in self.agent_name:
            return {
                "success": False,
                "error": "Only Bossy McArchitect can modify devplan.md or master_plan.md. "
                         "Ask the Architect to adjust the plan/dashboard instead of editing directly.",
            }
            
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}"}
            
        # Check if locked by another agent
        if await self.lock_manager.is_locked_by_other(str(resolved), self.agent_id):
            return {"success": False, "error": "File is locked by another agent"}
            
        try:
            async with aiofiles.open(resolved, 'r', encoding='utf-8') as f:
                content = await f.read()
                
            if old_string not in content:
                return {"success": False, "error": "old_string not found in file"}
                
            # Replace only the first occurrence to be safe
            new_content = content.replace(old_string, new_string, 1)
            
            async with aiofiles.open(resolved, 'w', encoding='utf-8') as f:
                await f.write(new_content)
                
            return {
                "success": True, 
                "result": f"Replaced text in {path}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to replace text: {e}"}
    
    async def _list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory."""
        path = args.get("path", ".")
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        if not resolved.exists():
            return {"success": False, "error": f"Directory not found: {path}"}
        
        if not resolved.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}
        
        try:
            items = []
            for item in resolved.iterdir():
                rel_path = item.relative_to(self.scratch_dir)
                items.append({
                    "name": item.name,
                    "path": str(rel_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {
                "success": True,
                "result": {
                    "directory": str(resolved.relative_to(self.scratch_dir)),
                    "items": items
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to list files: {e}"}
    
    async def _delete_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file."""
        path = args.get("path", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        # Check if locked by another agent
        if await self.lock_manager.is_locked_by_other(str(resolved), self.agent_id):
            return {"success": False, "error": "File is locked by another agent"}
        
        if self._is_protected_planning_file(resolved) and "Architect" not in self.agent_name:
            return {
                "success": False,
                "error": "Only Bossy McArchitect can delete devplan.md or master_plan.md. "
                         "Ask the Architect to adjust the plan/dashboard instead of deleting directly.",
            }
        
        try:
            if resolved.is_file():
                resolved.unlink()
            else:
                return {"success": False, "error": "Cannot delete directories with this tool"}
            
            return {"success": True, "result": f"Deleted {path}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete: {e}"}
    
    async def _create_folder(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder."""
        path = args.get("path", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            return {"success": True, "result": f"Created folder: {path}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to create folder: {e}"}
    
    async def _search_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for text in files."""
        query = args.get("query", "")
        path = args.get("path", ".")
        
        if not query:
            return {"success": False, "error": "query is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        try:
            results = []
            search_dir = resolved if resolved.is_dir() else resolved.parent
            
            for file_path in search_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            content = await f.read()
                        
                        for i, line in enumerate(content.split('\n'), 1):
                            if query.lower() in line.lower():
                                results.append({
                                    "file": str(file_path.relative_to(self.scratch_dir)),
                                    "line": i,
                                    "content": line.strip()[:200]
                                })
                    except:
                        pass  # Skip binary/unreadable files
            
            return {
                "success": True,
                "result": {
                    "query": query,
                    "matches": results[:50]  # Limit results
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {e}"}
    
    async def _run_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run a shell command (with safety restrictions)."""
        command = args.get("command", "")
        
        if not command:
            return {"success": False, "error": "command is required"}
        
        # Allowed commands (whitelist approach)
        allowed_prefixes = [
            "python", "pip", "node", "npm", "npx",
            "git status", "git log", "git diff", "git branch",
            "ls", "dir", "cat", "type", "echo", "head", "tail",
            "grep", "find", "wc"
        ]
        
        cmd_lower = command.lower().strip()
        is_allowed = any(cmd_lower.startswith(prefix) for prefix in allowed_prefixes)
        
        if not is_allowed:
            return {
                "success": False,
                "error": f"Command not allowed. Allowed: {', '.join(allowed_prefixes)}"
            }
        
        try:
            # Run in agent workspace
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.agent_workspace)
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            
            return {
                "success": proc.returncode == 0,
                "result": {
                    "stdout": stdout.decode('utf-8', errors='replace')[:5000],
                    "stderr": stderr.decode('utf-8', errors='replace')[:2000],
                    "return_code": proc.returncode
                }
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Command timed out (30s limit)"}
        except Exception as e:
            return {"success": False, "error": f"Command failed: {e}"}

    async def _get_git_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get git status for the current project's workspace (read-only)."""
        from pathlib import Path

        # Run git from the repo root, but restrict the status to the current
        # project scratch/shared workspace so agents don't see or reason about
        # unrelated files.
        repo_root = Path(__file__).parent.parent

        try:
            rel = self.agent_workspace.relative_to(repo_root)
            pathspec = str(rel)
        except ValueError:
            # Fallback: just show status for the current working directory
            pathspec = "."

        cmd = f"git status --short -- {pathspec}"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_root),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20)

            return {
                "success": proc.returncode == 0,
                "result": {
                    "command": cmd,
                    "stdout": stdout.decode("utf-8", errors="replace")[:5000],
                    "stderr": stderr.decode("utf-8", errors="replace")[:2000],
                    "return_code": proc.returncode,
                },
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "git status timed out (20s limit)"}
        except Exception as e:
            return {"success": False, "error": f"git status failed: {e}"}

    async def _get_git_diff(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summarized git diff for the current project's workspace (read-only)."""
        from pathlib import Path

        repo_root = Path(__file__).parent.parent

        # Optional narrower path relative to the agent workspace
        rel_path = (args.get("path") or "").strip()

        if rel_path:
            try:
                target = (self.agent_workspace / rel_path).resolve()
                rel = target.relative_to(repo_root)
                pathspec = str(rel)
            except Exception:
                pathspec = rel_path
        else:
            try:
                rel = self.agent_workspace.relative_to(repo_root)
                pathspec = str(rel)
            except ValueError:
                pathspec = "."

        cmd = f"git diff --stat -- {pathspec}"

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_root),
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            return {
                "success": proc.returncode == 0,
                "result": {
                    "command": cmd,
                    "stdout": stdout.decode("utf-8", errors="replace")[:8000],
                    "stderr": stderr.decode("utf-8", errors="replace")[:2000],
                    "return_code": proc.returncode,
                },
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "git diff timed out (30s limit)"}
        except Exception as e:
            return {"success": False, "error": f"git diff failed: {e}"}
    
    async def _git_commit(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stage and commit changes for the current project's workspace.

        Safety rules:
        - Only Checky McManager or Deployo McOps may invoke this tool.
        - Commits are restricted to the active project's scratch/shared
          workspace so other code in the repo is not touched.
        - This tool never pushes to remotes; the human is responsible for
          any git push / PR operations.
        """
        from pathlib import Path

        message = (args.get("message") or "").strip()
        if not message:
            return {"success": False, "error": "message is required"}

        lower = (self.agent_name or "").lower()
        if "checky mcmanager" not in lower and "deployo mcops" not in lower:
            return {
                "success": False,
                "error": "Only Checky McManager or Deployo McOps can perform git commits. "
                         "Ask them to review and commit on your behalf.",
            }

        repo_root = Path(__file__).parent.parent

        try:
            rel_workspace = self.agent_workspace.relative_to(repo_root)
            pathspec = str(rel_workspace)
        except ValueError:
            # Fallback: commit from the current workspace directory
            repo_root = self.agent_workspace
            pathspec = "."

        try:
            # First stage changes under the workspace
            add_proc = await asyncio.create_subprocess_exec(
                "git",
                "add",
                pathspec,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_root),
            )
            add_stdout, add_stderr = await asyncio.wait_for(add_proc.communicate(), timeout=30)

            add_out = add_stdout.decode("utf-8", errors="replace")
            add_err = add_stderr.decode("utf-8", errors="replace")
            if add_proc.returncode != 0:
                return {
                    "success": False,
                    "error": f"git add failed: {add_err.strip() or 'non-zero exit code'}",
                    "result": {
                        "step": "git add",
                        "command": f"git add {pathspec}",
                        "stdout": add_out[:3000],
                        "stderr": add_err[:2000],
                        "return_code": add_proc.returncode,
                    },
                }

            # Then commit with the provided message
            commit_proc = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(repo_root),
            )
            commit_stdout, commit_stderr = await asyncio.wait_for(commit_proc.communicate(), timeout=30)

            c_out = commit_stdout.decode("utf-8", errors="replace")
            c_err = commit_stderr.decode("utf-8", errors="replace")

            result_payload = {
                "step": "git commit",
                "command": f"git commit -m '<message>' -- {pathspec}",
                "stdout": c_out[:5000],
                "stderr": c_err[:2000],
                "return_code": commit_proc.returncode,
            }

            if commit_proc.returncode != 0:
                # Common case: nothing to commit
                return {
                    "success": False,
                    "error": c_err.strip() or "git commit failed",
                    "result": result_payload,
                }

            return {"success": True, "result": result_payload}

        except asyncio.TimeoutError:
            return {"success": False, "error": "git commit timed out (30s limit)"}
        except Exception as e:
            return {"success": False, "error": f"git commit failed: {e}"}
    
    async def _claim_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Claim exclusive access to a file."""
        path = args.get("path", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        success, message = await self.lock_manager.claim_file(
            str(resolved), self.agent_id, self.agent_name
        )
        
        return {"success": success, "result" if success else "error": message}
    
    async def _release_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Release a file lock."""
        path = args.get("path", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        success, message = await self.lock_manager.release_file(
            str(resolved), self.agent_id, self.agent_name
        )
        
        return {"success": success, "result" if success else "error": message}
    
    async def _get_file_locks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get all current file locks."""
        locks = await self.lock_manager.get_all_locks()
        return {
            "success": True,
            "result": {"locks": locks}
        }
    
    async def _spawn_worker(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Spawn a new worker agent.
        
        Accepts either a role key (e.g., "backend_dev") or display name 
        (e.g., "Codey McBackend") and resolves it to the correct role.
        """
        role = args.get("role", "")
        if not role:
            return {"success": False, "error": "role is required"}
        
        # Resolve display name or role key to valid role key
        from agents import resolve_role, AGENT_CLASSES, DISPLAY_NAME_TO_ROLE
        try:
            resolved_role = resolve_role(role)
        except ValueError:
            valid_roles = list(AGENT_CLASSES.keys())
            valid_names = list(DISPLAY_NAME_TO_ROLE.keys())
            return {
                "success": False, 
                "error": f"Unknown role: '{role}'. Valid role keys: {valid_roles}. Valid display names: {valid_names}"
            }
            
        from core.chatroom import get_chatroom
        chatroom = await get_chatroom()
        agent = await chatroom.spawn_agent(resolved_role)
        
        if agent:
            return {"success": True, "result": f"Spawned agent: {agent.name} ({resolved_role})"}
        return {"success": False, "error": f"Failed to spawn agent with role: {resolved_role}"}

    async def _create_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        description = args.get("description", "")
        if not description:
            return {"success": False, "error": "description is required"}
            
        from core.task_manager import get_task_manager
        tm = get_task_manager()
        task = tm.create_task(description)
        return {"success": True, "result": f"Task created: {task.id}"}

    async def _update_task_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update the status and optional result of an existing task.

        Expected arguments:
            task_id: ID of the task
            status: One of "pending", "in_progress", "completed", "failed"
            result: Optional result / error summary
        """
        task_id = args.get("task_id", "")
        status = args.get("status", "")
        result = args.get("result")

        if not task_id:
            return {"success": False, "error": "task_id is required"}
        if not status:
            return {"success": False, "error": "status is required"}

        from core.task_manager import get_task_manager
        tm = get_task_manager()
        task = tm.update_task_status(task_id, status, result=result)
        if not task:
            return {"success": False, "error": f"Failed to update task {task_id}. Ensure the ID and status are valid."}

        return {
            "success": True,
            "result": f"Task {task_id} updated to status '{task.status.value}'",
        }

    async def _assign_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a task to an agent."""
        agent_name = args.get("agent_name", "")
        description = args.get("description", "")
        
        if not agent_name:
            return {"success": False, "error": "agent_name is required"}
        if not description:
            return {"success": False, "error": "description is required"}
            
        from core.chatroom import get_chatroom
        chatroom = await get_chatroom()
        
        success = await chatroom.assign_task(agent_name, description)
        
        if success:
            return {"success": True, "result": f"Assigned task to {agent_name}: {description[:50]}..."}
        return {"success": False, "error": f"Failed to assign task to {agent_name} - agent not found"}

    async def _append_decision_log(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Append a structured entry to the shared decisions log.

        Writes to scratch/shared/decisions.md, creating the file with a header
        if it does not exist yet.
        """
        title = (args.get("title") or "").strip()
        details = (args.get("details") or "").strip()

        if not title and not details:
            return {"success": False, "error": "title or details is required"}

        path = "shared/decisions.md"

        # Ensure the log file exists with a simple header
        try:
            valid, resolved, error = self._validate_path(path)
            if not valid:
                return {"success": False, "error": error}
            if not resolved.exists():
                header = "# Decision Log\n\nThis file records important technical and process decisions made by the swarm.\n\n"
                create_result = await self._write_file({"path": path, "content": header})
                if not create_result.get("success"):
                    return {"success": False, "error": create_result.get("error", "Failed to create decisions.md")}
        except Exception as e:
            return {"success": False, "error": f"Failed to prepare decisions.md: {e}"}

        timestamp = datetime.now().isoformat(timespec="seconds")
        agent = self.agent_name or "Unknown"

        lines: list[str] = []
        lines.append(f"## {title or 'Decision'} ({timestamp})")
        lines.append(f"- By: {agent}")
        if details:
            lines.append("")
            lines.append(details)
        lines.append("")

        entry = "\n".join(lines) + "\n"

        return await self._append_file({"path": path, "content": entry})

    async def _append_team_log(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Append an event entry to the shared team log.

        Writes to scratch/shared/team_log.md, which acts as a chronological
        feed of notable swarm events that all agents can read.
        """
        summary = (args.get("summary") or "").strip()
        category = (args.get("category") or "general").strip()
        details = (args.get("details") or "").strip()

        if not summary:
            return {"success": False, "error": "summary is required"}

        path = "shared/team_log.md"

        # Ensure the log file exists with a header
        try:
            valid, resolved, error = self._validate_path(path)
            if not valid:
                return {"success": False, "error": error}
            if not resolved.exists():
                header = "# Team Event Log\n\nChronological log of notable swarm events, status changes, and handoffs.\n\n"
                create_result = await self._write_file({"path": path, "content": header})
                if not create_result.get("success"):
                    return {"success": False, "error": create_result.get("error", "Failed to create team_log.md")}
        except Exception as e:
            return {"success": False, "error": f"Failed to prepare team_log.md: {e}"}

        timestamp = datetime.now().isoformat(timespec="seconds")
        agent = self.agent_name or "Unknown"

        lines: list[str] = []
        lines.append(f"## {timestamp} — {summary}")
        lines.append(f"- By: {agent}")
        if category:
            lines.append(f"- Category: {category}")
        if details:
            lines.append("")
            lines.append(details)
        lines.append("")

        entry = "\n".join(lines) + "\n"

        return await self._append_file({"path": path, "content": entry})

    async def _get_swarm_state(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get the state of all agents and tasks."""
        from core.task_manager import get_task_manager
        from core.chatroom import get_chatroom
        
        tm = get_task_manager()
        chatroom = await get_chatroom()
        
        tasks = [t.to_dict() for t in tm.get_all_tasks()]
        agents = [a.get_info() for a in chatroom._agents.values()]
        
        return {
            "success": True,
            "result": {
                "agents": agents,
                "tasks": tasks
            }
        }

    async def _update_devplan_dashboard(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and write a *non-destructive* devplan dashboard from current swarm state.

        Behavior:
        - If scratch/shared/devplan.md exists, everything before the
          ``<!-- LIVE_DASHBOARD_START -->`` marker is treated as the
          canonical plan/scope and is preserved as-is.
        - The section starting at that marker is fully regenerated from the
          current agents and tasks and appended after the preserved scope.
        - If the marker is not present, the entire existing devplan file is
          treated as scope and left intact, with the live dashboard appended
          to the end.
        """
        from core.task_manager import get_task_manager
        from core.chatroom import get_chatroom

        tm = get_task_manager()
        chatroom = await get_chatroom()

        tasks = tm.get_all_tasks()
        agents = list(chatroom._agents.values())

        # Index agents by id for quick lookup
        agents_by_id = {a.agent_id: a for a in agents}

        # Basic task stats
        status_counts: Dict[str, int] = {"pending": 0, "in_progress": 0, "completed": 0, "failed": 0}
        for t in tasks:
            key = getattr(t.status, "value", str(t.status))
            if key in status_counts:
                status_counts[key] += 1

        # Group tasks by agent
        tasks_by_agent: Dict[str, list] = {}
        for t in tasks:
            owner = agents_by_id.get(t.assigned_to).name if t.assigned_to in agents_by_id else "Unassigned"
            tasks_by_agent.setdefault(owner, []).append(t)

        # Build the live dashboard section with a clear marker
        dashboard_lines: list[str] = []
        dashboard_lines.append("<!-- LIVE_DASHBOARD_START -->")
        dashboard_lines.append("")
        dashboard_lines.append("## Live Task Dashboard")
        dashboard_lines.append("")
        dashboard_lines.append("### Overall Status")
        dashboard_lines.append("")
        dashboard_lines.append(f"- Active agents: {len(agents)}")
        total_tasks = len(tasks)
        dashboard_lines.append(f"- Total tasks: {total_tasks}")
        if total_tasks:
            dashboard_lines.append(f"  - Pending: {status_counts['pending']}")
            dashboard_lines.append(f"  - In Progress: {status_counts['in_progress']}")
            dashboard_lines.append(f"  - Completed: {status_counts['completed']}")
            dashboard_lines.append(f"  - Failed: {status_counts['failed']}")

        dashboard_lines.append("")
        dashboard_lines.append("### Tasks by Agent")
        dashboard_lines.append("")

        if not tasks:
            dashboard_lines.append("No tasks have been created yet.")
        else:
            # Stable order: Architect and then others by name
            agent_names = sorted(tasks_by_agent.keys(), key=lambda n: ("Bossy McArchitect" not in n, n))
            for name in agent_names:
                dashboard_lines.append(f"#### {name}")
                for t in tasks_by_agent[name]:
                    status = getattr(t.status, "value", str(t.status))
                    checked = "x" if status == "completed" else " "
                    icon = "✅" if status == "completed" else ("⏳" if status == "pending" else ("🔄" if status == "in_progress" else "❌"))
                    short_id = t.id.split("-")[0]
                    desc = t.description.strip().replace("\n", " ")
                    if len(desc) > 120:
                        desc = desc[:117] + "..."
                    dashboard_lines.append(f"- [{checked}] {icon} ({short_id}) {desc}")
                dashboard_lines.append("")

        dashboard_lines.append("### Blockers & Risks")
        dashboard_lines.append("")
        blockers = [t for t in tasks if getattr(t.status, "value", str(t.status)) == "failed"]
        if not blockers:
            dashboard_lines.append("- None currently recorded. If something is blocked, describe it here so the human can help.")
        else:
            for t in blockers:
                short_id = t.id.split("-")[0]
                desc = (t.result or t.description).strip().replace("\n", " ")
                if len(desc) > 160:
                    desc = desc[:157] + "..."
                dashboard_lines.append(f"- ⚠️ ({short_id}) {desc}")

        dashboard_section = "\n".join(dashboard_lines).rstrip() + "\n"

        # Preserve any existing devplan scope content before the marker
        scope_prefix = ""
        try:
            existing = await self._read_file({"path": "shared/devplan.md"})
            if existing.get("success"):
                raw = existing["result"].get("content", "")
                marker = "<!-- LIVE_DASHBOARD_START -->"
                idx = raw.find(marker)
                if idx != -1:
                    scope_prefix = raw[:idx].rstrip()
                else:
                    scope_prefix = raw.rstrip()
        except Exception:
            scope_prefix = ""

        if scope_prefix:
            content = scope_prefix + "\n\n---\n\n" + dashboard_section
        else:
            content = dashboard_section

        # Write to shared/devplan.md (Architect's internal tracking)
        write_result = await self._write_file({
            "path": "shared/devplan.md",
            "content": content,
        })

        if not write_result.get("success"):
            return {"success": False, "error": write_result.get("error", "Failed to write devplan.md")}

        # Also generate a user-facing dashboard.md with cleaner formatting
        user_dashboard = self._generate_user_dashboard(agents, tasks, status_counts, tasks_by_agent, blockers)
        await self._write_file({
            "path": "shared/dashboard.md",
            "content": user_dashboard,
        })

        return {
            "success": True,
            "result": {
                "message": "Devplan and dashboard updated",
                "paths": ["shared/devplan.md", "shared/dashboard.md"],
            },
        }

    def _generate_user_dashboard(self, agents, tasks, status_counts, tasks_by_agent, blockers) -> str:
        """Generate a clean, user-facing dashboard showing current project status."""
        from datetime import datetime
        
        lines = []
        lines.append("# 📊 Project Dashboard")
        lines.append("")
        lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        
        # Progress bar
        total = len(tasks)
        completed = status_counts.get("completed", 0)
        if total > 0:
            pct = int((completed / total) * 100)
            filled = int(pct / 5)
            bar = "█" * filled + "░" * (20 - filled)
            lines.append(f"## Progress: [{bar}] {pct}% ({completed}/{total} tasks)")
        else:
            lines.append("## Progress: No tasks yet")
        lines.append("")
        
        # Current Status Summary
        lines.append("## 🔄 Current Status")
        lines.append("")
        in_progress = [t for t in tasks if getattr(t.status, "value", str(t.status)) == "in_progress"]
        if in_progress:
            lines.append("**Currently Working On:**")
            for t in in_progress[:5]:  # Show max 5
                desc = t.description.strip().replace("\n", " ")[:80]
                lines.append(f"- 🔄 {desc}")
            lines.append("")
        
        pending = [t for t in tasks if getattr(t.status, "value", str(t.status)) == "pending"]
        if pending:
            lines.append("**Up Next:**")
            for t in pending[:3]:  # Show max 3
                desc = t.description.strip().replace("\n", " ")[:80]
                lines.append(f"- ⏳ {desc}")
            if len(pending) > 3:
                lines.append(f"- ... and {len(pending) - 3} more pending")
            lines.append("")
        
        # Blockers (important for user visibility)
        if blockers:
            lines.append("## ⚠️ Blockers & Issues")
            lines.append("")
            for t in blockers:
                desc = (t.result or t.description).strip().replace("\n", " ")[:120]
                lines.append(f"- ❌ {desc}")
            lines.append("")
        
        # Active Agents
        lines.append("## 👥 Active Agents")
        lines.append("")
        for agent in agents:
            status = getattr(agent, "status", None)
            status_str = status.value if status else "unknown"
            icon = "🟢" if status_str == "working" else "⚪"
            task_count = len(tasks_by_agent.get(agent.name, []))
            lines.append(f"- {icon} **{agent.name}** ({task_count} tasks)")
        lines.append("")
        
        # Recent Completions
        completed_tasks = [t for t in tasks if getattr(t.status, "value", str(t.status)) == "completed"]
        if completed_tasks:
            lines.append("## ✅ Recently Completed")
            lines.append("")
            for t in completed_tasks[-5:]:  # Show last 5
                desc = t.description.strip().replace("\n", " ")[:60]
                lines.append(f"- ✓ {desc}")
            lines.append("")
        
        return "\n".join(lines)

    async def _complete_my_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mark the agent's currently assigned task as complete.

        This is the preferred way for workers to signal task completion.
        It updates the task registry and sets the agent status to IDLE.
        """
        result_summary = (args.get("result") or "").strip()

        # Get the agent's current task from the chatroom
        from core.chatroom import get_chatroom
        from core.task_manager import get_task_manager

        chatroom = await get_chatroom()
        agent = chatroom._agents.get(self.agent_id)

        if not agent:
            return {"success": False, "error": "Agent not found in chatroom"}

        task_id = getattr(agent, "current_task_id", None)
        if not task_id:
            return {"success": False, "error": "No task currently assigned to you"}

        tm = get_task_manager()
        task = tm.complete_task(task_id, result=result_summary or "Task completed successfully")

        if not task:
            return {"success": False, "error": f"Failed to complete task {task_id}"}

        # Update agent state
        agent.status = AgentStatus.IDLE
        agent.current_task_id = None
        agent.current_task_description = ""

        logger.info(f"[{self.agent_name}] Completed task {task_id} via complete_my_task tool")

        # Check if all tasks are done and trigger auto-resume
        all_tasks = tm.get_all_tasks()
        open_tasks = [t for t in all_tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]

        auto_resume_triggered = False
        if not open_tasks and completed_tasks:
            try:
                auto_msg = Message(
                    content=(
                        f"Phase milestone reached: {len(completed_tasks)} task(s) completed, 0 remaining. "
                        "Bossy McArchitect: Review the devplan, check what work remains in the master plan, "
                        "and assign the next batch of tasks to keep development moving."
                    ),
                    sender_name="Auto Orchestrator",
                    sender_id="auto_orchestrator",
                    role=MessageRole.HUMAN,
                    message_type=MessageType.CHAT
                )
                await chatroom._broadcast_message(auto_msg)
                for a in list(chatroom._agents.values()):
                    await a.process_incoming_message(auto_msg)
                auto_resume_triggered = True
                logger.info("Auto-orchestrator triggered via complete_my_task: all tasks complete")
            except Exception as e:
                logger.warning(f"Failed to trigger auto-resume: {e}")

        return {
            "success": True,
            "result": {
                "message": f"Task {task_id} marked as complete",
                "auto_resume_triggered": auto_resume_triggered,
            },
        }

    async def _append_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Append content to an existing file."""
        path = args.get("path", "")
        content = args.get("content", "")
        
        if not path:
            return {"success": False, "error": "path is required"}
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}. Use write_file to create new files."}
        
        # Check if locked by another agent
        if await self.lock_manager.is_locked_by_other(str(resolved), self.agent_id):
            return {"success": False, "error": "File is locked by another agent."}
        
        if self._is_protected_planning_file(resolved) and "Architect" not in self.agent_name:
            return {
                "success": False,
                "error": "Only Bossy McArchitect can modify devplan.md or master_plan.md. "
                         "Ask the Architect to adjust the plan/dashboard instead of editing directly.",
            }
        
        try:
            async with aiofiles.open(resolved, 'a', encoding='utf-8') as f:
                await f.write(content)
            
            return {
                "success": True,
                "result": f"Successfully appended {len(content)} bytes to {path}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to append to file: {e}"}

    async def _scaffold_project(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a project scaffold with common structure."""
        project_type = args.get("project_type", "python")
        project_name = args.get("project_name", "myproject")
        
        valid, base_path, error = self._validate_path(f"shared/{project_name}")
        if not valid:
            return {"success": False, "error": error}
        
        try:
            base_path.mkdir(parents=True, exist_ok=True)
            
            created_files = []
            
            if project_type == "python":
                # Python project structure
                dirs = ["src", "tests", "docs", "config"]
                for d in dirs:
                    (base_path / d).mkdir(exist_ok=True)
                
                # Create __init__.py files
                (base_path / "src" / "__init__.py").touch()
                (base_path / "tests" / "__init__.py").touch()
                
                # Create basic files
                files = {
                    "README.md": f"# {project_name}\n\nProject description here.\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```python\n# Example usage\n```\n",
                    "requirements.txt": "# Project dependencies\n",
                    ".gitignore": "__pycache__/\n*.py[cod]\n*$py.class\n.env\nvenv/\n.venv/\ndist/\nbuild/\n*.egg-info/\n",
                    "src/main.py": '"""Main entry point."""\n\ndef main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()\n',
                    "tests/test_main.py": '"""Tests for main module."""\nimport pytest\nfrom src.main import main\n\ndef test_main():\n    # Add tests here\n    pass\n',
                    "config/settings.py": '"""Configuration settings."""\nimport os\nfrom dotenv import load_dotenv\n\nload_dotenv()\n\n# Add configuration here\n',
                }
                
            elif project_type == "node" or project_type == "javascript":
                dirs = ["src", "tests", "public", "config"]
                for d in dirs:
                    (base_path / d).mkdir(exist_ok=True)
                
                files = {
                    "README.md": f"# {project_name}\n\nProject description here.\n\n## Installation\n\n```bash\nnpm install\n```\n\n## Usage\n\n```bash\nnpm start\n```\n",
                    "package.json": f'{{\n  "name": "{project_name}",\n  "version": "1.0.0",\n  "description": "",\n  "main": "src/index.js",\n  "scripts": {{\n    "start": "node src/index.js",\n    "test": "jest"\n  }},\n  "dependencies": {{}},\n  "devDependencies": {{}}\n}}',
                    ".gitignore": "node_modules/\n.env\ndist/\ncoverage/\n*.log\n",
                    "src/index.js": '// Main entry point\nconsole.log("Hello, World!");\n',
                    "tests/index.test.js": '// Tests\ndescribe("Main", () => {\n  test("should work", () => {\n    expect(true).toBe(true);\n  });\n});\n',
                }
                
            elif project_type == "react":
                dirs = ["src", "src/components", "src/hooks", "src/utils", "public", "tests"]
                for d in dirs:
                    (base_path / d).mkdir(exist_ok=True)
                
                files = {
                    "README.md": f"# {project_name}\n\nReact application.\n\n## Getting Started\n\n```bash\nnpm install\nnpm start\n```\n",
                    "package.json": f'{{\n  "name": "{project_name}",\n  "version": "1.0.0",\n  "dependencies": {{\n    "react": "^18.2.0",\n    "react-dom": "^18.2.0"\n  }}\n}}',
                    ".gitignore": "node_modules/\n.env\nbuild/\ndist/\n",
                    "src/App.jsx": 'import React from "react";\n\nfunction App() {\n  return (\n    <div className="App">\n      <h1>Hello, World!</h1>\n    </div>\n  );\n}\n\nexport default App;\n',
                    "src/index.jsx": 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\n\nconst root = ReactDOM.createRoot(document.getElementById("root"));\nroot.render(<App />);\n',
                    "public/index.html": '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>' + project_name + '</title>\n</head>\n<body>\n  <div id="root"></div>\n</body>\n</html>\n',
                }
                
            else:
                # Generic project
                dirs = ["src", "tests", "docs"]
                for d in dirs:
                    (base_path / d).mkdir(exist_ok=True)
                
                files = {
                    "README.md": f"# {project_name}\n\nProject description here.\n",
                    ".gitignore": "*.log\n.env\n",
                }
            
            # Write all files
            for filename, content in files.items():
                filepath = base_path / filename
                filepath.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
                    await f.write(content)
                created_files.append(str(filepath.relative_to(self.scratch_dir)))
            
            return {
                "success": True,
                "result": {
                    "message": f"Created {project_type} project scaffold",
                    "project_path": f"shared/{project_name}",
                    "created_files": created_files
                }
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to scaffold project: {e}"}

    async def _get_project_structure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get a tree view of the project structure."""
        path = args.get("path", "shared")
        max_depth = args.get("max_depth", 4)
        
        valid, resolved, error = self._validate_path(path)
        if not valid:
            return {"success": False, "error": error}
        
        if not resolved.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        
        def build_tree(dir_path: Path, prefix: str = "", depth: int = 0) -> str:
            if depth > max_depth:
                return prefix + "...\n"
            
            lines = []
            try:
                items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    connector = "└── " if is_last else "├── "
                    
                    if item.is_dir():
                        lines.append(f"{prefix}{connector}{item.name}/")
                        extension = "    " if is_last else "│   "
                        lines.append(build_tree(item, prefix + extension, depth + 1))
                    else:
                        size = item.stat().st_size
                        size_str = f"{size}B" if size < 1024 else f"{size//1024}KB"
                        lines.append(f"{prefix}{connector}{item.name} ({size_str})")
            except PermissionError:
                lines.append(f"{prefix}[Permission Denied]")
            
            return "\n".join(lines)
        
        tree = f"{path}/\n{build_tree(resolved)}"
        
        return {
            "success": True,
            "result": tree
        }

    async def _move_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Move or rename a file."""
        source = args.get("source", "")
        destination = args.get("destination", "")
        
        if not source or not destination:
            return {"success": False, "error": "source and destination are required"}
            
        valid_src, res_src, err_src = self._validate_path(source)
        if not valid_src:
            return {"success": False, "error": f"Source error: {err_src}"}
            
        valid_dst, res_dst, err_dst = self._validate_path(destination)
        if not valid_dst:
            return {"success": False, "error": f"Destination error: {err_dst}"}
            
        if not res_src.exists():
            return {"success": False, "error": f"Source file not found: {source}"}
            
        # Check locks
        if await self.lock_manager.is_locked_by_other(str(res_src), self.agent_id):
            return {"success": False, "error": "Source file is locked by another agent"}
            
        if res_dst.exists() and await self.lock_manager.is_locked_by_other(str(res_dst), self.agent_id):
            return {"success": False, "error": "Destination file is locked by another agent"}
            
        try:
            # Ensure destination directory exists
            res_dst.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            # Use shutil.move for robustness
            shutil.move(str(res_src), str(res_dst))
            
            return {"success": True, "result": f"Moved {source} to {destination}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to move file: {e}"}


# Tool definitions for the API
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Returns the file content with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file (relative to your workspace)"
                    }
                },
                "required": ["path"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with new content. You MUST provide the COMPLETE file content. Do not use placeholders like '# ... rest of code ...' or truncate code. The file must be fully functional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit specific lines in an existing file. Provide the exact new content for the specified line range. Do not replace code with comments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Starting line number (1-indexed)"
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Ending line number (inclusive)"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "New content to replace the lines"
                    }
                },
                "required": ["path", "start_line", "end_line", "new_content"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": "Replace a specific string in a file with a new string. Use this for precise edits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "old_string": {
                        "type": "string",
                        "description": "The exact string to replace (must match exactly)"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The new string to replace it with"
                    }
                },
                "required": ["path", "old_string", "new_string"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (default: current workspace)"
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to delete"
                    }
                },
                "required": ["path"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move or rename a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Current path of the file"
                    },
                    "destination": {
                        "type": "string",
                        "description": "New path for the file"
                    }
                },
                "required": ["source", "destination"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a folder (including parent folders if needed).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path of the folder to create"
                    }
                },
                "required": ["path"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for text/code patterns in files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (default: workspace)"
                    }
                },
                "required": ["query"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command. Limited to safe commands like python, pip, node, npm, git status/log/diff, ls, cat, grep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run"
                    }
                },
                "required": ["command"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_git_status",
            "description": "View git status for the current project's scratch/shared workspace. Read-only wrapper around 'git status --short'.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_git_diff",
            "description": "View a summarized git diff for the current project's scratch/shared workspace. Read-only wrapper around 'git diff --stat'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Optional path (relative to the workspace) to narrow the diff."
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Stage and commit changes for the current project's scratch/shared workspace. Only Checky McManager or Deployo McOps may call this tool. This tool NEVER pushes to remotes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Commit message summarizing the work being checked in."
                    }
                },
                "required": ["message"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "claim_file",
            "description": "Claim exclusive access to a file before editing. Other agents won't be able to edit it until you release it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to claim"
                    }
                },
                "required": ["path"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "release_file",
            "description": "Release your exclusive claim on a file so others can edit it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to release"
                    }
                },
                "required": ["path"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_locks",
            "description": "See which files are currently claimed/locked by agents.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_worker",
            "description": "Spawn a new worker agent with a specific role. Use this to scale the swarm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The role of the agent (e.g., 'backend_dev', 'frontend_dev', 'qa_engineer')"
                    }
                },
                "required": ["role"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task in the swarm task registry without assigning it yet. Returns the new task ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the task to be performed"
                    }
                },
                "required": ["description"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assign_task",
            "description": "Assign a task to a specific agent. This wakes them up and sets their status to WORKING.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "The name of the agent to assign the task to"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the task to be performed"
                    }
                },
                "required": ["agent_name", "description"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task_status",
            "description": "Update the status/result of an existing task by ID (pending, in_progress, completed, failed). Use this to keep the task registry and dashboard in sync.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "ID of the task to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status: pending, in_progress, completed, or failed",
                        "enum": ["pending", "in_progress", "completed", "failed"]
                    },
                    "result": {
                        "type": "string",
                        "description": "Optional result or error summary to record with the task"
                    }
                },
                "required": ["task_id", "status"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_swarm_state",
            "description": "Get the current state of the swarm, including all agents (status) and tasks (status).",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Append content to the end of an existing file without overwriting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to append to"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to append to the file"
                    }
                },
                "required": ["path", "content"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scaffold_project",
            "description": "Create a project scaffold with standard directory structure and boilerplate files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_type": {
                        "type": "string",
                        "description": "Type of project: 'python', 'node', 'react', or 'generic'",
                        "enum": ["python", "node", "react", "generic"]
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (will be used as folder name)"
                    }
                },
                "required": ["project_type", "project_name"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_structure",
            "description": "Get a tree view of the project directory structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory (default: 'shared')"
                    },
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum depth to traverse (default: 4)"
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_devplan_dashboard",
            "description": "Regenerate the live devplan dashboard (devplan.md) from current agents and tasks. Use this to keep the project dashboard in sync as work progresses.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_decision_log",
            "description": "Append a structured entry to the shared decisions log (shared/decisions.md).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title for the decision."
                    },
                    "details": {
                        "type": "string",
                        "description": "Longer description of the decision and context."
                    }
                }
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_team_log",
            "description": "Append an event entry to the shared team log (shared/team_log.md).",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Short one-line summary of the event."
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category label (e.g. planning, risk, release)."
                    },
                    "details": {
                        "type": "string",
                        "description": "Optional longer description of the event."
                    }
                },
                "required": ["summary"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_my_task",
            "description": "Mark your currently assigned task as complete. Call this when you have finished your assigned work. This updates the task registry and frees you for new assignments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "string",
                        "description": "Brief summary of what was accomplished (e.g. 'Implemented ECS core with Entity, Component, System classes')"
                    }
                },
                "required": ["result"]
            },
        },
    },
]


# Orchestrator-only tools (for Architect)
ORCHESTRATOR_TOOL_NAMES = {
    "spawn_worker",
    "create_task",
    "assign_task",
    "get_swarm_state",
    "read_file",
    "write_file",
    "list_files",
    "get_project_structure",
    "update_devplan_dashboard",
}

ORCHESTRATOR_TOOLS = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in ORCHESTRATOR_TOOL_NAMES]

# Worker tools (everything except orchestration)
WORKER_TOOL_NAMES = {
    "read_file",
    "write_file",
    "edit_file",
    "replace_in_file",
    "list_files",
    "delete_file",
    "move_file",
    "create_folder",
    "search_code",
    "run_command",
    "get_git_status",
    "get_git_diff",
    "claim_file",
    "release_file",
    "get_file_locks",
    "append_file",
    "get_project_structure",
    "scaffold_project",
    "complete_my_task",  # Workers use this to signal task completion
}

WORKER_TOOLS = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in WORKER_TOOL_NAMES]


def get_tools_for_agent(agent_name: str) -> list:
    """Get the appropriate tool set for an agent based on their role."""
    # Architect gets full orchestration + dashboard tools
    if "Architect" in agent_name:
        return ORCHESTRATOR_TOOLS

    lowered = agent_name.lower()

    # Project Manager can see swarm state for reporting and can commit after approvals
    if "checky mcmanager" in lowered or "project_manager" in lowered:
        pm_tools = list(WORKER_TOOLS)
        for tool_name in ["get_swarm_state", "create_task", "update_task_status", "git_commit"]:
            tool_def = next((t for t in TOOL_DEFINITIONS if t["function"]["name"] == tool_name), None)
            if tool_def and tool_def not in pm_tools:
                pm_tools.append(tool_def)
        return pm_tools

    # DevOps gets worker tools plus git commit for release automation
    if "deployo mcops" in lowered or "devops" in lowered:
        devops_tools = list(WORKER_TOOLS)
        tool_def = next((t for t in TOOL_DEFINITIONS if t["function"]["name"] == "git_commit"), None)
        if tool_def and tool_def not in devops_tools:
            devops_tools.append(tool_def)
        return devops_tools

    return WORKER_TOOLS


def get_tools_system_prompt() -> str:
    """Get the system prompt addition for tool usage."""
    return """

## FILE TOOLS
You have access to tools for working with files in the SHARED workspace. Use them to:
- Read, write, and edit code files
- Search for code patterns
- Run safe commands (python, pip, node, npm, git status/log, etc.)

IMPORTANT RULES:
1. All file paths are relative to the shared workspace (scratch/shared/)
2. You are working in a SHARED environment. All agents see the same files.
3. Before editing a file that others might work on, use claim_file to get exclusive access
4. Release files with release_file when done
5. Keep responses SHORT when not using tools - tools do the heavy lifting
6. **NO MOCK CODE**: When writing files, you must provide the FULL implementation. No placeholders.

Your workspace folder: scratch/shared/
"""
