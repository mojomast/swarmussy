# Multi-Agent AI Swarm

A multi-agent AI development system where specialized AI agents collaborate to build software projects. Features an Architect who orchestrates a swarm of developers, testers, and other specialists.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **11 Specialized AI Agents** - Architect plus 10 specialists (backend, frontend, QA, DevOps, PM, Tech Writer, DB specialist, API designer, code reviewer, research)
- **True Orchestration** - Architect delegates, workers execute (no micromanagement). Only the Architect speaks directly to you; worker agents report status and results back to the Architect.
- **One-Task-Per-Worker Enforcement** - Task assignment pipeline ensures each worker has at most one active task; new assignments are rejected with a clear status message until `complete_my_task()` is called.
- **Role-Based Tools** - Architect + Project Manager get orchestration tools, workers get coding tools
- **Live DevPlan + Dashboard Pair**  - `scratch/shared/devplan.md` is the Architect's internal tracker; `scratch/shared/dashboard.md` is an auto-generated, user-facing view of in-progress work, what's next, and blockers
- **Devussy DevPlan Integration (Optional)** - Generate swarm-ready devplans, phase files, and task queues, then safely resume partially-completed phases using the Architect's resume logic and dashboard recovery helpers.
- **Rich Terminal Dashboard** - Real-time view of agents, tasks, tokens, tools, and activity
- **Persistent Settings** - Preferences saved between sessions
- **Multi-Project Support** - Isolated workspaces for each project
- **History Control** - Optional "Load previous messages?" prompt per project so you can start from a clean slate or resume prior context
- **Per-Agent Models** - Use `/model <agent> <model>` in the TUI to override models for specific agents at runtime
- **Snapshots** - `/snapshot [label]` copies the entire project workspace into a timestamped `snapshots/` folder for safe checkpoints
- **Protected DevPlan Ownership** - Only Bossy McArchitect can edit `devplan.md` and `master_plan.md`; workers and Checky request changes which the Architect applies
- **Team Logs** - Shared `scratch/shared/decisions.md` and `scratch/shared/team_log.md` capture decisions, milestones, and major swarm events
- **Floating File Browser** - Press `Ctrl+F` (or click `📁 FILES` in the TUI header) to browse the current project's tree and preview files
- **Context-Aware Auto Orchestrator** - Auto-resumes work when all tasks complete and handles long-context handoffs when a single call nears ~80k tokens
- **Context & Collaboration Tools** - `get_context_summary`, `list_agents`, `delegate_subtask`, `create_checkpoint`, and `get_recent_changes` keep workers aligned and reduce duplicate effort
- **Pluggable API Providers** - Use Requesty (default), Z.AI, OpenAI, or a custom endpoint, and optionally spoof the tool identifier (e.g. Claude Code, Cursor, Windsurf) via the Settings → API tab
- **Git-Aware Local Workflow** - Agents can inspect `git status`/`git diff` for the active project's `scratch/shared` workspace; Checky McManager and Deployo McOps can run a safe, local `git_commit` (no pushes) after review
- **Skeptical QA Gate for Commits** - Bugsy McTester reviews changes and tests, emitting `QA DECISION: APPROVED` / `REQUEST_CHANGES`; Checky only commits when QA has approved the scope
- **Singleton Workers per Role** - Architect reuses a single Codey/Pixel/Bugsy/Deployo/Checky/Docy per project to avoid multiple workers trampling the same files

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
| **Schema McDatabase** | Database Specialist | DB schema design, migrations, queries |
| **Swagger McEndpoint** | API Designer | API design, OpenAPI specs, contract definition |
| **Nitpick McReviewer** | Code Reviewer | Code quality, refactoring, best practices |
| **Googly McResearch** | Researcher | Patterns, best practices, technical research |

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
3. The Architect creates a master plan in `scratch/shared/master_plan.md` and an internal devplan tracker in `scratch/shared/devplan.md`; once tasks exist, the dashboard panel shows a user-facing snapshot from `scratch/shared/dashboard.md`
4. Review the plan/devplan and say "Go" to proceed

### Phase 2: Execution
1. Architect spawns workers (backend_dev, frontend_dev, etc.) and ensures Checky McManager (Project Manager) is in the swarm
2. Architect assigns specific tasks to each worker
3. Workers write code to `scratch/shared/` using their tools
4. Architect and Checky monitor progress via `get_swarm_state()` and keep `devplan.md` (Architect-only) and the user-facing `dashboard.md` up to date using `update_devplan_dashboard`

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
| `/tasks` | View tasks (Ctrl+T) |
| `/files` | Browse project files (Ctrl+F) |
| `/stop` | Stop current task (Ctrl+X) |
| `/plan` | Refresh the dashboard panel from disk (Ctrl+P) |
| `/devplan` | Print the raw `devplan.md` (Architect's internal tracker) into chat |
| `/spawn <role>` | Spawn a new agent |
| `/model [<agent> <model>]` | List agent models or set a specific agent's model in the running swarm |
| `/status` | Show swarm status summary |
| `/snapshot [label]` | Snapshot the current project folder into `projects/snapshots/` |
| `/api [base_url api_key]` | View or change API provider/base URL and key |
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
| `Ctrl+P` | Refresh DevPlan panel |
| `Ctrl+F` | Open File Browser |
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

**Center Column:**
- A collapsible **In-Flight Requests** bar at the top (up to ~1/3 of the center column), showing current API calls; each entry is clickable to expand details.
- Main chat log with word-wrapped messages beneath the in-flight section
- Input box for commands and messages at the bottom

**Right Column:**
- Token usage panel (totals and per-agent breakdown)
- Tool calls panel (real-time tool activity)
- DevPlan panel (user-facing `dashboard.md`; the Architect-only `devplan.md` and `master_plan.md` live alongside it in `scratch/shared/`)
- A collapsible **API History** panel anchored to the bottom-right, taking roughly one-third of the right column height and listing completed/error API calls with multi-level expansion (collapsed → summary → full request/response + tool calls)
- `📁 FILES` button and `Ctrl+F` shortcut open a floating file browser with project tree and read-only file preview

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
- `read_file`, `write_file` - Maintain status/reporting artifacts (e.g. `status_report.md`, `blockers.md`, `timeline.md`, `decisions.md`, `team_log.md`)
- `get_git_status`, `get_git_diff` - Read-only view of git state/diff for the active project's `scratch/shared` workspace
- `git_commit` - Stage and commit changes under the active project's `scratch/shared` tree (never pushes; human owns remotes/PRs)

**Worker Tools** (Backend/Frontend/QA/DevOps/Tech Writer):
- `read_file`, `write_file`, `edit_file`, `append_file` - Code and content operations
- `list_files`, `search_code` - Navigation and search
- `run_command` - Safe shell commands (linting, tests, git status, etc.)
- `get_git_status`, `get_git_diff` - Read-only inspection of git state/diff for the active project's workspace
- `claim_file`, `release_file`, `get_file_locks` - File locking for concurrent edits
- `get_project_structure` - High-level project tree

Architect ownership of `devplan.md` and `master_plan.md` is enforced at the tool layer: non‑Architect agents can read these files but cannot modify, move, or delete them, and must instead describe desired changes for Bossy to apply.

Additionally, git operations are constrained:
- All git tools run from the repo root but are **scoped to the active project's `scratch/shared` workspace`**.
- Only Checky McManager and Deployo McOps may call `git_commit`, and the swarm **never** pushes to remotes.

### Conversation & Git Workflow

1. You send a message → **only Bossy McArchitect responds directly to you**.
2. Architect spawns workers (one per core role) and assigns tasks.
3. Workers execute tasks (with configurable tool call depth, default 250) and log progress/results back to the Architect and Checky (not to the human user).
4. Bugsy McTester reviews code and tests, then records a clear `QA DECISION: APPROVED` or `REQUEST_CHANGES`.
5. At phase boundaries, Checky McManager inspects git status/diff and, **only when QA is APPROVED**, calls `git_commit` to checkpoint the current project workspace.
6. Architect reviews worker/PM/QA output, responds to you, and assigns the next batch of tasks.
7. Repeat until the project is complete.

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
| `max_tokens` | `16000` | Max tokens per response (workers can still request up to 32k when using tools) |
| `temperature` | `0.8` | Response creativity (0-1) |
| `max_tool_depth` | `250` | Max consecutive tool calls per turn |
| `load_previous_history` | `true` | Whether to load prior chat history on TUI startup (prompted at project selection) |

Additional provider-related settings (managed via the Settings → Models/API tabs):

- `default_provider`, `architect_provider`, `swarm_provider` – which backend to use (`requesty`, `zai`, `openai`, or `custom`)
- `api_base_url`, `api_key`, `zai_api_key` – override base URL and keys when not using Requesty defaults
- `tool_identifier`, `custom_tool_id` – control the `User-Agent`/tool identity sent with API calls so you can experiment with behaving like other coding tools

## Token Tracking

The dashboard shows real-time token usage:
- Prompt tokens (input)
- Completion tokens (output)
- Total tokens
- API call count

Token totals are cumulative for the lifetime of the current TUI session (they do not reset per task or round), so long-running swarms can easily reach millions of tokens. Per-agent rows show each agent's cumulative share, which may look similar when all workers share the same long context.

Use `/dashboard` to see a snapshot anytime.

## Logging

Logs are saved under `logs/` (e.g. `dashboard_YYYYMMDD_HHMMSS.log` for the legacy Rich dashboard and `tui_YYYYMMDD_HHMMSS.log` for the Textual TUI) with:
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
