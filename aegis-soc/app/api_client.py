"""HTTP client for the AEGIS SOC Streamlit application.

Connects the user interface to the local FastAPI runtime and, when
configured, the published n8n workflow webhook.
"""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 300


class AegisAPIError(RuntimeError):
    """Raised when an AEGIS service cannot be reached or returns an error."""


class AegisAPIClient:
    """Small, reusable HTTP client for the AEGIS SOC dashboard."""

    def __init__(
        self,
        base_url: str | None = None,
        n8n_webhook_url: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("AEGIS_API_URL") or DEFAULT_API_URL
        ).rstrip("/")
        self.n8n_webhook_url = (
            n8n_webhook_url or os.getenv("AEGIS_N8N_WEBHOOK_URL") or ""
        ).strip()
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        """Make a request and return a JSON object, or raise AegisAPIError."""
        kwargs.setdefault("timeout", (5, self.timeout))

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            raise AegisAPIError("AEGIS request timed out.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise AegisAPIError(f"Unable to connect to AEGIS service: {url}") from exc
        except requests.exceptions.HTTPError as exc:
            details = response.text[:500]
            raise AegisAPIError(
                f"AEGIS HTTP {response.status_code}: {details}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise AegisAPIError(f"AEGIS request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise AegisAPIError("AEGIS returned an invalid JSON response.") from exc

        if not isinstance(data, dict):
            raise AegisAPIError("AEGIS returned an unexpected response format.")
        return data

    def health(self) -> dict[str, Any]:
        """Retrieve health information from the FastAPI backend."""
        return self._request(
            "GET", f"{self.base_url}/health", timeout=(5, 10)
        )

    def investigate(
        self, alert_id: str, via_n8n: bool = False
    ) -> dict[str, Any]:
        """Investigate an alert through FastAPI or the n8n production webhook."""
        alert_id = alert_id.strip()
        if not alert_id:
            raise AegisAPIError("Alert ID cannot be empty.")

        if via_n8n:
            if not self.n8n_webhook_url:
                raise AegisAPIError(
                    "AEGIS_N8N_WEBHOOK_URL is not configured."
                )
            url = self.n8n_webhook_url
        else:
            url = f"{self.base_url}/investigate"

        return self._request("POST", url, json={"alert_id": alert_id})

    def is_online(self) -> bool:
        """Return whether the FastAPI backend reports healthy status."""
        try:
            return self.health().get("status") == "ok"
        except AegisAPIError:
            return False

    def close(self) -> None:
        """Release the underlying HTTP session."""
        self.session.close()


def get_api_client() -> AegisAPIClient:
    """Create a configured API client instance."""
    return AegisAPIClient()
