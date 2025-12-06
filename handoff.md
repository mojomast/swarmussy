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
