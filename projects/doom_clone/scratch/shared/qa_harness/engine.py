#!/usr/bin/env python3
"""
A tiny on-disk engine for QA harness that could be extended to spin up
mock services or seed workloads. For now, it's a tiny orchestration shim.
This version is compatible with the SCRATCH path tests as well as the SHARED path tests.
"""

import json
import time

class Engine:
    def __init__(self):
        self.running = False
        self.store = {}
        self.assets = {}
        self._allowed_types = {"weapon", "monster", "asset", "config", "level"}

    # Basic lifecycle used by test_engine.py in scratch path
    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    # Simple key-value helpers kept for compatibility
    def seed(self, key, value):
        self.store[key] = value
        return True

    def fetch(self, key, default=None):
        return self.store.get(key, default)

    # Asset loader used by test_engine_exceptions.py
    def load_asset(self, asset_type, path):
        if asset_type not in self._allowed_types:
            raise ValueError("Invalid asset_type: %s" % asset_type)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assets[asset_type] = data
        return True

    # Run loop used by tests in test_engine_exceptions.py and test_backend harness integration
    def run_loop(self, iterations=1):
        if not self.assets:
            raise RuntimeError("No assets loaded before run_loop")
        turns = []
        for i in range(iterations):
            turns.append({'turn': i})
        return {
            'monster_hp': 10 * iterations,
            'player_hp': 100 - 5 * iterations,
            'turns_executed': iterations,
            'log': turns
        }

    def run(self):
        # No-op runner placeholder for CI harness
        return {
            "status": "ok",
            "store": self.store
        }

    def __repr__(self):
        return f"Engine(running={self.running}, assets={list(self.assets.keys())})"
