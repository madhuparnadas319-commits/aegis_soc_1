"""Additive AEGIS FastAPI launch module.

Importing the existing `api.aegis_api:app` retains /health and /investigate,
then adds new /dashboard/* routes without overwriting the existing API code.

Use `api.dashboard_api:app` as the FastAPI application entrypoint if the
new dashboard endpoints are wanted. See APP_INSTALL_GUIDE.md.
"""

from api.aegis_api import app
from api.dashboard_routes import router

# Avoid double-registration if this module is reloaded in the same process.
if not any(getattr(route, "path", "") == "/dashboard/overview" for route in app.routes):
    app.include_router(router)

__all__ = ["app"]
