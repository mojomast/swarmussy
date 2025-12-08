from typing import List, Dict, Optional
import uuid

class Task:
    """Lightweight task container used by the in-memory repository tests.
    This class is intentionally permissive: tests may pass arbitrary fields.
    The API layer will map to a full API model when returning results.
    """

    def __init__(self, name: str, description: str | None = None, **kwargs):
        # Backward-compatible: tests may construct Task(name, description)
        self.name = name
        self.description = description
        # Additional arbitrary fields supported
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"Task(name={self.name!r}, description={self.description!r})"


class InMemoryRepo:
    """Pluggable in-memory repository for per-project tasks.

    Stores tasks per-project and supports a minimal CRUD surface to satisfy
    tests and the repository-driven API wiring.
    """

    def __init__(self) -> None:
        # Store as: { project_id: [Task, ...], ... }
        self._store: Dict[str, List[Task]] = {}

    # Basic CRUD-like operations
    def list_tasks(self, project: str) -> List[Task]:
        return list(self._store.get(project, []))

    def create_task(self, project: str, task) -> Task:
        # Accept either a Task instance or a dict-like payload; tests pass Task
        if isinstance(task, Task):
            self._store.setdefault(project, []).append(task)
            return task
        else:
            # Fallback: store as-is (dict-like)
            self._store.setdefault(project, []).append(task)  # type: ignore
            return task  # type: ignore

    def __repr__(self) -> str:
        return f"InMemoryRepo(store_keys={list(self._store.keys())})"

__all__ = ["Task", "InMemoryRepo"]
