"""
Localhost Bridge Server
Listens on http://127.0.0.1:48123 to receive video URLs directly from the UserScript
and feed them into the CLI/TUI download queue.
"""

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class BridgeQueue:
    """Thread-safe queue for incoming bridge URLs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._items: list[dict[str, Any]] = []
        self._listeners: list[Callable[[dict[str, Any]], None]] = []

    def add_batch(self, platform: str, urls: list[str]) -> int:
        with self._lock:
            entry = {
                "platform": platform,
                "urls": urls,
                "count": len(urls),
            }
            self._items.append(entry)
            listeners_copy = list(self._listeners)

        for cb in listeners_copy:
            try:
                cb(entry)
            except Exception:
                pass
        return len(urls)

    def subscribe(self, callback: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def get_all_pending(self) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._items)
            self._items.clear()
            return items

    @property
    def total_count(self) -> int:
        with self._lock:
            return sum(item["count"] for item in self._items)


GLOBAL_BRIDGE_QUEUE = BridgeQueue()


class _BridgeRequestHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests with CORS support for UserScript integration."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            resp = {
                "status": "online",
                "app": "f0rkdownloader",
                "pending": GLOBAL_BRIDGE_QUEUE.total_count,
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/queue":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)

                platform = data.get("platform", "generic")
                urls = data.get("urls", [])

                if not isinstance(urls, list):
                    urls = [urls]

                count = GLOBAL_BRIDGE_QUEUE.add_batch(platform, urls)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "received": count}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP logging to stdout
        pass


class LocalBridgeServer:
    """Background HTTP server for browser UserScript communication."""

    def __init__(self, host: str = "127.0.0.1", port: int = 48123):
        self.host = host
        self.port = port
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self._running = False

    def start(self) -> bool:
        """Start the bridge server in a daemon thread."""
        if self._running:
            return True

        try:
            self.server = ThreadingHTTPServer((self.host, self.port), _BridgeRequestHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self._running = True
            return True
        except Exception:
            self._running = False
            return False

    def stop(self) -> None:
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
