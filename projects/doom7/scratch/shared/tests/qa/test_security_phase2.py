from __future__ import annotations

import pytest

from shared.engine.phase2_game_loop import Phase2GameLoop, Level, LevelLoader


class SafeWorld:
    def __init__(self):
        self.updated = 0

    def update(self, dt: float) -> None:
        self.updated += 1


def test_tick_with_non_numeric_dt_raises_value_error():
    world = SafeWorld()
    loop = Phase2GameLoop(world=world, level_loader=None, level_path=None, dt_fixed=0.01)
    with pytest.raises(ValueError):
        loop.tick("not-a-number")


def test_run_for_large_duration_computes_steps():
    world = SafeWorld()
    loop = Phase2GameLoop(world=world, level_loader=None, level_path=None, dt_fixed=0.01)
    steps = loop.run_for(0.2)  # 20 steps
    assert steps == 20
    assert world.updated == 20
