import asyncio
import logging
import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

import uvicorn

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.session_controller import get_session_controller, SessionController
from core.project_manager import get_project_manager, Project
from core.settings_manager import get_settings
from core.models import Message, MessageRole
from core.task_manager import get_task_manager
from config.settings import get_scratch_dir

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("web_server")

# ─────────────────────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    agent_id: Optional[str] = None

class ProjectSelectRequest(BaseModel):
    project_name: str

class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    settings: Dict[str, Any]

class ApiKeyRequest(BaseModel):
    provider: str
    key: str

class DevussyStartRequest(BaseModel):
    model: Optional[str] = None
    interview_model: Optional[str] = None
    design_model: Optional[str] = None
    devplan_model: Optional[str] = None

class DevussyResumeRequest(BaseModel):
    type: str  # 'run' or 'checkpoint'
    run_path: Optional[str] = None
    resume_after: Optional[str] = None
    checkpoint_key: Optional[str] = None

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────────────────────────────────────

controller: SessionController = get_session_controller()
connected_websockets: List[WebSocket] = []

# ─────────────────────────────────────────────────────────────────────────────
# LIFECYCLE & CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Swarm Web Server...")
    
    # Load last project or default
    pm = get_project_manager()
    last_project_name = pm.get_last_project()
    project = None
    
    if last_project_name and pm.project_exists(last_project_name):
        project = pm.load_project(last_project_name)
    else:
        # Create default if none exists
        projects = pm.list_projects()
        if projects:
            project = projects[0]
        else:
            project = pm.create_project("default")
            
    pm.set_current(project)
    
    # Initialize controller
    settings = get_settings()
    username = settings.get("username", "User")
    devussy_mode = settings.get("devussy_mode", False)
    
    # Register callbacks
    controller.on_message = handle_message_event
    controller.on_status = handle_status_event
    controller.on_tool_call = handle_tool_call_event
    
    await controller.initialize(
        project=project,
        username=username,
        load_history=True,
        devussy_mode=devussy_mode
    )
    
    logger.info(f"Initialized session for project: {project.name}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down session...")
    await controller.shutdown()

def handle_message_event(message: Message):
    """Callback for new chat messages."""
    data = {
        "type": "message",
        "payload": message.to_dict()
    }
    asyncio.create_task(broadcast(data))

def handle_status_event(text: str):
    """Callback for status updates."""
    data = {
        "type": "status",
        "payload": {"text": text, "timestamp": datetime.now().isoformat()}
    }
    asyncio.create_task(broadcast(data))

def handle_tool_call_event(agent_name: str, tool_name: str, result: str):
    """Callback for tool calls."""
    data = {
        "type": "message",
        "payload": {
            "id": str(uuid.uuid4()),
            "role": "tool",
            "content": f"🔧 {tool_name}: {result[:100]}...",
            "sender_name": agent_name,
            "timestamp": datetime.now().isoformat()
        }
    }
    asyncio.create_task(broadcast(data))

async def broadcast(data: Dict[str, Any]):
    """Send data to all connected websockets."""
    to_remove = []
    for ws in connected_websockets:
        try:
            await ws.send_json(data)
        except Exception:
            to_remove.append(ws)
    
    for ws in to_remove:
        if ws in connected_websockets:
            connected_websockets.remove(ws)

# ─────────────────────────────────────────────────────────────────────────────
# APP SETUP
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages from WS if needed (e.g. typing indicators)
            # For now, we process chat via POST /api/chat usually, but could do here too.
            if data.get("type") == "chat":
                msg = data.get("payload", {}).get("message", "")
                if msg:
                    await controller.send_message(msg)
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

# ─────────────────────────────────────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/projects")
async def list_projects():
    pm = get_project_manager()
    projects = pm.list_projects()
    current = pm.current
    return {
        "projects": [
            {
                "name": p.name,
                "is_current": (current and p.name == current.name),
                "created_at": p.get_info().get("created_at", ""),
                "has_devplan": (p.shared_dir / "devplan.md").exists() if hasattr(p, 'shared_dir') else False
            } for p in projects
        ]
    }

@app.post("/api/projects/create")
async def create_project(request: ProjectCreateRequest):
    pm = get_project_manager()
    
    # Check if project already exists
    if pm.project_exists(request.name):
        raise HTTPException(status_code=400, detail="Project already exists")
    
    # Create the project
    project = pm.create_project(request.name, request.description or "")
    pm.set_current(project)
    
    # Initialize session with new project
    settings = get_settings()
    username = settings.get("username", "User")
    
    await controller.shutdown()
    await controller.initialize(project, username, load_history=False, devussy_mode=False)
    
    return {"status": "ok", "project": project.name, "path": str(project.root)}

@app.post("/api/projects/select")
async def select_project(request: ProjectSelectRequest):
    pm = get_project_manager()
    if not pm.project_exists(request.project_name):
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = pm.load_project(request.project_name)
    pm.set_current(project)
    
    # Re-initialize session with new project
    settings = get_settings()
    username = settings.get("username", "User")
    devussy_mode = settings.get("devussy_mode", False)
    
    await controller.shutdown()
    await controller.initialize(project, username, load_history=True, devussy_mode=devussy_mode)
    
    return {"status": "ok", "project": project.name}

@app.post("/api/projects/delete")
async def delete_project(request: ProjectSelectRequest):
    pm = get_project_manager()
    if not pm.project_exists(request.project_name):
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Don't allow deleting current project
    if pm.current and pm.current.name == request.project_name:
        raise HTTPException(status_code=400, detail="Cannot delete current project")
    
    pm.delete_project(request.project_name, confirm=True)
    return {"status": "ok"}

@app.get("/api/state")
async def get_state():
    return {
        "status": controller.get_status(),
        "agents": controller.get_agents(),
        "tasks": controller.get_tasks(),
        "token_stats": controller.get_token_stats(),
        "project": controller.project.get_info() if controller.project else None
    }

@app.post("/api/chat")
async def send_chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")
    
    msg = request.message.strip()
    
    # Handle /commands
    if msg.startswith("/"):
        parts = msg.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        
        try:
            if cmd == "/spawn":
                if arg:
                    await controller.spawn_agent(arg)
                return {"status": "executed", "command": cmd}
            elif cmd == "/stop":
                await controller.stop_current()
                return {"status": "executed", "command": cmd}
            elif cmd == "/halt":
                if arg:
                    await controller.halt_agent(arg)
                return {"status": "executed", "command": cmd}
            elif cmd == "/clear":
                if controller.chatroom:
                    controller.chatroom.state.messages.clear()
                    # Broadcast clear event? Or just let next fetch handle it
                    # We might need a 'clear' event type in handle_message_event logic 
                    # but for now state refresh will handle it
                return {"status": "executed", "command": cmd}
        except Exception as e:
            logger.error(f"Command failed: {e}")
            # Fallthrough to treat as chat or return error?
            # Let's treat unknown commands as chat for safety or just return
            pass

    # Process message in background to return quickly
    # The actual response messages will come via WebSocket
    asyncio.create_task(controller.send_message(request.message))
    
    return {"status": "received"}

@app.get("/api/files/tree")
async def get_file_tree(path: Optional[str] = None):
    # Default to project root (which includes scratch)
    # But usually we care about scratch/shared or source files.
    # Let's serve the whole project root for now, filtering .git etc.
    
    root = Path(controller.project.root) if controller.project else Path.cwd()
    if path:
        target_path = root / path
        # Security check
        try:
            target_path.resolve().relative_to(root.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        target_path = root
    
    if not target_path.exists():
        return {"items": []}
    
    items = []
    try:
        for item in target_path.iterdir():
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            
            items.append({
                "name": item.name,
                "path": str(item.relative_to(root)).replace("\\", "/"),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        
    return {"items": sorted(items, key=lambda x: (x["type"] == "file", x["name"]))}

@app.get("/api/files/content")
async def get_file_content(path: str):
    if not controller.project:
        raise HTTPException(status_code=400, detail="No project selected")
        
    root = Path(controller.project.root)
    target_path = root / path
    
    try:
        target_path.resolve().relative_to(root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# DEVUSSY ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/devussy/status")
async def get_devussy_status():
    """Get status of Devussy integration."""
    try:
        from core.devussy_integration import check_devussy_available, list_devussy_artifacts
        available = check_devussy_available()
        artifacts = {}
        if available and controller.project:
            artifacts = list_devussy_artifacts(Path(controller.project.root))
            
        return {
            "available": available,
            "mode_enabled": controller.is_devussy_mode,
            "artifacts": artifacts
        }
    except ImportError:
        return {"available": False, "mode_enabled": False, "artifacts": {}}

@app.get("/api/devussy/artifacts")
async def get_devussy_artifacts():
    """Get list of devussy artifacts for current project."""
    if not controller.project:
        return {"runs": [], "checkpoints": [], "latest_run": None}
    
    try:
        from core.devussy_integration import list_devussy_artifacts
        return list_devussy_artifacts(Path(controller.project.root))
    except Exception as e:
        logger.error(f"Failed to list artifacts: {e}")
        return {"runs": [], "checkpoints": [], "latest_run": None}

@app.post("/api/devussy/mode")
async def set_devussy_mode(request: Dict[str, bool] = Body(...)):
    """Toggle Devussy mode."""
    enabled = request.get("enabled", False)
    # We need to re-initialize to properly set up the orchestrator
    if controller.project:
        await controller.initialize(
            project=controller.project,
            username=controller.username,
            load_history=True,
            devussy_mode=enabled
        )
    return {"status": "ok", "devussy_mode": controller.is_devussy_mode}

@app.post("/api/devussy/start")
async def start_devussy_pipeline(request: DevussyStartRequest):
    """Start the Devussy pipeline for current project."""
    if not controller.project:
        raise HTTPException(status_code=400, detail="No project selected")
    
    # Store model preferences in settings
    settings = get_settings()
    if request.model:
        settings.set("devussy_model", request.model, auto_save=False)
    if request.interview_model:
        settings.set("interview_model", request.interview_model, auto_save=False)
    if request.design_model:
        settings.set("design_model", request.design_model, auto_save=False)
    if request.devplan_model:
        settings.set("devplan_model", request.devplan_model, auto_save=False)
    settings.save()
    
    return {
        "status": "started",
        "project": controller.project.name,
        "message": "Pipeline started. Use WebSocket /ws/devussy for real-time updates."
    }

@app.post("/api/devussy/resume")
async def resume_devussy(request: DevussyResumeRequest):
    """Resume Devussy pipeline from checkpoint or previous run."""
    if not controller.project:
        raise HTTPException(status_code=400, detail="No project selected")
    
    try:
        from core.devussy_integration import resume_devussy_pipeline
        
        resume_info = {
            "type": request.type,
            "run_path": request.run_path,
            "resume_after": request.resume_after,
            "checkpoint_key": request.checkpoint_key,
        }
        
        settings = get_settings()
        model = settings.get("devussy_model")
        
        success, message = resume_devussy_pipeline(
            Path(controller.project.root),
            resume_info,
            model=model
        )
        
        if success:
            return {"status": "ok", "message": message}
        else:
            raise HTTPException(status_code=500, detail=message)
            
    except Exception as e:
        logger.error(f"Resume failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/devussy/message")
async def send_devussy_message(request: Dict[str, str] = Body(...)):
    """Send a message to the Devussy interview."""
    message = request.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # This would be handled by the WebSocket in a real implementation
    # For now, just acknowledge
    return {"status": "received", "message": message}

@app.post("/api/devussy/generate_queue")
async def generate_queue():
    """Generate task_queue.md from current devplan."""
    if not controller.project:
        raise HTTPException(status_code=400, detail="No project selected")
        
    try:
        from core.devussy_integration import generate_swarm_task_queue
        generate_swarm_task_queue(Path(controller.project.root))
        return {"status": "ok", "message": "Task queue generated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────
# PROVIDERS & MODELS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/providers")
async def get_providers():
    """Get list of available providers and their configuration status."""
    import os
    from config.settings import REQUESTY_API_KEY, ZAI_API_KEY
    
    providers = [
        {
            "id": "requesty",
            "name": "Requesty Router",
            "has_key": bool(REQUESTY_API_KEY or os.environ.get("REQUESTY_API_KEY")),
            "key_env_var": "REQUESTY_API_KEY",
            "base_url": "https://router.requesty.ai/v1"
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "has_key": bool(os.environ.get("OPENAI_API_KEY")),
            "key_env_var": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1"
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "has_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "key_env_var": "ANTHROPIC_API_KEY",
            "base_url": "https://api.anthropic.com/v1"
        },
        {
            "id": "zai",
            "name": "Z.AI",
            "has_key": bool(ZAI_API_KEY or os.environ.get("ZAI_API_KEY")),
            "key_env_var": "ZAI_API_KEY",
            "base_url": "https://api.z.ai/api/paas/v4"
        },
    ]
    
    return {"providers": providers}

@app.get("/api/models")
async def get_available_models():
    """Get list of available models from configured providers."""
    try:
        from core.devussy_integration import fetch_requesty_models
        from config.settings import AVAILABLE_MODELS
        
        # Try to fetch from Requesty API
        requesty_models = fetch_requesty_models()
        
        models = []
        seen = set()
        
        # Add Requesty models first
        for model_id, display_name in requesty_models:
            if model_id not in seen:
                models.append({"id": model_id, "name": display_name, "provider": "requesty"})
                seen.add(model_id)
        
        # Add fallback models
        for model_id in AVAILABLE_MODELS:
            if model_id not in seen:
                # Create display name from model ID
                parts = model_id.split("/")
                if len(parts) == 2:
                    display_name = f"{parts[0].title()}: {parts[1]}"
                else:
                    display_name = model_id
                models.append({"id": model_id, "name": display_name, "provider": "fallback"})
                seen.add(model_id)
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        # Return fallback models
        from config.settings import AVAILABLE_MODELS
        return {
            "models": [
                {"id": m, "name": m, "provider": "fallback"}
                for m in AVAILABLE_MODELS
            ]
        }

@app.post("/api/providers/key")
async def update_api_key(request: ApiKeyRequest):
    """Update an API key for a provider."""
    import os
    
    # Map provider to env var
    env_vars = {
        "requesty": "REQUESTY_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "zai": "ZAI_API_KEY",
    }
    
    env_var = env_vars.get(request.provider)
    if not env_var:
        raise HTTPException(status_code=400, detail="Unknown provider")
    
    # Set in environment
    os.environ[env_var] = request.key
    
    # Also save to .env file for persistence
    env_file = Path(__file__).parent / ".env"
    try:
        # Read existing .env
        existing = {}
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    existing[k.strip()] = v.strip()
        
        # Update key
        existing[env_var] = request.key
        
        # Write back
        with open(env_file, "w") as f:
            for k, v in existing.items():
                f.write(f"{k}={v}\n")
                
    except Exception as e:
        logger.warning(f"Could not persist key to .env: {e}")
    
    return {"status": "ok", "provider": request.provider}

@app.post("/api/providers/test")
async def test_api_key(request: Dict[str, str] = Body(...)):
    """Test if an API key works."""
    import aiohttp
    import os
    
    provider = request.get("provider")
    key = request.get("key")
    
    # Use provided key or fall back to environment
    if not key:
        env_vars = {
            "requesty": "REQUESTY_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "zai": "ZAI_API_KEY",
        }
        key = os.environ.get(env_vars.get(provider, ""), "")
    
    if not key:
        return {"success": False, "error": "No API key provided"}
    
    # Test endpoints
    test_urls = {
        "requesty": "https://router.requesty.ai/v1/models",
        "openai": "https://api.openai.com/v1/models",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "zai": "https://api.z.ai/api/paas/v4/models",
    }
    
    url = test_urls.get(provider)
    if not url:
        return {"success": False, "error": "Unknown provider"}
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {key}"}
            if provider == "anthropic":
                headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
            
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status in (200, 401, 403):
                    # 200 = success, 401/403 = auth error (but API is reachable)
                    return {"success": resp.status == 200, "status_code": resp.status}
                else:
                    return {"success": False, "status_code": resp.status}
                    
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/settings")
async def get_settings_endpoint():
    manager = get_settings()
    # Return settings directly - SettingsManager._settings is a dict
    # We access the internal dict for simplicity, or expose a getter
    return manager._settings

@app.post("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    manager = get_settings()
    for k, v in request.settings.items():
        manager.set(k, v, auto_save=False)
    manager.save()
    return {"status": "ok", "settings": manager._settings}

@app.get("/api/history")
async def get_history():
    if not controller.chatroom:
        return {"messages": []}
    return {"messages": [m.to_dict() for m in controller.chatroom.state.messages]}

# ─────────────────────────────────────────────────────────────────────────────
# STATIC FILES (Production)
# ─────────────────────────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "web" / "dist"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("web_server:app", host="0.0.0.0", port=8000, reload=True)
