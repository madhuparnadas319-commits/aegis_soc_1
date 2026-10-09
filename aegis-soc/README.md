# AEGIS SOC | Governed Agentic AI Alert Triage

**Local educational SOC prototype. Synthetic alert data only.**

This repaired project includes one consolidated Streamlit application (`app/app.py`), a FastAPI investigation runtime and dashboard API, five investigation stages, deterministic governance, SQLite persistence, analyst actions, and a local Ollama classification benchmark.

## First launch on macOS

1. **Merge** this repaired `aegis-soc/` folder into the existing `~/Desktop/aegis-soc/`. Keep your existing `.venv`, `.env`, `.git`, and the Docker n8n volume. Do not delete your current project folder. Back up any existing `database/aegis.db` before copying the bundle: the bundled database is a clean replacement with eight synthetic cases, not your old history.
2. Start Docker Desktop and Ollama if you want the n8n and LLM features. The Ollama model previously used was `qwen3:8b`.
3. Double-click `START_AEGIS_MAC.command` or use the two Terminal commands below. This launcher starts the updated backend and the main Streamlit app.
4. Open the Streamlit address shown in Terminal (usually `http://localhost:8501`).

If the macOS launcher is blocked, open Terminal in the project directory and use separate Terminal windows:

**Backend:**

```bash
cd ~/Desktop/aegis-soc
source .venv/bin/activate
python -m uvicorn api.dashboard_api:app --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd ~/Desktop/aegis-soc
source .venv/bin/activate
python -m streamlit run app/app.py
```

The API includes `GET /health`, `POST /investigate`, and `/dashboard/*` routes. The dashboard indicator should turn green once the backend can read SQLite. The bundled `database/aegis.db` begins with **eight cases and zero investigations**; perform a real synthetic-alert investigation through Streamlit to populate history.

## Application structure

- `app/app.py`: full original-style dark Streamlit application with all ten SOC sections in a single Python file. No separate Streamlit pages are required.
- `api/aegis_api.py`: real five-stage investigation endpoint.
- `api/dashboard_api.py`, `dashboard_routes.py`: live case, investigation, queue, and audit endpoints.
- `agents/`: LLM correlation and incident-summary agents, deterministic TI, asset context, risk governance, and orchestration.
- `database/aegis.db`: freshly initialized SQLite with the original runtime tables and three analyst-action tables. `database/schema.sql` documents the native schema.
- `scripts/initialize_database.py`: safe initializer that adds missing synthetic cases without erasing an existing database.
- `services/`: local review, escalation, and audit persistence.
- `evaluation/`: three-model Ollama evaluation. **No benchmark results are fabricated.**
- `tests/`: automated unit/API integration and offline fake-model smoke tests.
- `workflows/`: n8n export instructions, not an invented workflow export. Your n8n workflow remains in your existing Docker volume.

## Verification and limits

During repair, **15 pytest checks passed**. A running FastAPI server returned HTTP 200 for `/health`, `/dashboard/overview`, `/dashboard/cases`, `/dashboard/alerts`, and `/dashboard/queues/human-review`. Full three-route investigations were tested using **deterministic fake LLM responses** against a temporary database. These tests verify the Python/SQLite/API wiring, **not live inference quality**.

The actual Mac Streamlit UI, Ollama inference, and your Docker-hosted n8n workflow could not be exercised inside the repair sandbox. The separate n8n Autonomous and HITL paths were verified earlier in your live environment; the Escalation path was not fully tested. This package does not contain the n8n workflow JSON because it resides in the user's Docker volume, not the uploaded folder.

The original `aegis.db` was missing from your ZIP. **Lost investigation history cannot be recreated** without a real backup; the new database does not invent past AI decisions. Keep backups of the database before overwriting the bundle in the future.

The local analyst identifiers are not authentication. There is no production authorization, rate limiting, or TLS. This is not suitable for exposure to a public network or real production security systems, and it does not execute banking or firewall actions.

## Additional help

See `APP_INSTALL_GUIDE.md` for troubleshooting, starting and stopping services, n8n production URL configuration, database initialization, and evaluation.
