import json
from shared.src.server_orchestrator import run_phase1_flow, initialize_phase2_backlog, run_phase2_flow


def test_phase1_to_phase2_kickoff():
    phase1_state = run_phase1_flow()
    assert isinstance(phase1_state, dict)
    assert phase1_state.get("phase1_final_state") is not None

    # Initialize Phase 2 backlog after Phase 1
    phase2_state = initialize_phase2_backlog()
    assert isinstance(phase2_state, dict)
    assert phase2_state.get("backlog") is not None

    # Kick off Phase 2 flow; run a few iterations
    for _ in range(3):
        res = run_phase2_flow()
        assert isinstance(res, dict)
        if res.get("phase2_final_state"):
            break
