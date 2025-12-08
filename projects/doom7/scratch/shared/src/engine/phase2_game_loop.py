from __future__ import annotations

# Scratch-side Phase 2 fixed-timestep game loop used by unit tests in this sandbox.
# This implementation focuses on determinism and a minimal surface to satisfy tests.

import time
from typing import Optional, Any, Callable

# Lightweight Level/LevelLoader compatibility for scratch tests
try:
    from scratch.shared.src.game.level_loader import LevelLoader  # type: ignore
except Exception:
    try:
        from shared.src.game.level_loader import LevelLoader  # type: ignore
    except Exception:
        class LevelLoader:
            def load_level(self, path: str):  # pragma: no cover
                raise RuntimeError("LevelLoader not available in scratch environment")


try:
    from scratch.shared.src.game.level_loader import Level  # type: ignore
except Exception:
    try:
        from shared.src.game.level_loader import Level  # type: ignore
    except Exception:
        class Level:
            def __init__(self, name: str, data=None):
                self.name = name
                self.data = data or {}


class Phase2GameLoop:
    """Scratch Phase 2 fixed-timestep loop with simple tick() semantics."""

    def __init__(self, world: Any = None, level_loader: Optional[LevelLoader] = None, level_path: Optional[str] = None, dt_fixed: float = 1.0/60.0):
        self.world = world
        self.level_loader = level_loader
        self.level_path = level_path
        self.dt_fixed = float(dt_fixed)
        self.accum = 0.0
        self.level: Optional[Level] = None
        # Initialize level if path is provided
        if self.level_loader is not None and self.level_path:
            self._load_level()

    def _load_level(self) -> None:
        if self.level_loader is None or not self.level_path:
            return
        if hasattr(self.level_loader, "load_level"):
            self.level = self.level_loader.load_level(self.level_path)  # type: ignore

    def initialize_with_level(self, level: dict) -> None:
        if not isinstance(level, dict):
            raise ValueError("Level data must be a dict.")
        self.level = Level(name=level.get("name", "Phase2Level"), data=level)

    def tick(self, dt: float) -> int:
        if dt is None:
            dt = 0.0
        if dt < 0:
            raise ValueError("dt must be non-negative")
        if self.level is None:
            raise RuntimeError("Phase 2 level is not loaded")
        self.accum += float(dt)
        steps = 0
        while self.accum >= self.dt_fixed:
            if self.world is not None and hasattr(self.world, "update"):
                self.world.update(self.dt_fixed)
            self.accum -= self.dt_fixed
            steps += 1
        return steps

    def run_for(self, duration: float) -> int:
        duration = float(duration) if duration is not None else 0.0
        if self.dt_fixed <= 0:
            return 0
        steps = int(duration / self.dt_fixed)
        for _ in range(steps):
            self.tick(self.dt_fixed)
        return steps

    def update(self, dt: float) -> None:
        if self.world is None:
            return
        if hasattr(self.world, "update"):
            self.world.update(dt)

    def load_level_from_path(self, path: str) -> None:
        if self.level_loader is None:
            return
        if hasattr(self.level_loader, "load_level"):
            self.level = self.level_loader.load_level(path)  # type: ignore
