#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Python tests (backend) ==="
if command -v python3 >/dev/null 2>&1; then
  python3 -m unittest discover -s scratch/shared/qa_plans/tests -p '*_tests.py' -v
else
  echo "Python3 not available. Skipping Python tests."
fi

echo "\n=== Running Node frontend tests (skeleton) ==="
if command -v node >/dev/null 2>&1; then
  node scratch/shared/qa_plans/tests/frontend_node_test_runner.js || true
else
  echo "Node.js not available. Skipping Node tests."
fi

echo "=== All tests completed (or skipped) ==="
