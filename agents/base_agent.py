"""
Base Agent class for Multi-Agent Chatroom.

This module defines the abstract base class for all AI agents in the chatroom.
Each agent has a distinct persona, uses an LLM model, and can use tools.
"""

import asyncio
import aiohttp
import random
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
import logging

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    REQUESTY_API_KEY,
    REQUESTY_API_BASE_URL,
    ZAI_API_KEY,
    ZAI_API_BASE_URL,
    DEFAULT_MODEL,
    SHORT_TERM_MEMORY_SIZE,
    DEFAULT_TEMPERATURE,
    MAX_RESPONSE_TOKENS,
    AGENT_SPEAK_PROBABILITY,
    TOOL_MAX_TOKENS
)

# API key loaded silently

# API logging callback - set by dashboard_tui
_api_log_callback = None

def set_api_log_callback(callback):
    """Set the callback for API logging from the TUI."""
    global _api_log_callback
    _api_log_callback = callback

def get_api_log_callback():
    """Get the current API log callback."""
    return _api_log_callback
from core.models import Message, MessageRole, MessageType, AgentConfig, MemoryEntry, AgentStatus, TaskStatus
from core.memory_store import get_memory_store
from core.summarizer import ConversationMemoryManager
from core.agent_tools import AgentToolExecutor, TOOL_DEFINITIONS, get_tools_system_prompt, get_tools_for_agent
from core.slim_tools import get_slim_tools_for_agent, get_slim_tools_prompt
from core.task_manager import get_task_manager
from core.token_tracker import get_token_tracker
from core.settings_manager import get_settings

logger = logging.getLogger(__name__)

_ZAI_RESPONSE_CACHE: Dict[str, Any] = {}
_ZAI_CACHE_MAX_ENTRIES = 256


@dataclass
class TaskContext:
    """
    Per-task context cache for efficient file discovery.
    
    Stores information discovered during a task to avoid redundant
    searches and file reads across tool calls.
    """
    task_id: str
    key_files: List[str] = field(default_factory=list)
    indexed_queries: Dict[str, List[str]] = field(default_factory=dict)  # query -> [paths]
    related_files: Dict[str, List[str]] = field(default_factory=dict)  # path -> [related]
    created_at: float = field(default_factory=time.time)
    
    def add_key_file(self, path: str) -> None:
        """Add a file to the key files list (deduped)."""
        if path not in self.key_files:
            self.key_files.append(path)
    
    def add_search_result(self, query: str, paths: List[str]) -> None:
        """Cache search results for a query."""
        self.indexed_queries[query] = paths
    
    def get_search_result(self, query: str) -> Optional[List[str]]:
        """Get cached search results for a query."""
        return self.indexed_queries.get(query)
    
    def add_related_files(self, path: str, related: List[str]) -> None:
        """Cache related files for a path."""
        self.related_files[path] = related
    
    def get_related_files(self, path: str) -> Optional[List[str]]:
        """Get cached related files for a path."""
        return self.related_files.get(path)


class BaseAgent(ABC):
    """
    Abstract base class for AI agents in the chatroom.
    
    Each agent has:
    - A unique persona defined by system prompt
    - An LLM model for generating responses
    - Short-term memory (rolling window of recent messages)
    - Long-term memory (persisted facts and summaries)
    - Tool calling capabilities for file operations
    - Per-task context cache for efficient file discovery
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the agent.
        
        Args:
            config: AgentConfig containing name, model, system prompt, etc.
        """
        self.config = config
        self.name = config.name
        self.agent_id = config.agent_id
        self.model = config.model
        self.system_prompt = config.system_prompt
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.speak_probability = config.speak_probability
        
        # Tools enabled by default
        self.tools_enabled = get_settings().get("tools_enabled", True)
        
        # Orchestration State
        self.status = AgentStatus.IDLE
        self.current_task_id: Optional[str] = None
        self.current_task_description: str = ""
        
        # Short-term memory: recent messages
        self._short_term_memory: List[Message] = []
        
        # Memory manager for long-term storage
        self._memory_manager = ConversationMemoryManager(self.agent_id)
        
        # Tool executor for file operations
        self._tool_executor = AgentToolExecutor(self.agent_id, self.name)
        
        # HTTP session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Track messages seen for summarization
        self._messages_since_summary = 0
        
        # Per-task context cache for efficient file discovery
        self._task_context_cache: Dict[str, TaskContext] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create the aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Clean up resources."""
        if self._session and not self._session.closed:
            await self._session.close()
        await self._memory_manager.close()
        # Release any file locks this agent holds
        from core.agent_tools import get_lock_manager
        await get_lock_manager().release_all_by_agent(self.agent_id)
    
    def get_task_context(self) -> Optional[TaskContext]:
        """Get the context cache for the current task."""
        if not self.current_task_id:
            return None
        return self._task_context_cache.get(self.current_task_id)
    
    def get_or_create_task_context(self) -> Optional[TaskContext]:
        """Get or create a context cache for the current task."""
        if not self.current_task_id:
            return None
        
        if self.current_task_id not in self._task_context_cache:
            self._task_context_cache[self.current_task_id] = TaskContext(
                task_id=self.current_task_id
            )
            # Prune old task contexts (keep last 5)
            if len(self._task_context_cache) > 5:
                oldest_key = min(
                    self._task_context_cache.keys(),
                    key=lambda k: self._task_context_cache[k].created_at
                )
                del self._task_context_cache[oldest_key]
        
        return self._task_context_cache[self.current_task_id]
    
    def update_task_context_files(self, files: List[str]) -> None:
        """Update the current task's key files list."""
        ctx = self.get_or_create_task_context()
        if ctx:
            for f in files:
                ctx.add_key_file(f)
    
    @property
    @abstractmethod
    def persona_description(self) -> str:
        """Return a brief description of this agent's persona."""
        pass
    
    def should_respond(self) -> bool:
        """
        Determine if this agent should respond.
        
        Strict Orchestration Logic:
        - Architect: Responds to NEW human messages OR auto-orchestrator messages
        - Workers: Only if assigned a task (WORKING)
        - Project Manager: Has its own should_respond() override
        """
        # Architect: respond to new human messages or auto-orchestrator messages
        if "Architect" in self.__class__.__name__:
            # Find the last message we should respond to (human or auto-orchestrator)
            last_trigger_msg_id = None
            for msg in reversed(self._short_term_memory):
                # Respond to human messages (including Auto Orchestrator which uses HUMAN role)
                if msg.role == MessageRole.HUMAN:
                    last_trigger_msg_id = msg.id
                    # Log for debugging auto-orchestrator triggers
                    if getattr(msg, 'sender_id', '') == 'auto_orchestrator':
                        logger.info(f"[{self.name}] Found Auto Orchestrator trigger: {msg.id}")
                    break
            
            # If no trigger messages, only respond on first join
            if not last_trigger_msg_id:
                return len(self._short_term_memory) == 0
            
            # Check if we already responded after this trigger message
            if hasattr(self, '_last_responded_to_human_id'):
                if self._last_responded_to_human_id == last_trigger_msg_id:
                    logger.debug(f"[{self.name}] Already responded to {last_trigger_msg_id[:8]}")
                    return False  # Already responded, wait for new input
            
            # New trigger message, we should respond
            # IMPORTANT: Set the ID immediately to prevent race conditions where
            # multiple rounds could start before respond() completes
            self._last_responded_to_human_id = last_trigger_msg_id
            logger.info(f"[{self.name}] Will respond to new trigger: {last_trigger_msg_id[:8]}")
            return True
        
        # Project Manager: delegate to its own should_respond() if it has one
        # The base class check here is a fallback; ProjectManager overrides this
        if "ProjectManager" in self.__class__.__name__ or "McManager" in self.name:
            # Let the subclass handle it - this code path shouldn't be hit
            # if ProjectManager properly overrides should_respond()
            return False

        # Workers only speak when working
        if self.status == AgentStatus.WORKING:
            return True
            
        return False
    
    def update_short_term_memory(self, message: Message):
        """
        Add a message to short-term memory, maintaining the rolling window.
        
        Args:
            message: The new message to add
        """
        self._short_term_memory.append(message)
        
        # Trim to window size
        if len(self._short_term_memory) > SHORT_TERM_MEMORY_SIZE:
            self._short_term_memory = self._short_term_memory[-SHORT_TERM_MEMORY_SIZE:]
    
    async def _build_context(self, global_history: List[Message]) -> List[Dict[str, str]]:
        """
        Build the message context for the API call.
        
        In EFFICIENT MODE (default):
        - Uses lean system prompts (~70% smaller)
        - Minimal tool descriptions (~80% smaller)
        - Fewer history messages (5 vs 10)
        - Skips long-term memory context
        
        Args:
            global_history: The global chat history
            
        Returns:
            List of messages in API format
        """
        settings = get_settings()
        efficient_mode = settings.get("efficient_mode", True)
        context_msg_count = settings.get("context_messages", 5)
        skip_memory = settings.get("skip_memory_context", True)
        
        messages = []
        
        # Get long-term memory context (only if not in efficient mode)
        memory_context = ""
        if not efficient_mode and not skip_memory:
            memory_store = await get_memory_store()
            memory_context = await self._memory_manager.get_context_memories(memory_store)
        
        # Build system prompt - LEAN version for efficient mode
        if efficient_mode:
            # Minimal focus instruction
            focus_instruction = """
## RULES
- NO placeholders. Write COMPLETE code.
- Use write_file for code, not chat.
- Call complete_my_task(result="...") when done.
- Keep chat SHORT. Tools do the work.
"""
        else:
            # Original verbose instruction
            focus_instruction = """

## CRITICAL - PROFESSIONAL CODING STANDARDS:
You are part of a high-performance software development swarm. Your goal is to ship high-quality, production-ready code.

1. **NO MOCK CODE**: You must write the FULL, WORKING implementation. Do not use placeholders like `# ... rest of code ...` or `# implementation here`.
2. **Be Thorough**: Do not skip steps or leave "TODOs" unless explicitly told to.
3. **Be Explicit**: When planning, list every file and function.
4. **Be Collaborative**: If you need expertise you don't have, ask the relevant specialist (e.g., Backend asking Frontend).
5. **Use Tools**: Do not write code in chat. Use `write_file` to create actual files.
6. **No Truncation**: When using `write_file`, you MUST write the FULL content. Never truncate.
7. **Big Files Are OK**: For core modules (engines, servers, routers, key UI screens), it is acceptable and expected to produce large, self-contained files. Avoid leaving tiny stubs where a full implementation is needed.
8. **Finish Core Modules First**: Prioritize completing core modules before starting new ones.

## FILE SYSTEM PROTOCOL:
- **Shared Work**: Use `shared/filename.ext` for anything other agents need to see (plans, source code, docs).
- **Private Work**: Use `filename.ext` (no prefix) for your own temporary scratchpad.
- **Access**: You can read any file in `shared/`.

## ORCHESTRATION PROTOCOL:
- **Wait for Tasks**: Do not start work until assigned.
- **Acknowledge**: When assigned, say "Acknowledged. Starting task..."
- **Signal Completion**: When done, call `complete_my_task(result="Brief summary of what you accomplished")`. This is REQUIRED to mark your task as done.
- **Silence**: Do not chat casually. Only speak to coordinate work.

Keep chat responses concise and focused on the task. Use the tools for the heavy lifting."""
        
        enhanced_system_prompt = self.system_prompt + focus_instruction
        
        # Add tool instructions if enabled
        if self.tools_enabled:
            if efficient_mode:
                tool_prompt = get_slim_tools_prompt(self.name)
            else:
                tool_prompt = get_tools_system_prompt().replace("{agent_name}", self.name)
            enhanced_system_prompt += tool_prompt
        
        if memory_context:
            enhanced_system_prompt += f"\n\n## Your Memories:\n{memory_context}"
            
        # Add Current Task Context (always include - it's essential)
        if self.current_task_id:
            task_manager = get_task_manager()
            task = task_manager.get_task(self.current_task_id)
            if task:
                enhanced_system_prompt += f"\n\n## TASK: {task.description}"
        
        messages.append({
            "role": "system",
            "content": enhanced_system_prompt
        })
        
        # Build role-aware view of recent history - use configured count
        recent_messages = global_history[-context_msg_count:]
        is_architect = "Architect" in self.__class__.__name__ or "Architect" in self.name

        if is_architect:
            # Architect sees the normal recent tail to reason about overall context
            for msg in recent_messages:
                messages.append(msg.to_api_format())
        else:
            # Workers: MINIMAL context - just task assignment + last human message
            seen_ids = set()
            worker_context: List[Message] = []

            # Always try to include the latest human message (for requirements)
            last_human: Optional[Message] = None
            for msg in reversed(recent_messages):
                if msg.role == MessageRole.HUMAN:
                    last_human = msg
                    break

            if last_human is not None:
                worker_context.append(last_human)
                seen_ids.add(last_human.id)

            # Include task assignment message if present
            for msg in recent_messages:
                if msg.id in seen_ids:
                    continue
                # System notices that mention this worker (task assignments)
                if msg.role == MessageRole.SYSTEM and self.name in msg.content:
                    worker_context.append(msg)
                    seen_ids.add(msg.id)
                    break  # Just the most recent assignment

            # Fallback: if nothing found, use last 2 messages only
            if not worker_context:
                worker_context = recent_messages[-2:] if len(recent_messages) >= 2 else recent_messages

            for msg in worker_context:
                messages.append(msg.to_api_format())
        
        return messages
    
    async def _call_api(
        self,
        messages: List[Dict[str, str]],
        use_tools: bool = False
    ) -> Dict[str, Any]:
        """
        Call the API to generate a response.
        
        Args:
            messages: List of messages in API format
            use_tools: Whether to include tool definitions
            
        Returns:
            Full API response data, or empty dict on error
        """
        settings = get_settings()

        # Global custom override (used when provider == "custom" or as legacy
        # fallback when no Requesty key is present).
        custom_base = (settings.get("api_base_url", "") or "").strip()
        custom_key = (settings.get("api_key", "") or "").strip()

        # Determine which provider this agent should use.
        is_architect = "Architect" in self.__class__.__name__ or "Architect" in getattr(self, "name", "")
        default_provider = settings.get("default_provider", "requesty") or "requesty"
        provider_key = "architect_provider" if is_architect else "swarm_provider"
        provider = settings.get(provider_key, default_provider) or "requesty"

        api_base_url = ""
        api_key = ""

        if provider == "zai":
            zai_base = (settings.get("zai_api_base_url", "") or "").strip()
            zai_key = (settings.get("zai_api_key", "") or "").strip() or ZAI_API_KEY
            api_base_url = zai_base or ZAI_API_BASE_URL
            api_key = zai_key
        elif provider == "openai":
            # Direct OpenAI API
            api_base_url = custom_base or "https://api.openai.com/v1/chat/completions"
            api_key = custom_key or os.getenv("OPENAI_API_KEY", "")
        elif provider == "custom":
            api_base_url = custom_base or REQUESTY_API_BASE_URL
            api_key = custom_key or REQUESTY_API_KEY
        else:  # requesty (default)
            api_base_url = REQUESTY_API_BASE_URL
            api_key = REQUESTY_API_KEY
            # Backwards compatibility: if no Requesty key is set but a custom
            # provider is configured, fall back to that.
            if not api_key and custom_base and custom_key:
                api_base_url = custom_base
                api_key = custom_key

        if not api_key:
            logger.error(
                f"API key not configured for provider '{provider}'. "
                "Set REQUESTY_API_KEY, configure a custom provider via /api, or provide ZAI_API_KEY / z.ai settings."
            )
            return {}

        if not api_base_url:
            logger.error(f"API base URL not configured for provider '{provider}'.")
            return {}

        session = await self._get_session()

        # Build tool identifier for API headers (for spoofing as different tools)
        tool_id = settings.get("tool_identifier", "swarm")
        tool_id_map = {
            "swarm": "swarm-agent/1.0",
            "claude-code": "claude-code/1.0",
            "cursor": "cursor/0.45",
            "windsurf": "windsurf/1.0",
            "aider": "aider/0.50",
            "continue": "continue/1.0",
        }
        if tool_id == "custom":
            user_agent = settings.get("custom_tool_id", "swarm-agent/1.0") or "swarm-agent/1.0"
        else:
            user_agent = tool_id_map.get(tool_id, "swarm-agent/1.0")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": TOOL_MAX_TOKENS if use_tools else self.max_tokens
        }

        cache_key = None
        cached_data: Dict[str, Any] = None
        is_cache_hit = False
        if provider == "zai":
            try:
                cache_key = json.dumps(
                    {
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                        "max_tokens": payload.get("max_tokens"),
                        "tools": payload.get("tools"),
                        "tool_choice": payload.get("tool_choice"),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
                cached_data = _ZAI_RESPONSE_CACHE.get(cache_key)
                if cached_data is not None:
                    is_cache_hit = True
            except TypeError:
                cache_key = None
                cached_data = None
        
        # Add tools if enabled - use slim tools in efficient mode
        if use_tools and self.tools_enabled:
            efficient_mode = settings.get("efficient_mode", True)
            if efficient_mode:
                payload["tools"] = get_slim_tools_for_agent(self.name)
            else:
                payload["tools"] = get_tools_for_agent(self.name)
            payload["tool_choice"] = "auto"
        
        logger.info(f"[{self.name}] Making API request (tools={use_tools}, max_tokens={payload['max_tokens']})")
        logger.debug(f"[{self.name}] Request payload: {json.dumps(payload, indent=2)[:20000]}")
        
        # Get last user message for preview
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")[:60]
                break
        
        # Log API request to TUI
        callback = get_api_log_callback()
        import time
        start_time = time.time()
        request_id = f"{self.agent_id}-{int(start_time * 1000)}"
        
        if callback:
            try:
                callback("request", self.name, {
                    "request_id": request_id,
                    "model": self.model,
                    "max_tokens": payload.get("max_tokens"),
                    "tools": bool(payload.get("tools")),
                    "msg_count": len(messages),
                    "preview": last_user_msg,
                    "messages": messages,  # Full messages for expandable view
                    "tool_names": [t.get("function", {}).get("name", "?") for t in payload.get("tools", [])] if payload.get("tools") else [],
                    "temperature": self.temperature,
                    "task": getattr(self, "current_task_description", ""),
                })
            except Exception:
                pass  # Don't let logging errors break API calls
        
        try:
            if is_cache_hit:
                elapsed = time.time() - start_time
                data = cached_data
            else:
                async with session.post(
                    api_base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 minutes for large generations
                ) as response:
                    elapsed = time.time() - start_time
                    response_text = await response.text()
                    
                    logger.info(f"[{self.name}] Response status: {response.status}")
                    logger.debug(f"[{self.name}] Response body: {response_text[:20000]}")
                    
                    if response.status != 200:
                        logger.error(f"[{self.name}] API error {response.status}: {response_text}")
                        # Log error to TUI
                        if callback:
                            try:
                                callback("response", self.name, {"request_id": request_id, "status": response.status, "elapsed": elapsed})
                            except Exception:
                                pass
                        return {}
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"[{self.name}] Failed to parse JSON: {e}")
                        if callback:
                            try:
                                callback("error", self.name, {"request_id": request_id, "error": "JSON parse error", "elapsed": elapsed})
                            except Exception:
                                pass
                        return {}

                    if provider == "zai" and cache_key:
                        if len(_ZAI_RESPONSE_CACHE) >= _ZAI_CACHE_MAX_ENTRIES:
                            _ZAI_RESPONSE_CACHE.clear()
                        _ZAI_RESPONSE_CACHE[cache_key] = data

            # Extract response preview
            response_preview = ""
            if "choices" in data and data["choices"]:
                choice = data["choices"][0]
                if "message" in choice:
                    content = choice["message"].get("content", "")
                    if content:
                        response_preview = content[:60]
                    elif choice["message"].get("tool_calls"):
                        tool_call = choice["message"]["tool_calls"][0]
                        response_preview = f"[tool: {tool_call.get('function', {}).get('name', '?')}]"
            
            if "usage" in data and not is_cache_hit:
                logger.info(f"[{self.name}] Tokens: {data['usage'].get('total_tokens', '?')}")
                # Track token usage with agent name
                tracker = get_token_tracker()
                prompt_tokens = data['usage'].get('prompt_tokens', 0)
                completion_tokens = data['usage'].get('completion_tokens', 0)
                current_task = getattr(self, 'current_task_description', '')
                tracker.add_usage(prompt_tokens, completion_tokens, agent_name=self.name, task=current_task)
                # If a single request's prompt context is very large, nudge
                # the orchestrator to consider a handoff to a fresh worker.
                try:
                    CONTEXT_HANDOFF_THRESHOLD = 80_000
                    if (
                        prompt_tokens >= CONTEXT_HANDOFF_THRESHOLD
                        and self.current_task_id
                        and getattr(self, "_context_handoff_task_id", None) != self.current_task_id
                    ):
                        from core.chatroom import get_chatroom

                        self._context_handoff_task_id = self.current_task_id
                        chatroom = await get_chatroom()
                        await chatroom.add_human_message(
                            content=(
                                f"Context for {self.name}'s current task has grown to about "
                                f"{prompt_tokens} prompt tokens. "
                                "Please hand off this work to a fresh worker with a concise summary "
                                "so future calls stay under ~80k tokens of context."
                            ),
                            username="Auto Orchestrator",
                            user_id="auto_orchestrator",
                        )
                except Exception:
                    pass
            
            # Log successful response to TUI
            if callback:
                try:
                    # Extract full response content
                    full_response = ""
                    tool_calls_data = []
                    if "choices" in data and data["choices"]:
                        choice = data["choices"][0]
                        if "message" in choice:
                            full_response = choice["message"].get("content", "") or ""
                            if choice["message"].get("tool_calls"):
                                tool_calls_data = choice["message"]["tool_calls"]
                    
                    callback("response", self.name, {
                        "request_id": request_id,
                        "status": 200,
                        "usage": data.get("usage", {}),
                        "elapsed": elapsed,
                        "preview": response_preview,
                        "full_response": full_response,
                        "tool_calls": tool_calls_data
                    })
                except Exception:
                    pass
            
            return data
                
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            logger.error(f"[{self.name}] API timeout after 120 seconds")
            if callback:
                try:
                    callback("error", self.name, {"request_id": request_id, "error": "Timeout", "elapsed": elapsed})
                except Exception:
                    pass
            return {}
        except aiohttp.ClientError as e:
            elapsed = time.time() - start_time
            logger.error(f"[{self.name}] HTTP client error: {e}")
            if callback:
                try:
                    callback("error", self.name, {"request_id": request_id, "error": str(e)[:40], "elapsed": elapsed})
                except Exception:
                    pass
            return {}
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[{self.name}] Unexpected API error: {type(e).__name__}: {e}")
            if callback:
                try:
                    callback("error", self.name, {"request_id": request_id, "error": f"{type(e).__name__}: {str(e)[:30]}", "elapsed": elapsed})
                except Exception:
                    pass
            return {}
    
    async def _handle_tool_calls(
        self, 
        messages: List[Dict[str, str]], 
        tool_calls: List[Dict],
        status_callback: Optional[Callable] = None,
        depth: int = 0,
        _failure_counts: Optional[Dict[str, int]] = None,
        _call_history: Optional[List[str]] = None,
    ) -> str:
        """
        Execute tool calls and get final response.
        
        Args:
            messages: Current message context
            tool_calls: List of tool calls from API
            status_callback: Optional callback for status updates
            depth: Current recursion depth
            
        Returns:
            Final text response after tool execution
        """
        # Allow more tool calls - agents need room to work!
        # Get from settings or use generous default
        from core.settings_manager import get_settings
        settings = get_settings()
        MAX_TOOL_DEPTH = settings.get("max_tool_depth", 50)

        if _failure_counts is None:
            _failure_counts = {}
        
        if _call_history is None:
            _call_history = []
        
        if depth >= MAX_TOOL_DEPTH:
            logger.warning(f"[{self.name}] Max tool call depth ({MAX_TOOL_DEPTH}) reached, stopping")
            return f"[Completed {depth} tool operations. Reached limit. I will pause here. If the task is not finished, please say 'continue' to let me resume.]"
        
        # LOOP DETECTION: Check for repeated identical tool calls
        for tool_call in tool_calls:
            call_sig = f"{tool_call.get('function', {}).get('name', '')}:{tool_call.get('function', {}).get('arguments', '')}"
            
            # Count how many times this exact call has been made
            repeat_count = _call_history.count(call_sig)
            if repeat_count >= 2:
                tool_name = tool_call.get('function', {}).get('name', '')
                logger.warning(f"[{self.name}] LOOP DETECTED: {tool_name} called {repeat_count + 1} times with same args")
                return (f"[STOPPED: You called {tool_name} {repeat_count + 1} times with the same arguments. "
                       f"This is a loop. If you need data from a file, you already have it in context. "
                       f"Execute assign_task() or complete_my_task() instead of reading again.]")
            
            _call_history.append(call_sig)
        
        logger.info(f"[{self.name}] Executing {len(tool_calls)} tool call(s) (depth={depth})")
        
        # Add assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls
        })
        
        # Execute each tool and collect results
        fatal_error_key = None
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name", "")
            tool_args_str = tool_call.get("function", {}).get("arguments", "{}")
            tool_id = tool_call.get("id", "")
            
            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                tool_args = {}
            
            # Broadcast tool action status
            tool_display = self._get_tool_display_name(tool_name, tool_args)
            if status_callback:
                await status_callback(f"🔧 {self.name}: {tool_display}")
            
            logger.info(f"[{self.name}] Calling tool: {tool_name}({tool_args})")
            
            # Pass status callback to tool executor for streaming command output
            self._tool_executor.set_status_callback(status_callback)
            
            # Execute tool
            result = await self._tool_executor.execute_tool(tool_name, tool_args)
            
            # Clear callback after execution
            self._tool_executor.set_status_callback(None)
            
            logger.info(f"[{self.name}] Tool result: {str(result)[:500]}")

            if isinstance(result, dict) and not result.get("success"):
                error_msg = (result.get("error") or "").strip()
                if error_msg:
                    key = f"{tool_name}:{error_msg}"
                    count = _failure_counts.get(key, 0) + 1
                    _failure_counts[key] = count
                    if count >= 3 and fatal_error_key is None:
                        fatal_error_key = key
            
            # Broadcast result summary for write operations
            if status_callback and tool_name in ["write_file", "append_file", "edit_file"]:
                if isinstance(result, dict) and result.get("success"):
                    # Prefer a human-readable result/message (often includes bytes/lines)
                    result_msg = (
                        result.get("result")
                        or result.get("message")
                        or "Done"
                    )[:80]
                    await status_callback(f" {self.name}: {result_msg}")
                elif isinstance(result, dict) and not result.get("success"):
                    error_msg = result.get("error", "Failed")[:80]
                    await status_callback(f" {self.name}: {error_msg}")
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": json.dumps(result)
            })

        if fatal_error_key:
            try:
                tool_name, error_msg = fatal_error_key.split(":", 1)
            except ValueError:
                tool_name = fatal_error_key
                error_msg = ""
            summary = (
                f"[Tool '{tool_name}' failed repeatedly with the same error. "
                f"Error: {error_msg}. "
                "I will stop calling tools for this task. Please adjust the inputs or fix the configuration and try again.]"
            )
            return summary

        # Get final response after tool execution
        final_data = await self._call_api(messages, use_tools=True)
        
        if not final_data:
            return "[Tool execution completed but couldn't generate response]"
        
        # Broadcast token usage for tool follow-up calls
        if status_callback and "usage" in final_data:
            usage = final_data["usage"]
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            await status_callback(f"📊 {self.name}: {prompt_tokens:,} in / {completion_tokens:,} out = {total_tokens:,} tokens")
        
        choice = final_data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        # Check for more tool calls (recursive with depth limit)
        if message.get("tool_calls"):
            return await self._handle_tool_calls(messages, message["tool_calls"], status_callback, depth + 1, _failure_counts, _call_history)
        
        return message.get("content", "")
    
    def _get_tool_display_name(self, tool_name: str, tool_args: Dict) -> str:
        """Get a human-readable description of a tool call."""
        if tool_name == "write_file":
            path = tool_args.get("path", "file")
            content = tool_args.get("content", "")
            lines = len(content.split('\n')) if content else 0
            return f"Writing {path} ({lines} lines)"
        elif tool_name == "append_file":
            path = tool_args.get("path", "file")
            content = tool_args.get("content", "")
            lines = len(content.split('\n')) if content else 0
            return f"Appending to {path} (+{lines} lines)"
        elif tool_name == "edit_file":
            path = tool_args.get("path", "file")
            return f"Editing {path}"
        elif tool_name == "replace_in_file":
            path = tool_args.get("path", "file")
            return f"Replacing text in {path}"
        elif tool_name == "read_file":
            path = tool_args.get("path", "file")
            return f"Reading {path}"
        elif tool_name == "delete_file":
            path = tool_args.get("path", "file")
            return f"Deleting {path}"
        elif tool_name == "move_file":
            src = tool_args.get("source", "file")
            dst = tool_args.get("destination", "file")
            return f"Moving {src} → {dst}"
        elif tool_name == "create_folder":
            path = tool_args.get("path", "folder")
            return f"Creating folder {path}"
        elif tool_name == "list_files":
            path = tool_args.get("path", ".")
            return f"Listing {path}"
        elif tool_name == "search_code":
            pattern = tool_args.get("pattern", "")
            return f"Searching: {pattern}"
        elif tool_name == "run_command":
            cmd = tool_args.get("command", "")
            return f"Running: {cmd}"
        elif tool_name == "spawn_worker":
            role = tool_args.get("role", "agent")
            return f"Spawning {role}"
        elif tool_name == "assign_task":
            agent = tool_args.get("agent_name", "agent")
            task = tool_args.get("task_description", "")
            return f"Task → {agent}: {task}"
        elif tool_name == "get_swarm_state":
            return "Checking swarm status"
        elif tool_name == "get_project_structure":
            return "Getting project structure"
        elif tool_name == "claim_file":
            path = tool_args.get("path", "file")
            return f"Claiming {path}"
        elif tool_name == "release_file":
            path = tool_args.get("path", "file")
            return f"Releasing {path}"
        else:
            return f"{tool_name}"
    
    async def respond(
        self, 
        global_history: List[Message],
        status_callback: Optional[Callable] = None
    ) -> Optional[Message]:
        """
        Generate a response to the conversation.
        
        This is the main entry point for getting an agent's response.
        Supports tool calling for file operations.
        
        Args:
            global_history: The complete chat history
            status_callback: Optional async callback for status updates
            
        Returns:
            A new Message from this agent, or None if not responding
        """
        # Guard against concurrent API calls from the same agent
        if getattr(self, '_responding', False):
            logger.debug(f"Agent {self.name} already responding, skipping duplicate call")
            return None
        self._responding = True
        
        try:
            return await self._do_respond(global_history, status_callback)
        finally:
            self._responding = False
    
    async def _do_respond(
        self, 
        global_history: List[Message],
        status_callback: Optional[Callable] = None
    ) -> Optional[Message]:
        """Internal respond implementation.

        NOTE: Orchestrators (Chatroom, CLI) are responsible for calling
        should_respond() before scheduling this agent. We deliberately do
        NOT call should_respond() again here to avoid double-trigger bugs
        where the same HUMAN message is seen twice in one round.
        """

        # Build context
        context = await self._build_context(global_history)
        
        # Call API with tools enabled
        data = await self._call_api(context, use_tools=self.tools_enabled)
        
        if not data:
            return None
        
        # Broadcast token usage if status_callback is available
        if status_callback and "usage" in data:
            usage = data["usage"]
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            await status_callback(f"📊 {self.name}: {prompt_tokens:,} in / {completion_tokens:,} out = {total_tokens:,} tokens")
        
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        # Check for tool calls
        if message.get("tool_calls"):
            response_text = await self._handle_tool_calls(context.copy(), message["tool_calls"], status_callback)
        else:
            response_text = message.get("content", "")
        
        if not response_text:
            return None
        
        # Clean up response
        response_text = self._clean_response(response_text)
        
        # Create message
        msg = Message(
            content=response_text,
            sender_name=self.name,
            sender_id=self.agent_id,
            role=MessageRole.ASSISTANT,
            metadata={"model": self.model}
        )
        
        # Track last human message we responded to (for Architect)
        if "Architect" in self.__class__.__name__:
            for m in reversed(self._short_term_memory):
                if m.role == MessageRole.HUMAN:
                    self._last_responded_to_human_id = m.id
                    break
        
        # Update short-term memory
        self.update_short_term_memory(msg)
        
        # Process for long-term memory
        memory_store = await get_memory_store()
        await self._memory_manager.process_new_message(msg, memory_store)
        
        # Check for task completion triggers (multiple patterns for robustness)
        task_complete_triggers = [
            "Task Complete",
            "task complete",
            "Task completed",
            "task completed",
            "TASK COMPLETE",
            "Acknowledged. Task done",
            "I have completed",
            "Successfully completed",
            "Work complete",
            "Implementation complete",
            "Done with task",
        ]
        
        is_task_complete = self.current_task_id and any(
            trigger in response_text for trigger in task_complete_triggers
        )
        
        if is_task_complete:
            task_manager = get_task_manager()
            task_manager.complete_task(self.current_task_id, result=response_text[:500])
            completed_task_id = self.current_task_id
            self.status = AgentStatus.IDLE
            self.current_task_id = None
            self.current_task_description = ""
            logger.info(f"Agent {self.name} completed task {completed_task_id} and is now IDLE")

            # Check if this was the last open task and trigger auto-resume
            # Note: chatroom.run_conversation_round also checks this at the end of each round
            # This is a redundant check for robustness
            try:
                all_tasks = task_manager.get_all_tasks()
                open_tasks = [t for t in all_tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
                completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
                
                if not open_tasks and completed_tasks:
                    from core.chatroom import get_chatroom
                    chatroom = await get_chatroom()
                    # Use centralized method with cooldown to prevent spam
                    await chatroom._send_auto_orchestrator_message(len(completed_tasks))
            except Exception as e:
                logger.warning(f"[{self.name}] Failed to trigger auto-orchestration: {e}")
        
        return msg
    
    def _clean_response(self, response: str) -> str:
        """
        Clean up the response text.
        
        Removes artifacts like self-prefixes that the model might generate.
        
        Args:
            response: Raw response from API
            
        Returns:
            Cleaned response text
        """
        # Remove common prefixes the model might add
        prefixes_to_remove = [
            f"[{self.name}]: ",
            f"{self.name}: ",
            f"[{self.name}]:",
            f"{self.name}:",
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):]
        
        return response.strip()
    
    async def process_incoming_message(self, message: Message):
        """
        Process a message from another participant.
        
        Updates short-term memory and triggers long-term memory processing.
        
        Args:
            message: The incoming message
        """
        self.update_short_term_memory(message)
        
        # Process for long-term memory
        memory_store = await get_memory_store()
        await self._memory_manager.process_new_message(message, memory_store)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.
        
        Returns:
            Dictionary with agent details
        """
        return {
            "name": self.name,
            "agent_id": self.agent_id,
            "model": self.model,
            "persona": self.persona_description,
            "speak_probability": self.speak_probability,
            "tools_enabled": self.tools_enabled,
            "short_term_memory_size": len(self._short_term_memory),
            "status": self.status.value,
            "current_task_id": self.current_task_id
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' model='{self.model}'>"
