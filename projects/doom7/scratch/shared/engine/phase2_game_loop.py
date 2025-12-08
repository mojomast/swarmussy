from __future__ import annotations

from typing import Optional, Callable, Any


class Level:
    """Simple Level container used by Phase 2 engine.

    Attributes:
      - name: human-readable level name
      - data: arbitrary level data dictionary
    """

    def __init__(self, name: str = "", data: Optional[dict] = None):
        self.name = name
        self.data = data or {}


class LevelLoader:
    """Abstract loader interface for loading levels at runtime."""

    def load_level(self, path: str) -> Level:
        raise NotImplementedError


class Phase2GameLoop:
    """Deterministic fixed-timestep Phase 2 engine loop skeleton.

    This class provides a minimal, test-friendly surface:
    - tick(dt) advances the loop by fixed sub-steps using the provided world.update(dt).
    - run_for(duration) runs the loop for a duration, returning the number of fixed steps.
    - initialize_with_level(level_dict) stores a level descriptor for the engine.
    - load_level_from_path(path) loads a level using the provided LevelLoader if available.
    """

    def __init__(
        self,
        world: Any,
        level_loader: Optional[LevelLoader] = None,
        level_path: Optional[str] = None,
        dt_fixed: float = 1.0 / 60.0,
    ) -> None:
        if world is None:
            raise ValueError("world is required")
        self.world = world
        self.level_loader = level_loader
        self.level_path = level_path
        self.dt_fixed = float(dt_fixed) if dt_fixed is not None else 1.0 / 60.0
        self._accum = 0.0
        self.level: Optional[Level] = None
        if self.level_loader is not None and self.level_path is not None:
            self.load_level_from_path(self.level_path)

    def load_level_from_path(self, path: str) -> None:
        if self.level_loader is None:
            return
        if hasattr(self.level_loader, "load_level"):
            try:
                self.level = self.level_loader.load_level(path)
            except Exception:
                self.level = None

    def initialize_with_level(self, level: dict) -> None:
        """Store the provided level data as a Level instance."""
        name = level.get("name", "InlineLevel") if isinstance(level, dict) else "InlineLevel"
        self.level = Level(name=name, data=level if isinstance(level, dict) else {})

    def tick(self, dt: Optional[float]) -> int:
        """Advance the loop by dt seconds, returning the number of fixed steps executed."""
        if dt is None:
            return 0
        # Coerce dt to float to support numeric-like inputs and raise for invalid values
        try:
            dt_val = float(dt)
        except (TypeError, ValueError):
            raise ValueError("dt must be a number")
        if dt_val < 0:
            raise ValueError("dt must be non-negative")
        steps = 0
        self._accum += dt_val
        while self._accum + 1e-12 >= self.dt_fixed:
            if not hasattr(self.world, "update"):
                raise RuntimeError("World has no update method")
            # Call the world's update for a single fixed step
            self.world.update(self.dt_fixed)
            steps += 1
            self._accum -= self.dt_fixed
        return steps

    def run_for(self, duration: float) -> int:
        duration = float(duration)
        if duration <= 0:
            return 0
        steps = 0
        remaining = duration
        while remaining >= self.dt_fixed - 1e-12:
            steps += self.tick(self.dt_fixed)
            remaining -= self.dt_fixed
        return steps
