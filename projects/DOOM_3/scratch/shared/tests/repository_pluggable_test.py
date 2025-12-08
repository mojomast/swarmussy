import pytest
from shared.infra.cleanup.app.repository.in_memory import InMemoryRepo, Task


def test_in_memory_repo_basic():
    repo = InMemoryRepo()
    t = Task('sample-task', 'desc')
    repo.create_task('proj1', t)
    tasks = repo.list_tasks('proj1')
    assert isinstance(tasks, list)
    assert tasks[-1] is t


def test_in_memory_repo_multiple():
    repo = InMemoryRepo()
    t1 = Task('task1', 'd1')
    t2 = Task('task2', 'd2')
    repo.create_task('proj2', t1)
    repo.create_task('proj2', t2)
    tasks = repo.list_tasks('proj2')
    assert len(tasks) == 2
    assert tasks[0] is t1 and tasks[1] is t2


def test_in_memory_repo_isolation():
    repo = InMemoryRepo()
    t1 = Task('alpha-task', 'proj1')
    t2 = Task('beta-task', 'proj2')
    repo.create_task('proj1', t1)
    repo.create_task('proj2', t2)
    list1 = repo.list_tasks('proj1')
    list2 = repo.list_tasks('proj2')
    assert len(list1) == 1 and list1[0] is t1
    assert len(list2) == 1 and list2[0] is t2
