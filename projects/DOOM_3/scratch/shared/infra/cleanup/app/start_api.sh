#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
REPO_API_URL="${REPO_API_URL:-}"
REPO_API_BRANCH="${REPO_API_BRANCH:-main}"

if [ -n "$REPO_API_URL" ]; then
  echo "[repo-backend] Cloning API from $REPO_API_URL (branch: $REPO_API_BRANCH)"
  rm -rf /repo_api
  git clone --depth 1 --single-branch --branch "$REPO_API_BRANCH" "$REPO_API_URL" /repo_api
  cd /repo_api
  if [ -f requirements.txt ]; then
    echo "[repo-backend] Installing repo requirements..."
    python -m pip install --upgrade pip
    pip install --no-cache-dir -r requirements.txt
  fi
  if [ -f setup.py ]; then
    echo "[repo-backend] Installing repo package..."
    pip install --no-cache-dir .
  fi
  if [ -f main.py ]; then
    echo "[repo-backend] Running uvicorn: main:app"
    uvicorn main:app --host 0.0.0.0 --port "$PORT"
  elif [ -f app.py ]; then
    echo "[repo-backend] Running uvicorn: app:app"
    uvicorn app:app --host 0.0.0.0 --port "$PORT"
  else
    echo "[repo-backend] No entrypoint (main.py or app.py) found in repo." >&2
    exit 1
  fi
else
  echo "[local] Running local Cleanup API: uvicorn main:app"
  if [ -f main.py ]; then
    uvicorn main:app --host 0.0.0.0 --port "$PORT"
  else
    echo "[local] No local entrypoint main.py found." >&2
    exit 1
  fi
fi
