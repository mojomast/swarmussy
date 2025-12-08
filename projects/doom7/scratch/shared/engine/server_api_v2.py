from flask import Flask, request, jsonify, Response
from typing import Dict, Any

# Simple in-process runtime surface wiring for Phase 2 OpenAPI contract
# Exposes the following endpoints under /v2:
# - GET /editor/level -> returns a Level contract
# - POST /editor/level -> upserts a Level
# - GET /engine/render_stats -> returns RenderStats snapshot
# - GET /events/stream -> Server-Sent Events stream of simple events

# In-memory store for levels (phase 2 surface)
_levels: Dict[str, Dict[str, Any]] = {}

# Simple stats surface
_render_stats: Dict[str, Any] = {
    "frames_rendered": 0,
    "average_fps": 60.0,
    "memory_mb": 512.0,
}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/v2/editor/level", methods=["GET"])
    def get_level():
        # Return the first level if present, else a sensible default
        if _levels:
            # return first inserted level
            level = next(iter(_levels.values()))
            return jsonify(level)
        default = {
            "level_id": "level_01",
            "name": "Intro Level",
            "version": "v2.0",
            "content": {"entities": [], "assets": []},
        }
        return jsonify(default)

    @app.route("/v2/editor/level", methods=["POST"])
    def upsert_level():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"code": "INVALID_INPUT", "message": "Invalid payload"}), 400
        required = ["level_id", "name", "version", "content"]
        if not all(k in data for k in required):
            return jsonify({"code": "INVALID_INPUT", "message": "Missing required fields"}), 400
        level_id = data["level_id"]
        _levels[level_id] = {
            "level_id": level_id,
            "name": data["name"],
            "version": data["version"],
            "content": data["content"],
        }
        return jsonify(_levels[level_id])

    @app.route("/v2/engine/render_stats", methods=["GET"])
    def get_render_stats():
        # Flatten a snapshot that increases frames_rendered to simulate activity
        _render_stats["frames_rendered"] = int(_render_stats.get("frames_rendered", 0)) + 60
        return jsonify(_render_stats)

    @app.route("/v2/events/stream", methods=["GET"])
    def stream_events():
        def generate():
            # Emit a few sample events and then close
            for i in range(3):
                yield f"data: {{'event_type':'frame_rendered','frame':{i},'ms':{i*16}}}\n\n"
                import time
                time.sleep(0.05)
        return Response(generate(), mimetype="text/event-stream")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
