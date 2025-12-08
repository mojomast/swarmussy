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

8. **TUI API Log & History**: In TUI mode, watch the right sidebar's API log:
   - Send a few messages so multiple API calls are in flight.
   - Verify that requests with a wrench icon appear in the **In-flight** section at the top.
   - After responses arrive, verify those entries move into the **History** section below and remain scrollable.
   - Click an entry multiple times and confirm it cycles through collapsed → summary → full details.

9. **Floating File Browser**: In TUI mode, open the file browser:
   - Press `Ctrl+F` or click the `📁 FILES` button in the header.
   - Verify the left-hand list shows the current project's files (without noisy internal/hidden directories).
   - Select several files and confirm their contents appear in the right-hand preview, with large or binary files handled gracefully (truncated or placeholder).

10. **Checky McManager Proactivity**:
    - Use the Tasks screen (`Ctrl+T`) or commands to create, assign, and complete/fail tasks.
    - Verify that Checky posts new status updates whenever task state changes (new tasks, assignments, completions, failures), rather than only after very long runs.

11. **Auto-Orchestrator Handoff**:
    - Run a longer swarm session with `auto_chat` enabled.
    - After all open tasks for a project complete, watch for an "Auto Orchestrator" message prompting next steps and confirm a new round starts without you typing.
    - For heavy-context tasks, monitor logs and the TOKENS panel; when a single worker call grows very large, you should see an "Auto Orchestrator" message asking to hand off work to a fresh worker with a concise summary.

12. **Git-Aware Workflow & Commit Gatekeeper**:
    - Run a project long enough for workers to produce non-trivial code under `scratch/shared/` (for example, a small backend or game engine slice).
    - From a shell, run `git status` and confirm that only the current project's workspace (e.g. `projects/<name>/scratch/shared/...`) shows as changed.
    - In the TUI, watch Bugsy McTester reports for explicit `QA DECISION: APPROVED` / `QA DECISION: REQUEST_CHANGES` lines.
    - After QA reports APPROVED for a scope, watch Checky McManager's logs for a description of the pending changes and a `git_commit` action.
    - From a shell, run `git log -n 3` and `git show` to confirm that:
      - Commits only touch the active project's workspace.
      - Commit messages look like small PR titles summarizing the work.
    - Verify there is **no automatic `git push`**; pushing to remotes remains a manual human step.

13. **Singleton Workers Per Role**:
    - Start a new TUI session and describe a project that needs backend, frontend, QA, DevOps, and PM work.
    - Let the Architect autospawn its usual team, then use `/spawn` or additional planning instructions to try to create more `backend_dev`, `frontend_dev`, or `qa_engineer` workers.
    - Confirm in the AGENTS panel that there is at most one Codey, Pixel, Bugsy, Deployo, Checky, and Docy at any time (no `Codey McBackend 2`, `3`, etc.).
    - Verify that repeated `spawn_worker` calls for these roles simply reuse the existing agent instances.

14. **DevPlan vs Dashboard Files**:
    - Run a project long enough for the Architect to create a master plan and several tasks.
    - Inspect `projects/<name>/scratch/shared/` and verify that:
        - `master_plan.md` contains the long-form architecture/phase plan.
        - `devplan.md` contains the Architect's internal tracker (phases, detailed tasks, notes) including a `<!-- LIVE_DASHBOARD_START -->` section.
        - `dashboard.md` exists and shows a concise, user-facing snapshot (progress bar, "Currently Working On", "Up Next", blockers, active agents, recent completions).
    - In the TUI, confirm that the right sidebar DEVPLAN panel is rendering the same content as `dashboard.md`.
    - Use `/devplan` in the TUI and verify that the raw `devplan.md` content (or a truncated slice) is printed to chat for debugging.

15. **Task Completion via `complete_my_task` + Auto-Orchestrator**:
    - Start a project, let the Architect assign a few concrete coding tasks, then allow workers to run.
    - In the logs, confirm that workers call the `complete_my_task` tool when they are done, and that their agent cards flip back to `IDLE` with no lingering `current_task_id`.
    - After the final open task completes, watch for a human-role "Auto Orchestrator" message indicating that a phase milestone was reached and asking the Architect to start the next phase or summarize deliverables.
    - Verify that the next auto-chat tick kicks off a new round and that the dashboard/devplan are updated to reflect the new phase or final project status.

16. **API Provider & Tool Identifier Configuration**:
    - Open Settings → Models and Settings → API in the TUI (Ctrl+S).
    - Set Architect/Worker providers to different values (`requesty`, `zai`, `openai`, `custom`) and provide the appropriate keys or base URLs as needed for your environment.
    - Change the tool identifier to several options (e.g. `claude-code`, `cursor`, `windsurf`, or a custom string) and verify via server-side logs or a proxy that the outgoing `User-Agent` / tool identity header changes accordingly.
    - Confirm that changing providers and tool identifiers does not break the swarm's orchestration flow (Architect → workers → devplan/dashboard updates still function as expected).

---

## Contact

If tests fail or you need clarification, check:
- `.kiro/specs/swarm-fixes/requirements.md` - Original requirements
- `.kiro/specs/swarm-fixes/design.md` - Design decisions
- `.kiro/specs/swarm-fixes/tasks.md` - Implementation tasks

---

*Generated: December 2024*
*Status: Ready for testing*
