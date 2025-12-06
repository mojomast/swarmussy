# Testing Handoff Document: Multi-Agent Swarm Fixes

## Overview

This document provides instructions for running and validating the test suite for the Multi-Agent Swarm fixes. The tests cover role resolution, token tracking, dashboard coloring, settings persistence, and agent state toggling.

---

## Prerequisites

### Install Dependencies

```bash
pip install pytest hypothesis rich aiofiles
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Required Packages for Testing

| Package | Purpose |
|---------|---------|
| `pytest` | Test runner |
| `hypothesis` | Property-based testing |
| `rich` | Dashboard UI (needed for import) |
| `aiofiles` | Async file operations |

---

## Test Files

| File | Description | Properties Tested |
|------|-------------|-------------------|
| `tests/test_role_resolution.py` | Role mapping from display names to role keys | Property 1, 2 |
| `tests/test_token_tracker.py` | Token counting accumulation | Property 4 |
| `tests/test_dashboard_coloring.py` | User message lime green coloring | Property 3 |
| `tests/test_settings_persistence.py` | Settings save/load round-trip | Property 5 |
| `tests/test_agent_state_toggle.py` | Agent enable/disable toggling | Property 6 |

---

## Running Tests

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test File

```bash
# Role resolution tests
python -m pytest tests/test_role_resolution.py -v

# Token tracker tests
python -m pytest tests/test_token_tracker.py -v

# Dashboard coloring tests
python -m pytest tests/test_dashboard_coloring.py -v

# Settings persistence tests
python -m pytest tests/test_settings_persistence.py -v

# Agent state toggle tests
python -m pytest tests/test_agent_state_toggle.py -v
```

### Run with Coverage

```bash
pip install pytest-cov
python -m pytest tests/ -v --cov=. --cov-report=html
```

### Run Property Tests with More Examples

```bash
# Run with 500 examples per property (default is 100)
python -m pytest tests/ -v --hypothesis-seed=0
```

---

## Test Descriptions

### 1. Role Resolution Tests (`test_role_resolution.py`)

**Purpose**: Verify the Architect can spawn agents using display names (e.g., "Codey McBackend") or role keys (e.g., "backend_dev").

**Properties Tested**:
- **Property 1**: For any valid display name, `resolve_role()` returns the correct role key
- **Property 2**: For any valid role key, `resolve_role()` returns the same key (backwards compatible)

**Key Test Cases**:
- All display names resolve correctly
- All role keys resolve correctly
- Case-insensitive matching
- Whitespace handling
- Invalid role raises `ValueError` with helpful message

**Expected Behavior**:
```python
resolve_role("Codey McBackend") == "backend_dev"
resolve_role("backend_dev") == "backend_dev"
resolve_role("BACKEND_DEV") == "backend_dev"
resolve_role("  codey mcbackend  ") == "backend_dev"
```

---

### 2. Token Tracker Tests (`test_token_tracker.py`)

**Purpose**: Verify token counting accumulates correctly across API calls.

**Properties Tested**:
- **Property 4**: For any sequence of token usages, totals equal the sum of all individual values

**Key Test Cases**:
- Singleton pattern works correctly
- Initial state is zero
- Reset clears all counters
- Zero token usage still increments call count
- Accumulation is accurate for random sequences

**Expected Behavior**:
```python
tracker.add_usage(100, 50)
tracker.add_usage(200, 100)
stats = tracker.get_stats()
# stats["prompt_tokens"] == 300
# stats["completion_tokens"] == 150
# stats["total_tokens"] == 450
# stats["call_count"] == 2
```

---

### 3. Dashboard Coloring Tests (`test_dashboard_coloring.py`)

**Purpose**: Verify user messages display with lime green username color.

**Properties Tested**:
- **Property 3**: Human role messages use `USER_STYLE` ("bold bright_green")

**Key Test Cases**:
- `USER_STYLE` is "bold bright_green"
- Human role messages use `USER_STYLE`
- Agent messages use `AGENT_STYLES`
- Unknown agents use "white" style
- All message roles handled correctly

**Expected Behavior**:
```python
# Human messages
if message.role == MessageRole.HUMAN:
    name_style = USER_STYLE  # "bold bright_green"
else:
    name_style = AGENT_STYLES.get(message.sender_name, "white")
```

---

### 4. Settings Persistence Tests (`test_settings_persistence.py`)

**Purpose**: Verify settings save and load correctly (round-trip).

**Properties Tested**:
- **Property 5**: Any setting saved should be retrievable with the exact same value

**Key Test Cases**:
- Single setting round-trip
- Multiple settings round-trip
- Default settings preserved
- Username persistence
- Disabled agents list persistence
- Delay settings persistence
- Reset restores defaults

**Expected Behavior**:
```python
manager.set("username", "TestUser")
manager.save()
# Restart app...
manager2 = SettingsManager()
assert manager2.get("username") == "TestUser"
```

---

### 5. Agent State Toggle Tests (`test_agent_state_toggle.py`)

**Purpose**: Verify agent enable/disable toggling works correctly.

**Properties Tested**:
- **Property 6**: Toggling an agent's state flips the boolean value

**Key Test Cases**:
- Single toggle flips state
- Double toggle restores original state
- Toggle only affects target agent
- Toggle persists to settings
- All agents initially enabled
- Enable already enabled agent (no-op)
- Disable already disabled agent (no-op)
- Toggle all agents

**Expected Behavior**:
```python
# If agent is enabled (not in disabled_agents)
toggle_agent_state("backend_dev", [])  # Returns ["backend_dev"]
# If agent is disabled (in disabled_agents)
toggle_agent_state("backend_dev", ["backend_dev"])  # Returns []
```

---

## Troubleshooting

### Import Errors

If you see import errors, ensure you're running from the project root:

```bash
cd /path/to/multi-agent-swarm
python -m pytest tests/ -v
```

### Missing Modules

If `core.token_tracker` is missing, the implementation may not be complete. Check that `core/token_tracker.py` exists.

If `DISPLAY_NAME_TO_ROLE` is missing from `agents/__init__.py`, the role mapping implementation may not be complete.

### Hypothesis Flaky Tests

If property tests are flaky, try running with a fixed seed:

```bash
python -m pytest tests/ -v --hypothesis-seed=12345
```

### Settings File Conflicts

Tests use temporary settings files via `tmp_path` fixture. If you see conflicts, ensure no other process is modifying `data/settings.json`.

---

## Validation Checklist

After running all tests, verify:

- [ ] All role resolution tests pass (Property 1, 2)
- [ ] All token tracker tests pass (Property 4)
- [ ] All dashboard coloring tests pass (Property 3)
- [ ] All settings persistence tests pass (Property 5)
- [ ] All agent state toggle tests pass (Property 6)
- [ ] No import errors
- [ ] No deprecation warnings

---

## Manual Testing

After automated tests pass, manually verify:

1. **Role Resolution**: Run the app and have the Architect spawn "Codey McBackend" - should work without "Unknown role" error

2. **Token Counting**: Check the dashboard shows token usage after agent responses

3. **User Coloring**: Send a message and verify your username appears in lime green

4. **Settings**: Change username via `/name`, restart app, verify it persists

5. **Dashboard Default**: Run `python main.py` and verify dashboard launches (not CLI)

6. **TUI Agents Panel UX**: Run `python main.py --tui`, spawn several agents, verify that:
   - Clicking an agent card toggles its expanded/collapsed state (`▸`/`▾`) and shows more/fewer items under **Latest**.
   - `Ctrl+A` focuses the AGENTS panel and `Ctrl+Up` / `Ctrl+Down` scroll through the list when there are more cards than fit on screen.

7. **API Pulse Indicator**: In TUI mode, send a message and watch the header subtitle:
   - It should switch from `API ○ idle` to `API ↑ req` when a request is sent, then `API ↓ resp` when a response arrives, before returning to `idle`.

---

## Contact

If tests fail or you need clarification, check:
- `.kiro/specs/swarm-fixes/requirements.md` - Original requirements
- `.kiro/specs/swarm-fixes/design.md` - Design decisions
- `.kiro/specs/swarm-fixes/tasks.md` - Implementation tasks

---

*Generated: December 2024*
*Status: Ready for testing*
