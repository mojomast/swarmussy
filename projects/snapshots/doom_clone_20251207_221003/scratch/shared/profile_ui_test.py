import unittest
import requests
import time

BASE = 'http://127.0.0.1:5001'

class ProfileAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # reset state
        import subprocess
        # assume server will be started by tests; if not, spawn it
        try:
            requests.post(f"{BASE}/reset")
        except Exception:
            pass
        time.sleep(0.5)

    def test_bootstrap(self):
        r = requests.post(f"{BASE}/profiles/bootstrap")
        self.assertIn(r.status_code, [201, 409])

    def test_save_load_delete(self):
        payload = {'id': 'u1', 'data': {'name': 'Alice'}}
        r = requests.post(f"{BASE}/profiles", json=payload)
        self.assertEqual(r.status_code, 201)
        r2 = requests.get(f"{BASE}/profiles/{payload['id']}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()['data'], payload['data'])
        delr = requests.delete(f"{BASE}/profiles/{payload['id']}")
        self.assertEqual(delr.status_code, 204)
        r3 = requests.get(f"{BASE}/profiles/{payload['id']}")
        self.assertEqual(r3.status_code, 404)

if __name__ == '__main__':
    unittest.main()
