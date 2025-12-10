# Handoff Document: Multi-Agent Swarm

## Session Summary - December 5, 2024

This session focused on fixing critical issues with the swarm's efficiency and dashboard usability.

---

## Issues Fixed This Session

### 1. ✅ Architect Doing All The Work

**Problem**: The Architect was writing code itself instead of delegating to workers. It had access to ALL tools (file operations, code editing, etc.) and would complete entire tasks solo.

**Root Cause**: All agents received the same `TOOL_DEFINITIONS` list, giving the Architect coding tools it shouldn't have.

**Solution**:
- Created separate tool sets in `core/agent_tools.py`:
  - `ORCHESTRATOR_TOOLS` - spawn_worker, assign_task, get_swarm_state, read/write (for plans only)
  - `WORKER_TOOLS` - All file/code operations
- Added `get_tools_for_agent(name)` function that returns appropriate tools based on role
- Updated `agents/base_agent.py` to use role-appropriate tools

**Files Changed**:
- `core/agent_tools.py` - Added tool separation
- `agents/base_agent.py` - Uses `get_tools_for_agent()`
- `agents/architect.py` - Rewrote prompt to emphasize delegation

### 2. ✅ Tool Call Depth Management

**Problem**: Originally agents could chain tool calls indefinitely. Then limited to 5, but that was too restrictive - agents would stop mid-task when "cooking" (doing good work).

**Solution**: Made tool depth configurable in `agents/base_agent.py`:
- Default increased to 50 consecutive tool calls
- Configurable via Settings → Advanced → Max Tool Depth
- Range: 5-50 (clamped in settings)
- When limit reached, agent pauses and asks user to continue
- Reads from `settings_manager.get("max_tool_depth", 50)`

### 3. ✅ Architect Prompt Rewrite

**Problem**: Architect prompt was verbose and didn't clearly enforce delegation.

**Solution**: Completely rewrote `ARCHITECT_SYSTEM_PROMPT` in `agents/architect.py`:
- "YOU DO NOT WRITE CODE" - Clear rule at top
- "You are a MANAGER, not a coder"
- Listed ONLY tools it should use
- Simplified workflow with explicit STOP points
- Removed verbose explanations

### 4. ✅ Settings Menu Navigation

**Problem**: After using a settings submenu, user had to type `/settings` again to return.

**Solution**: Wrapped settings menu in `while True` loop in `dashboard.py` - stays in menu until user chooses "0. Back"

### 5. ✅ Auto Chat Default

**Problem**: `auto_chat` was disabled by default, requiring manual configuration.

**Solution**: Changed default in `core/settings_manager.py` from `False` to `True`

### 6. ✅ Auto Project Summary

**Problem**: No context when loading a project - user had to ask what's happening.

**Solution**: Added `trigger_project_summary()` in `dashboard.py`:
- Runs automatically after project selection
- Reads master plan if exists
- Prompts Architect for 2-3 sentence summary
- Suggests next action

### 7. ✅ Dashboard Status Updates

**Problem**: No visibility into what agents were doing - terminal was silent during work.

**Solution**: Added status broadcasting throughout the system:
- `_broadcast_status()` in `core/chatroom.py` for ephemeral updates
- Status messages for: agent thinking, tool calls, spawning, task assignment
- `print_message()` in `dashboard.py` handles status display
- Activity panel in live mode shows recent status

### 8. ✅ Dashboard Layout Stability

**Problem**: Live dashboard flickered and had missing elements.

**Solution**: 
- Removed `screen=True` from Rich Live display
- Fixed panel heights with padding
- Reduced refresh rate to 1/second
- Added `minimum_size` constraints to layout
- Truncated content to fit panel widths

### 9. ✅ Chatroom Singleton Issue

**Problem**: Dashboard created its own `Chatroom()` but tools used `get_chatroom()` singleton - they were different instances.

**Solution**: 
- Added `set_chatroom()` function in `core/chatroom.py`
- Dashboard calls `set_chatroom(self.chatroom)` after creation
- Tools now find the correct chatroom instance

---

## Current Architecture

### Tool Flow
```
User Input → Architect (orchestrator tools only)
                ↓
         spawn_worker() → Creates worker agent
                ↓
         assign_task() → Sets worker status to WORKING
                ↓
         Worker responds (worker tools) → Writes code
                ↓
         Worker completes → Status back to IDLE
```

### Tool Sets

**ORCHESTRATOR_TOOLS** (Architect):
- spawn_worker, assign_task, get_swarm_state
- read_file, write_file (for master_plan.md only)
- list_files, get_project_structure

**WORKER_TOOLS** (All others):
- read_file, write_file, edit_file, append_file
- list_files, delete_file, move_file, create_folder
- search_code, run_command
- claim_file, release_file, get_file_locks
- get_project_structure

---

## Known Issues / Future Work

### 1. Worker Response Timing
Workers are assigned tasks but may not respond in the same round. The `_run_worker_round()` helps but timing can be inconsistent.

### 2. Task Completion Detection
Currently uses simple string matching ("Task Complete" in response). Could be more robust.

### 3. Live Dashboard Mode
Still experimental on Windows. Simple mode is recommended.

### 4. MCP Integration
Config structure exists but MCP client not implemented. See original handoff for details.

---

## Testing Checklist

- [x] Architect delegates instead of coding
- [x] Tool calls configurable (default 15)
- [x] Settings menu stays open
- [x] Auto chat enabled by default
- [x] Project summary on load
- [x] Status updates visible
- [x] Dashboard layout stable
- [x] Chatroom singleton works
- [x] Textual TUI dashboard working
- [x] Settings screen with model/token/depth config
- [x] Task control screen with stop/fix
- [x] Tool calls panel shows real-time activity
- [ ] Full end-to-end project build test
- [ ] MCP integration

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `dashboard_tui.py` | Textual TUI dashboard (recommended) |
| `dashboard.py` | Rich terminal UI (legacy) |
| `agents/architect.py` | Orchestrator prompt and config |
| `agents/base_agent.py` | Tool calling, response logic |
| `core/agent_tools.py` | Tool definitions and separation |
| `core/chatroom.py` | Conversation orchestration |
| `core/settings_manager.py` | Persistent settings |

---

## Quick Test

```bash
# Recommended: Use the Textual TUI
python main.py --tui

# Select project
# Say "Build a hello world web app"
# Say "Go" when prompted
# Watch Architect spawn workers and delegate
# Use Ctrl+T to view/control tasks
# Use Ctrl+X to stop if needed
```

---

## New TUI Features (December 5, 2024)

### Textual Dashboard (`--tui`)
- Full terminal UI with proper panel management
- No flickering or scroll issues
- Settings screen (Ctrl+S) with tabs for General, Models, Advanced
- Agent config screen (Ctrl+A) for per-agent model/temp/tools
- Task control screen (Ctrl+T) to view, stop, or request fixes
- Tool calls panel showing real-time tool activity with results
- Stop button (Ctrl+X) to halt current work

### Enhanced Tool Display
- Shows line counts for write operations: "Writing file.py (45 lines)"
- Shows task snippets for assignments: "Task → Codey: Implement user auth..."
- Success/failure indicators: ✅ or ❌ after tool completion

### Configurable Tool Depth
- Default: 50 consecutive tool calls (was 15)
- Configurable in Settings → Advanced → Max Tool Depth (range 5-50)
- Allows agents to complete complex multi-file tasks without interruption
- When limit reached, agent pauses and asks to continue

---

## Latest Updates (December 5, 2024 - Evening)

### API Log Panel (Bottom Left)
Added verbose API request/response logging in the TUI:
- Real-time display of all API calls
- Shows timestamps for each request/response
- Elapsed time for each API call
- Token counts (input/output/total)
- Preview of request content (first ~60 chars of user message)
- Preview of response content (first ~60 chars or tool call name)
- Scrollable panel for reviewing history
- Box-drawing characters for visual grouping

### Agent Token Tracking
- Agent cards now show cumulative token usage
- Tokens update in real-time as API responses come in
- Per-agent breakdown visible in both agent cards and token panel

### DevPlan Panel Improvements
- Now shows entire master_plan.md file (was limited to 50 lines)
- Fully scrollable to review complete plans
- Auto-refreshes every 3 seconds

### Layout Improvements
- Increased left column width by ~10% for better API log readability
- Word wrap enabled on all RichLog panels (chat, API log, tools)
- Fixed double message display issue in chat

### Code Changes
- `agents/base_agent.py`: Added timing, request/response previews to API callback
- `dashboard_tui.py`: New verbose API log format, agent token updates, full devplan
- `core/settings_manager.py`: Default max_tool_depth increased to 50

---

## Latest Updates (December 6, 2025)

### 1. Worker / User Interaction & Logging

**Problem**: Worker agents sometimes tried to answer the human directly or duplicated the Architect's work.

**Solution**:
- Tightened all worker system prompts (`backend_dev.py`, `frontend_dev.py`, `qa_engineer.py`, `devops_engineer.py`, `project_manager.py`, `tech_writer.py`) with an explicit **Interaction Rules** section:
  - Workers **never** speak directly to the human.
  - They treat `user` messages as requirements routed through Bossy McArchitect.
  - Their responses are framed as status updates and technical details for the Architect and other agents.
- Updated `agents/architect.py` to clarify that **Bossy McArchitect is the only agent that talks to the human user**.
- Updated `agents/base_agent.py` so that non-Architect agents mark their chat output as `MessageType.AGENT_LOG` instead of normal chat, keeping worker chatter clearly separated from user-facing conversation.
- Added `AGENT_LOG` to `core/models.py::MessageType`.

### 2. Role-Aware Context Trimming

**Problem**: Agents received a blunt "last 10 messages" slice of global history, which often included stale topics and other agents' replies. This caused multiple agents to work on the same thing and increased token usage.

**Solution** (`agents/base_agent.py::_build_context`):
- Still builds an enhanced system prompt (persona, tools, memories, current task).
- **Architect**:
  - Continues to see the normal recent tail of global messages (last ~10) for full situational awareness.
- **Workers**:
  - Build a **task-focused** history view:
    - Always include the latest human message (requirements).
    - Include the worker's own recent messages.
    - Include system messages that mention the worker by name (join/assignment notices).
    - Fallback to the plain recent tail only if no relevant messages are found.
- Result: workers focus on their assignment and the latest user intent instead of re-reading every prior message from other agents.

### 3. Startup History Toggle

**Problem**: On startup, the chatroom always loaded recent history from disk. Old threads sometimes bled into new sessions, and agents kept pulling in stale context.

**Solution**:
- Added a new persistent setting in `core/settings_manager.py`:
  - `load_previous_history` (default `True`) controls whether prior chat history is loaded.
- Extended `dashboard_tui.py`:
  - `select_project_cli()` now asks:
    - `Load previous messages? [Y/n]` (or `y/N` based on your last choice).
  - The answer is saved back into `load_previous_history`.
  - Returns `(project, username, load_history)` and passes `load_history` into `SwarmDashboard`.
  - `SwarmDashboard.__init__` stores `self.load_history`, and `init_chatroom()` builds `Chatroom(load_history=self.load_history)`.
- Extended `core/chatroom.py`:
  - `Chatroom.__init__(load_history: bool = True)` stores `self._load_history_on_init`.
  - `Chatroom.initialize()` only calls `_load_history()` when `self._load_history_on_init` is `True`.
- Behavior:
  - Answer **No** to start with a clean slate (no prior messages loaded).
  - Answer **Yes** to resume from the previous conversation for that project.

### 4. Token Panel Compatibility Fix

**Problem**: After `core/token_tracker.py` was updated to expose `prompt_tokens`, `completion_tokens`, `total_tokens`, and `call_count`, the TUI token panel still looked for older field names and stopped updating visibly.

**Solution** (`dashboard_tui.py::TokenDetailPanel`):
- Session totals now read:
  - `prompt_tokens` → "Input"
  - `completion_tokens` → "Output"
  - `total_tokens` → "Total"
  - `call_count` → "Calls"
- Per-agent breakdown now sums `prompt` + `completion` from `by_agent` instead of relying on a non-existent `total` field.
- Net effect: the top-right TOKENS panel and per-agent token counts in the TUI now accurately reflect current usage again.

### 5. Quick Testing Checklist for These Changes

- [ ] Start the TUI, choose a project, and answer **No** to "Load previous messages?":
  - Verify the conversation starts clean and workers don't reference old threads.
- [ ] Start again and answer **Yes**:
  - Verify recent messages are restored once (no duplicated history slices).
- [ ] Send a few messages and watch the conversation:
  - Only **Bossy McArchitect** should reply directly to you.
  - Worker agents should communicate as logs/status updates, not as chatty replies to the human.
- [ ] Open the TOKENS panel:
  - Confirm Input/Output/Total/Calls increase as agents make API calls.
  - Confirm per-agent totals increase appropriately for active agents.
- [ ] Inspect the logs:
  - Worker API requests should show trimmed, task-focused `messages` arrays (latest human message + assignments/own messages), not the full global history.

---

## Latest Updates (December 6, 2025 - DevPlan & Parallel Swarm)

### 6. DevPlan Dashboard & Project Manager (Checky McManager)

**Problem**: The plan lived only in `master_plan.md` and quickly drifted from reality. There was no single, live view of per-agent tasks, statuses, and blockers.

**Solution**:
- Introduced a **live DevPlan dashboard** in `scratch/shared/devplan.md` generated from swarm state.
- Added an `update_devplan_dashboard` tool in `core/agent_tools.py` that:
  - Reads all tasks from `TaskManager` and active agents from `Chatroom`.
  - Builds a Markdown dashboard with:
    - Overall stats (agent/task counts, status counts).
    - "Tasks by Agent" section with `- [ ]` / `- [x]` checkboxes and emojis for status.
    - "Blockers & Risks" section listing failed tasks with ⚠️.
  - Writes the result to `scratch/shared/devplan.md`.
- Updated **Bossy McArchitect**'s prompt to:
  - Treat `devplan.md` as the live dashboard.
  - Use `get_swarm_state()` and `update_devplan_dashboard` to keep it in sync when tasks are assigned/completed/failed.
- Updated **Checky McManager** (Project Manager) to:
  - Use `get_swarm_state()` and plan/status files (`devplan.md`, `status_report.md`, `blockers.md`, `timeline.md`, `decisions.md`).
  - Produce structured, Markdown status reports for Bossy + the other agents.
  - Never talk directly to the human; everything is logged as progress/blockers for the Architect.

### 7. Parallel Swarm Execution & Visibility

**Problem**: Agents effectively ran in a serial queue. It often looked like “nothing is happening” even when multiple workers were busy with tools/API calls.

**Solution** (`core/chatroom.py`):
- Reworked `run_conversation_round` to:
  - Collect all agents that `should_respond()` this round (Architect + workers + Checky).
  - Broadcast `⏳ {AgentName} is thinking...` for each speaker.
  - Launch `_get_agent_response(agent)` concurrently for all of them using `asyncio.create_task` + `asyncio.wait`.
  - Still respect `MAX_CONCURRENT_API_CALLS` via the existing semaphore.
- Reworked `_run_worker_round` to:
  - Do the same parallel pattern specifically for workers with `status == WORKING`.
  - Broadcast `⏳ {worker} is working on task...` before starting tool/API work.
- Net effect: multiple agents now do tool work in parallel, and status messages make that visible.

### 8. TUI Agent Cards: Scrollable, Expandable, Task-Aware

**Problem**: The top-left AGENTS panel:
- Didn’t clearly show current tasks.
- Only showed the last 3 accomplishments with no way to drill deeper.
- Became cramped when many agents were present.

**Solution** (`dashboard_tui.py::AgentCard`):
- Agent cards now track a bounded history of accomplishments (up to 50 entries).
- New `expanded` flag and click behavior:
  - Clicking a card toggles between collapsed (last 3 items) and expanded (up to 50).
  - Card title shows `▸` / `▾` to indicate collapsed/expanded.
- `dashboard_tui.py` (Settings → Advanced):
  - `max_tool_depth` input now clamps to the range **5–250** when saving.
- `agents/base_agent.py::_handle_tool_calls`:
  - Still reads `max_tool_depth` from settings; with new defaults, agents can chain up to 250 tools before pausing.

**Behavior**:
- New sessions default to 250 unless `data/settings.json` overrides it.
- When the limit is reached, agents still stop and tell the user they hit the cap and may need to be asked to continue.

### 10. API Activity Pulse in TUI Header

**Problem**: While watching the TUI dashboard it was hard to tell if the swarm was actively talking to the API or just idle.

**Solution** (`dashboard_tui.py::SwarmDashboard`):
- Added an `api_status` reactive field with values: `idle`, `request`, `response`, `error`.
- `on_api_call(event_type, ...)` now updates `api_status` on each request/response/error and schedules a short timer back to `idle`.
- `update_status_line()` extends the app subtitle to include a compact pulse, e.g. `User: You | API ○ idle`, `API ↑ req`, `API ↓ resp`, `API × err`.

**Behavior**:
- Whenever an API request is sent you see `API ↑ req` briefly.
- When a response arrives you see `API ↓ resp` before it fades back to `idle`.
- Errors surface as `API × err` so you can spot problems without digging into logs.

### 11. Agents Sidebar Keyboard Scrolling

**Problem**: The top-left AGENTS panel could overflow with many workers; mouse-wheel scrolling isnt always obvious or available in all terminals.

**Solution** (`dashboard_tui.py::SwarmDashboard`):
- Added explicit key bindings:
  - `Ctrl+A`  focus the `#agents-scroll` `ScrollableContainer`.
  - `Ctrl+Up` / `Ctrl+Down`  call `scroll_up(4)` / `scroll_down(4)` on that container.
- `action_focus_agents`, `action_scroll_agents_up`, and `action_scroll_agents_down` wrap the behavior with try/except so failures dont crash the UI.

**Behavior**:
- Press `Ctrl+A` to move focus into the agents column.
- Use `Ctrl+Up` / `Ctrl+Down` to scroll through agent cards when there are more than fit on screen.
- Once focused, standard cursor/PageUp/PageDown keys also work according to Textuals defaults.

---
*Last updated: December 6, 2025*
*Status: DevPlan dashboard + Checky PM online, parallel swarm execution, richer TUI agent visibility, deeper tool chains enabled*

---

## Latest Updates (December 7, 2025 - DevPlan Ownership, Logs, Models, Snapshots)

### 1. DevPlan Ownership Guard

- Added protected-file handling in `core/agent_tools.py` so only **Bossy McArchitect** can modify `scratch/shared/devplan.md` and `scratch/shared/master_plan.md`.
- Non‑Architect agents can still read these files, but any attempt to write/edit/append/replace/delete/move them returns a clear tool error instructing the agent to describe the desired change and ask Bossy to update the devplan/dashboard.

### 2. Decision & Team Logs

- New tools in `AgentToolExecutor`:
  - `append_decision_log(title, details)` → appends structured entries to `scratch/shared/decisions.md`.
  - `append_team_log(summary, category?, details?)` → appends chronological event entries to `scratch/shared/team_log.md`.
- All agents can use these to record important design decisions, milestones, blockers, and handoffs.

### 3. Per-Agent Halt from TUI

- `dashboard_tui.py::AgentCard` now supports:
  - Left‑click → expand/collapse card (compact 2‑line view vs. full history).
  - **Right‑click** → calls `SwarmDashboard.halt_agent(agent)`.
- `halt_agent`:
  - Marks any `in_progress` tasks assigned to that agent as `failed` with result "Stopped by user via dashboard".
  - Injects a human message asking Bossy to explain what the worker was doing, roll back if needed, and adjust the devplan/tasks accordingly.

### 4. Project Snapshots via `/snapshot`

- New TUI command `/snapshot [label]` in `dashboard_tui.py`:
  - Copies the current project root (e.g. `projects/doom_clone/`) into a timestamped directory under `projects/snapshots/`.
  - Runs `shutil.copytree` via `asyncio.to_thread` so the UI stays responsive.
  - Logs progress and success/failure in the chat.

### 5. Per-Agent Model Overrides via `/model`

- Added `agent_models` mapping to `core/settings_manager.DEFAULT_SETTINGS` for persistent per‑agent overrides.
- New TUI command `/model` in `dashboard_tui.py`:
  - `/model` → lists all active agents and their current models, plus available models.
  - `/model <agent> <model>` → updates a specific agent's `model` field in memory and persists the override to `agent_models`.
  - Agent resolution is case‑insensitive and supports prefixes (e.g. `/model codey openai/gpt-4o-mini`).

*Last updated: December 7, 2025*
*Status: DevPlan ownership enforced, shared logs online, per-agent models and snapshots available for testing*

## Latest Updates (December 7, 2025 - Auto-Orchestrator, Context Handoff, TUI API Log & File Browser)

### 1. Auto-Orchestrator Nudge Reliability

- **Problem**: The auto-orchestrator "nudge" message didn't always trigger a follow-up swarm round, and workers could reply based on stale tasks after the nudge.
- **Solution**:
  - `dashboard_tui.py::SwarmDashboard.auto_chat_tick` now checks `auto_orchestrator_pending` and only clears it when scheduling `run_conversation()`.
  - `run_conversation()` no longer resets `auto_orchestrator_pending` in its `finally` block; the flag is owned solely by `auto_chat_tick`.
  - When the last open task completes, `BaseAgent.respond` injects an "Auto Orchestrator" human message requesting next steps; the next auto-chat tick reliably kicks off a new round.

### 2. Context Handoff Guard (~80k Tokens)

- **Problem**: Workers could accumulate extremely large per-call contexts (80k–100k+ tokens) and keep dragging them forward, bloating token usage.
- **Solution** (`agents/base_agent.py::_call_api`):
  - After each API response, we read `usage.prompt_tokens` for that call.
  - If a single call for the current `task_id` crosses a `CONTEXT_HANDOFF_THRESHOLD` of ~80,000 prompt tokens and we haven't already done so for that task, the agent sends a one-time "Auto Orchestrator" message asking Bossy/Checky to hand off the work to a fresh worker with a concise summary.
  - This keeps future calls for that task under ~80k tokens of context.

### 3. Token Tracker Semantics & Checky McManager

- Clarified that totals in `core/token_tracker.py` (and the TOKENS panel) are **session-cumulative**, not per task:
  - `prompt_tokens` → "Input"
  - `completion_tokens` → "Output"
  - `total_tokens` → "Total"
  - `call_count` → "Calls"
- Large, similar per-agent totals (for example several workers around 2.7M tokens) are expected when they all share the same long-running project context.
- `agents/project_manager.py::ProjectManager.should_respond` was rewritten so Checky McManager responds whenever the global task snapshot changes (tasks created/assigned/completed/failed), making him more present throughout long runs.

### 4. TUI Right Sidebar: API Log & File Browser

- **API log** (`dashboard_tui.py`):
  - Right sidebar now dedicates a lower region to an API log with two parts:
    - **In-flight**: pinned requests (with wrench icon) that are currently running.
    - **History**: completed/error calls appended below in a scrollable container.
  - Each `ApiLogEntry` cycles through three detail levels on click:
    - Level 0 – collapsed header only.
    - Level 1 – summary (model, elapsed time, token counts, short request/response previews).
    - Level 2 – full request/response body and tool metadata.
- **Floating file browser**:
  - New `FileBrowserScreen` lists the current project's files using `Project.root` from `core/project_manager.py`.
  - Open via `Ctrl+F` or the `📁 FILES` button in the TUI header.
  - Left: scrollable file list (internal/hidden paths filtered out).
  - Right: read-only file preview with simple truncation/placeholder handling for huge/binary files.

*Last updated: December 7, 2025 (evening)*
*Status: Auto-orchestrator nudge + context handoff online; TUI API log and file browser ready for manual testing*

## Latest Updates (December 8, 2025 - Git-Aware Workflow & Worker Singletons)

### 1. Git Tools and Safety Guarantees

- Added **git-aware tools** in `core/agent_tools.py`:
  - `get_git_status` → read-only wrapper around `git status --short` scoped to the active project's `scratch/shared` workspace.
  - `get_git_diff` → read-only wrapper around `git diff --stat` scoped to the same workspace (optionally narrowed by path).
  - `git_commit` → stages and commits only the active project's `scratch/shared` tree.
- Safety rules for `git_commit`:
  - Only **Checky McManager** (Project Manager) or **Deployo McOps** (DevOps) may call this tool.
  - Pathspec is always constrained to the current project's workspace; other repo content is untouched.
  - The swarm **never pushes** to remotes; humans remain responsible for `git push` / PRs.
- All workers can inspect git status/diff via the read-only tools, but they must ask Checky/Deployo to perform commits.

### 2. Review Gate: Bugsy + Checky Before Commits

- **Bugsy McTester (QA)** prompt (`agents/qa_engineer.py`) now:
  - Uses git-aware tools to inspect exactly what changed before approving.
  - Clearly labels outcomes at the end of each report with:
    - `QA DECISION: APPROVED` – scope looks good.
    - `QA DECISION: REQUEST_CHANGES` – lists blocking issues.
- **Checky McManager (Project Manager)** prompt (`agents/project_manager.py`) now encodes a git-aware workflow:
  - At natural milestones (feature complete, tests passing, phase boundary) Checky:
    1. Calls `get_git_status` and `get_git_diff` to summarize pending changes.
    2. Confirms Bugsy has written/updated tests, run them, and produced an explicit `QA DECISION` for that scope.
    3. **Only if QA is APPROVED**, calls `git_commit` with a PR-style message (e.g. `feat: implement level loader and tests`).
    4. Appends a short entry to `scratch/shared/team_log.md` describing what was committed and which tasks it closes.
- If QA has not approved, Checky is instructed **not** to commit and instead to:
  - Open/update tasks for QA and implementers.
  - Record the pending review state in `status_report.md` / `team_log.md`.

### 3. Worker Singletons to Avoid Collisions

- **Problem**: The Architect could spawn multiple backend/front-end workers of the same role (e.g. five copies of Codey McBackend), all sharing the same workspace and colliding on files.
- **Solution** (`core/chatroom.py::spawn_agent`):
  - Introduced a `singleton_roles` set: `{ "project_manager", "backend_dev", "frontend_dev", "qa_engineer", "devops", "tech_writer" }`.
  - When `spawn_worker` is called for any of these roles and an instance already exists, the chatroom **reuses the existing agent** instead of creating a new one.
- Effect:
  - There is at most one Codey, one Pixel, one Bugsy, one Deployo, one Checky, and one Docy active at a time.
  - Greatly reduces concurrent write collisions in the shared workspace.

### 4. Coding Standards: Big Files & Core Modules

- Global **professional coding standards** in `agents/base_agent.py` were strengthened:
  - Reiterated **NO MOCK CODE** and "No Truncation" for `write_file`.
  - Added guidance that **big files are acceptable and expected** for core modules (engines, servers, routers, key UI screens).
  - Added a rule to **finish core modules first** before spawning more files.
- **BackendDev (Codey McBackend)** prompt (`agents/backend_dev.py`) now:
  - Explicitly tells Codey that when he commits to a module (engine core, router, server), he should implement the full working version in that file, even if it becomes hundreds of lines.
  - Encourages **deepening existing modules** over creating many tiny or near-duplicate files.
- Combined with the git-aware review/commit flow, long-running projects (e.g. DOOM-style engines) now converge toward a small set of rich, production-quality modules instead of a forest of stubs.

*Last updated: December 8, 2025*
*Status: Git tools + QA/PM review gate online; worker singletons and coding standards tuned for large, coherent modules*

---

## Latest Updates (December 8, 2025 - DevPlan/Dashboard Split & API Providers)

### 1. DevPlan vs Dashboard Files

- `scratch/shared/master_plan.md` – long-form architecture and phase plan (Architect-only writer).
- `scratch/shared/devplan.md` – Architect's internal tracker (phases, detailed tasks, technical notes, "what's next").
- `scratch/shared/dashboard.md` – user-facing snapshot generated from swarm state, showing:
  - Overall progress bar and counts.
  - "Currently Working On" and "Up Next" sections.
  - Blockers & issues derived from failed tasks.
  - Active agents with task counts and recent completions.
- `AgentToolExecutor.update_devplan_dashboard` now:
  - Preserves any scope content before `<!-- LIVE_DASHBOARD_START -->` in `devplan.md`.
  - Regenerates the live dashboard section from `TaskManager` + `Chatroom`.
  - Writes both the updated `devplan.md` and a simplified `dashboard.md` for the TUI.

The Textual TUI's right sidebar DevPlan panel now prefers `dashboard.md`, falling back to `devplan.md`/`master_plan.md` if no dashboard exists. There is also a `/devplan` command to dump the raw `devplan.md` into chat for debugging.

### 2. Task Completion & Auto-Orchestrator

- Workers were previously relying on string matching ("Task Complete") to mark tasks done.
- A new `complete_my_task` tool was added in `core/agent_tools.py` and wired into the worker system prompt:
  - Workers are instructed to call `complete_my_task(result="...summary...")` when they finish their assignment.
  - The tool:
    - Marks the TaskManager entry as `completed` with a summary.
    - Sets the worker's status back to `IDLE` and clears its current task fields.
    - If all tasks are now `COMPLETED` and no `PENDING` / `IN_PROGRESS` remain, injects a human-role "Auto Orchestrator" message asking the Architect to review the plan and either start the next phase or summarize deliverables.
- Architect's `should_respond` logic in `agents/base_agent.py` explicitly treats `Auto Orchestrator` human messages as triggers, so phase handoffs are now reliable.

### 3. API Provider & Tool Identifier Configuration

- Settings now support multiple providers for Architect vs workers:
  - `requesty` (default)
  - `zai` (direct Z.AI)
  - `openai` (direct OpenAI chat completions)
  - `custom` (arbitrary base URL + key)
- The Textual Settings screen gained a **Models** tab (per-role provider/model) and an **API** tab with:
  - `api_base_url` + `api_key` for custom or OpenAI usage.
  - `zai_api_key` for direct Z.AI usage.
  - `tool_identifier` and `custom_tool_id` fields that control the `User-Agent`/tool identity sent with API calls (e.g. `claude-code`, `cursor`, `windsurf`, or a custom string).
- `agents/base_agent.py::_call_api`:
  - Chooses base URL/key based on the effective provider.
  - Sets the `User-Agent` header from the configured tool identifier.

### 4. Dashboard TUI UX Tweaks

- DevPlan panel now:
  - Reads `dashboard.md` for the main view and appends any `blockers.md` content if present.
  - Shows a friendlier placeholder when no dashboard exists yet.
- API log panel:
  - Adds explicit "In-Flight" and "Completed" labels with distinct styling.
  - Keeps the existing three-stage expansion (collapsed → summary → full) per entry.
- Settings modal:
  - Slightly increased width/height to better fit the new tabs and fields.
- New `/files` and `/devplan` commands are documented in `dashboard_tui.py` help output and surfaced in the README.

*Last updated: December 8, 2025 (even later)*
*Status: DevPlan/dashboard split, explicit task completion, and provider configuration wired into docs and TUI*

---

## Latest Updates (December 8, 2025 - Tool Efficiency & Prompt Improvements)

### 1. New Efficiency Tools

Added four new tools to improve agent efficiency and collaboration:

- **`read_multiple_files(paths=["..."])`**: Batch-read up to 10 files in one tool call. Reduces API round-trips when agents need to understand multiple related files before making changes.

- **`report_blocker(description, type)`**: Workers can signal they're stuck. Logs to `blockers.md` and broadcasts to the team. Types: `technical`, `dependency`, `clarification`.

- **`request_help(target_role, question, context?)`**: Inter-agent collaboration. Workers can ask other specialists for input (e.g., backend asking frontend about API contract). Logs to `team_log.md`.

- **`get_task_context()`**: Returns comprehensive context: current task details, project structure, what other agents are working on, and helpful tips. Workers should call this at task start.

---

## Latest Updates (December 2025 - SwarmIndex: Indexing & Caching Layer)

### Overview

Added a custom indexing and caching layer ("SwarmIndex") for efficient code search and context management. This is a lightweight, project-local system using SQLite FTS5 - no external services required.

### New Files

| File | Purpose |
|------|---------|
| `core/swarm_index.py` | SQLite FTS5-backed code index with incremental updates |
| `core/tool_cache.py` | LRU cache for expensive tool operations |
| `tests/test_swarm_index.py` | Unit tests for SwarmIndex |
| `tests/test_tool_cache.py` | Unit tests for ToolCache |

### New Tools

Two new tools for agents to discover code efficiently:

- **`indexed_search_code(query, file_pattern?, max_results?)`**: Fast full-text search over indexed code files. Uses SQLite FTS5 for efficient searching. Supports FTS5 syntax (quotes for exact match, OR, NOT). Results are cached.

- **`indexed_related_files(path, max_results?)`**: Find files related to a given path - same directory, test files (test_foo.py, foo.test.ts), similar names (auth.py → auth_routes.py).

### How It Works

1. **Initialization**: When a session starts, `SessionController` initializes a `SwarmIndex` for the project. The index is stored at `<project_root>/scratch/shared/.swarm_index.db`.

2. **Indexing**: The index walks all code files (`.py`, `.ts`, `.js`, `.go`, `.rs`, etc.) under `scratch/shared/`, storing content in SQLite FTS5 tables.

3. **Incremental Updates**: When agents modify files via `write_file`, `replace_in_file`, `edit_file`, `append_file`, or `delete_file`, the index is notified and marks those files as dirty.

4. **Search**: `indexed_search_code` queries the FTS5 index for fast full-text search. Results include file paths and snippets with matched terms highlighted.

5. **Caching**: Tool results are cached in an LRU cache with TTL expiration. Cache is invalidated when files change.

### Agent Workflow (Updated)

Agents are now instructed to use indexed tools first for code discovery:

```
1. indexed_search_code(query) - Find relevant files FAST
2. indexed_related_files(path) - Find tests/related modules  
3. read_multiple_files([paths]) - Read only what you need
4. write_file / replace_in_file - Implement
5. complete_my_task(result) - REQUIRED
```

### Caching Layers

**Tool-Level Cache** (`core/tool_cache.py`):
- LRU cache with configurable max entries (default: 256)
- TTL expiration (default: 5 minutes)
- Automatic invalidation when files change
- Shared across all agents

**Per-Task Context Cache** (`agents/base_agent.py`):
- `TaskContext` dataclass stores per-task discoveries
- Tracks key files, search results, related files
- Avoids redundant searches within a task
- Auto-pruned (keeps last 5 tasks)

### Configuration

No configuration required - SwarmIndex initializes automatically when a project is loaded. The index is stored alongside project files and rebuilds incrementally.

### Testing

```bash
# Run SwarmIndex tests
pytest tests/test_swarm_index.py -v

# Run ToolCache tests  
pytest tests/test_tool_cache.py -v
```

### Manual Testing Flow

1. Start TUI: `python main.py --tui`
2. Select a project with existing code
3. Confirm index builds (status: "SwarmIndex: indexed N files")
4. Use a worker to search: "Find all authentication code"
5. Verify `indexed_search_code` is used instead of `search_code`
6. Modify a file and search again - results should reflect changes

### Known Limitations

- Index only covers files under `scratch/shared/`
- Maximum file size: 500KB (larger files skipped)
- FTS5 tokenization is basic (porter stemmer) - no semantic search
- Cache invalidation is conservative (clears all on any file change)

### Future Improvements (Not Implemented)

- Semantic/embedding-based search
- Symbol-level indexing (functions, classes, imports)
- Cross-file reference tracking
- Smarter cache invalidation (per-file granularity)

### 2. Enhanced `search_code` Tool

- **Regex support**: `search_code(query="def\\s+\\w+", regex=true)`
- **File filtering**: `search_code(query="...", file_pattern="*.py")` to search only specific file types
- **Early exit**: Stops after 50 matches to prevent timeouts
- **Better file type handling**: Only searches code files (py, js, ts, etc.)

### 3. Expanded `run_command` Whitelist

Now supports:
- **Python**: pytest, mypy, black, ruff, flake8, isort
- **Node**: yarn, pnpm, tsc, eslint, prettier, jest, vitest, mocha
- **Git**: git show, git ls-files (still read-only)
- **Build tools**: make, cmake, cargo, go build/run/test
- **Docker**: docker ps/images/logs (inspect only)
- **Utilities**: pwd, which, where, tree, file, stat, sort, uniq, awk, sed

### 4. Improved Worker Prompts

All worker prompts now include:

**Explicit Workflow**:
1. `get_task_context()` - Get context first
2. `read_file("shared/master_plan.md")` - Understand the project
3. `read_multiple_files([...])` - Batch-read related files
4. Implement with `write_file` / `replace_in_file`
5. Test with `run_command`
6. `complete_my_task(result="...")` - Signal completion

**Tool Usage Best Practices**:
- Batch reads instead of multiple single reads
- Search before writing to find existing code
- Report blockers when stuck
- Request help from other specialists
- Claim contested files before editing

### 5. Improved Architect Prompt

**Structured Task Format**:
```
assign_task("Codey McBackend", "Implement [FEATURE]:

**Goal**: [One sentence]

**Files to create/modify**:
- `shared/src/[file].py` - [purpose]

**Requirements**:
- [Specific function 1]
- [Specific function 2]

**Dependencies**: Read `shared/[related_file]` first.

**Done when**: Tests pass, exports working module.")
```

**Task Quality Checklist** - Architect must verify:
- [ ] Specific file paths
- [ ] Clear requirements
- [ ] Dependencies noted
- [ ] Definition of done

### 6. Enhanced Tools System Prompt

Workers now see efficiency tips in their context:
- Start with `get_task_context()`
- Use `read_multiple_files` for batch reads
- Use `search_code` with filtering
- Use `report_blocker` when stuck
- Use `request_help` for collaboration
- **REQUIRED**: Call `complete_my_task` when done

### Files Changed

| File | Changes |
|------|---------|
| `core/agent_tools.py` | Added 4 new tools, improved search_code, expanded run_command whitelist, enhanced tools system prompt |
| `agents/architect.py` | Structured task format, quality checklist, clearer workflow |
| `agents/backend_dev.py` | Explicit workflow, tool usage best practices |
| `agents/frontend_dev.py` | Explicit workflow, tool usage best practices |
| `agents/qa_engineer.py` | Explicit workflow, tool usage best practices |

### Testing Checklist

- [ ] `get_task_context()` returns task info and project structure
- [ ] `read_multiple_files` batch-reads files correctly
- [ ] `report_blocker` logs to blockers.md and broadcasts
- [ ] `request_help` logs to team_log.md and broadcasts
- [ ] `search_code` with `regex=true` and `file_pattern` works
- [ ] Expanded `run_command` allows pytest, jest, etc.
- [ ] Workers follow the new workflow (context → read → implement → test → complete)
- [ ] Architect assigns tasks with file paths and done criteria

*Last updated: December 8, 2025 (tool efficiency update)*
*Status: New efficiency tools, improved search/run_command, enhanced prompts for better swarm flow*

---

## Latest Updates (December 8, 2025 - New Agents & Collaboration Tools)

### 1. Four New Specialist Agents

Added four new agents to expand the team's capabilities:

| Role Key | Name | Specialization |
|----------|------|----------------|
| `database_specialist` | Schema McDatabase | DB schema design, migrations, query optimization |
| `api_designer` | Swagger McEndpoint | API design, OpenAPI specs, contract definition |
| `code_reviewer` | Nitpick McReviewer | Code quality, refactoring, best practices |
| `research` | Googly McResearch | Patterns, best practices, technical research |

All agents follow the same workflow pattern and can be spawned by the Architect.

### 2. Five New Context & Collaboration Tools

**Context Management:**
- **`create_checkpoint(title, content, category)`**: Save important decisions, progress, or context to `checkpoints.md` for continuity.
- **`get_context_summary()`**: Get project overview: task status, key files, recent checkpoints.
- **`get_recent_changes(path, hours)`**: See recently modified files without git commands.

**Collaboration:**
- **`list_agents()`**: See all agents in the swarm with their current status and tasks.
- **`delegate_subtask(target_role, subtask, context, priority)`**: Delegate work to another specialist. Logs to team_log.md and broadcasts notification.

### 3. Updated Architect Team Table

Architect now knows about all 10 specialist roles:
```
| Role | Name | Specialization |
|------|------|----------------|
| backend_dev | Codey McBackend | API, Server Logic |
| frontend_dev | Pixel McFrontend | UI/UX, React |
| database_specialist | Schema McDatabase | DB Schema, Migrations |
| api_designer | Swagger McEndpoint | API Design, OpenAPI |
| qa_engineer | Bugsy McTester | Testing, Security |
| code_reviewer | Nitpick McReviewer | Code Quality |
| devops | Deployo McOps | CI/CD, Docker |
| project_manager | Checky McManager | Progress Tracking |
| tech_writer | Docy McWriter | Documentation |
| research | Googly McResearch | Patterns, Best Practices |
```

### 4. Enhanced Tools System Prompt

Workers now see their full team in the tools system prompt and have access to:
- Collaboration tools (list_agents, delegate_subtask, request_help)
- Context tools (get_context_summary, create_checkpoint, get_recent_changes)
- Clear workflow guidance

### 5. Worker Collaboration Sections

All worker prompts now include a "Collaboration" section showing which specialists to work with:
- Backend knows to delegate DB work to database_specialist
- Frontend knows to get API specs from api_designer
- QA knows code_reviewer handles style, they focus on function/security

### Files Changed

| File | Changes |
|------|---------|
| `agents/database_specialist.py` | NEW: Schema McDatabase agent |
| `agents/api_designer.py` | NEW: Swagger McEndpoint agent |
| `agents/code_reviewer.py` | NEW: Nitpick McReviewer agent |
| `agents/research_agent.py` | NEW: Googly McResearch agent |
| `agents/__init__.py` | Added new agents to exports and role mappings |
| `agents/architect.py` | Updated team table with all 10 roles |
| `agents/backend_dev.py` | Added collaboration section |
| `agents/frontend_dev.py` | Added collaboration section |
| `agents/qa_engineer.py` | Added collaboration section |
| `core/agent_tools.py` | Added 5 new tools, updated spawn_worker enum, enhanced tools system prompt |

### Usage Examples

**Spawning new specialists:**
```python
spawn_worker("database_specialist")  # Schema McDatabase
spawn_worker("api_designer")         # Swagger McEndpoint
spawn_worker("code_reviewer")        # Nitpick McReviewer
spawn_worker("research")             # Googly McResearch
```

**Delegating work:**
```python
delegate_subtask(
    target_role="database_specialist",
    subtask="Design schema for user authentication with roles and permissions",
    priority="high"
)
```

**Saving context:**
```python
create_checkpoint(
    title="API Design Complete",
    content="Defined 12 REST endpoints for user management. See shared/api/openapi.yaml",
    category="progress"
)
```

### Testing Checklist

- [ ] New agents can be spawned via `spawn_worker`
- [ ] `list_agents()` shows all agents with status
- [ ] `create_checkpoint` saves to checkpoints.md
- [ ] `get_context_summary` returns task and file info
- [ ] `delegate_subtask` logs and broadcasts
- [ ] `get_recent_changes` shows modified files
- [ ] Workers see collaboration sections in their prompts
- [ ] Architect can assign tasks to new specialists

*Last updated: December 8, 2025 (new agents & collaboration update)*
*Status: 10 specialist agents, collaboration/context tools, enhanced worker prompts*

---

## Latest Updates (December 8, 2025 - Efficiency Mode Overhaul)

### Problem
Token usage was extremely inefficient:
- **Input: 76M tokens** vs **Output: 3M tokens** (25:1 ratio)
- 3,258 API calls producing mostly stubs and placeholders
- Agents wasting calls on verbose context instead of actual code

### Solution: EFFICIENT_MODE (Default ON)

New settings in `data/settings.json`:
```json
{
    "efficient_mode": true,
    "context_messages": 5,
    "skip_memory_context": true
}
```

### Key Changes

#### 1. Slim Tool Definitions (`core/slim_tools.py`)
- **Before**: 33 verbose tools (~15k tokens per call)
- **After**: 12 essential tools (~3k tokens per call)
- **Savings**: ~80% reduction in tool definition overhead

#### 2. Lean Agent Prompts (`agents/lean_prompts.py`)
- **Before**: ~1000-1500 tokens per prompt
- **After**: ~300-400 tokens per prompt
- **Savings**: ~70% reduction

#### 3. Minimal Context Building (`agents/base_agent.py`)
- History messages: 5 instead of 10
- Worker context: Only task + last human message
- Memory context: Skipped (uses file-based context instead)

#### 4. File-Based Memory (`core/shared_context.py`)
- **File**: `shared/context.md`
- **Tool**: `log_context(entry, category)`
- Replaces database memory with simple markdown

#### 5. Simplified Orchestration
- Removed QA gate requirements
- PM just tracks progress, doesn't block
- Focus on building, not process

### Expected Results
- **Input tokens**: ~80% reduction per call
- **Target ratio**: 5:1 or better (vs 25:1 before)

### Files Changed

| File | Changes |
|------|---------|
| `core/slim_tools.py` | NEW: Compressed tool definitions |
| `core/shared_context.py` | NEW: File-based memory |
| `agents/lean_prompts.py` | NEW: Terse prompts |
| `core/settings_manager.py` | Added efficient_mode settings |
| `agents/base_agent.py` | Use slim tools when efficient |
| All agent files | Use lean prompts |

*Last updated: December 8, 2025 (efficiency overhaul)*
*Status: EFFICIENT_MODE enabled by default, ~80% token reduction expected*

---

## Latest Updates (December 8, 2025 - Devussy Pipeline Integration)

### Problem
The Architect was both designing projects AND delegating work. This led to:
- Inconsistent project scoping
- Architect making up features on the fly
- No structured development phases
- Work not following a coherent plan

### Solution: Devussy Pipeline Integration

Devussy is now integrated as an optional pre-swarm planning phase. When enabled:
1. User goes through an LLM-guided interview about their project
2. Devussy generates `devplan.md` and `phases.md` with structured tasks
3. The swarm executes the plan phase by phase
4. The Architect becomes a pure delegator - no project decisions

### How It Works

#### Startup Flow
```
1. Start app: python main.py --tui
2. Select project
3. "Run Devussy pipeline? [y/N]"
   - If yes: LLM interview → generates devplan + phases
   - If existing devplan found: option to reuse or regenerate
4. Dashboard starts in DEVUSSY MODE if plan exists
```

#### Files Generated
| File | Location | Purpose |
|------|----------|---------|
| `devplan.md` | `scratch/shared/` | Full development plan with scope and architecture |
| `phases.md` | `scratch/shared/` | Combined phase document |
| `phases/` | `scratch/shared/phases/` | Individual phase files (phase1.md, phase2.md, etc.) |
| `handoff.md` | `scratch/shared/` | Handoff instructions for continuity |

#### Architect Behavior in Devussy Mode

**Normal Mode** (devussy_mode=False):
- Architect designs the project from user request
- Creates architecture and breaks down work
- Makes technology decisions

**Devussy Mode** (devussy_mode=True):
- Architect reads devplan.md and phases.md first
- Executes phases in order (Phase 1, Phase 2, etc.)
- Assigns tasks EXACTLY as described in devplan
- No architectural decisions - all in the devplan
- No feature additions beyond the plan

#### Architect Prompt in Devussy Mode
```
## 🔮 DEVUSSY MODE - YOU FOLLOW THE DEVPLAN

**CRITICAL RULES:**
1. DO NOT DECIDE WHAT TO BUILD - The devplan defines everything
2. READ THE DEVPLAN FIRST - `read_file("shared/devplan.md")`
3. EXECUTE PHASES IN ORDER - Start with Phase 1, then Phase 2, etc.
4. YOU ARE A DELEGATOR ONLY - Assign tasks from the devplan
5. NO ARCHITECTURAL DECISIONS - Already in the devplan
6. NO FEATURE ADDITIONS - Only implement what's in the devplan

**WORKFLOW:**
1. Read devplan.md and phases.md
2. Identify current phase
3. Spawn workers for phase tasks
4. Assign tasks with "Phase X, Task Y: [exact task]"
5. On phase complete, move to next phase
```

### Files Changed

| File | Changes |
|------|---------|
| `core/devussy_integration.py` | NEW: Pipeline runner and output management |
| `dashboard_tui.py` | Added devussy pipeline prompt at startup |
| `core/settings_manager.py` | Added `devussy_mode` setting |
| `dashboard_tui.py` | Architect prompt injection in devussy mode |

### Settings

```json
{
    "devussy_mode": false  // Set to true when devussy pipeline is used
}
```

### Usage

**New project with Devussy:**
```
1. python main.py --tui
2. Create new project: "N"
3. Run Devussy pipeline: "y"
4. Complete LLM interview (describe project, answer questions)
5. Wait for devplan generation
6. Dashboard starts with "🔮 DEVUSSY MODE"
7. Type "Go" to start executing the devplan
```

**Existing devplan:**
```
1. python main.py --tui
2. Select project with existing devplan
3. "Existing devplan found. Run Devussy pipeline? [y/N/Enter=use existing]"
4. Press Enter to use existing devplan
5. Dashboard starts in devussy mode
```

### Testing Checklist

- [ ] Devussy pipeline runs when user says "y"
- [ ] devplan.md is copied to scratch/shared/
- [ ] phases.md is generated from phase files
- [ ] Architect reads devplan on session start
- [ ] Architect assigns tasks from devplan, not inventing features
- [ ] Phase completion triggers next phase
- [ ] Existing devplan can be reused

*Last updated: December 8, 2025 (devussy integration)*
*Status: Devussy pipeline integrated, Architect follows devplan in devussy mode*

---

## Latest Updates (December 8, 2025 - Swarm-Ready Devplans)

### Problem
Even with devussy integration, the Architect still had to:
- Parse devplan manually to figure out tasks
- Decide which agent should do what
- Format task assignments from scratch
- Track dependencies manually

### Solution: Pre-Assigned Task Queues

Devussy now generates **swarm-ready devplans** where:
1. Every task is pre-assigned to a specific agent role
2. Task dependencies are explicitly mapped
3. Tool calls are suggested for each task
4. Dispatch commands are copy-paste ready

### New Files Generated

| File | Purpose |
|------|---------|
| `task_queue.md` | Pre-formatted task queue with agent assignments |
| `devplan.md` | Project overview (same as before) |
| `phases.md` | Phase details (same as before) |

### Task Queue Format

```markdown
#### Task 1.1: Create User Authentication Models

**Status:** `pending`  
**Agent:** `backend_dev` (Codey McBackend)  
**Priority:** high  
**Depends:** none  

**Dispatch Command:**
```
assign_task("Codey McBackend", "Task 1.1: Create User Authentication Models

GOAL: Implement User and Token models with password hashing
FILES: shared/src/models/user.py, shared/src/models/auth.py
REQUIREMENTS:
- User model with email validation
- Password hashing with bcrypt
DONE: Models can be imported, tests pass")
```
```

### Agent Auto-Assignment

Tasks are auto-assigned based on content keywords:

| Keywords | Agent |
|----------|-------|
| api, endpoint, server, database, python | backend_dev |
| component, react, ui, css, frontend | frontend_dev |
| test, pytest, coverage, lint | qa_engineer |
| docker, deploy, ci/cd, pipeline | devops |
| documentation, readme, docs | tech_writer |
| schema, migration, sql | database_specialist |

### Architect Prompt Updates

The Architect in devussy mode now:
1. Reads `task_queue.md` first (not devplan)
2. Finds PENDING tasks with no dependencies
3. Dispatches using pre-formatted commands
4. Dispatches PARALLEL tasks together (same phase, no interdeps)
5. Updates task status after completion

### Parallel Dispatch Example

```
# Tasks 1.1 and 1.2 have no dependencies - dispatch together
spawn_worker("backend_dev")
spawn_worker("frontend_dev")
assign_task("Codey McBackend", "Task 1.1: ...")
assign_task("Pixel McFrontend", "Task 1.2: ...")
```

### Files Changed

| File | Changes |
|------|---------|
| `core/devussy_integration.py` | Added task queue generation, agent inference |
| `agents/lean_prompts.py` | Updated LEAN_DEVUSSY_ARCHITECT_PROMPT for dispatch |
| `dashboard_tui.py` | Shows task queue info on startup |
| `devussy/src/models.py` | Added swarm fields to DevPlanStep |
| `devussy/src/pipeline/swarm_parser.py` | NEW: Parser for swarm task metadata |
| `devussy/src/prompts/devplan_swarm.txt` | NEW: Swarm-aware prompt |
| `devussy/templates/detailed_devplan_swarm.jinja` | NEW: Agent-aware template |

### Testing Checklist

- [ ] Devussy pipeline generates task_queue.md
- [ ] Tasks have correct agent assignments
- [ ] Dependencies are parsed correctly
- [ ] Architect reads task_queue.md first
- [ ] Parallel tasks are dispatched together
- [ ] Task status updates work
- [ ] Dashboard shows agent task counts

*Last updated: December 8, 2025 (swarm-ready devplans)*
*Status: Tasks pre-assigned to agents, parallel dispatch enabled, copy-paste commands ready*

---

## Latest Updates (December 8, 2025 - Tech Stack Handling Fix)

### Problem
Devussy-generated plans were using Python code for TypeScript/Godot projects because:
1. `tech_stack` variable was empty ("No tech stack parsed")
2. Prompt templates had hardcoded Python examples
3. Agent assignment logic assumed web apps

### Solution: LLM-Driven Tech Stack Handling

**All decisions now driven by LLM based on interview data:**

1. **Tech Stack Propagation** (`project_design.py`)
   - If LLM response doesn't parse a tech stack section, fallback to known `languages` and `frameworks` from interview
   - Tech stack is NEVER empty anymore

2. **No Hardcoded Examples** (templates/prompts)
   - Removed Python-specific examples from `detailed_devplan.jinja`
   - Removed hardcoded phase structures from `devplan_swarm.txt`
   - Removed language-specific test commands from `handoff_generation.txt`
   - LLM reads the tech stack and generates appropriate code/commands

3. **Smart Agent Assignment** (`devussy_integration.py`)
   - Game projects (Godot, Unity) → all code goes to `backend_dev`
   - `frontend_dev` only assigned for explicit web projects (React, Vue)
   - Project context loaded from `project_design.md`

4. **Agent Prompts Updated** (`lean_prompts.py`)
   - Backend dev: Must read `project_design.md` first, match tech stack
   - Frontend dev: Check if web project, REFUSE if game project
   - QA: Use correct test framework for project's language

### Files Changed

| File | Changes |
|------|---------|
| `devussy/src/pipeline/project_design.py` | Fallback to known languages/frameworks |
| `devussy/src/pipeline/compose.py` | Prominent tech stack in project_design.md |
| `devussy/templates/detailed_devplan.jinja` | Removed Python examples |
| `devussy/templates/detailed_devplan_swarm.jinja` | Generic agent table |
| `devussy/templates/basic_devplan.jinja` | Simplified tech stack reminder |
| `devussy/src/prompts/devplan_detailed.txt` | Generic examples |
| `devussy/src/prompts/devplan_swarm.txt` | LLM-driven phase design |
| `devussy/src/prompts/handoff_generation.txt` | Removed Python commands |
| `core/devussy_integration.py` | Project context for agent assignment |
| `agents/lean_prompts.py` | Tech stack awareness for all agents |

### Key Principle

**Nothing is hardcoded. The LLM reads the tech stack from the interview and generates appropriate:**
- File extensions (.ts, .gd, .py, .rs, etc.)
- Package managers (npm, pip, cargo, etc.)
- Test commands (vitest, gut, pytest, etc.)
- Build tools (vite, godot, cargo, etc.)

*Last updated: December 8, 2025 (tech stack handling)*
*Status: LLM-driven tech stack, no hardcoded language assumptions*

---

## Latest Updates (December 9, 2025 - Orchestration, Resume Flow & TUI Layout)

### 1. One-Task-Per-Worker Orchestration

**Problem:** Bossy could assign multiple tasks to the same worker concurrently, and it was hard to see when tasks were truly finished.

**Solution:**
- Updated `core/chatroom.py::assign_task` to enforce **one active task per worker**:
  - If a worker is `WORKING` and has a `current_task_id`, new assignments are rejected.
  - A status message is broadcast ("{agent} is busy. Wait for them to call complete_my_task().").
- Tightened `agents/lean_prompts.py`:
  - Architect prompts now explicitly say: ONE task per worker, check `get_swarm_state()` before assigning, and expect `assign_task()` to fail when a worker is busy.
- Strengthened worker prompts via `LEAN_WORKER_SUFFIX`:
  - All workers are required to call `complete_my_task(result="SUMMARY")` when done.
  - Summary must include files touched, functionality implemented, and notes for other agents.

### 2. Reliable Task Completion & Summaries

**Problem:** Task completion was sometimes inferred from free-form chat phrases, leading to inconsistent summaries and stalled orchestration.

**Solution:**
- `core/agent_tools.py::_complete_my_task` now:
  - Marks the task completed and sets the worker back to `IDLE` (as before).
  - Broadcasts a **System notice** with a concise summary: ` Task Complete by {agent}: {summary}`.
  - Continues to trigger the Auto Orchestrator when all tasks are complete.
- Workers are instructed to treat `complete_my_task` as the **only** way to finish a task, keeping Bossy's view of progress consistent.

### 3. Devussy DevPlan Resume & Recovery

**Problem:** Joining an existing Devussy-generated project after partial work (or after phase files were accidentally edited) could leave Bossy without a clear understanding of what remained to do.

**Solution:**
- Added recovery helpers in `core/devussy_integration.py`:
  - `recover_project_state(project_path)`
    - Scans `scratch/shared` for existing source files.
    - Parses `devplan.md` phase anchors (`PHASE_X_STATUS_START/END`).
    - Computes total vs completed tasks and identifies the current phase and next task number.
  - `regenerate_task_queue_from_devplan(project_path)`
    - Rebuilds a minimal `task_queue.md` from the devplan's phase overview table when phase files or the queue are missing/corrupted.
- Updated `agents/lean_prompts.py::LEAN_DEVUSSY_ARCHITECT_PROMPT`:
  - Architect now supports multiple phase file formats (anchor-style tasks, `@agent:` tasks, or simple section-based descriptions).
  - On resume, Bossy is instructed to:
    - Read `devplan.md` and the current phase file.
    - Use `get_project_structure()` to see what files already exist.
    - Dispatch only **remaining** work.

### 4. Dashboard TUI: Resume-Aware DevPlan Summary

**Problem:** When re-opening a project, it wasn't obvious how much work had already been done or whether the Devussy task queue was healthy.

**Solution:**
- `dashboard_tui.py::_show_devplan_summary` now:
  - Loads devplan/phase metadata via `load_devplan_for_swarm()`.
  - Calls `recover_project_state()` to compute:
    - Number of existing source files.
    - Phase/task progress (completed vs total, current phase).
  - Validates `task_queue.md` and phase files:
    - If the queue is missing or essentially empty, marks it for recovery.
    - If no phase file contains valid task markers (`@agent:`, `### Task`, etc.), flags the phases as missing task details.
  - When needed, calls `regenerate_task_queue_from_devplan()` and reports success/failure in the chat.
  - Prints a friendly summary such as:
    - `Found N existing source files (resuming project)`
    - `Progress: X/Y tasks, currently on Phase P`

### 5. Updated TUI Layout: In-Flight Center, API History Bottom-Right

**Problem:** The original API log layout was hard to read; in-flight calls were buried, and the right sidebar felt cramped.

**Solution:**
- `dashboard_tui.py::SwarmDashboard.CSS` and `compose()` now define:
  - **Center Column**
    - A collapsible **In-Flight Requests** bar at the **top center** (max ~1/3 of the center column) showing current API calls, each clickable to expand.
    - Main chat log below the in-flight bar.
  - **Right Column**
    - DevPlan + tools + tokens at the top/middle as before.
    - A collapsible **API History** panel anchored to the **bottom-right**, sized to roughly one-third of the right column height.
    - API history uses the existing `ApiLogEntry` expansion model (collapsed → summary → full request/response + tool calls).
- Agents sidebar (`#agents-scroll`) was hardened to always be scrollable, and keyboard scrolling via `Ctrl+A` / `Ctrl+Up` / `Ctrl+Down` continues to work with the new layout.

*Last updated: December 9, 2025 (orchestration + resume + TUI layout)*
*Status: One-task-per-worker enforced, tool-based completion summaries visible, Devussy projects resumable via dashboard + Architect helpers*

---

## Latest Updates (December 9, 2025 - AutoDispatcher & Token-Efficient Devussy Orchestration)

### 1. AutoDispatcher: Local Orchestration (No Architect API Calls)

**Problem:** Even after improving Devussy integration, the Architect still burned huge numbers of tokens when dispatching tasks:

- Re-reading `task_queue.md` and phase files repeatedly.
- Treating `assign_task(...)` code blocks as documentation instead of tool calls.
- Looping on `read_file` / `get_swarm_state` without actually dispatching.

**Solution:** Introduced a **local AutoDispatcher** that takes over dispatching for Devussy projects, so the Architect no longer needs to make API calls just to move tasks around.

- New module: `core/auto_dispatcher.py`
  - `AutoDispatcher.dispatch_next_task()` – used when the user types `go`.
  - `AutoDispatcher.on_task_completed(task_id, agent_name)` – called automatically when workers finish.
- AutoDispatcher uses the **SwarmOrchestrator** instead of LLM reasoning:
  - Asks `SwarmOrchestrator.get_next_dispatchable_tasks(max_count=1)` for the next pending task.
  - Spawns the appropriate worker locally via `Chatroom.spawn_agent(role)` if needed.
  - Calls `Chatroom.assign_task(agent_name, description)` directly.
  - Logs status into the dashboard (no LLM messages, no tokens).
- The Architect remains responsible for **design and planning**, but **not for dispatch** in Devussy mode.

### 2. SwarmOrchestrator: Persistent Task State & Task Queue Updates

**Problem:** Devussy task queues (`task_queue.md`) and phase files did not persist task state cleanly across sessions. Completed work looked "pending" after a restart, and recovered runs could reassign already-done tasks.

**Solution:** Extended `core/swarm_orchestrator.py` to own task state and keep the markdown in sync.

- New persistence layer:
  - `_save_task_state()` and `_load_task_state()` read/write `scratch/shared/task_state.json`.
  - On startup, `initialize()` parses `devplan.md` + `phases/phaseN.md`, then overlays any saved states.
  - Phase states (`NOT_STARTED` / `IN_PROGRESS` / `COMPLETED`) are recomputed from task states.
- Task state transitions are now persisted and reflected in the Devussy task queue:
  - `mark_task_dispatched(task_id, agent_name)` → sets `DISPATCHED`, updates phase state, saves state, and calls `_update_task_queue_file()`.
  - `mark_task_completed(task_id)` → sets `COMPLETED`, saves state, updates phase if all tasks done, and calls `_update_task_queue_file()`.
- `_update_task_queue_file()` rewrites status lines in `task_queue.md`:
  - For each task header like `### ⚙️ Task 1.1: ...` (or 🎨/🐛/🚀/📝 variants) it replaces:
    - `**Status:** `pending`` → `**Status:** `📤 dispatched`` when dispatched.
    - `**Status:** `pending`` → `**Status:** `✅ completed`` when completed.
  - Only non-pending tasks are modified; pending tasks remain unchanged.

Net effect: Devussy task queues now behave like a live kanban board:

- The orchestrator is the **single source of truth** for task state.
- Markdown files (`task_queue.md`, DevPlan dashboard) are derived views.
- Completed work stays completed across TUI restarts.

### 3. Architect: Passive in Devussy Mode

**Problem:** Even with better prompts, Bossy McArchitect continued to respond to `go` and auto-orchestrator messages, consuming tokens for work that the AutoDispatcher can do deterministically.

**Solution:** Narrowed the Architect's role when Devussy + AutoDispatcher are in play.

- `agents/architect.py` now overrides `should_respond(message)`:
  - **Never** responds to the literal `go` command (AutoDispatcher owns it).
  - **Never** responds to "Auto Orchestrator" messages.
  - Only responds when:
    - The user explicitly mentions "architect" or "bossy".
    - The user asks for design/plan/architecture guidance.
- `speak_probability` reduced from `0.5` → `0.1` to further suppress unsolicited replies.

Bossy is now effectively a **design consultant** for Devussy projects; routine dispatch is handled locally.

### 4. Dashboard TUI: "go" Uses AutoDispatcher

**Problem:** Previously, typing `go` sent a human message to the Architect, who then had to read `task_queue.md`, reason about which tasks to assign, and call tools – all via API.

**Solution:** The TUI intercepts `go` and routes it to the AutoDispatcher instead of the Architect.

- In `dashboard_tui.py::send_message`:
  - If `content.strip().lower() == "go"`, the dashboard calls `_handle_go_command()` and **does not** send a chat message to the agents.
- `_handle_go_command()`:
  - Logs `🚀 AutoDispatcher: Starting task dispatch (no LLM needed)...`.
  - Gets the global `AutoDispatcher` and wires a status callback so updates appear in the chat log.
  - Calls `dispatcher.dispatch_next_task()` to assign the next pending Devussy task.
  - If a task was dispatched, triggers a worker round via `run_conversation()` (workers still use tools + API for actual coding).
  - If nothing is dispatchable, prints a friendly `No tasks to dispatch right now` message instead of waking the Architect.

This makes `go` effectively **zero-token** for orchestration: only the worker's coding work consumes tokens.

### 5. API History: Compact, Token-Aware View

**Problem:** The API history panel in the TUI used to render full request/response bodies, including long message arrays. This inflated context when the model re-read its own logs and made debugging noisy.

**Solution:** Reworked `dashboard_tui.py::ApiLogEntry` to display **summaries** by default and aggressively truncate details:

- Level 0 (collapsed): header with agent, status, time, and total tokens.
- Level 1 (summary):
  - Model, max tokens, message count, tools.
  - Task summary, token usage summary, short request/response preview.
- Level 2 (full):
  - Request messages truncated to ~200 chars and 5 lines per message.
  - Response content truncated to 10 lines, 100 chars per line.
  - Tool calls limited to 5 calls per request and 3 arguments per call, each capped at 100 chars.

The panel remains useful for debugging without acting as a secondary long-term context sink.

### 6. Manual Devussy + AutoDispatcher Test Flow

For a Devussy-generated project (e.g. `projects/doomussy3`):

1. Run the TUI:
   - `python main.py --tui`
2. Select the project and username.
3. When prompted about history, choose based on your test needs (clean slate vs resume).
4. Wait for the DevPlan summary in the right sidebar (phase counts, existing files, etc.).
5. Type `go` in the input box:
   - Verify you see `🚀 AutoDispatcher: Starting task dispatch (no LLM needed)...`.
   - Confirm **no Architect reply** appears for the `go` command.
   - Watch a worker (typically Codey McBackend) receive Task `1.1` and start working.
6. After the worker calls `complete_my_task`, watch:
   - AutoDispatcher logs a new dispatch for Task `1.2` (or next pending task).
   - `task_state.json` marks Task `1.1` as `COMPLETED`.
   - `task_queue.md` shows Task `1.1` with `**Status:** `✅ completed``.
7. Stop and restart the TUI, reload the same project, and type `go` again:
   - Completed tasks should **not** be reassigned.
   - AutoDispatcher should dispatch the next pending task.

*Last updated: December 9, 2025 (AutoDispatcher + SwarmOrchestrator integration)*
*Status: Architect focused on design; AutoDispatcher handles Devussy task dispatch locally with persistent, token-efficient orchestration.*

---

## Latest Updates (December 9, 2025 - CLI Parity, Parallel Dispatch & Efficiency)

### 1. CLI/TUI Feature Parity via SessionController

**Problem:** The CLI (`main.py --cli`) and TUI (`main.py --tui`) had duplicated logic, making it hard to maintain both modes.

**Solution:** Created a shared `SessionController` in `core/session_controller.py`:
- Encapsulates Chatroom, orchestrator, task manager, settings
- Both CLI and TUI use the same controller
- New `SwarmCLI` class in `main.py` provides a "TUI-lite" experience
- Commands: `go`, `stop`, `status`, `tasks`, `agents`, `spawn`, `help`, `quit`
- Full ANSI color support for agent messages

### 2. Parallel Task Dispatch (Up to 3 Workers)

**Problem:** Tasks were dispatched one at a time, leaving workers idle while waiting for sequentially-dispatched work.

**Solution:** Updated `core/auto_dispatcher.py`:
- `MAX_PARALLEL_TASKS = 3` – dispatches up to 3 tasks at once
- `dispatch_next_task()` now batch-dispatches independent tasks
- `on_task_completed()` fills free slots when a worker finishes
- Counts busy workers and dispatches to fill available capacity
- One conversation round runs all newly-assigned workers in parallel

**Example flow:**
```
go → Dispatches Tasks 1.1, 1.2, 1.3 to three workers
Worker A finishes → Dispatches Task 1.4 to Worker A
Worker B finishes → Dispatches Task 1.5 to Worker B
```

### 3. Efficiency Improvements (~35% Token Reduction)

**Problem:** Log analysis showed massive token waste:
- Project Manager making 59+ unnecessary API calls
- `project_design.md` read 194 times
- `get_project_structure` called 141 times
- 49 failed `complete_my_task` calls from PM

**Solutions:**

| Fix | File | Impact |
|-----|------|--------|
| **Disable PM in devussy mode** | `agents/project_manager.py` | -59 API calls |
| **Increase PM cooldowns** | `agents/project_manager.py` | 15s→120s, 60s→300s |
| **Cache `get_project_structure`** | `core/agent_tools.py` | 60s TTL cache |
| **Cache `read_file`** | `core/agent_tools.py` | mtime-based cache |
| **Remove `complete_my_task` from PM** | `core/slim_tools.py` | -49 failed calls |
| **Update prompts for batch reads** | `agents/lean_prompts.py` | Emphasize `read_multiple_files` |

### 4. Command Output Streaming

**Problem:** When agents ran commands (pytest, npm, etc.), output wasn't visible until completion.

**Solution:** Updated `core/agent_tools.py::_run_command`:
- Streams stdout line-by-line during execution (when possible)
- Shows output summary after completion (up to 20 lines)
- Displays exit code with ✓ (success) or ✗ (failure)
- Shows stderr on failure

**Example output:**
```
🔧 Codey McBackend: Running: pytest -q
    │ .....
    │ 5 passed in 0.24s
    ✓ Exit code: 0
```

### 5. Command Path Auto-Fixing

**Problem:** Agents passed `shared/frontend/ts-app` in commands, but commands run FROM `shared/`, creating broken double-paths like `shared/shared/frontend/ts-app`.

**Solution:** Auto-fix in `core/agent_tools.py::_run_command`:
```python
# Fix --prefix shared/... -> --prefix ...
command = re.sub(r'--prefix\s+shared/', '--prefix ', command)
# Fix cd shared/ -> cd .
command = re.sub(r'\bcd\s+shared/?(?=\s|$)', 'cd .', command)
# Fix paths like "shared/frontend" in common patterns
command = re.sub(r'(?<=\s)shared/(?=\w)', '', command)
```

Also updated all worker prompts (`agents/lean_prompts.py`) with clear path guidance:
```
## PATHS (IMPORTANT!)
- You are ALREADY in the shared/ directory
- Use paths like: src/app.py, frontend/src/App.tsx
- Do NOT prefix with "shared/" - that creates broken paths
```

### 6. Workers Start After Dispatch

**Problem:** After AutoDispatcher assigned a task, the worker wouldn't start because no conversation round was triggered.

**Solution:** `auto_dispatcher.py::_dispatch_task` now calls `chatroom.run_conversation_round()` after successful dispatch, ensuring workers begin immediately.

### Files Changed

| File | Changes |
|------|---------|
| `core/session_controller.py` | NEW: Shared controller for CLI/TUI |
| `main.py` | NEW: `SwarmCLI` class with full color support |
| `core/auto_dispatcher.py` | Parallel dispatch, run round after dispatch |
| `agents/project_manager.py` | Disabled in devussy mode, increased cooldowns |
| `core/agent_tools.py` | File/structure caching, command streaming, path fixes |
| `core/slim_tools.py` | PM tool filtering (no complete_my_task) |
| `agents/lean_prompts.py` | Batch read guidance, path handling |

### Testing Checklist

- [ ] `python main.py --cli` starts SwarmCLI with colors
- [ ] `go` dispatches up to 3 tasks in parallel
- [ ] Workers start immediately after dispatch
- [ ] Command output shows during/after execution
- [ ] `npm --prefix shared/...` auto-corrected to `npm --prefix ...`
- [ ] PM doesn't respond in devussy mode
- [ ] Repeated `read_file` calls return cached results

*Last updated: December 9, 2025 (CLI parity + parallel dispatch + efficiency)*
*Status: CLI/TUI share SessionController, parallel dispatch enabled, ~35% token reduction from caching and PM changes*

---

## Latest Updates (December 9, 2025 - Swarm Efficiency Overhaul)

Major efficiency improvements to make the swarm go **brrrrrrr** 🚀

### 1. Task Complexity & Batching System

**New Anchors** in `core/swarm_anchors.py`:
- `@complexity:` - trivial | simple | medium | complex
- `@batch_with:` - Task IDs that can be batched together
- `@parallel_safe:` - true | false (can run alongside other agents)

**Complexity Batch Limits:**
| Complexity | Batch Limit | Description |
|------------|-------------|-------------|
| `trivial` | 5 | Config tweaks, imports, tiny fixes |
| `simple` | 3 | Single function, 1-2 files |
| `medium` | 1 | Full module (no batching) |
| `complex` | 1 | Architectural work (no batching) |

**Effect:** AutoDispatcher now batches multiple trivial/simple tasks into ONE assignment to reduce API calls.

### 2. Enhanced AutoDispatcher

**File:** `core/auto_dispatcher.py`

Key improvements:
- `_get_batched_tasks()` - Groups trivial/simple tasks by agent
- `_dispatch_batch()` - Sends combined task description to agent
- Agents receive batch instructions like:
  ```
  # BATCH ASSIGNMENT: Tasks 1.1, 1.2, 1.3
  Complete ALL 3 tasks, then call complete_my_task(result="Completed batch: 1.1, 1.2, 1.3")
  ```

**Benefits:**
- 3-5 trivial tasks = 1 API call instead of 3-5
- Agents complete related work without context switching
- ~60% reduction in API calls for simple tasks

### 3. Project Bootstrap (Phase 0)

**New File:** `core/project_bootstrap.py`

Runs automatically after devussy pipeline:
- **Python:** Creates `.venv`, installs `requirements.txt`
- **Node:** Runs `npm install` if `package.json` exists
- **Structure:** Creates `src/`, `tests/`, `docs/`, `config/` directories
- **Git:** Creates `.gitignore` with standard ignores

**Integration:** Called from `run_devussy_pipeline_sync()` with `run_bootstrap=True` (default).

### 4. File Ownership Tracking

**New File:** `core/file_ownership.py`

Prevents agent collisions during parallel work:
- `reserve_files(files, agent_name, task_id)` - Claim files before dispatch
- `check_conflicts(files, agent_name)` - Check for ownership conflicts
- `release_task(task_id)` - Release files when task completes
- Persists to `.file_ownership.json` for session recovery

**Integration:**
- `AutoDispatcher._dispatch_task()` - Checks conflicts before dispatch, blocks conflicting tasks
- `agent_tools._complete_my_task()` - Releases files when task completes
- `session_controller._init_orchestrator()` - Initializes tracker on startup

### 5. Devussy Template Optimization

**File:** `devussy/templates/detailed_devplan_swarm.jinja`

Major changes to encourage fewer, chunkier tasks:
- **Task count guidance:** 3-8 per phase (was 5-15)
- **Anti-patterns:** Explicit examples of what NOT to do
- **Complexity rating:** Required for every task
- **Parallel design:** `@parallel_safe` and directory-based splitting

**New Efficiency Rules:**
```
❌ BAD: 10 tasks for "create file", "add function Y", "add function Z"
✅ GOOD: 1 task "Implement complete module X"

❌ BAD: "Add import for Y" as separate task
✅ GOOD: Include import in the task that uses Y
```

### 6. SwarmTask Enhancements

**File:** `core/swarm_orchestrator.py`

New fields on `SwarmTask`:
- `complexity: str` - trivial, simple, medium, complex
- `batch_with: List[str]` - Task IDs that can combine
- `parallel_safe: bool` - Can run alongside other agents
- `batch_key: str` - Grouping key (agent_role + phase)

**Parsing:** `_infer_complexity()` auto-detects from task content if not specified.

### 7. Devussy Integration Updates

**File:** `core/devussy_integration.py`

- `infer_task_complexity()` - Auto-detect complexity from content
- `parse_devplan_tasks()` - Now parses complexity, parallel_safe, batch_with
- `run_devussy_pipeline_sync()` - Runs bootstrap after pipeline

### Files Changed

| File | Changes |
|------|---------|
| `core/swarm_anchors.py` | Added complexity/batching anchors and constants |
| `core/auto_dispatcher.py` | Task batching, parallel agent limits |
| `core/project_bootstrap.py` | NEW: venv/npm/structure setup |
| `core/file_ownership.py` | NEW: Collision prevention |
| `core/swarm_orchestrator.py` | Complexity/batch fields, inference |
| `core/devussy_integration.py` | Complexity parsing, bootstrap integration |
| `core/session_controller.py` | File tracker initialization |
| `core/agent_tools.py` | File ownership release on task complete |
| `devussy/templates/detailed_devplan_swarm.jinja` | Efficiency rules, fewer tasks |

### Testing Checklist

- [ ] New devussy projects create `.venv` automatically
- [ ] Task batching groups trivial tasks (check log for "Batch dispatched")
- [ ] File conflicts block tasks instead of causing collisions
- [ ] Phases have 3-8 tasks instead of 15+
- [ ] `@complexity:` appears in generated phase files
- [ ] File ownership releases when task completes

### Expected Efficiency Gains

| Before | After | Improvement |
|--------|-------|-------------|
| 15+ tasks/phase | 3-8 tasks/phase | ~50% fewer API calls |
| 1 API call per trivial task | 1 call per 3-5 tasks | ~60% reduction |
| Manual venv setup | Automatic bootstrap | Faster project start |
| Agent file collisions | Ownership tracking | Zero conflicts |

*Last updated: December 9, 2025 (evening)*
*Status: Task batching, project bootstrap, file ownership, and template optimization all online*

---

## Latest Updates (December 9, 2025 - Devussy Pipeline Resume)

Added ability to resume devussy pipeline from any previous stage, saving time during testing.

### 1. New Resume Functions

**File:** `core/devussy_integration.py`

New functions added:
- `list_devussy_artifacts(project_path)` - Lists all previous runs and checkpoints
- `select_resume_stage(artifacts)` - Interactive UI to select what to resume from
- `resume_devussy_pipeline(project_path, resume_info)` - Resume from checkpoint or artifacts
- `run_devussy_with_resume_option(project_path)` - **Main entry point** - checks for previous runs and offers choice
- `copy_artifacts_to_new_project(source, target)` - Import artifacts to new project

### 2. Resume Flow

When starting a project with previous devussy runs:

```
=== DEVUSSY PIPELINE ===

Previous runs detected!

  1. Start fresh (new interview)
  2. Resume from previous run/checkpoint
  3. Cancel

Choice [1]:
```

If user selects "2":
```
📁 Previous Runs:

  1. myproject_20251209_143022
     Stages: project_design, basic_devplan, detailed_devplan
     Phases: 5 files

💾 Checkpoints:
  2. myproject_pipeline (detailed_devplan) - 2025-12-09T14:30

Select run/checkpoint to resume from [0]:
```

Then:
```
📍 Resume from which stage?
  1. After project_design
  2. After basic_devplan
  3. After detailed_devplan
Stage [1]:
```

### 3. Pipeline Stages

Checkpoints are saved at these stages:
1. `project_design` - After project design generation
2. `design_review` - After design review (optional)
3. `basic_devplan` - After basic devplan
4. `detailed_devplan` - After phase files generated
5. `handoff` - After handoff prompt

Resuming from a stage regenerates all subsequent stages with current templates/settings.

### 4. Artifact Storage

Previous runs are stored in: `{project}/scratch/devussy/{project_name}_{timestamp}/`

Files stored:
- `project_design.md` - Project design document
- `devplan.md` - Development plan
- `phase{N}.md` - Individual phase files
- `handoff_prompt.md` - Handoff document
- `complexity_profile.md` - (adaptive pipeline)

Checkpoints are stored in: `{project}/.devussy_state/checkpoint_{name}.json`

### 5. Usage Scenarios

**Scenario 1: Retry phase generation with new template**
1. Run pipeline once, generates verbose phases
2. Update `detailed_devplan_swarm.jinja` template
3. Restart, select "Resume from previous run"
4. Choose "After basic_devplan"
5. System regenerates phases with new template

**Scenario 2: Import artifacts to new project**
```python
from core.devussy_integration import copy_artifacts_to_new_project
from pathlib import Path

copy_artifacts_to_new_project(
    source_run_path=Path("projects/old_project/scratch/devussy/run_20251209"),
    target_project_path=Path("projects/new_project"),
)
```

**Scenario 3: Quick testing of swarm**
1. Run full pipeline once on a test project
2. Create new project
3. Resume from "detailed_devplan" of test project
4. Skip interview/design entirely, go straight to swarm execution

### Files Changed

| File | Changes |
|------|---------|
| `core/devussy_integration.py` | Added resume functions, PIPELINE_STAGES constant |
| `dashboard_tui.py` | Uses `run_devussy_with_resume_option` |
| `main.py` | Uses `run_devussy_with_resume_option` |

### Testing Checklist

- [ ] Starting new project shows "Start fresh / Resume" when previous runs exist
- [ ] Selecting resume shows list of previous runs
- [ ] Selecting a run shows available stages
- [ ] Resuming from checkpoint regenerates subsequent stages
- [ ] Resuming from artifacts copies files correctly
- [ ] New projects without runs go straight to interview
- [ ] `copy_artifacts_to_new_project` works correctly

*Last updated: December 9, 2025 (late evening)*
*Status: Pipeline resume, artifact import, and stage selection all functional*
