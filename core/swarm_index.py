"""
SwarmIndex - Lightweight SQLite-backed code indexing for multi-agent swarm.

Provides fast FTS-based code search without external dependencies.
Each project gets its own index at <project_root>/scratch/shared/.swarm_index.db

Usage:
    index = SwarmIndex(project_root)
    await index.initialize()
    await index.build_or_update()
    results = await index.search("auth", file_pattern="*.py")
"""

import asyncio
import hashlib
import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)

# File extensions to index (code files only)
INDEXABLE_EXTENSIONS = {
    # Python
    '.py', '.pyi', '.pyx',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    # Web
    '.html', '.css', '.scss', '.sass', '.less',
    # Data/Config
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    # Systems
    '.rs', '.go', '.c', '.cpp', '.h', '.hpp', '.cc',
    # JVM
    '.java', '.kt', '.scala', '.groovy',
    # Other
    '.rb', '.php', '.swift', '.cs', '.gd', '.lua',
    # Shell
    '.sh', '.bash', '.zsh', '.fish', '.ps1',
    # Docs (light indexing)
    '.md', '.rst', '.txt',
}

# Directories to skip
SKIP_DIRS = {
    '__pycache__', '.git', '.svn', '.hg',
    'node_modules', '.venv', 'venv', 'env',
    '.mypy_cache', '.pytest_cache', '.ruff_cache',
    'dist', 'build', '.next', '.nuxt',
    'coverage', '.coverage', 'htmlcov',
    '.idea', '.vscode', '.devussy_state',
}

# Files to skip
SKIP_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitignore',
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
}

# Maximum file size to index (500KB)
MAX_FILE_SIZE = 500 * 1024


class SwarmIndex:
    """
    SQLite FTS5-backed code index for a project workspace.
    
    Features:
    - Incremental updates (only reindex changed files)
    - Full-text search with snippet extraction
    - Related file discovery (same dir, tests, similar names)
    - Thread-safe for async operations
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize SwarmIndex for a project.
        
        Args:
            project_root: Root path of the project (contains scratch/shared/)
        """
        self.project_root = Path(project_root).resolve()
        self.workspace_dir = self.project_root / "scratch" / "shared"
        self.db_path = self.workspace_dir / ".swarm_index.db"
        self._conn: Optional[sqlite3.Connection] = None
        self._dirty_paths: Set[str] = set()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._last_build_time = 0.0
        
    async def initialize(self) -> bool:
        """
        Create database and tables if needed.
        
        Returns:
            True if initialization succeeded
        """
        async with self._lock:
            try:
                # Ensure workspace exists
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
                
                # Connect to SQLite (creates file if not exists)
                self._conn = sqlite3.connect(
                    str(self.db_path),
                    check_same_thread=False,
                    timeout=30.0
                )
                self._conn.row_factory = sqlite3.Row
                
                # Enable WAL mode for better concurrency
                self._conn.execute("PRAGMA journal_mode=WAL")
                self._conn.execute("PRAGMA synchronous=NORMAL")
                
                # Create tables
                self._conn.executescript("""
                    -- Tracks indexed files with metadata
                    CREATE TABLE IF NOT EXISTS files (
                        path TEXT PRIMARY KEY,
                        mtime REAL NOT NULL,
                        size INTEGER NOT NULL,
                        hash TEXT NOT NULL,
                        indexed_at REAL NOT NULL
                    );
                    
                    -- Full-text search index
                    CREATE VIRTUAL TABLE IF NOT EXISTS file_fts USING fts5(
                        path,
                        content,
                        tokenize='porter unicode61'
                    );
                    
                    -- Index metadata
                    CREATE TABLE IF NOT EXISTS index_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    );
                """)
                self._conn.commit()
                
                self._initialized = True
                logger.info(f"SwarmIndex initialized at {self.db_path}")
                return True
                
            except Exception as e:
                logger.error(f"SwarmIndex initialization failed: {e}")
                return False
    
    async def build_or_update(self, force: bool = False) -> Dict[str, int]:
        """
        Incrementally index project files.
        
        Args:
            force: If True, reindex all files regardless of mtime
            
        Returns:
            Dict with counts: {added, updated, removed, unchanged}
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._lock:
            start_time = time.time()
            stats = {"added": 0, "updated": 0, "removed": 0, "unchanged": 0}
            
            try:
                # Get current files on disk
                disk_files = self._walk_code_files()
                disk_paths = set(disk_files.keys())
                
                # Get indexed files from DB
                cursor = self._conn.execute("SELECT path, mtime, hash FROM files")
                indexed = {row["path"]: (row["mtime"], row["hash"]) for row in cursor}
                indexed_paths = set(indexed.keys())
                
                # Find files to add, update, or remove
                to_add = disk_paths - indexed_paths
                to_remove = indexed_paths - disk_paths
                to_check = disk_paths & indexed_paths
                
                # Remove deleted files
                for path in to_remove:
                    self._remove_file(path)
                    stats["removed"] += 1
                
                # Add new files
                for path in to_add:
                    info = disk_files[path]
                    if self._index_file(path, info):
                        stats["added"] += 1
                
                # Check existing files for updates
                for path in to_check:
                    info = disk_files[path]
                    old_mtime, old_hash = indexed[path]
                    
                    # Quick check: mtime changed?
                    if not force and info["mtime"] == old_mtime:
                        stats["unchanged"] += 1
                        continue
                    
                    # Content check: hash changed?
                    content_hash = self._compute_hash(info["full_path"])
                    if not force and content_hash == old_hash:
                        # Update mtime but content unchanged
                        self._conn.execute(
                            "UPDATE files SET mtime = ? WHERE path = ?",
                            (info["mtime"], path)
                        )
                        stats["unchanged"] += 1
                        continue
                    
                    # Content changed, reindex
                    self._remove_file(path)
                    if self._index_file(path, info, content_hash):
                        stats["updated"] += 1
                
                self._conn.commit()
                self._last_build_time = time.time()
                
                elapsed = time.time() - start_time
                total = stats["added"] + stats["updated"]
                logger.info(
                    f"SwarmIndex: indexed {total} files in {elapsed:.2f}s "
                    f"(+{stats['added']} ~{stats['updated']} -{stats['removed']})"
                )
                
                return stats
                
            except Exception as e:
                logger.error(f"SwarmIndex build failed: {e}")
                self._conn.rollback()
                return stats
    
    def mark_dirty(self, path: str) -> None:
        """
        Mark a file path for reindexing.
        
        Called after write operations to ensure index stays current.
        
        Args:
            path: Relative or absolute path to the modified file
        """
        # Normalize to relative path from workspace
        try:
            if Path(path).is_absolute():
                rel_path = str(Path(path).relative_to(self.workspace_dir))
            else:
                rel_path = path
            self._dirty_paths.add(rel_path)
            logger.debug(f"SwarmIndex: marked dirty: {rel_path}")
        except ValueError:
            # Path not under workspace, ignore
            pass
    
    async def flush_dirty(self) -> int:
        """
        Reindex all dirty files.
        
        Returns:
            Number of files reindexed
        """
        if not self._dirty_paths:
            return 0
        
        async with self._lock:
            count = 0
            paths_to_process = list(self._dirty_paths)
            self._dirty_paths.clear()
            
            for rel_path in paths_to_process:
                full_path = self.workspace_dir / rel_path
                
                if not full_path.exists():
                    # File was deleted
                    self._remove_file(rel_path)
                    count += 1
                    continue
                
                if not full_path.is_file():
                    continue
                
                # Check if indexable
                if full_path.suffix.lower() not in INDEXABLE_EXTENSIONS:
                    continue
                
                # Reindex
                info = {
                    "full_path": full_path,
                    "mtime": full_path.stat().st_mtime,
                    "size": full_path.stat().st_size,
                }
                
                self._remove_file(rel_path)
                if self._index_file(rel_path, info):
                    count += 1
            
            if count > 0:
                self._conn.commit()
                logger.debug(f"SwarmIndex: flushed {count} dirty files")
            
            return count
    
    async def search(
        self,
        query: str,
        file_pattern: Optional[str] = None,
        max_results: int = 20
    ) -> List[Dict]:
        """
        Full-text search over indexed code.
        
        Args:
            query: Search query (supports FTS5 syntax)
            file_pattern: Optional glob pattern to filter files (e.g., "*.py")
            max_results: Maximum number of results to return
            
        Returns:
            List of {path, snippet, rank} dicts
        """
        if not self._initialized:
            await self.initialize()
        
        # Flush any pending dirty files first
        await self.flush_dirty()
        
        async with self._lock:
            try:
                # Escape special FTS5 characters for simple queries
                # but allow explicit FTS syntax if user includes quotes
                if '"' not in query and '*' not in query:
                    # Simple query - escape and wrap terms
                    terms = query.split()
                    safe_query = ' '.join(f'"{t}"' for t in terms if t)
                else:
                    safe_query = query
                
                # Build SQL with optional file pattern filter
                sql = """
                    SELECT 
                        path,
                        snippet(file_fts, 1, '>>>', '<<<', '...', 64) as snippet,
                        rank
                    FROM file_fts
                    WHERE file_fts MATCH ?
                """
                params = [safe_query]
                
                if file_pattern:
                    # Convert glob to SQL LIKE pattern
                    like_pattern = file_pattern.replace('*', '%').replace('?', '_')
                    sql += " AND path LIKE ?"
                    params.append(like_pattern)
                
                sql += " ORDER BY rank LIMIT ?"
                params.append(max_results)
                
                cursor = self._conn.execute(sql, params)
                results = []
                
                for row in cursor:
                    results.append({
                        "path": row["path"],
                        "snippet": row["snippet"],
                        "rank": row["rank"],
                    })
                
                logger.debug(f"SwarmIndex search '{query}': {len(results)} results")
                return results
                
            except sqlite3.OperationalError as e:
                # FTS query syntax error - try simpler search
                logger.warning(f"FTS query failed, falling back: {e}")
                return await self._fallback_search(query, file_pattern, max_results)
    
    async def _fallback_search(
        self,
        query: str,
        file_pattern: Optional[str],
        max_results: int
    ) -> List[Dict]:
        """Simple LIKE-based fallback search when FTS fails."""
        try:
            sql = """
                SELECT path, substr(content, 1, 200) as snippet
                FROM file_fts
                WHERE content LIKE ?
            """
            params = [f"%{query}%"]
            
            if file_pattern:
                like_pattern = file_pattern.replace('*', '%').replace('?', '_')
                sql += " AND path LIKE ?"
                params.append(like_pattern)
            
            sql += " LIMIT ?"
            params.append(max_results)
            
            cursor = self._conn.execute(sql, params)
            return [
                {"path": row["path"], "snippet": row["snippet"], "rank": 0}
                for row in cursor
            ]
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return []
    
    async def related_files(self, path: str, max_results: int = 10) -> List[str]:
        """
        Find files related to the given path.
        
        Heuristics:
        - Files in the same directory
        - Test files (foo.py → test_foo.py, foo.test.py, foo.spec.ts)
        - Similar base names (auth.py → auth_routes.py, auth_service.py)
        - Import/require relationships (future enhancement)
        
        Args:
            path: Path to find related files for
            max_results: Maximum number of related files to return
            
        Returns:
            List of related file paths
        """
        if not self._initialized:
            await self.initialize()
        
        async with self._lock:
            related: List[str] = []
            path_obj = Path(path)
            base_name = path_obj.stem  # filename without extension
            parent_dir = str(path_obj.parent)
            extension = path_obj.suffix
            
            try:
                # 1. Files in same directory
                cursor = self._conn.execute(
                    "SELECT path FROM files WHERE path LIKE ? AND path != ? LIMIT 10",
                    (f"{parent_dir}/%", path)
                )
                same_dir = [row["path"] for row in cursor]
                
                # 2. Test files
                test_patterns = [
                    f"test_{base_name}%",      # test_foo.py
                    f"{base_name}_test%",      # foo_test.py
                    f"{base_name}.test%",      # foo.test.ts
                    f"{base_name}.spec%",      # foo.spec.ts
                    f"%/test_{base_name}%",    # tests/test_foo.py
                    f"%/tests/{base_name}%",   # tests/foo.py
                ]
                
                test_files = []
                for pattern in test_patterns:
                    cursor = self._conn.execute(
                        "SELECT path FROM files WHERE path LIKE ? LIMIT 5",
                        (pattern,)
                    )
                    test_files.extend(row["path"] for row in cursor)
                
                # 3. Similar base names
                cursor = self._conn.execute(
                    "SELECT path FROM files WHERE path LIKE ? AND path != ? LIMIT 10",
                    (f"%{base_name}%{extension}", path)
                )
                similar = [row["path"] for row in cursor]
                
                # Combine and deduplicate, prioritizing test files
                seen = {path}  # exclude the input path
                
                for f in test_files:
                    if f not in seen:
                        related.append(f)
                        seen.add(f)
                
                for f in same_dir:
                    if f not in seen:
                        related.append(f)
                        seen.add(f)
                
                for f in similar:
                    if f not in seen:
                        related.append(f)
                        seen.add(f)
                
                return related[:max_results]
                
            except Exception as e:
                logger.error(f"related_files failed: {e}")
                return []
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        if not self._conn:
            return {"initialized": False}
        
        try:
            cursor = self._conn.execute("SELECT COUNT(*) as count FROM files")
            file_count = cursor.fetchone()["count"]
            
            cursor = self._conn.execute(
                "SELECT SUM(size) as total_size FROM files"
            )
            total_size = cursor.fetchone()["total_size"] or 0
            
            return {
                "initialized": self._initialized,
                "file_count": file_count,
                "total_size_kb": total_size // 1024,
                "db_path": str(self.db_path),
                "dirty_count": len(self._dirty_paths),
                "last_build": self._last_build_time,
            }
        except Exception:
            return {"initialized": self._initialized, "error": "stats unavailable"}
    
    async def close(self):
        """Close the database connection."""
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            self._initialized = False
    
    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _walk_code_files(self) -> Dict[str, Dict]:
        """
        Walk the workspace and find all indexable code files.
        
        Returns:
            Dict mapping relative paths to file info dicts
        """
        files = {}
        
        if not self.workspace_dir.exists():
            return files
        
        for item in self.workspace_dir.rglob("*"):
            # Skip directories
            if not item.is_file():
                continue
            
            # Skip by directory name
            if any(skip in item.parts for skip in SKIP_DIRS):
                continue
            
            # Skip by filename
            if item.name in SKIP_FILES:
                continue
            
            # Skip by extension
            if item.suffix.lower() not in INDEXABLE_EXTENSIONS:
                continue
            
            # Skip large files
            try:
                stat = item.stat()
                if stat.st_size > MAX_FILE_SIZE:
                    continue
                if stat.st_size == 0:
                    continue
            except OSError:
                continue
            
            # Get relative path
            try:
                rel_path = str(item.relative_to(self.workspace_dir))
            except ValueError:
                continue
            
            files[rel_path] = {
                "full_path": item,
                "mtime": stat.st_mtime,
                "size": stat.st_size,
            }
        
        return files
    
    def _compute_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file content."""
        try:
            with open(path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            return ""
    
    def _index_file(
        self,
        rel_path: str,
        info: Dict,
        content_hash: Optional[str] = None
    ) -> bool:
        """
        Index a single file.
        
        Returns:
            True if file was indexed successfully
        """
        try:
            full_path = info["full_path"]
            
            # Read content
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                return False
            
            # Compute hash if not provided
            if content_hash is None:
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            
            # Insert into files table
            self._conn.execute(
                """
                INSERT OR REPLACE INTO files (path, mtime, size, hash, indexed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rel_path, info["mtime"], info["size"], content_hash, time.time())
            )
            
            # Insert into FTS index
            self._conn.execute(
                "INSERT INTO file_fts (path, content) VALUES (?, ?)",
                (rel_path, content)
            )
            
            return True
            
        except Exception as e:
            logger.debug(f"Failed to index {rel_path}: {e}")
            return False
    
    def _remove_file(self, rel_path: str) -> None:
        """Remove a file from the index."""
        try:
            self._conn.execute("DELETE FROM files WHERE path = ?", (rel_path,))
            self._conn.execute("DELETE FROM file_fts WHERE path = ?", (rel_path,))
        except Exception as e:
            logger.debug(f"Failed to remove {rel_path} from index: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETON MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

_index_instance: Optional[SwarmIndex] = None


def get_swarm_index() -> Optional[SwarmIndex]:
    """Get the current SwarmIndex instance."""
    return _index_instance


def set_swarm_index(index: Optional[SwarmIndex]) -> None:
    """Set the global SwarmIndex instance."""
    global _index_instance
    _index_instance = index


async def init_swarm_index(project_root: Path) -> SwarmIndex:
    """
    Initialize and return a SwarmIndex for the given project.
    
    This is the main entry point for creating an index.
    """
    global _index_instance
    
    index = SwarmIndex(project_root)
    if await index.initialize():
        await index.build_or_update()
        _index_instance = index
        return index
    
    raise RuntimeError(f"Failed to initialize SwarmIndex for {project_root}")
