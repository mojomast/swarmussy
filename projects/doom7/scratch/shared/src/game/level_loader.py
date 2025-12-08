from __future__ import annotations

import json
from typing import Any, Dict


class Level:
    def __init__(self, name: str, data: Dict[str, Any] | None = None):
        self.name = name
        self.data = data or {}


class LevelLoader:
    def load(self, level_data: Dict[str, Any]) -> Level:
        if not isinstance(level_data, dict):
            raise ValueError("Level data must be a dict")
        name = level_data.get("name", "Unknown")
        return Level(name=name, data=level_data)
