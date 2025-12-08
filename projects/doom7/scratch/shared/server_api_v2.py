from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
import json, time

# Phase 2 API surface wired into runtime (minimal in-memory store)
app = FastAPI(title="Phase 2 API", version="v2", description="Phase 2 runtime surface implementing engine/editor endpoints.")

# In-memory storage for levels and render stats
_level_store: Dict[str, Dict[str, Any]] = {
    "level_01": {
        "level_id": "level_01",
        "name": "Intro Level",
        "version": "v2.0",
        "content": {"entities": [], "assets": []},
    }
}
_render_stats = {
    "frames_rendered": 0,
    "average_fps": 0.0,
    "memory_mb": 0.0,
}

class Level(BaseModel):
    level_id: str
    name: str
    version: str
    content: Dict[str, Any]

class LevelInput(BaseModel):
    level_id: str
    name: str
    version: str
    content: Dict[str, Any]

class RenderStats(BaseModel):
    frames_rendered: int
    average_fps: float
    memory_mb: float


@app.get("/v2/editor/level", response_model=Level)
async def get_editor_level() -> Level:
    # Return existing level if available, else a sensible default
    if _level_store.get("level_01"):
        data = _level_store["level_01"]
    else:
        data = {
            "level_id": "level_01",
            "name": "Intro Level",
            "version": "v2.0",
            "content": {"entities": [], "assets": []},
        }
    return Level(**data)


@app.post("/v2/editor/level", response_model=Level)
async def upsert_editor_level(level_input: LevelInput) -> Level:
    # Persist in-memory for this scaffold
    _level_store[level_input.level_id] = {
        "level_id": level_input.level_id,
        "name": level_input.name,
        "version": level_input.version,
        "content": level_input.content,
    }
    return Level(**_level_store[level_input.level_id])


@app.get("/v2/engine/render_stats", response_model=RenderStats)
async def get_render_stats() -> RenderStats:
    return RenderStats(**_render_stats)


@app.get("/v2/events/stream")
async def stream_events():
    def event_generator():
        # emit a few sample events
        for i in range(3):
            payload = {
                "event_type": "frame_rendered",
                "frame": i,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            yield f"data: {json.dumps(payload)}\n\n"
            time.sleep(0.05)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Expose app for tests
__all__ = ["app"]
