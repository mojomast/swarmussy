from typing import Protocol, List

class Task:
    name: str
    description: str | None

class Repo(Protocol):
    def list_tasks(self, project: str) -> List[Task]: ...
    def create_task(self, project: str, task: Task) -> Task: ...
