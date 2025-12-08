import json
import importlib.util
from pathlib import Path

ENGINE_PATH = Path(__file__).resolve().parents[1] / 'engine.py'
spec = importlib.util.spec_from_file_location("qa_engine", str(ENGINE_PATH))
qa_engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa_engine)  # type: ignore
Engine = qa_engine.Engine


def test_invalid_asset_type_raises(tmp_path: Path):
    eng = Engine()
    # create a fake file
    fpath = tmp_path / 'bad.json'
    fpath.write_text('{"a":1}', encoding='utf-8')
    try:
        eng.load_asset("not_a_type", str(fpath))
    except ValueError:
        return
    raise AssertionError("Expected ValueError for invalid asset_type")


def test_run_without_assets_raises(tmp_path: Path):
    eng = Engine()
    try:
        eng.run_loop(iterations=1)
    except RuntimeError:
        return
    raise AssertionError("Expected RuntimeError when assets not loaded before run_loop")
