# Repository API (Pluggable Layer)

This document describes the pluggable repository interface and its in-memory implementation used for unit testing and progressive backend wiring. The repository layer isolates data access from API logic and is designed to be swapped with a DB-backed implementation in the future.

- Task model: a generic dictionary-like payload with per-project scoping.
- Interfaces:
  - TaskRepository with list_tasks(project), create_task(project, task).
- Implementations:
  - InMemoryRepo (in scratch/shared/infra/cleanup/app/repository/in_memory.py)

