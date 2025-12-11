# SwarmUssY Web Interface

This directory contains the modern web frontend for the SwarmUssY project. It replaces the legacy TUI with a snappy, feature-rich single-page application.

## Implementation Overview

### 1. Backend (`web_server.py`)
- **Framework**: FastAPI + Uvicorn
- **Integration**: Wraps existing `core/` components (`SessionController`, `Chatroom`, `SettingsManager`, Devussy integration).
- **Key API Endpoints**:
  - `GET /api/state` – Full swarm state snapshot (agents, tasks, token stats, project).
  - `POST /api/chat` – Send messages and commands ("go", `/forcestart`, etc.).
  - `WS /ws/chat` – Real-time event streaming for chat and status.
  - `GET /api/files/tree` / `GET /api/files/content` – File browser APIs.
  - `GET /api/settings` / `POST /api/settings` – Persistent settings.
  - `GET /api/devussy/status` / `POST /api/devussy/start` – Devussy pipeline controls.
  - `GET /api/agents/{id}/config` / `POST /api/agents/{id}/config` – Per-agent configuration.
  - `POST /api/assistant/chat` – Project-aware assistant chat endpoint.
- **Run Command**: `python web_server.py`

### 2. Frontend (`web/`)
- **Stack**: Vite + Preact + TypeScript + Tailwind CSS.
- **State Management**: `useSwarm` hook + WebSocket for live updates.
- **Core Components**:
  - `App` – Main 3-column dashboard layout (ChatPanel · AgentList · ProjectDashboard/TaskBoard) with sidebar navigation.
  - `ChatPanel` – Split-view chat with:
    - Left **System Console** column for system/status/tool logs.
    - Middle **Orchestrator & User** column for Architect/PM + user conversation.
    - Right per-agent columns with collapsible headers and token usage badges.
    - Per-message token counts and expandable details.
  - `AgentList` – Swarm agents panel with:
    - Active agents pinned at the top with current/next objectives and token usage.
    - Collapsible "All Agents" section for the full roster.
    - Quick access to per-agent settings.
  - `TaskBoard` – Phase-aware task queue:
    - Grouped by phase with progress indicators.
    - Filter tabs (all/active/completed).
    - Expandable task details (status, priority, blockers, done-when).
  - `ProjectDashboard` – High-level project status:
    - Overall completion, per-phase progress bars, blockers, and token stats.
  - `AgentSettingsPanel` – Modal for configuring a single agent (model, max tokens, retries, temperature, timeout, enabled flag).
  - `AssistantChat` – Floating, project-aware helper chat that understands Devussy artifacts and current task state.
  - `SystemConsole` – Reusable console log viewer used by `ChatPanel`.
  - `FileBrowser` – Project tree + read-only code viewer.
  - `SettingsModal` – Tabbed settings modal (General, Models, Efficiency, Theme) with integrated theme picker.

## Setup & Running

### Prerequisites
- Node.js (v18+)
- Python 3.10+

### 1. Install Dependencies

**Backend:**
```bash
pip install fastapi uvicorn python-multipart
```

**Frontend:**
```bash
cd web
npm install
```

### 2. Run the Backend
From the project root:
```bash
python web_server.py
```
This will start the API server on `http://localhost:8000`.

### 3. Run the Frontend
From the `web/` directory:
```bash
npm run dev
```
Access the UI at `http://localhost:5173`.

### 4. Build for Production
```bash
cd web
npm run build
```
The backend can be configured to serve the static files from `web/dist`.
