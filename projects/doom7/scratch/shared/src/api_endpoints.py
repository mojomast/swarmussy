#!/usr/bin/env python3
"""Phase 1 API consolidation and finalization layer

This module exposes a minimal, stable API surface for Phase 1 endpoints.
The endpoints are designed to be lightweight and side-effect free for the
Phase 1 consolidation pass. Real HTTP handlers would wire this into a web
framework; here we provide simple function interfaces that can be called by
frontend contracts or integration tests.
"""

from __future__ import annotations

from typing import Any, Dict

from .server_orchestrator import get_orchestrator, run_phase1_flow, get_phase1_state


def phase1_health_check() -> Dict[str, Any]:
    """Return a simple health report for Phase 1 orchestration.

    This acts as a lightweight replacement for an HTTP GET /phase1/health
    endpoint in tests.
    """
    state = get_phase1_state()
    healthy = True
    reasons = []

    if not isinstance(state, dict):
        healthy = False
        reasons.append("invalid_state")

    return {
        "healthy": healthy,
        "state": state,
        "notes": "Phase 1 orchestrator is in good standing" if healthy else "Phase 1 orchestrator state invalid",
        "version": "1.0.0",
    }


def run_phase1_optimization() -> Dict[str, Any]:
    """Run the Phase 1 optimization flow and return a summary."""
    result = run_phase1_flow()
    return {
        "completed": True,
        "summary": result,
        "version": "1.0.0",
    }


def get_phase1_summary() -> Dict[str, Any]:
    """Expose current Phase 1 summary state."""
    return get_phase1_state()
