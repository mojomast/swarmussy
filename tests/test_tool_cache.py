"""
Tests for ToolCache - LRU caching for tool results.

Run with: pytest tests/test_tool_cache.py -v
"""

import time
import pytest

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tool_cache import ToolCache, get_tool_cache, reset_tool_cache


@pytest.fixture
def cache():
    """Create a fresh ToolCache for testing."""
    return ToolCache(max_entries=10, default_ttl=60)


@pytest.fixture(autouse=True)
def reset_global_cache():
    """Reset the global cache before each test."""
    reset_tool_cache()
    yield
    reset_tool_cache()


class TestToolCacheBasics:
    """Basic cache operations."""
    
    def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        cache.set("test_tool", {"result": "data"}, query="test")
        
        result = cache.get("test_tool", query="test")
        
        assert result == {"result": "data"}
    
    def test_get_missing_returns_none(self, cache):
        """Test that getting a missing key returns None."""
        result = cache.get("nonexistent", query="test")
        
        assert result is None
    
    def test_different_args_different_keys(self, cache):
        """Test that different arguments create different cache keys."""
        cache.set("search", "result1", query="auth")
        cache.set("search", "result2", query="user")
        
        assert cache.get("search", query="auth") == "result1"
        assert cache.get("search", query="user") == "result2"
    
    def test_same_args_same_key(self, cache):
        """Test that same arguments produce same cache key."""
        cache.set("search", "result1", query="auth", pattern="*.py")
        
        # Same args in different order should still match
        result = cache.get("search", pattern="*.py", query="auth")
        
        assert result == "result1"


class TestToolCacheTTL:
    """TTL expiration tests."""
    
    def test_expired_entry_returns_none(self):
        """Test that expired entries return None."""
        cache = ToolCache(default_ttl=0.1)  # 100ms TTL
        
        cache.set("test", "value", query="test")
        
        # Wait for expiration
        time.sleep(0.15)
        
        result = cache.get("test", query="test")
        assert result is None
    
    def test_custom_ttl_per_entry(self, cache):
        """Test that custom TTL can be set per entry."""
        cache.set("test", "value", ttl=0.1, query="test")
        
        # Should still be valid
        assert cache.get("test", query="test") == "value"
        
        # Wait for expiration
        time.sleep(0.15)
        
        assert cache.get("test", query="test") is None
    
    def test_prune_expired_removes_old_entries(self):
        """Test that prune_expired removes expired entries."""
        cache = ToolCache(default_ttl=0.1)
        
        cache.set("test1", "value1", query="a")
        cache.set("test2", "value2", query="b")
        
        time.sleep(0.15)
        
        removed = cache.prune_expired()
        
        assert removed == 2
        assert len(cache._cache) == 0


class TestToolCacheLRU:
    """LRU eviction tests."""
    
    def test_evicts_oldest_when_full(self):
        """Test that oldest entries are evicted when cache is full."""
        cache = ToolCache(max_entries=3)
        
        cache.set("tool", "value1", query="a")
        cache.set("tool", "value2", query="b")
        cache.set("tool", "value3", query="c")
        
        # This should evict "a"
        cache.set("tool", "value4", query="d")
        
        assert cache.get("tool", query="a") is None
        assert cache.get("tool", query="b") == "value2"
        assert cache.get("tool", query="c") == "value3"
        assert cache.get("tool", query="d") == "value4"
    
    def test_access_updates_recency(self):
        """Test that accessing an entry updates its recency."""
        cache = ToolCache(max_entries=3)
        
        cache.set("tool", "value1", query="a")
        cache.set("tool", "value2", query="b")
        cache.set("tool", "value3", query="c")
        
        # Access "a" to make it recent
        cache.get("tool", query="a")
        
        # This should evict "b" (now oldest)
        cache.set("tool", "value4", query="d")
        
        assert cache.get("tool", query="a") == "value1"
        assert cache.get("tool", query="b") is None


class TestToolCacheInvalidation:
    """Cache invalidation tests."""
    
    def test_invalidate_specific_entry(self, cache):
        """Test invalidating a specific cache entry."""
        cache.set("tool", "value", query="test")
        
        removed = cache.invalidate("tool", query="test")
        
        assert removed is True
        assert cache.get("tool", query="test") is None
    
    def test_invalidate_nonexistent_returns_false(self, cache):
        """Test that invalidating nonexistent entry returns False."""
        removed = cache.invalidate("tool", query="nonexistent")
        
        assert removed is False
    
    def test_invalidate_by_path_clears_cache(self, cache):
        """Test that invalidate_by_path clears related entries."""
        cache.set("search", "result1", query="auth")
        cache.set("search", "result2", query="user")
        
        count = cache.invalidate_by_path("/some/path.py")
        
        # Currently invalidates all entries (conservative approach)
        assert count == 2
        assert cache.get("search", query="auth") is None
    
    def test_clear_removes_all_entries(self, cache):
        """Test that clear removes all entries."""
        cache.set("tool1", "value1", query="a")
        cache.set("tool2", "value2", query="b")
        
        cache.clear()
        
        assert len(cache._cache) == 0


class TestToolCacheStats:
    """Cache statistics tests."""
    
    def test_stats_tracks_hits_and_misses(self, cache):
        """Test that stats track hits and misses."""
        cache.set("tool", "value", query="test")
        
        # One hit
        cache.get("tool", query="test")
        
        # One miss
        cache.get("tool", query="nonexistent")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate_pct"] == 50.0
    
    def test_stats_shows_entry_count(self, cache):
        """Test that stats show entry count."""
        cache.set("tool1", "value1", query="a")
        cache.set("tool2", "value2", query="b")
        
        stats = cache.get_stats()
        
        assert stats["entries"] == 2
        assert stats["max_entries"] == 10


class TestGlobalToolCache:
    """Tests for global cache singleton."""
    
    def test_get_tool_cache_returns_singleton(self):
        """Test that get_tool_cache returns the same instance."""
        cache1 = get_tool_cache()
        cache2 = get_tool_cache()
        
        assert cache1 is cache2
    
    def test_reset_tool_cache_clears_singleton(self):
        """Test that reset_tool_cache clears the singleton."""
        cache1 = get_tool_cache()
        cache1.set("tool", "value", query="test")
        
        reset_tool_cache()
        
        cache2 = get_tool_cache()
        assert cache2.get("tool", query="test") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
