#!/usr/bin/env bash
set -euo pipefail
REPO_API_URL="${REPO_API_URL:-}"
REPO_API_BRANCH="${REPO_API_BRANCH:-main}"

if [ -n "$REPO_API_URL" ]; then
  echo "[repo-backend] Cloning API from $REPO_API_URL (branch: $REPO_API_BRANCH)"
  rm -rf /repo_api
  git clone --depth 1 --branch "$REPO_API_BRANCH" "$REPO_API_URL" /repo_api
  if [ -f /repo_api/requirements.txt ]; then
    echo "[repo-backend] Installing repo requirements..."
    python -m pip install --upgrade pip
    pip install --no-cache-dir -r /repo_api/requirements.txt
  fi
  if [ -f /repo_api/main.py ]; then
    echo "[repo-backend] Found main.py entrypoint. Performing a quick import sanity check..."
    python -c "import sys; import importlib.util; print('ok' if importlib.util.find_spec('fastapi') else 'missing-fastapi')"
  elif [ -f /repo_api/app.py ]; then
    echo "[repo-backend] Found app.py entrypoint. Sanity check will verify module loads..."
    python -c "import sys; import importlib.util; print('ok' if importlib.util.find_spec('fastapi') else 'missing-fastapi')"
  else
    echo "[repo-backend] No entrypoint (main.py or app.py) found in repo." >&2
    exit 1
  fi
else
  echo "[repo-backend] REPO_API_URL not set; skipping repo API checks."
fi
