import requests
from threading import Thread
import time

BASE = 'http://127.0.0.1:5001'

def start_server():
    import scratch.shared.backend_server as srv
    srv.app.run(port=5001, use_reloader=False)

# Basic tests
def test_bootstrap():
    r = requests.post(f"{BASE}/profiles/bootstrap")
    assert r.status_code in (201, 409)

def test_save_load_delete():
    payload = {'id': 'u1', 'data': {'name': 'Alice'}}
    r = requests.post(f"{BASE}/profiles", json=payload)
    assert r.status_code == 201
    r2 = requests.get(f"{BASE}/profiles/{payload['id']}")
    assert r2.status_code == 200
    assert r2.json()['data'] == payload['data']
    delr = requests.delete(f"{BASE}/profiles/{payload['id']}")
    assert delr.status_code == 204
    r3 = requests.get(f"{BASE}/profiles/{payload['id']}")
    assert r3.status_code == 404

if __name__ == '__main__':
    start_server()
