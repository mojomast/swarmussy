from fastapi import FastAPI
import os

app = FastAPI(title="Phase 2 API")


@app.get("/")
def read_root():
    return {"message": "Phase 2 API"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    # Expose a read-only view of environment/config for debugging in container
    db_url = os.environ.get("DATABASE_URL", "")
    return {"DATABASE_URL": db_url}
