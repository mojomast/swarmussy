"""
Unit tests for Phase 2 Engine skeleton
"""

import json
import pytest

from shared.src.game.level_loader import LevelLoader
from shared.src.phase2_engine import Phase2Engine


def test_initialize_with_valid_level_and_tick():
    loader = LevelLoader()
    engine = Phase2Engine()

    level_json = json.dumps({"name": "TestLevel", "world": {"seed": 1}})
    engine.initialize_with_level(level_json)

    # Start the engine's fixed-timestep loop in background; let it run briefly
    engine.start()
    # Sleep a short time to allow a few ticks to accumulate
    import time
    time.sleep(0.15)
    engine.stop()

    # We expect at least some ticks to have occurred
    assert engine.tick_count >= 1
