import json
import socket
import time
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib import request as urlrequest


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class SimpleAPIHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_GET(self):
        path = self.path
        if path == "/v1/engine/render":
            payload = {"width": 1280, "height": 720, "data": [0, 1, 2, 3, 4, 5]}
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(payload).encode())
        elif path == "/v1/editor/level":
            payload = {
                "level_id": "level_01",
                "name": "Intro Level",
                "version": "v1.0",
                "content": {"entities": [], "assets": []},
            }
            self._set_headers(200, "application/json")
            self.wfile.write(json.dumps(payload).encode())
        elif path == "/v1/events/stream":
            self._set_headers(200, "text/event-stream")
            # Simple SSE-like payload
            self.wfile.write(b"data: {\"event_type\":\"frame_rendered\"}\n\n")
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Not Found\n")

    def do_POST(self):
        path = self.path
        if path == "/v1/editor/level":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b"{}"
            try:
                payload = json.loads(body.decode()) if body else {}
            except Exception:
                self._set_headers(400, "application/json")
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
                return
            # Validate required fields
            required = {"level_id", "name", "version", "content"}
            if required.issubset(set(payload.keys())):
                self._set_headers(200, "application/json")
                self.wfile.write(
                    json.dumps({"success": True, "level_id": payload.get("level_id")}).encode()
                )
            else:
                self._set_headers(400, "application/json")
                self.wfile.write(
                    json.dumps({"error": "Missing required fields"}).encode()
                )
        else:
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Not Found\n")

    def log_message(self, format, *args):
        return


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Phase1EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = get_free_port()
        cls.server = ThreadedHTTPServer(("127.0.0.1", cls.port), SimpleAPIHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.1)  # ensure server started
        cls.base = f"http://127.0.0.1:{cls.port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def test_engine_render(self):
        with urlrequest.urlopen(f"{self.base}/engine/render") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertIsInstance(data, dict)
            self.assertEqual(data.get("width"), 1280)
            self.assertEqual(data.get("height"), 720)
            self.assertIsInstance(data.get("data"), list)

    def test_editor_level_get(self):
        with urlrequest.urlopen(f"{self.base}/editor/level") as resp:
            self.assertEqual(resp.status, 200)
            level = json.loads(resp.read().decode())
            self.assertEqual(level["level_id"], "level_01")
            self.assertEqual(level["name"], "Intro Level")
            self.assertEqual(level["version"], "v1.0")
            self.assertIsInstance(level["content"], dict)

    def test_editor_level_post_success(self):
        payload = {
            "level_id": "level_01",
            "name": "Intro Level",
            "version": "v1.0",
            "content": {"entities": [], "assets": []},
        }
        data = json.dumps(payload).encode()
        req = urlrequest.Request(
            f"{self.base}/editor/level",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlrequest.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            result = json.loads(resp.read().decode())
            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("level_id"), payload["level_id"])

    def test_editor_level_post_bad(self):
        bad_payload = {"level_id": "level_01"}
        data = json.dumps(bad_payload).encode()
        req = urlrequest.Request(
            f"{self.base}/editor/level",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req) as resp:
                self.fail("Expected HTTPError for bad payload")
        except urlrequest.HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_events_stream(self):
        with urlrequest.urlopen(f"{self.base}/events/stream") as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))
            body = resp.read().decode()
            self.assertTrue("data:" in body)


if __name__ == '__main__':
    unittest.main()
