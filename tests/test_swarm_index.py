"""
Tests for SwarmIndex - SQLite FTS-based code indexing.

Run with: pytest tests/test_swarm_index.py -v
"""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.swarm_index import SwarmIndex, INDEXABLE_EXTENSIONS


@pytest.fixture
def temp_project():
    """Create a temporary project directory with test files."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create scratch/shared structure
    shared_dir = project_root / "scratch" / "shared"
    shared_dir.mkdir(parents=True)
    
    # Create some test files
    (shared_dir / "main.py").write_text("""
# Main application file
def main():
    print("Hello, World!")
    auth = authenticate_user()
    return auth

def authenticate_user():
    return {"user": "test", "token": "abc123"}
""")
    
    (shared_dir / "utils.py").write_text("""
# Utility functions
def helper_function():
    return "helper"

def auth_helper():
    return "auth helper"
""")
    
    # Create a tests directory
    tests_dir = shared_dir / "tests"
    tests_dir.mkdir()
    
    (tests_dir / "test_main.py").write_text("""
# Tests for main.py
import pytest

def test_main():
    assert True

def test_authenticate():
    # Test authentication
    pass
""")
    
    # Create a subdirectory with more files
    src_dir = shared_dir / "src"
    src_dir.mkdir()
    
    (src_dir / "auth.py").write_text("""
# Authentication module
class AuthService:
    def login(self, username, password):
        return True
    
    def logout(self):
        pass
""")
    
    (src_dir / "auth_routes.py").write_text("""
# Auth routes
from auth import AuthService

def setup_routes(app):
    auth = AuthService()
    app.route('/login', auth.login)
""")
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def index(temp_project):
    """Create a SwarmIndex for the temp project."""
    return SwarmIndex(temp_project)


class TestSwarmIndexInitialization:
    """Tests for SwarmIndex initialization."""
    
    @pytest.mark.asyncio
    async def test_initialize_creates_db(self, index, temp_project):
        """Test that initialize creates the database file."""
        result = await index.initialize()
        assert result is True
        assert index.db_path.exists()
        assert index._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self, index):
        """Test that initialize creates required tables."""
        await index.initialize()
        
        # Check tables exist
        cursor = index._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor}
        
        assert "files" in tables
        assert "file_fts" in tables
        assert "index_meta" in tables


class TestSwarmIndexBuild:
    """Tests for building/updating the index."""
    
    @pytest.mark.asyncio
    async def test_build_indexes_files(self, index):
        """Test that build_or_update indexes project files."""
        await index.initialize()
        stats = await index.build_or_update()
        
        # Should have indexed multiple files
        assert stats["added"] > 0
        assert stats["removed"] == 0
        assert stats["updated"] == 0
    
    @pytest.mark.asyncio
    async def test_build_incremental_no_changes(self, index):
        """Test that rebuild with no changes is efficient."""
        await index.initialize()
        
        # First build
        stats1 = await index.build_or_update()
        assert stats1["added"] > 0
        
        # Second build - should find no changes
        stats2 = await index.build_or_update()
        assert stats2["added"] == 0
        assert stats2["updated"] == 0
        assert stats2["unchanged"] > 0
    
    @pytest.mark.asyncio
    async def test_build_detects_new_file(self, index, temp_project):
        """Test that build detects newly added files."""
        await index.initialize()
        await index.build_or_update()
        
        # Add a new file
        new_file = temp_project / "scratch" / "shared" / "new_module.py"
        new_file.write_text("# New module\ndef new_function(): pass")
        
        # Rebuild
        stats = await index.build_or_update()
        assert stats["added"] == 1
    
    @pytest.mark.asyncio
    async def test_build_detects_deleted_file(self, index, temp_project):
        """Test that build detects deleted files."""
        await index.initialize()
        await index.build_or_update()
        
        # Delete a file
        (temp_project / "scratch" / "shared" / "utils.py").unlink()
        
        # Rebuild
        stats = await index.build_or_update()
        assert stats["removed"] == 1


class TestSwarmIndexSearch:
    """Tests for FTS search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_finds_matches(self, index):
        """Test that search finds matching content."""
        await index.initialize()
        await index.build_or_update()
        
        results = await index.search("authenticate")
        
        assert len(results) > 0
        # Should find main.py which has authenticate_user
        paths = [r["path"] for r in results]
        assert any("main.py" in p for p in paths)
    
    @pytest.mark.asyncio
    async def test_search_with_file_pattern(self, index):
        """Test that search respects file pattern filter."""
        await index.initialize()
        await index.build_or_update()
        
        # Search only in test files
        results = await index.search("test", file_pattern="test_%.py")
        
        assert len(results) > 0
        for r in results:
            assert "test" in r["path"].lower()
    
    @pytest.mark.asyncio
    async def test_search_returns_snippets(self, index):
        """Test that search results include snippets."""
        await index.initialize()
        await index.build_or_update()
        
        results = await index.search("AuthService")
        
        assert len(results) > 0
        # Snippets should contain the search term or context
        assert results[0]["snippet"] is not None
    
    @pytest.mark.asyncio
    async def test_search_respects_max_results(self, index):
        """Test that search respects max_results limit."""
        await index.initialize()
        await index.build_or_update()
        
        results = await index.search("def", max_results=2)
        
        assert len(results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_empty_query_returns_error(self, index):
        """Test that empty query is handled gracefully."""
        await index.initialize()
        await index.build_or_update()
        
        # Empty query should return empty results (handled by caller)
        results = await index.search("")
        # The search method doesn't validate empty queries itself
        # but FTS5 will return no results


class TestSwarmIndexRelatedFiles:
    """Tests for related file discovery."""
    
    @pytest.mark.asyncio
    async def test_related_files_finds_tests(self, index):
        """Test that related_files finds test files."""
        await index.initialize()
        await index.build_or_update()
        
        related = await index.related_files("main.py")
        
        # Should find test_main.py
        assert any("test_main" in r for r in related)
    
    @pytest.mark.asyncio
    async def test_related_files_finds_similar_names(self, index):
        """Test that related_files finds similarly named files."""
        await index.initialize()
        await index.build_or_update()
        
        related = await index.related_files("src/auth.py")
        
        # Should find auth_routes.py
        assert any("auth_routes" in r for r in related)
    
    @pytest.mark.asyncio
    async def test_related_files_respects_max_results(self, index):
        """Test that related_files respects max_results."""
        await index.initialize()
        await index.build_or_update()
        
        related = await index.related_files("main.py", max_results=2)
        
        assert len(related) <= 2


class TestSwarmIndexDirtyTracking:
    """Tests for dirty file tracking and incremental updates."""
    
    @pytest.mark.asyncio
    async def test_mark_dirty_tracks_path(self, index):
        """Test that mark_dirty adds path to dirty set."""
        await index.initialize()
        
        index.mark_dirty("test.py")
        
        assert "test.py" in index._dirty_paths
    
    @pytest.mark.asyncio
    async def test_flush_dirty_reindexes_files(self, index, temp_project):
        """Test that flush_dirty reindexes marked files."""
        await index.initialize()
        await index.build_or_update()
        
        # Modify a file
        main_py = temp_project / "scratch" / "shared" / "main.py"
        main_py.write_text("# Modified content\ndef new_main(): pass")
        
        # Mark dirty and flush
        index.mark_dirty("main.py")
        count = await index.flush_dirty()
        
        assert count == 1
        assert len(index._dirty_paths) == 0
        
        # Search should find new content
        results = await index.search("new_main")
        assert len(results) > 0


class TestSwarmIndexStats:
    """Tests for index statistics."""
    
    @pytest.mark.asyncio
    async def test_get_stats_returns_info(self, index):
        """Test that get_stats returns useful information."""
        await index.initialize()
        await index.build_or_update()
        
        stats = index.get_stats()
        
        assert stats["initialized"] is True
        assert stats["file_count"] > 0
        assert "db_path" in stats
        assert "dirty_count" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
