"""
Vercel Serverless Function Entrypoint for Smart Bot OS REST API.
"""

from http.server import BaseHTTPRequestHandler
import urllib.parse
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import main as backend_router


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed.query)
        status, data = backend_router.handle_api_request("GET", parsed.path, query_params)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed.query)
        length = int(self.headers.get('content-length', 0))
        body_json = None
        if length > 0:
            try:
                body_json = json.loads(self.rfile.read(length).decode('utf-8'))
            except Exception:
                pass
        status, data = backend_router.handle_api_request("POST", parsed.path, query_params, body_json=body_json)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
