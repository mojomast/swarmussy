#!/usr/bin/env python3
"""Phase 2 backend API scaffold

This module provides a minimal set of Phase 2 backend endpoints as pure
Python functions suitable for unit/integration tests in this environment.
It is designed to bridge Phase 1 and Phase 2 surfaces with lightweight
in-memory storage and simple error handling.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Iterator

# Phase 1 bridge utility (re-use Phase 1 summary/state via existing bridge)
try:
    from .api_endpoints import get_phase1_summary  # type: ignore
except Exception:
    # If import path changes in tests, provide a safe fallback
    def get_phase1_summary():  # type: ignore
        return {"healthy": True, "state": {"scope_frozen": False}}

# In-memory store for Phase 2 LevelContract
_level_store: Dict[str, Dict[str, Any]] = {
    "level2_01": {
        "level_id": "level2_01",
        "name": "Phase 2 Intro Level",
        "version": "v1.0",
        "content": {"entities": [], "assets": []},
    }
}

# Simple render stats store (could be updated by a running engine in a real scenario)
_stats = {
    "frames_per_second": 60,
    "last_render_time": time.time(),
    "data_points": [0, 1, 2, 3, 4, 5],
}


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def get_v2_engine_render_stats() -> Dict[str, Any]:
    """GET /v2/engine/render_stats

    Returns a small set of stats about the latest render pass and a bridge to
    Phase 1 state for interoperability in tests.
    """
    # In a real system, this would gather live stats. We expose a stable sample
    # plus a Phase 1 bridge payload for integration tests.
    _stats["last_render_time"] = time.time()
    phase1_bridge = get_phase1_summary()
    return {
        "frames_per_second": int(_stats["frames_per_second"]),
        "last_render_time": _stats["last_render_time"],
        "data_points": list(_stats["data_points"]),
        "phase1_bridge": phase1_bridge,
        "generated_at": _now_iso(),
    }


def get_v2_editor_level() -> Dict[str, Any]:
    """GET /v2/editor/level

    Returns the current Phase 2 LevelContract. If not present, returns a default.
    """
    # Return the latest level if present, else a sensible default contract
    level_id = "level2_01"
    contract = _level_store.get(level_id)
    if contract is None:
        contract = {
            "level_id": level_id,
            "name": "Phase 2 Intro Level",
            "version": "v1.0",
            "content": {"entities": [], "assets": []},
        }
        _level_store[level_id] = contract
    return contract


def post_v2_editor_level(payload: Any) -> Dict[str, Any]:
    """POST /v2/editor/level

    Accepts a LevelUpdate-like payload and stores/updates the Phase 2 LevelContract.
    Returns a simple acknowledgement with the level_id.
    """
    # Basic payload validation
    if not payload or not isinstance(payload, dict):
        return {"error": "Invalid payload", "status": 400}

    # Expect at least a level_id and content; allow partial updates as well
    level_id = payload.get("level_id") or payload.get("id")
    if not level_id:
        return {"error": "Missing level_id", "status": 400}

    # Merge or create contract
    existing = _level_store.get(level_id) or {
        "level_id": level_id,
        "name": payload.get("name", "Phase 2 Level"),
        "version": payload.get("version", "v1.0"),
        "content": payload.get("content", {}),
    }

    # Update fields from payload
    for k in ("name", "version", "content"):
        if k in payload:
            existing[k] = payload[k]

    _level_store[level_id] = existing
    return {"success": True, "level_id": level_id}


def stream_v2_events() -> Iterator[str]:
    """GET /v2/events/stream

    Simple Server-Sent Events stream generator. Yields a few events and ends.
    Tests can consume the first event for basic validation.
    """
    events = [
        {
            "event_type": "render_update",
            "timestamp": time.time(),
            "payload": {"fps": int(_stats["frames_per_second"]), "level_id": "level2_01"},
        }
    ]
    for ev in events:
        line = f"data: {json.dumps(ev)}\n\n"
        yield line
    return
