import pytest

from scratch.shared.qa_harness.engine import Engine


def test_engine_initialization():
    eng = Engine()
    assert eng.running is False


def test_engine_start_stop():
    eng = Engine()
    eng.start()
    assert eng.running is True
    eng.stop()
    assert eng.running is False
