"""Minimal Ollama-compatible mock for local LiteLLM validation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/tags":
            self._write_json(
                200,
                {
                    "models": [
                        {
                            "name": "llama3.1",
                            "model": "llama3.1",
                            "size": 0,
                            "digest": "mock",
                        }
                    ]
                },
            )
            return
        self._write_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        data = json.loads(raw.decode("utf-8") or "{}")
        model = data.get("model", "llama3.1")

        if self.path == "/api/chat":
            self._write_json(
                200,
                {
                    "model": model,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "message": {
                        "role": "assistant",
                        "content": "mock response from local ollama backend",
                    },
                    "done": True,
                },
            )
            return

        if self.path == "/api/generate":
            self._write_json(
                200,
                {
                    "model": model,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "response": "mock response from local ollama backend",
                    "done": True,
                },
            )
            return

        self._write_json(404, {"error": "not_found"})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 11435), Handler)
    server.serve_forever()
