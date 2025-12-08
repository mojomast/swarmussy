#!/usr/bin/env python3
"""Phase 1 and Phase 2 Orchestrator

This module provides a lightweight, deterministic orchestration layer for
Phase 1 and Phase 2 backlogs. It supports generic lifecycle flows:
- audit, prune, freeze, implement, integrate, prune_final
- automatic kickoff of Phase 2 backlog upon Phase 1 completion
- idempotent initialization of Phase 2 backlog
- thread-safe state management via per-phase locks
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class Phase1Orchestrator:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        # Phase 1 backlog with a few placeholder tasks, mirroring the Phase 1 cadence
        self.backlog: List[Dict[str, Any]] = [
            {"id": "P1-001", "name": "Audit completed Phase 1 work", "status": "completed"},
            {"id": "P1-002", "name": "Prune completed Phase 1 tasks from backlog", "status": "completed"},
            {"id": "P1-003", "name": "Freeze Phase 1 scope to critical remaining items", "status": "pending"},
            {"id": "P1-004", "name": "Implement remaining critical Phase 1 features", "status": "pending"},
        ]
        self.scope_frozen: bool = False
        self.remaining_items: List[Dict[str, Any]] = []
        self.integration_result: Dict[str, Any] | None = None
        self.last_run_summary: Dict[str, Any] = {}

    def is_complete(self) -> bool:
        with self.lock:
            # Phase 1 is complete when there are no non-completed items in backlog
            return all(t.get("status") == "completed" for t in self.backlog) if self.backlog else True

    def audit_completed_work(self) -> Dict[str, Any]:
        with self.lock:
            summary = {
                "audited": True,
                "backlog_length_before": len(self.backlog),
                "completed_in_backlog": [t for t in self.backlog if t["status"] == "completed"],
            }
            logger.debug("Audit completed work: %s", summary)
            self.last_run_summary = summary
            return summary

    def prune_completed_tasks(self) -> Dict[str, Any]:
        with self.lock:
            before = len(self.backlog)
            self.backlog = [t for t in self.backlog if t["status"] != "completed"]
            after = len(self.backlog)
            pruned = before - after
            self.last_run_summary = {
                "pruned": pruned,
                "backlog_length_after_prune": after,
            }
            logger.debug("Pruned %d completed tasks; backlog now %d items", pruned, after)
            return self.last_run_summary

    def freeze_phase1_scope(self) -> Dict[str, Any]:
        with self.lock:
            # Mark the specific scope item as completed to reflect freezing
            for t in self.backlog:
                if t["id"] == "P1-003":
                    t["status"] = "completed"
            self.scope_frozen = True
            self.remaining_items = [t for t in self.backlog if t["status"] != "completed"]
            summary = {
                "scope_frozen": self.scope_frozen,
                "remaining_items": [item["id"] for item in self.remaining_items],
            }
            logger.debug("Phase 1 scope frozen; remaining items: %s", summary["remaining_items"])
            self.last_run_summary = summary
            return summary

    def implement_critical_features(self) -> Dict[str, Any]:
        with self.lock:
            implemented_any = False
            for t in self.backlog:
                if t["id"] == "P1-004" and t["status"] != "completed":
                    t["status"] = "completed"
                    implemented_any = True
                    break
            self.remaining_items = [t for t in self.backlog if t["status"] != "completed"]
            summary = {
                "implemented_any": implemented_any,
                "remaining_after_implementation": [item["id"] for item in self.remaining_items],
            }
            logger.debug("Implemented critical features: %s", implemented_any)
            self.last_run_summary = summary
            return summary

    def integrate_with_modules(self) -> Dict[str, Any]:
        with self.lock:
            # Placeholder integration step with other modules (frontend contracts, DB schemas, etc.)
            integration = {
                "integrated": True,
                "notes": "Phase 1 consolidation integrated with contracts and schemas",
            }
            self.integration_result = integration
            logger.debug("Integration results: %s", integration)
            self.last_run_summary = integration
            return integration

    def prune_final_state(self) -> Dict[str, Any]:
        with self.lock:
            before = len(self.backlog)
            self.backlog = [t for t in self.backlog if t["status"] != "completed"]
            after = len(self.backlog)
            pruned = before - after
            summary = {"backlog_length_final": after, "pruned_final": pruned}
            logger.debug("Final prune: pruned %d, backlog now %d", pruned, after)
            self.last_run_summary = summary
            return summary

    def run_all(self) -> Dict[str, Any]:
        # Phases executed in order
        self.audit_completed_work()
        self.prune_completed_tasks()
        self.freeze_phase1_scope()
        self.implement_critical_features()
        self.integrate_with_modules()
        self.prune_final_state()

        # Kick off Phase 2 backlog automatically when Phase 1 backlog is effectively complete
        if self.is_complete():
            try:
                _global_phase2_orchestrator.initialize_backlog()
                logger.debug("Phase 2 backlog initialized from Phase 1 completion")
            except Exception as e:
                logger.exception("Failed to initialize Phase 2 backlog: %s", e)
        # Return a composite summary of latest state
        with self.lock:
            final_state = {
                "scope_frozen": self.scope_frozen,
                "backlog": self.backlog,
                "remaining_items": self.remaining_items,
            }
            return {"phase1_final_state": final_state}

    def get_state(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "scope_frozen": self.scope_frozen,
                "backlog": self.backlog,
                "remaining_items": self.remaining_items,
            }


class Phase2Orchestrator:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        # Separate Phase 2 backlog
        self.backlog: List[Dict[str, Any]] = []
        self.scope_frozen: bool = False
        self.remaining_items: List[Dict[str, Any]] = []
        self.integration_result: Dict[str, Any] | None = None
        self.last_run_summary: Dict[str, Any] = {}

    def is_complete(self) -> bool:
        with self.lock:
            return all(t.get("status") == "completed" for t in self.backlog) if self.backlog else True

    def initialize_backlog(self) -> Dict[str, Any]:
        with self.lock:
            if len(self.backlog) == 0:
                self.backlog = [
                    {"id": "P2-101", "name": "Initialize Phase 2 environment", "status": "pending"},
                    {"id": "P2-102", "name": "Freeze Phase 2 scope to approved items", "status": "pending"},
                    {"id": "P2-103", "name": "Implement Phase 2 core features", "status": "pending"},
                    {"id": "P2-104", "name": "Integrate Phase 2 with modules", "status": "pending"},
                ]
                self.scope_frozen = False
                self.remaining_items = [t for t in self.backlog if t["status"] != "completed"]
            else:
                logger.debug("Phase 2 backlog already initialized; idempotent path taken")
            self.last_run_summary = {
                "initialized": True,
                "backlog_length": len(self.backlog),
            }
            return self.get_state()

    def prune_completed_tasks(self) -> Dict[str, Any]:
        with self.lock:
            before = len(self.backlog)
            self.backlog = [t for t in self.backlog if t["status"] != "completed"]
            after = len(self.backlog)
            pruned = before - after
            self.last_run_summary = {
                "pruned": pruned,
                "backlog_length_after_prune": after,
            }
            logger.debug("Phase2 prune: pruned %d; backlog now %d", pruned, after)
            return self.last_run_summary

    def freeze_phase2_scope(self) -> Dict[str, Any]:
        with self.lock:
            for t in self.backlog:
                if t["id"] == "P2-102":
                    t["status"] = "completed"
            self.scope_frozen = True
            self.remaining_items = [t for t in self.backlog if t["status"] != "completed"]
            summary = {
                "scope_frozen": self.scope_frozen,
                "remaining_items": [item["id"] for item in self.remaining_items],
            }
            logger.debug("Phase 2 scope frozen: %s", summary["remaining_items"])
            self.last_run_summary = summary
            return summary

    def implement_critical_features(self) -> Dict[str, Any]:
        with self.lock:
            implemented_any = False
            for t in self.backlog:
                if t["id"] == "P2-103" and t["status"] != "completed":
                    t["status"] = "completed"
                    implemented_any = True
                    break
            self.remaining_items = [t for t in self.backlog if t["status"] != "completed"]
            summary = {
                "implemented_any": implemented_any,
                "remaining_after_implementation": [item["id"] for item in self.remaining_items],
            }
            logger.debug("Phase 2 implement: %s", implemented_any)
            self.last_run_summary = summary
            return summary

    def integrate_with_modules(self) -> Dict[str, Any]:
        with self.lock:
            integration = {
                "integrated": True,
                "notes": "Phase 2 integration with modules completed",
            }
            self.integration_result = integration
            logger.debug("Phase 2 integration: %s", integration)
            self.last_run_summary = integration
            return integration

    def prune_final_state(self) -> Dict[str, Any]:
        with self.lock:
            before = len(self.backlog)
            self.backlog = [t for t in self.backlog if t["status"] != "completed"]
            after = len(self.backlog)
            pruned = before - after
            summary = {"backlog_length_final": after, "pruned_final": pruned}
            logger.debug("Phase 2 final prune: pruned %d, backlog now %d", pruned, after)
            self.last_run_summary = summary
            return summary

    def run_all(self) -> Dict[str, Any]:
        self.prune_completed_tasks()
        self.freeze_phase2_scope()
        self.implement_critical_features()
        self.integrate_with_modules()
        self.prune_final_state()
        with self.lock:
            final = {
                "scope_frozen": self.scope_frozen,
                "backlog": self.backlog,
                "remaining_items": self.remaining_items,
            }
            return {"phase2_final_state": final}

    def get_state(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "scope_frozen": self.scope_frozen,
                "backlog": self.backlog,
                "remaining_items": self.remaining_items,
            }


# Global singletons for orchestration state shared across modules
_global_phase1_orchestrator = Phase1Orchestrator()
_global_phase2_orchestrator = Phase2Orchestrator()


def get_phase1_state() -> Dict[str, Any]:
    return _global_phase1_orchestrator.get_state()


def run_phase1_flow() -> Dict[str, Any]:
    return _global_phase1_orchestrator.run_all()


def initialize_phase2_backlog() -> Dict[str, Any]:
    return _global_phase2_orchestrator.initialize_backlog()


def initialize_phase2_backlog_if_needed() -> Dict[str, Any]:
    # Kick off Phase 2 backlog if Phase 1 has completed
    try:
        if _global_phase1_orchestrator.is_complete():
            return _global_phase2_orchestrator.initialize_backlog()
    except Exception:
        # If anything goes wrong, fall back to no-op
        pass
    return _global_phase2_orchestrator.get_state()


def run_phase2_flow() -> Dict[str, Any]:
    return _global_phase2_orchestrator.run_all()


def get_phase2_state() -> Dict[str, Any]:
    return _global_phase2_orchestrator.get_state()


def get_phase2_backlog() -> List[Dict[str, Any]]:
    return _global_phase2_orchestrator.backlog


def get_git_status():  # pragma: no cover - compatibility shim
    # Helper kept for compatibility with existing tests that may import this symbol
    return {"status": "unknown"}
