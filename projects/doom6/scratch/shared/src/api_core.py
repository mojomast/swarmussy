from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="Core API")

class HealthResponse(BaseModel):
    status: str

class ConfigResponse(BaseModel):
    env: dict
    defaults: dict

# We'll populate config in a simple way for now

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")

@app.get("/config", response_model=ConfigResponse)
def config():
    # Read a couple of sample env vars with defaults
    env = {
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        "DEBUG": os.getenv("DEBUG", "false"),
        "PORT": os.getenv("PORT", "8000"),
    }
    defaults = {
        "ENVIRONMENT": "development",
        "DEBUG": False,
        "PORT": 8000,
    }
    return ConfigResponse(env=env, defaults=defaults)
