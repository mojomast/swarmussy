#!/usr/bin/env python3
"""Phase 2 integration tests

This file exercises the Phase 2 endpoints implemented in shared/src/server_api_v2.py
for basic happy-path scenarios and error handling. The tests are designed to run with
pytest in the container environment.
"""

import json
import io
import time
from typing import Any

import pytest

from shared.src.server_api_v2 import (
    get_v2_engine_render_stats,
    get_v2_editor_level,
    post_v2_editor_level,
    stream_v2_events,
)


def test_render_stats_includes_phase1_bridge():
    stats = get_v2_engine_render_stats()
    assert isinstance(stats, dict)
    assert "frames_per_second" in stats
    assert "phase1_bridge" in stats


def test_editor_level_get_returns_contract():
    contract = get_v2_editor_level()
    assert isinstance(contract, dict)
    assert "level_id" in contract


def test_editor_level_post_updates():
    payload = {
        "level_id": "level2_01",
        "name": "Phase 2 Intro Level Updated",
        "content": {"entities": [{"type": "npc", "id": "e1"}]},
    }
    resp = post_v2_editor_level(payload)
    assert resp.get("success") is True
    assert resp.get("level_id") == "level2_01"


def test_events_stream_generation():
    lines = list(stream_v2_events())
    assert any("data:" in line for line in lines)
