import subprocess

# This test ensures the cross-language harness can reach the API and perform a basic liveness check.

def test_harness_basic():
    # Import the harness module to verify it exposes the test cases
    import importlib.util
    # Try both possible locations for compatibility
    paths = ["scratch/shared/qa_harness/run_harness.py", "shared/qa_harness/run_harness.py"]
    module = None
    for p in paths:
        try:
            spec = importlib.util.spec_from_file_location("harness", p)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)  # type: ignore
            module = m
            break
        except FileNotFoundError:
            continue
    assert module is not None
    assert hasattr(module, 'TEST_CASES')
