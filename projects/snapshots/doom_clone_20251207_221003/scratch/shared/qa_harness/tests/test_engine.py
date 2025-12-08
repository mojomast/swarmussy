import json
import os
import io
import importlib.util
from pathlib import Path

# Dynamically load Engine from sibling module engine.py to avoid packaging issues
ENGINE_PATH = Path(__file__).resolve().parents[1] / 'engine.py'
spec = importlib.util.spec_from_file_location("qa_engine", str(ENGINE_PATH))
qa_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa_engine)  # type: ignore
Engine = qa_engine.Engine


def load_asset(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_basic_run(tmp_path):
    # Prepare assets
    weapon = {"name": "Blaster", "damage": 15}
    monster = {"name": "Goblin", "hp": 40, "defense": 3, "attack": 4}

    w_path = tmp_path / "weapon.json"
    m_path = tmp_path / "monster.json"

    with open(w_path, 'w', encoding='utf-8') as f:
        json.dump(weapon, f)
    with open(m_path, 'w', encoding='utf-8') as f:
        json.dump(monster, f)

    eng = Engine()
    eng.load_asset("weapon", str(w_path))
    eng.load_asset("monster", str(m_path))
    res = eng.run_loop(iterations=3)

    assert res["monster_hp"] >= 0
    assert res["player_hp"] <= 100
    assert len(res["log"]) == 3
