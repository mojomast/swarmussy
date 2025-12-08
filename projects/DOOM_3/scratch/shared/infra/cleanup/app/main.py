from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Cleanup API")

class Task(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
def read_root():
    return {"status": "ok", "service": "cleanup-api"}

@app.post("/tasks/")
def create_task(task: Task):
    return {"status": "created", "task": task.dict()}
