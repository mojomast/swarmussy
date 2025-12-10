# SwarmUssY Web Interface

This directory contains the modern web frontend for the SwarmUssY project. It replaces the legacy TUI with a snappy, feature-rich single-page application.

## Implementation Plan

### 1. Backend (`web_server.py`)
- **Framework**: FastAPI + Uvicorn
- **Integration**: Wraps existing `core/` components (`Chatroom`, `SessionController`, `SettingsManager`).
- **API Endpoints**:
  - `GET /api/state`: Full swarm state snapshot (agents, tasks, project).
  - `POST /api/chat`: Send messages and commands.
  - `WS /ws/chat`: Real-time event streaming.
  - `GET /api/files/tree`: File browser API.
  - `GET /api/files/content`: File content API.
  - `GET /api/settings`: Get current settings.
  - `POST /api/settings`: Update settings.
- **Run Command**: `python web_server.py`

### 2. Frontend (`web/`)
- **Stack**: Vite + Preact + TypeScript + Tailwind CSS.
- **Architecture**:
  - **State Management**: React Context / Hooks for WebSocket synchronization.
  - **Components**:
    - `App`: Main layout with collapsible sidebars.
    - `ChatPanel`: Virtualized chat history.
    - `AgentsPanel`: Live status of all agents.
    - `AgentDetail`: Deep dive into a specific agent's logs/state.
    - `FileBrowser`: Tree view + code viewer.
    - `Terminal`: Command output stream.
    - `Settings`: Modal for configuration.

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
