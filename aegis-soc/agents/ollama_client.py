import json
import os
import time

import requests


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    os.getenv("AEGIS_OLLAMA_URL", "http://localhost:11434"),
)

DEFAULT_MODEL = os.getenv(
    "OLLAMA_MODEL",
    os.getenv("AEGIS_MODEL", "qwen3:8b"),
)


class OllamaError(RuntimeError):
    pass


def chat_json(
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    timeout: int = 300,
):
    """
    Send a governed JSON-only request to Ollama.

    Internal model thinking is explicitly disabled.
    """

    url = f"{OLLAMA_BASE_URL}/api/chat"

    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "format": "json",
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "options": {
            "temperature": 0,
        },
    }

    started = time.perf_counter()

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=timeout,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise OllamaError(
            f"Ollama request failed: {exc}"
        ) from exc

    latency_seconds = (
        time.perf_counter() - started
    )

    body = response.json()

    try:
        content = body["message"]["content"]
        parsed = json.loads(content)

    except (
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        raise OllamaError(
            "Ollama returned an invalid JSON response."
        ) from exc

    metadata = {
        "model": body.get(
            "model",
            model,
        ),
        "latency_seconds": round(
            latency_seconds,
            3,
        ),
        "total_duration_ns": body.get(
            "total_duration"
        ),
        "prompt_eval_count": body.get(
            "prompt_eval_count"
        ),
        "eval_count": body.get(
            "eval_count"
        ),
        "done_reason": body.get(
            "done_reason"
        ),
    }

    return parsed, metadata
