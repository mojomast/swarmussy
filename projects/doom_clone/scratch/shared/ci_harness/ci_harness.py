#!/usr/bin/env python3
"""
Lightweight CI harness for the desktop app (engine/editor/assets).

Usage:
  - Requires environment variable DESKTOP_APP_CLI pointing to the CLI binary/script.
  - Optional: CI_HARNESS_VERBOSE=1 for verbose logs.

Exit codes:
  0 on all tests pass; non-zero on any failure.

This harness implements a small, deterministic asset lifecycle test:
  - Health check
  - Asset create -> list -> get -> update -> delete -> verify
"""
import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


def log(message: str) -> None:
    verbose = os.environ.get("CI_HARNESS_VERBOSE")
    if verbose:
        print(message)


def run_cli(args: List[str]) -> Tuple[int, str, str]:
    cli = os.environ.get("DESKTOP_APP_CLI")
    if not cli:
        raise RuntimeError("DESKTOP_APP_CLI environment variable is not set to the CLI binary path.")

    cmd = [cli] + args
    log(f"Running CLI: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        raise RuntimeError("CLI command timed out after 60 seconds.")
    code = proc.returncode
    log(f"CLI stdout: {stdout.strip()}")
    if stderr.strip():
        log(f"CLI stderr: {stderr.strip()}")
    return code, stdout, stderr


def expect_json(text: str) -> Any:
    text = text.strip()
    if not text:
        raise ValueError("Expected JSON output, got empty string.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Output is not valid JSON: {e}\nOutput: {text}")


def health_check() -> None:
    code, out, err = run_cli(["health"])
    if code != 0:
        raise RuntimeError(f"Health check failed with exit code {code}. stderr: {err}")
    # Try to parse as JSON; if not JSON, just ensure non-empty.
    if out:
        try:
            data = expect_json(out)
            if isinstance(data, dict) and data.get("status") == "healthy":
                return
        except Exception:
            pass
    # If not JSON with status, accept any non-empty output as success
    if not out:
        raise RuntimeError("Health check produced no output.")


def create_asset(name: str, asset_type: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = {
        "name": name,
        "type": asset_type,
    }
    if metadata:
        payload["metadata"] = metadata
    code, out, err = run_cli(["assets", "create", "--data", json.dumps(payload)])
    if code != 0:
        raise RuntimeError(f"Create asset failed. exit={code}, stderr={err}")
    data = expect_json(out)
    if not isinstance(data, dict) or not data.get("id"):
        raise RuntimeError(f"Create asset did not return an asset with id. Output: {out}")
    return data


def list_assets() -> List[Dict[str, Any]]:
    code, out, err = run_cli(["assets", "list", "--format", "json"])
    if code != 0:
        raise RuntimeError(f"List assets failed. exit={code}, stderr={err}")
    data = expect_json(out)
    if not isinstance(data, list):
        raise RuntimeError(f"List assets did not return a list. Output: {out}")
    return data


def get_asset(asset_id: str) -> Dict[str, Any]:
    code, out, err = run_cli(["assets", "get", "--id", asset_id, "--format", "json"])
    if code != 0:
        raise RuntimeError(f"Get asset failed. exit={code}, stderr={err}")
    data = expect_json(out)
    if not isinstance(data, dict):
        raise RuntimeError(f"Get asset did not return an object. Output: {out}")
    return data


def update_asset(asset_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    code, out, err = run_cli(["assets", "update", "--id", asset_id, "--data", json.dumps(updates)])
    if code != 0:
        raise RuntimeError(f"Update asset failed. exit={code}, stderr={err}")
    data = expect_json(out)
    if not isinstance(data, dict):
        raise RuntimeError(f"Update asset did not return an object. Output: {out}")
    return data


def delete_asset(asset_id: str) -> None:
    code, out, err = run_cli(["assets", "delete", "--id", asset_id])
    if code != 0:
        raise RuntimeError(f"Delete asset failed. exit={code}, stderr={err}")


def invalid_command() -> None:
    code, out, err = run_cli(["assets", "invalid"])
    if code == 0:
        raise RuntimeError("Invalid command unexpectedly succeeded.")
    log("Invalid command returned non-zero as expected.")


def main() -> int:
    try:
        # Health check first
        health_check()
        log("Health check passed.")

        # Validate error handling for invalid commands
        invalid_command()

        # Asset lifecycle test
        asset_name = "qa_asset_01_" + os.environ.get("CI_BUILD_NUMBER", "0")
        asset_type = "texture"
        initial_metadata = {"description": "QA lifecycle asset", "version": 1}

        created = create_asset(asset_name, asset_type, initial_metadata)
        asset_id = created.get("id")
        if not asset_id:
            raise RuntimeError("Created asset did not return an id.")
        log(f"Asset created with id={asset_id}")

        # List includes the asset
        assets = list_assets()
        if not any(a.get("id") == asset_id for a in assets):
            raise RuntimeError("Created asset not found in list.")

        # Get by id
        fetched = get_asset(asset_id)
        if fetched.get("id") != asset_id:
            raise RuntimeError("Fetched asset id mismatch.")

        # Update metadata
        updates = {"metadata": {"description": "Updated by CI harness", "version": 2}}
        updated = update_asset(asset_id, updates)
        if updated.get("metadata", {}).get("description") != updates["metadata"]["description"]:
            raise RuntimeError("Asset metadata did not update as expected.")

        # Delete asset
        delete_asset(asset_id)

        # Verify deletion
        assets_after = list_assets()
        if any(a.get("id") == asset_id for a in assets_after):
            raise RuntimeError("Asset was not deleted properly.")

        print("CI harness: All tests passed.")
        return 0
    except Exception as e:
        print(f"CI harness failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
