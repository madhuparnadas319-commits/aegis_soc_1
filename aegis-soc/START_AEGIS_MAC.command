#!/bin/bash
# AEGIS SOC macOS local launcher. Does not terminate existing unrelated services.
set -e
cd "$(dirname "$0")"
ROOT="$PWD"
PYTHON="$ROOT/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "Missing local .venv. Preserve the .venv from your original AEGIS folder."
  echo "See APP_INSTALL_GUIDE.md."
  read -r -p "Press Enter to close..." _
  exit 1
fi

API_PID=""
cleanup() {
  if [ -n "$API_PID" ]; then
    echo "Stopping the FastAPI instance started by this launcher..."
    kill "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "AEGIS SOC | Local prototype | Synthetic security alerts"
if curl -fsS --max-time 3 "http://localhost:8000/dashboard/overview" >/dev/null 2>&1; then
  echo "Dashboard FastAPI already healthy on port 8000."
elif lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8000 is occupied, but the AEGIS dashboard API isn't healthy."
  echo "Stop the older FastAPI service in its Terminal before running this launcher."
  read -r -p "Press Enter to close..." _
  exit 1
else
  "$PYTHON" -m uvicorn api.dashboard_api:app --host 0.0.0.0 --port 8000 &
  API_PID=$!
  echo "Starting dashboard backend (PID $API_PID)..."
  for i in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS --max-time 2 "http://localhost:8000/dashboard/overview" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  if ! curl -fsS --max-time 3 "http://localhost:8000/dashboard/overview" >/dev/null; then
    echo "Backend could not reach the SQLite dashboard endpoint. Check its log above."
    read -r -p "Press Enter to close..." _
    exit 1
  fi
fi
if ! curl -fsS --max-time 3 "http://localhost:11434/api/tags" >/dev/null 2>&1; then
  echo "NOTE: Ollama is offline. Open Ollama before running an AI investigation."
fi
if ! curl -fsS --max-time 3 "http://localhost:5678" >/dev/null 2>&1; then
  echo "NOTE: n8n is offline. Direct FastAPI investigation mode is still available."
fi
echo "Starting Streamlit dashboard..."
"$PYTHON" -m streamlit run "$ROOT/app/app.py"
