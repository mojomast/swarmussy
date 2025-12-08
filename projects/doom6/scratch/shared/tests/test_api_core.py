import pytest
from fastapi.testclient import TestClient
from api_core import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_config_present():
    r = client.get("/config")
    assert r.status_code == 200
    data = r.json()
    assert "env" in data and "defaults" in data
    assert isinstance(data["env"], dict)
    assert isinstance(data["defaults"], dict)
