#!/usr/bin/env python3
"""
DevPlan Dashboard Consistency Test

Verifies basic structural integrity of the Doom Clone Dev Plan Dashboard file.
"""
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DASHBOARD_PATH = os.path.join(BASE_DIR, 'devplan_dashboard.md')


def read_dashboard(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    if not os.path.exists(DASHBOARD_PATH):
        print(f"FAIL: Dashboard file not found at {DASHBOARD_PATH}")
        return 2
    content = read_dashboard(DASHBOARD_PATH)

    required_snippets = [
        'Doom Clone Dev Plan Dashboard',
        'Active tasks by Owner',
        'Bugsy McTester',
        'Status: In Progress'
    ]
    for s in required_snippets:
        if s not in content:
            print(f"FAIL: Dashboard missing expected section or header: {s}")
            return 3

    # Basic sanity: at least one owner task present
    if 'Codey McBackend' not in content and 'Pixel McFrontend' not in content:
        print('WARN: No owner tasks found in dashboard; expected at least one task entry')
        return 0

    print('PASS: DevPlan Dashboard structure appears sane')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print('ERROR:', e)
        sys.exit(1)
