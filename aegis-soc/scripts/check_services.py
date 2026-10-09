"""Non-mutating local service health checker. No Ollama model inference."""

from __future__ import annotations

import json
import os

import requests


def check(name: str, url: str) -> dict:
    try:
        response = requests.get(url, timeout=5)
        return {"service": name, "url": url, "ok": response.ok,
                "status_code": response.status_code}
    except requests.RequestException as exc:
        return {"service": name, "url": url, "ok": False, "error": str(exc)}


def main() -> None:
    api = os.getenv("AEGIS_API_URL", "http://localhost:8000").rstrip("/")
    ollama = os.getenv("AEGIS_OLLAMA_URL", "http://localhost:11434").rstrip("/")
    print(json.dumps([
        check("FastAPI", f"{api}/health"),
        check("FastAPI dashboard", f"{api}/dashboard/overview"),
        check("Ollama", f"{ollama}/api/tags"),
        check("n8n", "http://localhost:5678/"),
    ], indent=2))


if __name__ == "__main__":
    main()
