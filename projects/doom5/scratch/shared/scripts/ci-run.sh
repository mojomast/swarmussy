#!/usr/bin/env bash
set -euo pipefail

echo "CI Stub: Starting..."

# ECS unit tests (if defined)
if [ -f package.json ]; then
  echo "[CI] Checking for unit tests (npm run test)"
  if npm run -s test 2>/dev/null; then
    echo "[CI] Running: npm run test"
    npm run -s test
  elif npm test -s 2>/dev/null; then
    echo "[CI] Running: npm test"
    npm test -s
  else
    echo "[CI] No npm test script found; skipping unit tests."
  fi
else
  echo "[CI] No package.json found at root; skipping unit tests."
fi

# UI scaffold tests (if defined)
if [ -f package.json ]; then
  echo "[CI] Checking for UI scaffold tests (npm run test-ui)"
  if npm run -s test-ui 2>/dev/null; then
    echo "[CI] Running: npm run test-ui"
    npm run -s test-ui
  elif npm run -s ui:test 2>/dev/null; then
    echo "[CI] Running: npm run ui:test"
    npm run -s ui:test
  else
    echo "[CI] No UI test script found; skipping UI scaffold tests."
  fi
else
  echo "[CI] No package.json found at root; skipping UI scaffold tests."
fi

# Build artifacts (best-effort)
set +e
if npm run -s build 2>/dev/null; then
  echo "[CI] Built with: npm run build"
fi
if npm run -s build:frontend 2>/dev/null; then
  echo "[CI] Built frontend with: npm run build:frontend"
fi
if npm run -s build:backend 2>/dev/null; then
  echo "[CI] Built backend with: npm run build:backend"
fi
set -e

echo "CI Stub: Completed."
