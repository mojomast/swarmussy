import pytest

from typing import Optional

# Import Phase2 game loop; rely on internal fallbacks if real modules aren't present
from shared.engine.phase2_game_loop import Phase2GameLoop, Level, LevelLoader  # type: ignore


class FakeWorld:
    def __init__(self):
        self.updates = []

    def update(self, dt: float) -> None:
        # Track that update was called with a timestep
        self.updates.append(dt)


class FakeLoader(LevelLoader):
    def load_level(self, path: str) -> Level:
        # Return a simple Level instance; ensure compatibility with Level constructor
        return Level(name="LoadedLevel", data={"path": path})


def test_tick_schedules_fixed_steps():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=FakeLoader(), level_path="path/to/level", dt_fixed=0.01)

    steps = loop.tick(0.033)  # should process floor(0.033 / 0.01) = 3 steps
    assert steps == 3
    # Ensure world.update called 3 times
    assert world.updates == 3


def test_tick_negative_dt_raises():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=FakeLoader(), level_path="path/to/level", dt_fixed=0.01)
    with pytest.raises(ValueError):
        loop.tick(-0.01)


def test_tick_without_update_raises():
    # World that lacks update method
    class NoUpdateWorld:
        pass

    loop = Phase2GameLoop(world=NoUpdateWorld(), level_loader=FakeLoader(), level_path="path/to/level", dt_fixed=0.01)
    with pytest.raises(RuntimeError):
        loop.tick(0.01)


def test_run_for_runs_expected_steps():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=FakeLoader(), level_path="path/to/level", dt_fixed=0.005)
    steps = loop.run_for(0.025)  # 5 steps
    assert steps == 5
    assert world.updates == 5


def test_level_loading_via_loader():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=FakeLoader(), level_path="levelX", dt_fixed=0.01)
    # If level was loaded, loop.level should not be None
    assert loop.level is not None
    assert getattr(loop.level, "name", None) == "LoadedLevel"


def test_tick_none_dt_no_effect_when_level_loaded():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=None, level_path=None, dt_fixed=0.01)
    loop.level = Level(name="TestLevel")
    steps = loop.tick(None)
    assert steps == 0
    assert len(world.updates) == 0


def test_run_for_zero_duration_returns_zero():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=None, level_path=None, dt_fixed=0.01)
    loop.level = Level(name="TestLevel")
    steps = loop.run_for(0.0)
    assert steps == 0
    assert len(world.updates) == 0


def test_initialize_with_level_sets_level():
    world = FakeWorld()
    loop = Phase2GameLoop(world=world, level_loader=None, level_path=None, dt_fixed=0.01)
    level_dict = {"name": "InlineLevel", "foo": "bar"}
    loop.initialize_with_level(level_dict)
    assert loop.level is not None
    assert loop.level.name == "InlineLevel"
