#!/usr/bin/env python3
import sys
from pathlib import Path

# Locate the workspace manifest (prefer scratch/shared/Cargo.toml in this repo layout)
script_path = Path(__file__).resolve()
workspace_root = script_path.parents[3].resolve()  # scratch/shared
workspace_toml = workspace_root / 'Cargo.toml'

if not workspace_toml.exists():
    print("0|", file=sys.stderr)
    sys.exit(0)

try:
    import tomli as toml  # type: ignore
except Exception:
    try:
        import tomllib as toml  # Python 3.11+
    except Exception:
        print(" tomli or tomllib is required to parse TOML", file=sys.stderr)
        sys.exit(1)

with open(workspace_toml, 'rb') as f:
    data = toml.load(f)

members = data.get('workspace', {}).get('members', [])
for m in members:
    print(m)
