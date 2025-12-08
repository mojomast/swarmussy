from __future__ import annotations

import json
from typing import Optional

from shared.engine.phase2_game_loop import Phase2GameLoop
from shared.src.game.level_loader import LevelLoader


class Phase2Engine:
    """Lightweight Phase 2 engine manager with initialization, start/stop lifecycle.

    This manager exposes an initialization API that accepts a Phase 2 level as
    a JSON payload and wires it into the underlying game loop. It keeps a minimal
    world wrapper so the loop can drive world state on each tick.
    """

    def __init__(self, level_path: Optional[str] = None, dt_fixed: float = 1.0 / 60.0):
        self.level_path = level_path
        self.dt_fixed = float(dt_fixed) if dt_fixed is not None else 1.0 / 60.0
        self.level_loader = LevelLoader()
        self.loop: Phase2GameLoop | None = None
        self.running = False
        self.tick_count = 0
        self._world = None

    def initialize_with_level(self, level_json) -> None:
        """Initialize the engine with an explicit Phase 2 level payload.

        The level_json should be a dictionary representing the level data
        (e.g. {"name": "Test Level", "world": {...}}). It can be a JSON string
        or a Python dict.
        """
        # Normalize input to dict
        if isinstance(level_json, str):
            try:
                level_dict = json.loads(level_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed level JSON: {e}")
        else:
            level_dict = level_json

        # Prepare a simple world wrapper that hooks into engine tick_count
        class _WorldWrapper:
            def __init__(self, engine: Phase2Engine):
                self.engine = engine

            def update(self, dt: float) -> None:
                # Increment engine tick counter for each fixed step
                self.engine.tick_count += 1

        self._world = _WorldWrapper(self)

        # Create the game loop with the world wrapper via a proper on_tick callback
        self.loop = Phase2GameLoop(lambda dt: self._world.update(dt), level_loader=self.level_loader, dt_fixed=self.dt_fixed)
        # Initialize the loop with provided level data
        self.loop.initialize_with_level(level_dict)

    def start(self) -> None:
        if self.loop is None:
            # If start is called before initialize_with_level, try to bootstrap
            if self.level_path is None:
                raise RuntimeError("Phase2Engine requires a level payload or a level_path to start.")
            # Load from path if available and create a minimal world
            class _WorldWrapper:
                def __init__(self, engine: Phase2Engine):
                    self.engine = engine

                def update(self, dt: float) -> None:
                    self.engine.tick_count += 1

            self._world = _WorldWrapper(self)
            self.loop = Phase2GameLoop(lambda dt: self._world.update(dt), level_loader=self.level_loader, level_path=self.level_path, dt_fixed=self.dt_fixed)
        self.running = True
        if self.loop:
            self.loop.start()

    def stop(self) -> None:
        if self.loop:
            self.loop.stop()
        self.running = False
