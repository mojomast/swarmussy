import json

def test_roundtrip():
  data = {"name": "world", "version": 1}
  s = json.dumps(data)
  d2 = json.loads(s)
  assert d2 == data
