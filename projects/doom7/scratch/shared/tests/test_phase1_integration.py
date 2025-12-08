import json

from shared.src.api_endpoints import phase1_health_check, run_phase1_optimization, get_phase1_summary


def test_health_endpoint():
    resp = phase1_health_check()
    assert isinstance(resp, dict)
    assert "healthy" in resp
    assert "state" in resp


def test_run_optimization():
    res = run_phase1_optimization()
    assert isinstance(res, dict)
    assert res.get("completed") is True
    assert "summary" in res


def test_summary_endpoint():
    state = get_phase1_summary()
    assert isinstance(state, dict)
    assert "scope_frozen" in state
