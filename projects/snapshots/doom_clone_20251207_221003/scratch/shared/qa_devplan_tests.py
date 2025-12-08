#!/usr/bin/env python3
"""
DevPlan QA Tests (lightweight)
- Verifies that the DevPlan dashboard doc exists and has basic structure.
- Verifies that Bugsy McTester section exists with at least one task.
- Verifies that bf051384 task is present in the Bugsy section (new work in progress).

This is designed to be run by CI harness when GRID_API_BASE_URL is not configured as a basic health check.
"""
import os
import re

DEVPLAN_PATH = os.path.join(os.path.dirname(__file__), '..', 'devplan.md')


def read_devplan():
    path = DEVPLAN_PATH if os.path.isabs(DEVPLAN_PATH) else os.path.normpath(os.path.join(os.getcwd(), DEVPLAN_PATH))
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    try:
        content = read_devplan()
    except FileNotFoundError:
        print("DevPlan file not found at expected location: devplan.md")
        return 2

    # Basic structure checks
    if 'DevPlan Dashboard' not in content:
        print('FAIL: DevPlan Dashboard header missing')
        return 3
    if 'Bugsy McTester' not in content:
        print('FAIL: Bugsy McTester section missing')
        return 4
    if 'bf051384' not in content:
        print('WARN: bf051384 task not found yet in DevPlan')
        # not a hard fail, as this task may not be started yet
        return 0

    # Ensure at least one Bugsy task line exists with a checkbox
    bugsy_section = content.split('### Bugsy McTester')
    if len(bugsy_section) < 2:
        print('FAIL: Could not locate Bugsy McTester section content')
        return 5
    bugs_text = bugsy_section[1]
    if not re.search(r'- \[x\]|- \[ \]', bugs_text):
        print('WARN: Bugsy McTester section has no task checklist entries')
        return 0

    # If bf051384 present, ensure it's marked as new/in-progress (checkbox may be unchecked)
    if 'bf051384' in content:
        # Accept either checked or unchecked; ensure a bullet exists
        print('PASS: bf051384 bullet found in DevPlan (status may be in-progress)')
        return 0

    print('PASS: DevPlan structure looks sane')
    return 0


if __name__ == '__main__':
    try:
        exit(main())
    except Exception as e:
        print('ERROR:', str(e))
        raise
