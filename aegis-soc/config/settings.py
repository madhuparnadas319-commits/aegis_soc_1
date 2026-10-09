"""Typed runtime settings with safe defaults for local AEGIS SOC prototype."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    api_url: str
    n8n_webhook_url: str
    ollama_url: str
    database_path: Path
    ollama_model: str
    request_timeout: int


def load_settings() -> Settings:
    path = Path(os.getenv("AEGIS_DB_PATH", str(ROOT / "database" / "aegis.db"))).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    return Settings(
        api_url=os.getenv("AEGIS_API_URL", "http://localhost:8000").rstrip("/"),
        n8n_webhook_url=os.getenv("AEGIS_N8N_WEBHOOK_URL", ""),
        ollama_url=os.getenv("AEGIS_OLLAMA_URL", "http://localhost:11434").rstrip("/"),
        database_path=path.resolve(),
        ollama_model=os.getenv("AEGIS_MODEL", "qwen3:8b"),
        request_timeout=max(5, int(os.getenv("AEGIS_TIMEOUT", "300"))),
    )
