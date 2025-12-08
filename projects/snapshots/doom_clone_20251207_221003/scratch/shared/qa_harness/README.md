# QA Harness: Grid API

This folder contains minimal QA harness scripts to exercise the Grid API during CI.
- grid_api_tests.py: basic health, list flows, unauthenticated access, and asset lifecycle (optional)

Usage: GRID_API_BASE_URL must be configured for tests to run. When not configured, tests gracefully skip and report.
