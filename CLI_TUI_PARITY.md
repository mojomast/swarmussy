# CLI ↔ TUI Parity Documentation

## Overview

This document describes the refactoring work done to achieve feature parity between CLI mode (`--cli`) and TUI mode (Textual dashboard).

## Summary of Changes

### New Files

| File | Purpose |
|------|---------|
| `core/session_controller.py` | Shared controller that both TUI and CLI use |
| `tests/test_session_controller.py` | Unit tests for the shared controller |

Phase 0 project bootstrap and Devussy orchestration are also shared:

- `core/project_bootstrap.py` runs once per Devussy project in both TUI and CLI:
  - Creates a Python `.venv` at the **project root** (outside `scratch/shared/`)
  - Ensures `scratch/shared/requirements.txt` exists and always includes `pytest`
  - Installs Python deps from `scratch/shared/requirements.txt`
  - If `scratch/shared/package.json` exists, runs `npm install` in `scratch/shared/`
  - Scaffolds `src/`, `tests/`, `docs/`, `config/` (and basic frontend dirs for web stacks)
- `core/agent_tools.py` and `agents/lean_prompts.py` enforce design-driven behavior in both modes:
  - Backend/frontend workers must read `project_design.md` and follow its tech stack (no Flask→FastAPI or React+Vite→Webpack swaps unless the design or user says so)
  - `get_project_structure` is cached and filters heavy dirs (`.venv`, `node_modules`, `.git`, `__pycache__`, IDE caches, build outputs)
  - `read_multiple_files` batch-reads up to 10 files and asks the agent to split larger lists into multiple calls.

### Modified Files

| File | Changes |
|------|---------|
| `main.py` | Added `SwarmCLI` class, updated argument parsing |

## Architecture

```
                    ┌─────────────────────────────┐
                    │     SessionController       │
                    │  - project, chatroom        │
                    │  - orchestrator, dispatcher │
                    │  - message callbacks        │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌────────────┐      ┌────────────┐      ┌────────────┐
       │  TUI Mode  │      │  CLI Mode  │      │ Future UIs │
       │  (Textual) │      │  (SwarmCLI)│      │            │
       └────────────┘      └────────────┘      └────────────┘
```

## Run Modes

### TUI Mode (Default)
```bash
python main.py
# or explicitly:
python main.py --tui
```
Uses the full Textual-based dashboard with panels, widgets, and real-time updates.

### CLI Mode (New - Feature Parity)
```bash
python main.py --cli
```
Uses the new `SwarmCLI` class with full feature parity:
- Devussy pipeline integration
- `go` command with AutoDispatcher (zero tokens)
- `/stop` and `/halt` commands
- Task/agent status display
- Settings management

### Legacy CLI Mode
```bash
python main.py --cli-legacy
```
Uses the old `InteractiveChatroom` class (preserved for backwards compatibility).

### Rich Dashboard (Legacy)
```bash
python main.py --rich
```
Uses the Rich-based dashboard (legacy mode).

## Feature Parity Table

| Feature | TUI | CLI (New) | CLI (Legacy) |
|---------|-----|-----------|--------------|
| Project Selection | ✅ | ✅ | ✅ |
| Devussy Pipeline | ✅ | ✅ | ❌ |
| AutoDispatcher (`go`) | ✅ | ✅ | ❌ |
| Stop Tasks (`/stop`) | ✅ | ✅ | ❌ |
| Halt Agent (`/halt`) | ✅ | ✅ | ❌ |
| Agent Status | ✅ Rich | ✅ Text | ✅ Basic |
| Task List | ✅ Panel | ✅ Text | ✅ Basic |
| DevPlan View | ✅ Panel | ✅ Text | ✅ Basic |
| Token Stats | ✅ Panel | ✅ Status | ✅ Status |
| Settings | ✅ Modal | ✅ Menu | ✅ Menu |
| Files Browser | ✅ Modal | ✅ Tree | ✅ Tree |
| API Provider | ✅ | ✅ | ✅ |
| Username | ✅ | ✅ | ✅ |
| Load History | ✅ | ✅ | Always |

## CLI Commands

```
/help         - Show help
/agents       - List active agents
/spawn <role> - Spawn new agent
/roles        - List available roles
/status       - Show swarm status
/tasks        - Show task list
/plan         - Show devplan/master plan
/files        - Show project files
/stop         - Stop all in-progress tasks
/halt <name>  - Halt a specific agent
/settings     - Open settings menu
/name <n>     - Set your display name
/api          - View/change API provider
/clear        - Clear chat history
/project      - Show current project
/quit         - Exit

go            - Dispatch next task (devussy mode)
```

## SessionController API

```python
class SessionController:
    # Initialization
    async def initialize(project, username, load_history, devussy_mode)
    async def shutdown()
    
    # User Actions
    async def send_message(text: str) -> List[Message]
    async def run_round() -> List[Message]
    async def handle_go_command() -> bool
    async def spawn_agent(role: str) -> Optional[Agent]
    async def stop_current() -> int
    async def halt_agent(agent_name: str) -> bool
    
    # State Queries
    def get_status() -> Dict
    def get_agents() -> List[Dict]
    def get_tasks() -> List[Dict]
    def get_devplan_summary() -> str
    def get_token_stats() -> Dict
    def get_available_roles() -> List[str]
    
    # Callbacks
    on_message: Callable[[Message], None]
    on_status: Callable[[str], None]
    
    # Properties
    @property project, username, chatroom, is_devussy_mode, is_processing
```

## Manual Test Plan

### TUI Mode Smoke Test
```bash
python main.py --tui
```
1. Select or create a project
2. Choose devussy (y/n) or use existing plan
3. Enter username
4. Dashboard should appear
5. Type a message and press Enter
6. Verify agents respond
7. Type `go` to dispatch tasks (if devussy mode)
8. Use Ctrl+S for settings
9. Use Ctrl+Q to quit

### CLI Mode Smoke Test
```bash
python main.py --cli
```
1. Select or create a project
2. Choose devussy (y/n)
3. Enter username
4. CLI header should appear
5. Type `/help` - see commands
6. Type `/agents` - see agent list
7. Type `/status` - see swarm status
8. Type `go` - dispatch task (if devussy mode)
9. Type `/tasks` - see task list
10. Type `/plan` - see devplan
11. Type `/quit` - clean exit

## Known Limitations

1. **CLI doesn't have real-time panels** - Agent status updates are shown as text, not live-updating panels
2. **No API log in CLI** - TUI shows expandable request/response history
3. **No file browser modal in CLI** - Uses simple tree printout
4. **Settings are menu-based in CLI** - TUI uses tabbed modal

## Future Work

1. **Wire TUI to SessionController** - Currently TUI uses its own chatroom wiring; could migrate to use SessionController for consistency
2. **Add `/model` command to CLI** - Runtime model changes per agent
3. **Add `/snapshot` command to CLI** - Project snapshots
4. **Rich text formatting in CLI** - Use Rich library for better formatting

## Running Tests

```bash
# Run session controller tests
python -m pytest tests/test_session_controller.py -v

# Run all tests
python -m pytest tests/ -v
```
