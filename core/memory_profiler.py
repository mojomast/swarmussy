"""
Live Memory Profiler for debugging memory leaks.

Periodically logs memory usage and top object types to help identify leaks.
"""

import gc
import sys
import asyncio
import logging
import tracemalloc
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)

# Global state
_profiler_task: Optional[asyncio.Task] = None
_snapshots: List[Tuple[datetime, int, Dict[str, int]]] = []
_tracemalloc_started = False


def get_memory_mb() -> float:
    """Get current process memory in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback: use gc to estimate
        return sum(sys.getsizeof(obj) for obj in gc.get_objects()) / (1024 * 1024)


def get_top_types(limit: int = 20) -> Dict[str, int]:
    """Get count of objects by type."""
    gc.collect()
    type_counts: Counter = Counter()
    
    for obj in gc.get_objects():
        try:
            type_name = type(obj).__name__
            type_counts[type_name] += 1
        except Exception:
            pass
    
    return dict(type_counts.most_common(limit))


def get_top_types_by_size(limit: int = 20) -> List[Tuple[str, int, int]]:
    """Get types sorted by total memory usage. Returns [(type_name, count, total_bytes), ...]"""
    gc.collect()
    type_stats: Dict[str, Tuple[int, int]] = {}  # type -> (count, total_size)
    
    for obj in gc.get_objects():
        try:
            type_name = type(obj).__name__
            size = sys.getsizeof(obj)
            if type_name in type_stats:
                count, total = type_stats[type_name]
                type_stats[type_name] = (count + 1, total + size)
            else:
                type_stats[type_name] = (1, size)
        except Exception:
            pass
    
    # Sort by total size descending
    sorted_stats = sorted(
        [(name, count, total) for name, (count, total) in type_stats.items()],
        key=lambda x: x[2],
        reverse=True
    )
    return sorted_stats[:limit]


def take_snapshot() -> Tuple[datetime, float, Dict[str, int]]:
    """Take a memory snapshot."""
    now = datetime.now()
    mem_mb = get_memory_mb()
    top_types = get_top_types(30)
    
    snapshot = (now, mem_mb, top_types)
    _snapshots.append(snapshot)
    
    # Keep last 20 snapshots
    if len(_snapshots) > 20:
        _snapshots.pop(0)
    
    return snapshot


def compare_snapshots() -> str:
    """Compare last two snapshots to see what's growing."""
    if len(_snapshots) < 2:
        return "Need at least 2 snapshots to compare"
    
    prev_time, prev_mem, prev_types = _snapshots[-2]
    curr_time, curr_mem, curr_types = _snapshots[-1]
    
    lines = []
    lines.append(f"=== Memory Comparison ===")
    lines.append(f"Time: {prev_time.strftime('%H:%M:%S')} -> {curr_time.strftime('%H:%M:%S')}")
    lines.append(f"Memory: {prev_mem:.1f} MB -> {curr_mem:.1f} MB ({curr_mem - prev_mem:+.1f} MB)")
    lines.append("")
    lines.append("Top growing types:")
    
    # Find types that grew the most
    growth = []
    all_types = set(prev_types.keys()) | set(curr_types.keys())
    for type_name in all_types:
        prev_count = prev_types.get(type_name, 0)
        curr_count = curr_types.get(type_name, 0)
        diff = curr_count - prev_count
        if diff > 0:
            growth.append((type_name, prev_count, curr_count, diff))
    
    # Sort by growth
    growth.sort(key=lambda x: x[3], reverse=True)
    
    for type_name, prev_count, curr_count, diff in growth[:15]:
        lines.append(f"  {type_name}: {prev_count} -> {curr_count} (+{diff})")
    
    return "\n".join(lines)


def start_tracemalloc():
    """Start tracemalloc for detailed memory tracking."""
    global _tracemalloc_started
    if not _tracemalloc_started:
        tracemalloc.start(25)  # 25 frames of traceback
        _tracemalloc_started = True
        logger.info("tracemalloc started")


def get_tracemalloc_top(limit: int = 10) -> str:
    """Get top memory allocations from tracemalloc."""
    if not _tracemalloc_started:
        return "tracemalloc not started"
    
    snapshot = tracemalloc.take_snapshot()
    stats = snapshot.statistics('lineno')
    
    lines = ["=== Top Memory Allocations ==="]
    for stat in stats[:limit]:
        lines.append(f"{stat.size / 1024:.1f} KB: {stat.traceback.format()[0]}")
    
    return "\n".join(lines)


def get_tracemalloc_diff() -> str:
    """Get memory allocation diff since last call."""
    global _last_tracemalloc_snapshot
    
    if not _tracemalloc_started:
        return "tracemalloc not started"
    
    current = tracemalloc.take_snapshot()
    
    if not hasattr(get_tracemalloc_diff, '_last_snapshot'):
        get_tracemalloc_diff._last_snapshot = current
        return "First snapshot taken, call again for diff"
    
    stats = current.compare_to(get_tracemalloc_diff._last_snapshot, 'lineno')
    get_tracemalloc_diff._last_snapshot = current
    
    lines = ["=== Memory Allocation Changes ==="]
    # Show top growers
    growers = [s for s in stats if s.size_diff > 0]
    growers.sort(key=lambda x: x.size_diff, reverse=True)
    
    for stat in growers[:15]:
        lines.append(f"+{stat.size_diff / 1024:.1f} KB ({stat.count_diff:+d} blocks): {stat.traceback.format()[0]}")
    
    return "\n".join(lines)


async def memory_monitor_loop(interval: float = 10.0, log_to_file: bool = True):
    """Background loop that monitors memory usage."""
    log_path = None
    if log_to_file:
        from pathlib import Path
        log_path = Path("logs") / f"memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path.parent.mkdir(exist_ok=True)
    
    logger.info(f"Memory monitor started (interval={interval}s, log={log_path})")
    
    start_tracemalloc()
    
    iteration = 0
    while True:
        try:
            await asyncio.sleep(interval)
            iteration += 1
            
            # Take snapshot
            snapshot = take_snapshot()
            now, mem_mb, top_types = snapshot
            
            # Build report
            lines = []
            lines.append(f"\n{'='*60}")
            lines.append(f"[{now.strftime('%H:%M:%S')}] Memory Report #{iteration}")
            lines.append(f"{'='*60}")
            lines.append(f"Process Memory: {mem_mb:.1f} MB")
            lines.append("")
            
            # Top types by count
            lines.append("Top Object Types (by count):")
            for type_name, count in list(top_types.items())[:10]:
                lines.append(f"  {type_name}: {count:,}")
            
            # Top types by size
            lines.append("")
            lines.append("Top Object Types (by size):")
            for type_name, count, total_bytes in get_top_types_by_size(10):
                lines.append(f"  {type_name}: {count:,} objects, {total_bytes / 1024 / 1024:.2f} MB")
            
            # Comparison if we have previous snapshot
            if len(_snapshots) >= 2:
                lines.append("")
                lines.append(compare_snapshots())
            
            # Tracemalloc diff
            lines.append("")
            lines.append(get_tracemalloc_diff())
            
            report = "\n".join(lines)
            
            # Log to console
            print(report)
            
            # Log to file
            if log_path:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(report + "\n")
            
            # Force garbage collection
            gc.collect()
            
        except asyncio.CancelledError:
            logger.info("Memory monitor stopped")
            break
        except Exception as e:
            logger.error(f"Memory monitor error: {e}")
            await asyncio.sleep(interval)


def start_memory_monitor(interval: float = 10.0):
    """Start the background memory monitor."""
    global _profiler_task
    
    if _profiler_task is not None and not _profiler_task.done():
        logger.warning("Memory monitor already running")
        return
    
    _profiler_task = asyncio.create_task(memory_monitor_loop(interval))
    logger.info("Memory monitor task created")


def stop_memory_monitor():
    """Stop the background memory monitor."""
    global _profiler_task
    
    if _profiler_task is not None:
        _profiler_task.cancel()
        _profiler_task = None
        logger.info("Memory monitor stopped")


def dump_memory_report() -> str:
    """Generate an immediate memory report."""
    gc.collect()
    
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"MEMORY DUMP @ {datetime.now().strftime('%H:%M:%S')}")
    lines.append(f"{'='*60}")
    
    mem_mb = get_memory_mb()
    lines.append(f"Process Memory: {mem_mb:.1f} MB")
    lines.append("")
    
    # Detailed type breakdown
    lines.append("Object Types by Size:")
    for type_name, count, total_bytes in get_top_types_by_size(25):
        mb = total_bytes / 1024 / 1024
        if mb > 0.1:  # Only show types using >0.1 MB
            lines.append(f"  {type_name}: {count:,} objects, {mb:.2f} MB")
    
    lines.append("")
    
    # Check for specific suspicious types
    suspicious = ['dict', 'list', 'str', 'tuple', 'Message', 'ApiLogEntry', 'bytes']
    lines.append("Suspicious types detail:")
    for obj in gc.get_objects():
        try:
            type_name = type(obj).__name__
            if type_name in suspicious and sys.getsizeof(obj) > 1024 * 1024:  # >1MB
                lines.append(f"  LARGE {type_name}: {sys.getsizeof(obj) / 1024 / 1024:.2f} MB")
                # Try to get a hint about what it contains
                if isinstance(obj, dict) and len(obj) > 0:
                    keys = list(obj.keys())[:5]
                    lines.append(f"    Keys: {keys}")
                elif isinstance(obj, list) and len(obj) > 0:
                    lines.append(f"    Length: {len(obj)}, first item type: {type(obj[0]).__name__ if obj else 'empty'}")
                elif isinstance(obj, str) and len(obj) > 1000:
                    lines.append(f"    String length: {len(obj)}, preview: {obj[:100]}...")
        except Exception:
            pass
    
    if _tracemalloc_started:
        lines.append("")
        lines.append(get_tracemalloc_top(15))
    
    return "\n".join(lines)
