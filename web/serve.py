"""
Smart Bot OS v5.0 — Beta Launch Live Backend & Web Server
Serves the multi-page public SPA website and dispatches REST APIs via backend.main
directly connected to SQLite WAL (botdata.db) & Discord OAuth.
"""

import http.server
import socketserver
import os
import sys
import json
import urllib.parse
import webbrowser

# Add parent directory to sys.path to import backend modules
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from backend import main as backend_router

PORT = 8080
WEB_DIR = os.path.dirname(os.path.abspath(__file__))


class LiveDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        auth_header = self.headers.get("Authorization", "").replace("Bearer ", "").strip() or None

        if path.startswith("/api/"):
            status_code, response_data = backend_router.handle_api_request(
                method="GET",
                path=path,
                query=query,
                body_json=None,
                auth_header=auth_header
            )
            return self._send_json(response_data, status=status_code)

        # Fallback to static web assets (HTML, CSS, JS)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        auth_header = self.headers.get("Authorization", "").replace("Bearer ", "").strip() or None

        body_json = None
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > 0:
            try:
                raw_body = self.rfile.read(content_len).decode("utf-8")
                body_json = json.loads(raw_body)
            except Exception:
                body_json = None

        if path.startswith("/api/"):
            status_code, response_data = backend_router.handle_api_request(
                method="POST",
                path=path,
                query=query,
                body_json=body_json,
                auth_header=auth_header
            )
            return self._send_json(response_data, status=status_code)

        self.send_error(404, "Not Found")


def run():
    os.chdir(WEB_DIR)
    with socketserver.TCPServer(("", PORT), LiveDashboardHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"==================================================")
        print(f"🚀 Smart Bot OS Beta Launch Server running at: {url}")
        print(f"📡 Serving Multi-Page Public Website & Live Backend APIs")
        print(f"📁 Root directory: {WEB_DIR}")
        print(f"Press Ctrl+C to stop the server.")
        print(f"==================================================")

        try:
            if "--open" in sys.argv:
                webbrowser.open(url)
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    run()
