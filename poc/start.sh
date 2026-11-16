#!/bin/sh
# PID 1 supervises Uvicorn. A single, synthetic smoke-run logs results for QA.
set -eu
PORT="${PORT:-8000}"
python -m uvicorn poc_app:app --host 0.0.0.0 --port "$PORT" &
APP_PID=$!
(
  sleep 9
  ASTROLOGER_TEST_API_KEY="${PRIVATE_ASTROLOGER_API_SECRET_KEY:-}" \
    python poc/smoke.py "http://127.0.0.1:$PORT" || true
) &
SMOKE_PID=$!
trap 'kill "$APP_PID" "$SMOKE_PID" 2>/dev/null || true' TERM INT
wait "$APP_PID"
