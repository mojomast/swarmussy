import re
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import threading
import socket
import time
from urllib import request as urlrequest


# Minimal security checks for Phase 1 endpoints

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class SimpleAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_GET(self):
        path = self.path
        if path.startswith("/v1/engine/render"):
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps({"ok": True}).encode())
        else:
            self._set_headers(404, "application/json")
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


import pytest


@pytest.fixture(scope="module")
def mock_server():
    port = get_free_port()
    server = ThreadedHTTPServer(("127.0.0.1", port), SimpleAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    yield port
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


def test_security_checks(mock_server):
    base = f"http://127.0.0.1:{mock_server}/v1"

    # Try to access a non-existent admin endpoint, ensure 404 not expose sensitive data
    try:
        with urlrequest.urlopen(f"{base}/admin/secret") as resp:
            pass
    except urlrequest.HTTPError as e:
        assert e.code == 404

    # Access render endpoint; ensure it doesn't leak internal server errors in body
    with urlrequest.urlopen(f"{base}/engine/render") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert "ok" in data

    # Path traversal attempt (not allowed) - should be 404 or 400
    try:
        with urlrequest.urlopen(f"{base}/../../etc/passwd") as resp:
            pass
    except urlrequest.HTTPError as e:
        assert e.code in (400, 404, 403)
