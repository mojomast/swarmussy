"""
Shared Context System - Lightweight file-based context sharing.

Instead of a database, agents share context via a simple markdown file:
  shared/context.md

This is much more token-efficient than the database memory system:
- Agents read this file at task start
- Key decisions/progress are appended
- File is periodically trimmed to keep it under a size limit
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
import aiofiles
import logging

logger = logging.getLogger(__name__)

# Max size of context file before trimming (in characters)
MAX_CONTEXT_SIZE = 8000


def get_context_path() -> Path:
    """Get path to shared context file."""
    from config.settings import get_scratch_dir
    return get_scratch_dir() / "shared" / "context.md"


async def read_shared_context() -> str:
    """Read the current shared context.
    
    Returns:
        The context content, or empty string if file doesn't exist.
    """
    path = get_context_path()
    try:
        if path.exists():
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                return await f.read()
    except Exception as e:
        logger.warning(f"Could not read context: {e}")
    return ""


async def append_context(entry: str, category: str = "note") -> bool:
    """Append an entry to the shared context.
    
    Args:
        entry: The context entry to add
        category: Category tag (e.g., "decision", "progress", "blocker")
        
    Returns:
        True if successful
    """
    path = get_context_path()
    timestamp = datetime.now().strftime("%H:%M")
    
    formatted_entry = f"\n[{timestamp}] **{category}**: {entry}\n"
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content
        existing = ""
        if path.exists():
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                existing = await f.read()
        
        # Trim if too large (keep last N characters)
        new_content = existing + formatted_entry
        if len(new_content) > MAX_CONTEXT_SIZE:
            # Keep header + last portion
            header = "# Shared Context\n\n*Recent project context and decisions.*\n\n---\n"
            trimmed = header + "\n...(older entries trimmed)...\n\n" + new_content[-(MAX_CONTEXT_SIZE - len(header) - 50):]
            new_content = trimmed
        
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(new_content)
        
        return True
    except Exception as e:
        logger.error(f"Could not append context: {e}")
        return False


async def init_shared_context(project_name: str = "Project") -> bool:
    """Initialize/reset the shared context file.
    
    Args:
        project_name: Name of the project
        
    Returns:
        True if successful
    """
    path = get_context_path()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    initial_content = f"""# Shared Context

*Project: {project_name}*
*Started: {timestamp}*

---

## Key Decisions


## Current Focus


## Blockers


---

"""
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(initial_content)
        return True
    except Exception as e:
        logger.error(f"Could not init context: {e}")
        return False


async def get_context_summary(max_chars: int = 2000) -> str:
    """Get a trimmed summary of the shared context.
    
    Args:
        max_chars: Maximum characters to return
        
    Returns:
        Trimmed context content
    """
    content = await read_shared_context()
    if len(content) <= max_chars:
        return content
    
    # Return last portion
    return "...(trimmed)...\n" + content[-max_chars:]


# Convenience function for agents
async def log_decision(decision: str) -> bool:
    """Log a key decision to shared context."""
    return await append_context(decision, "DECISION")


async def log_progress(progress: str) -> bool:
    """Log progress to shared context."""
    return await append_context(progress, "PROGRESS")


async def log_blocker(blocker: str) -> bool:
    """Log a blocker to shared context."""
    return await append_context(blocker, "BLOCKER")
