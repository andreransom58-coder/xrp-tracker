#!/usr/bin/env bash
set -euo pipefail

mkdir -p /app/data

python -m app.collector &
COLLECTOR_PID=$!

uvicorn app.mcp_server:app --host 0.0.0.0 --port 8000 &
API_PID=$!

cleanup() {
  kill $COLLECTOR_PID || true
  kill $API_PID || true
}

trap cleanup EXIT

wait $COLLECTOR_PID $API_PID
