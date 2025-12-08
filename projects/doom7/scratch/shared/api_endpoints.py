# Runtime OpenAPI endpoints wiring (phase 2)
from fastapi import FastAPI
from .server_api_v2 import app as app_v2

# Mount v2 surface under /v2
api = FastAPI()
api.mount("/v2", app_v2)

__all__ = ["api"]
