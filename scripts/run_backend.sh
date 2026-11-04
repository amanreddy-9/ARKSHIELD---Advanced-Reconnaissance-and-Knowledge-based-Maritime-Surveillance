#!/usr/bin/env bash
# ARKSHIELD - Start FastAPI Backend Server
set -e

# Change directory to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================="
echo "  ARKSHIELD Maritime Surveillance - Backend API   "
echo "=================================================="

# Activate virtual environment if present
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
fi

# Default environment configuration
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-8000}"

echo "Starting Uvicorn server on http://$HOST:$PORT ..."
exec python3 -m uvicorn backend.main:app --host "$HOST" --port "$PORT" --reload
