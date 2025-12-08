from __future__ import annotations

from typing import List

# Import Task type for type hints without enforcing a concrete implementation here

class Task:
    """Lightweight task container used by the in-memory repository tests.
    This is kept minimal to preserve compatibility with existing tests that
    instantiate Task(name, description).
    """

    def __init__(self, name: str, description: str | None = None):
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return f"Task(name={self.name!r}, description={self.description!r})"


class TaskRepository:
    """Abstract repository interface for per-project tasks.

    This is a lightweight interface to describe the required CRUD-like
    operations for tasks within a project. The concrete implementation (e.g.,
    InMemoryRepo) will provide the actual storage semantics.
    """

    def list_tasks(self, project: str) -> List[Task]:  # pragma: no cover - interface
        raise NotImplementedError

    def create_task(self, project: str, task: Task) -> Task:  # pragma: no cover - interface
        raise NotImplementedError

