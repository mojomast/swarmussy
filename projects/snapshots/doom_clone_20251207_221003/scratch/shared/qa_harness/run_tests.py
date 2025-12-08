import json
from pathlib import Path
import importlib.util
from typing import Dict, Any

# Dynamic import helper to load Engine from engine.py alongside this runner
ENGINE_PATH = Path(__file__).resolve().parent / 'engine.py'
spec = importlib.util.spec_from_file_location("qa_engine", str(ENGINE_PATH))
qa_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa_engine)  # type: ignore
Engine = qa_engine.Engine


def load_asset(path: Path) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_basic_run(tmp_path: Path) -> bool:
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

    ok = True
    if res.get("monster_hp", -1) < 0:
        ok = False
    if res.get("player_hp", 0) > 100 or res.get("player_hp", 0) < 0:
        ok = False
    if len(res.get("log", [])) != 3:
        ok = False
    return ok


def test_damage_defense_clamp(tmp_path: Path) -> bool:
    weapon = {"name": "PUNCH", "damage": 5}
    monster = {"name": "Armor", "hp": 20, "defense": 8, "attack": 3}

    w_path = tmp_path / "weapon2.json"
    m_path = tmp_path / "monster2.json"
    with open(w_path, 'w', encoding='utf-8') as f:
        json.dump(weapon, f)
    with open(m_path, 'w', encoding='utf-8') as f:
        json.dump(monster, f)

    eng = Engine()
    eng.load_asset("weapon", str(w_path))
    eng.load_asset("monster", str(m_path))
    res = eng.run_loop(iterations=3)

    # Damage should have been at least 1 per turn due to clamp
    return res.get("monster_hp", 0) == 17


def test_monster_defeat_short_loop(tmp_path: Path) -> bool:
    weapon = {"name": "Rocket",
              "damage": 50}
    monster = {"name": "Dragonlet", "hp": 5, "defense": 0, "attack": 2}

    w_path = tmp_path / "weapon3.json"
    m_path = tmp_path / "monster3.json"
    with open(w_path, 'w', encoding='utf-8') as f:
        json.dump(weapon, f)
    with open(m_path, 'w', encoding='utf-8') as f:
        json.dump(monster, f)

    eng = Engine()
    eng.load_asset("weapon", str(w_path))
    eng.load_asset("monster", str(m_path))
    res = eng.run_loop(iterations=5)

    # After first turn, monster dead; second turn should note defeat and stop
    return res.get("turns_executed", 0) == 1


def run_all_tests():
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as td:
        tdir = Path(td)
        results = {
            'basic_run': test_basic_run(tdir),
            'defense_clamp': test_damage_defense_clamp(tdir),
            'defeat_short_loop': test_monster_defeat_short_loop(tdir),
        }
        all_ok = all(results.values())
        print("QA Harness Results:")
        for name, ok in results.items():
            print(f" - {name}: {'PASS' if ok else 'FAIL'}")
        return all_ok


if __name__ == '__main__':
    success = run_all_tests()
    if not success:
        raise SystemExit(1)
    else:
        print("ALL TESTS PASSED")
        raise SystemExit(0)
