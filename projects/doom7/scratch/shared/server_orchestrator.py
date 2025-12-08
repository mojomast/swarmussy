# Minimal orchestrator glue for Phase 2 surface
from .server_api_v2 import app

# In a full system, this would route to engine plugins, manage lifecycle, etc.
# For this scaffold, we simply expose the engine surface through app.

__all__ = ["app"]
