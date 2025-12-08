"""
Configuration settings for the Multi-Agent Chatroom.

This module handles all environment variables and configuration constants
used throughout the application.
"""

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PROVIDER & MODEL CONFIGURATION
# ============================================================================

# Requesty router (default)
REQUESTY_API_KEY = os.getenv("REQUESTY_API_KEY", "")
REQUESTY_API_BASE_URL = "https://router.requesty.ai/v1/chat/completions"

# Z.AI direct API (GLM family). Uses general chat completions endpoint by
# default; advanced users can override via /api or environment if needed.
ZAI_API_KEY = os.getenv("ZAI_API_KEY", "")
ZAI_API_BASE_URL = "https://api.z.ai/api/paas/v4/chat/completions"

# Available models (union across providers; provider choice is configured in
# settings). These strings are passed directly to the selected provider.
AVAILABLE_MODELS = [
    # Requesty-routed models
    "openai/gpt-5-nano",
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    "anthropic/claude-3-5-sonnet",
    "anthropic/claude-3-haiku",
    "google/gemini-2.0-flash",
    "google/gemini-1.5-pro",
    "mistral/mistral-large",
    "meta-llama/llama-3.1-70b",
    # Z.AI GLM models (direct Z.AI provider)
    "glm-4.6",
    "glm-4.5",
    "glm-4.5-air",
    "glm-4.5-x",
    "glm-4.5-airx",
    "glm-4.5-flash",
    "glm-4-32b-0414-128k",
]

# Default model for agents
DEFAULT_MODEL = "openai/gpt-5-nano"

# Specific models for roles
ARCHITECT_MODEL = "openai/gpt-5-nano"
SWARM_MODEL = "openai/gpt-5-nano"

# ============================================================================
# Memory Configuration
# ============================================================================
# Short-term memory: number of recent messages to keep in context
SHORT_TERM_MEMORY_SIZE = 50

# Default data directory (used when no project is active)
DATA_DIR = Path(__file__).parent.parent / "data"

# Legacy static paths (for backwards compatibility)
MEMORY_DB_PATH = DATA_DIR / "memory.db"
CHAT_HISTORY_PATH = DATA_DIR / "chat_history.json"

# Summarization frequency (every N messages per agent)
SUMMARIZE_EVERY_N_MESSAGES = 5


# ============================================================================
# Dynamic Path Functions (Project-Aware)
# ============================================================================
def get_memory_db_path() -> Path:
    """Get the memory database path (project-aware)."""
    from core.project_manager import get_current_project
    project = get_current_project()
    if project:
        return project.memory_db_path
    return DATA_DIR / "memory.db"


def get_chat_history_path() -> Path:
    """Get the chat history path (project-aware)."""
    from core.project_manager import get_current_project
    project = get_current_project()
    if project:
        return project.chat_history_path
    return DATA_DIR / "chat_history.json"


def get_scratch_dir() -> Path:
    """Get the scratch directory (project-aware)."""
    from core.project_manager import get_current_project
    project = get_current_project()
    if project:
        return project.scratch_dir
    return DATA_DIR.parent / "scratch"

# ============================================================================
# WebSocket Server Configuration
# ============================================================================
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", "8765"))

# ============================================================================
# Discord Bot Configuration
# ============================================================================
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")

# ============================================================================
# Chatroom Configuration
# ============================================================================
# Delay between agent responses (seconds) to simulate natural conversation
AGENT_RESPONSE_DELAY_MIN = 1.0
AGENT_RESPONSE_DELAY_MAX = 3.0

# Maximum concurrent API calls
MAX_CONCURRENT_API_CALLS = 5

# Agent speaking probability per round (0.0 - 1.0)
AGENT_SPEAK_PROBABILITY = 0.6

# Maximum tokens per response (balanced for efficiency)
# Most responses don't need 100k tokens - use a reasonable default
MAX_RESPONSE_TOKENS = 16000

# Temperature for response generation
DEFAULT_TEMPERATURE = 0.8

# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# ============================================================================
# Helper Functions
# ============================================================================
def ensure_data_directory():
    """Ensure the data directory exists for persistent storage."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR

def validate_config():
    """Validate required configuration is present."""
    errors = []
    from core.settings_manager import get_settings
    settings = get_settings()

    custom_base = (settings.get("api_base_url", "") or "").strip()
    custom_key = (settings.get("api_key", "") or "").strip()
    zai_key = (settings.get("zai_api_key", "") or "").strip() or ZAI_API_KEY

    if not REQUESTY_API_KEY and not (custom_base and custom_key) and not zai_key:
        errors.append(
            "No API key configured. Set REQUESTY_API_KEY in .env, configure a custom provider via /api, "
            "or provide ZAI_API_KEY / z.ai settings."
        )
    
    if errors:
        return False, errors
    return True, []

# ============================================================================
# Tool Usage Configuration
# ============================================================================
# Maximum tokens for tool-using responses (needs more for code generation)
# 32k is sufficient for most code files while being more efficient
TOOL_MAX_TOKENS = 32000

# Default scratch directory (use get_scratch_dir() for project-aware path)
SCRATCH_DIR = DATA_DIR.parent / "scratch"


# ============================================================================
# Project Configuration
# ============================================================================
PROJECTS_DIR = Path(__file__).parent.parent / "projects"
