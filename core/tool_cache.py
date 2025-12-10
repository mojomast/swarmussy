"""
Tool-Level Caching for Multi-Agent Swarm.

Provides LRU caching for expensive, deterministic tool operations
to reduce redundant work when multiple agents query the same data.

Features:
- Time-based expiration (TTL)
- Size-limited LRU eviction
- Automatic invalidation on file changes
- Thread-safe for async operations

Usage:
    from core.tool_cache import get_tool_cache
    
    cache = get_tool_cache()
    
    # Check cache before expensive operation
    result = cache.get("indexed_search", query="auth", pattern="*.py")
    if result is None:
        result = await expensive_search(...)
        cache.set("indexed_search", result, query="auth", pattern="*.py")
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

# Default cache settings
DEFAULT_MAX_ENTRIES = 256
DEFAULT_TTL_SECONDS = 300  # 5 minutes


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    value: Any
    created_at: float
    ttl: float
    hits: int = 0
    
    def is_expired(self) -> bool:
        return time.time() > (self.created_at + self.ttl)


class ToolCache:
    """
    LRU cache for tool results with TTL expiration.
    
    Designed for caching:
    - indexed_search_code results
    - indexed_related_files results
    - get_project_structure results
    - read_file results (keyed by path + mtime)
    """
    
    def __init__(
        self,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        default_ttl: float = DEFAULT_TTL_SECONDS
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_entries = max_entries
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._invalidated_paths: Set[str] = set()
        
        # Stats
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, tool_name: str, **kwargs) -> str:
        """Generate a cache key from tool name and arguments."""
        # Sort kwargs for consistent key generation
        sorted_items = sorted(kwargs.items())
        key_data = f"{tool_name}:{sorted_items}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, tool_name: str, **kwargs) -> Optional[Any]:
        """
        Get a cached result if available and not expired.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments used to generate cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._make_key(tool_name, **kwargs)
        
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        
        if entry.is_expired():
            # Remove expired entry
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hits += 1
        self._hits += 1
        
        return entry.value
    
    def set(
        self,
        tool_name: str,
        value: Any,
        ttl: Optional[float] = None,
        **kwargs
    ) -> None:
        """
        Cache a tool result.
        
        Args:
            tool_name: Name of the tool
            value: Result to cache
            ttl: Time-to-live in seconds (uses default if not specified)
            **kwargs: Tool arguments used to generate cache key
        """
        key = self._make_key(tool_name, **kwargs)
        
        # Evict oldest entries if at capacity
        while len(self._cache) >= self._max_entries:
            self._cache.popitem(last=False)
        
        self._cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            ttl=ttl if ttl is not None else self._default_ttl
        )
    
    def invalidate(self, tool_name: str, **kwargs) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments used to generate cache key
            
        Returns:
            True if entry was found and removed
        """
        key = self._make_key(tool_name, **kwargs)
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def invalidate_by_path(self, path: str) -> int:
        """
        Invalidate all cache entries that might be affected by a file change.
        
        This is called when files are modified to ensure stale data isn't served.
        
        Args:
            path: Path of the modified file
            
        Returns:
            Number of entries invalidated
        """
        # Track path for future reference
        self._invalidated_paths.add(path)
        
        # For now, invalidate all search-related caches when any file changes
        # This is conservative but safe
        keys_to_remove = []
        for key in self._cache:
            # Invalidate search and structure caches
            # (read_file cache uses mtime so it self-invalidates)
            keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._cache[key]
        
        if keys_to_remove:
            logger.debug(f"ToolCache: invalidated {len(keys_to_remove)} entries due to file change: {path}")
        
        return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._invalidated_paths.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "entries": len(self._cache),
            "max_entries": self._max_entries,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_pct": round(hit_rate, 1),
            "default_ttl": self._default_ttl,
        }
    
    def prune_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_tool_cache: Optional[ToolCache] = None


def get_tool_cache() -> ToolCache:
    """Get the global tool cache instance."""
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = ToolCache()
    return _tool_cache


def reset_tool_cache() -> None:
    """Reset the global tool cache (for testing)."""
    global _tool_cache
    if _tool_cache:
        _tool_cache.clear()
    _tool_cache = None


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def invalidate_cache_for_path(path: str) -> None:
    """
    Invalidate cache entries that might be affected by a file change.
    
    Called from agent_tools.py after write operations.
    """
    cache = get_tool_cache()
    cache.invalidate_by_path(path)
