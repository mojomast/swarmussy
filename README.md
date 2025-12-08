# Multi-Agent AI Swarm

A multi-agent AI development system where specialized AI agents collaborate to build software projects. Features an Architect who orchestrates a swarm of developers, testers, and other specialists.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **7 Specialized AI Agents** - Each with distinct roles and personalities
- **True Orchestration** - Architect delegates, workers execute (no micromanagement). Only the Architect speaks directly to you; worker agents report status and results back to the Architect.
- **Role-Based Tools** - Architect + Project Manager get orchestration tools, workers get coding tools
- **Live DevPlan Dashboard** - `scratch/shared/devplan.md` shows per-agent tasks, checkboxes, and blockers kept in sync with swarm state
- **Rich Terminal Dashboard** - Real-time view of agents, tasks, tokens, tools, and activity
- **Persistent Settings** - Preferences saved between sessions
- **Multi-Project Support** - Isolated workspaces for each project
- **History Control** - Optional "Load previous messages?" prompt per project so you can start from a clean slate or resume prior context
- **Per-Agent Models** - Use `/model <agent> <model>` in the TUI to override models for specific agents at runtime
- **Snapshots** - `/snapshot [label]` copies the entire project workspace into a timestamped `snapshots/` folder for safe checkpoints
- **Protected DevPlan Ownership** - Only Bossy McArchitect can edit `devplan.md` and `master_plan.md`; workers and Checky request changes which the Architect applies
- **Team Logs** - Shared `scratch/shared/decisions.md` and `scratch/shared/team_log.md` capture decisions, milestones, and major swarm events

## Agent Roster

| Agent | Role | Specialty |
|-------|------|-----------|
| **Bossy McArchitect** | Lead Architect | System design, task orchestration (DELEGATES, doesn't code) |
| **Codey McBackend** | Backend Dev | APIs, databases, server logic |
| **Pixel McFrontend** | Frontend Dev | UI/UX, React, web components |
| **Bugsy McTester** | QA Engineer | Testing, security, code review |
| **Deployo McOps** | DevOps | CI/CD, Docker, infrastructure |
| **Checky McManager** | Project Manager | Progress tracking, status reports |
| **Docy McWriter** | Tech Writer | Documentation, API docs, guides |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your REQUESTY_API_KEY

# Run the Textual TUI dashboard (recommended)
python main.py --tui

# Or run the Rich dashboard (legacy)
python main.py

# Or run the basic CLI
python main.py --cli
```

## How It Works

### Phase 1: Planning
1. Start the dashboard, select your project and username, and choose whether to load previous messages – only the Architect joins initially
2. Describe your project to the Architect
3. The Architect creates a master plan in `scratch/shared/master_plan.md` and an initial DevPlan dashboard in `scratch/shared/devplan.md` (checklist with owners and blockers)
4. Review the plan/devplan and say "Go" to proceed

### Phase 2: Execution
1. Architect spawns workers (backend_dev, frontend_dev, etc.) and ensures Checky McManager (Project Manager) is in the swarm
2. Architect assigns specific tasks to each worker
3. Workers write code to `scratch/shared/` using their tools
4. Architect and Checky monitor progress via `get_swarm_state()` and keep `devplan.md` and status files up to date

### Phase 3: Delivery
1. QA reviews and tests the code
2. Tech Writer creates documentation
3. DevOps creates deployment configs
4. All artifacts are in `scratch/shared/`

## Dashboard Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/settings` | Open settings screen (Ctrl+S) |
| `/agents` | Configure agents (Ctrl+A) |
| `/tasks` | View/control tasks (Ctrl+T) |
| `/stop` | Stop current task (Ctrl+X) |
| `/plan` | Refresh the DevPlan panel from disk (Ctrl+P) |
| `/fix <reason>` | Stop and request a fix |
| `/spawn <role>` | Spawn a new agent |
| `/status` | Show swarm status |
| `/model [<agent> <model>]` | List agent models or set a specific agent's model in the running swarm |
| `/snapshot [label]` | Snapshot the current project folder into `projects/snapshots/` |
| `/clear` | Clear chat history |
| `/quit` | Exit (Ctrl+Q) |

## Keyboard Shortcuts (TUI Mode)

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Open Settings |
| `Ctrl+A` | Focus Agents panel |
| `Ctrl+Up` | Scroll Agents up |
| `Ctrl+Down` | Scroll Agents down |
| `Ctrl+T` | Task Control |
| `Ctrl+X` | Stop Current Task |
| `Ctrl+R` | Refresh Panels |
| `Ctrl+Q` | Quit |
| `F1` | Show Help |

## Display Modes

- **TUI Mode** (`--tui`, recommended) - Full Textual dashboard with panels, settings screens, API logging, and task control
- **Rich Mode** (default) - Rich terminal dashboard with live updates
- **CLI Mode** (`--cli`) - Basic scrolling chat interface

## TUI Dashboard Layout

The Textual TUI (`--tui`) features a 3-column layout:

**Left Column:**
- Agent cards with a compact 2‑line summary (tokens, current action, task, latest tool) that expand on click for full history; right‑click a card to halt that agent and prompt the Architect to adjust the plan
- Scrollable AGENTS panel for large swarms (`Ctrl+A` to focus, then `Ctrl+Up` / `Ctrl+Down` to scroll when many agents are present)
- API Log panel with real-time request/response tracking (timestamps, elapsed time, token counts, input/output previews)

**Center Column:**
- Main chat log with word-wrapped messages
- Input box for commands and messages

**Right Column:**
- Token usage panel (totals and per-agent breakdown)
- Tool calls panel (real-time tool activity)
- DevPlan panel (scrollable `devplan.md` dashboard with master plan and todo view)

## API Activity Pulse (TUI)

In TUI mode the header subtitle shows a compact API status pulse so you can see when the swarm is talking to the API:

- `API ○ idle` – no active calls
- `API ↑ req` – a request is in flight
- `API ↓ resp` – a response just arrived
- `API × err` – an error occurred

The pulse automatically returns to `idle` after a short delay.

## Architecture

### Tool Separation

The system uses role-based tool access to enforce proper orchestration:

**Orchestrator Tools** (Bossy McArchitect only):
- `spawn_worker` - Bring in team members
- `create_task` - Create tasks in the central TaskManager
- `assign_task` - Delegate work to workers and mark tasks in progress
- `get_swarm_state` - Check agent/task status
- `update_devplan_dashboard` - Regenerate the live DevPlan dashboard from swarm state
- `read_file`, `write_file` - For planning artifacts (e.g. `master_plan.md`, `devplan.md`) only
- `list_files`, `get_project_structure` - Project navigation

**Project Manager Tools** (Checky McManager):
- `get_swarm_state` - Inspect current agents and tasks
- `create_task`, `update_task_status` - Manage tasks and blockers
- `read_file`, `write_file` - Maintain status/reporting artifacts (e.g. `status_report.md`, `blockers.md`, `timeline.md`, `decisions.md`)

**Worker Tools** (Backend/Frontend/QA/DevOps/Tech Writer):
- `read_file`, `write_file`, `edit_file`, `append_file` - Code and content operations
- `list_files`, `search_code` - Navigation and search
- `run_command` - Safe shell commands (linting, tests, git status, etc.)
- `claim_file`, `release_file`, `get_file_locks` - File locking for concurrent edits
- `get_project_structure` - High-level project tree

Architect ownership of `devplan.md` and `master_plan.md` is enforced at the tool layer: non‑Architect agents can read these files but cannot modify, move, or delete them, and must instead describe desired changes for Bossy to apply.

### Conversation Flow

1. You send a message → **only Bossy McArchitect responds directly to you**.
2. Architect spawns workers and assigns tasks.
3. Workers execute tasks (with configurable tool call depth, default 250) and log progress/results back to the Architect and Checky (not to the human user).
4. Architect reviews worker/PM output and responds to you or assigns next tasks.
5. Repeat until the project is complete.

### Tool Call Depth

Agents can chain multiple tool calls when working on complex tasks. The default limit is 250 consecutive tool calls, configurable in Settings → Advanced → Max Tool Depth. This allows agents to:
- Write multiple files in sequence
- Read, modify, and save files
- Create folder structures
- Run commands and process results

If an agent hits the limit, they'll pause and ask you to continue.

## Project Structure

```
zaiswarmchat/
├── agents/                 # AI agent implementations
│   ├── architect.py        # Orchestrator (delegates only)
│   ├── backend_dev.py      # Codey McBackend
│   ├── frontend_dev.py     # Pixel McFrontend
│   └── ...
├── core/                   # Core functionality
│   ├── chatroom.py         # Conversation orchestration
│   ├── agent_tools.py      # Tool definitions & execution
│   ├── project_manager.py  # Multi-project support
│   ├── task_manager.py     # Task tracking
│   ├── settings_manager.py # Persistent settings
│   └── token_tracker.py    # API usage tracking
├── projects/               # Project workspaces
│   └── <project_name>/
│       ├── scratch/shared/ # Agent output files
│       └── data/           # Memory & history
├── logs/                   # Session logs
├── main.py                 # CLI entry point
├── dashboard.py            # Rich terminal UI
└── requirements.txt
```

## Configuration

Settings in `data/settings.json` (also accessible via Ctrl+S in TUI):

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_chat` | `true` | Auto-trigger architect on project load |
| `tools_enabled` | `true` | Enable agent tool usage |
| `default_model` | `openai/gpt-5-nano` | Default LLM model |
| `architect_model` | `openai/gpt-5-nano` | Model for Architect |
| `swarm_model` | `openai/gpt-5-nano` | Model for worker agents |
| `agent_models` | `{}` | Optional per-agent model overrides keyed by agent name, managed via `/model` |
| `max_tokens` | `100000` | Max tokens per response |
| `temperature` | `0.8` | Response creativity (0-1) |
| `max_tool_depth` | `250` | Max consecutive tool calls per turn |
| `load_previous_history` | `true` | Whether to load prior chat history on TUI startup (prompted at project selection) |

## Token Tracking

The dashboard shows real-time token usage:
- Prompt tokens (input)
- Completion tokens (output)
- Total tokens
- API call count

Use `/dashboard` to see a snapshot anytime.

## Logging

Logs are saved to `logs/dashboard_YYYYMMDD_HHMMSS.log` with:
- API requests/responses
- Tool calls and results
- Agent status changes
- Error details

## Requirements

- Python 3.9+
- Requesty API key (get one at https://requesty.ai)
- Rich library for terminal UI

## License

MIT License
