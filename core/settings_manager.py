"""
Settings Manager for Multi-Agent Chatroom.

Handles persistent user settings with JSON storage.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS = {
    "username": "You",
    "round_delay": 15.0,
    "response_delay_min": 2.0,
    "response_delay_max": 5.0,
    "max_responders": 3,
    "auto_chat": True,
    "verbose": False,
    "tools_enabled": True,
    "default_model": "openai/gpt-5-nano",
    "architect_model": "openai/gpt-5-nano",
    "swarm_model": "openai/gpt-5-nano",
    "agent_models": {},  # Optional per-agent model overrides keyed by agent name
    "disabled_agents": [],
    "theme": "dark",
    "max_tokens": 100000,
    "temperature": 0.8,
    "thinking_tokens": 50000,
    "max_tool_depth": 250,  # Allow agents to chain up to 250 tool calls when working
    "load_previous_history": True,  # Whether to load prior chat history on startup
}

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "settings.json"


class SettingsManager:
    """Manages persistent user settings."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = DEFAULT_SETTINGS.copy()
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        """Load settings from file."""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # Merge with defaults (in case new settings were added)
                    self._settings = {**DEFAULT_SETTINGS, **saved}
                logger.info("Settings loaded from file")
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")

    def save(self):
        """Save settings to file."""
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
            logger.info("Settings saved to file")
        except Exception as e:
            logger.error(f"Could not save settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True):
        """Set a setting value."""
        self._settings[key] = value
        if auto_save:
            self.save()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
    
    def reset(self):
        """Reset to default settings."""
        self._settings = DEFAULT_SETTINGS.copy()
        self.save()
    
    def update(self, settings: Dict[str, Any], auto_save: bool = True):
        """Update multiple settings at once."""
        self._settings.update(settings)
        if auto_save:
            self.save()


def get_settings() -> SettingsManager:
    """Get the singleton settings manager."""
    return SettingsManager()


# Convenience functions
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value."""
    return get_settings().get(key, default)


def set_setting(key: str, value: Any):
    """Set a setting value."""
    get_settings().set(key, value)
