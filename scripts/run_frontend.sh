#!/usr/bin/env bash
# ARKSHIELD - Start React Vite Frontend
set -e

# Change directory to frontend directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/frontend"

echo "=================================================="
echo "  ARKSHIELD Maritime Surveillance - Frontend UI   "
echo "=================================================="

# Check node modules
if [ ! -d "node_modules" ]; then
    echo "node_modules not found. Running npm install..."
    npm install
fi

echo "Starting Vite dev server on http://localhost:5173 ..."
exec npm run dev
