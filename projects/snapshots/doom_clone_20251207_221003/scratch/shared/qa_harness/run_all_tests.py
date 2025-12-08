import importlib.util
import inspect
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

QA_ROOT = Path(__file__).resolve().parent
TESTS_DIR = QA_ROOT / 'tests'


def load_module_from_path(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def get_test_functions(module) -> list:
    funcs = []
    for name in dir(module):
        if name.startswith('test_'):
            obj = getattr(module, name)
            if callable(obj):
                funcs.append(obj)
    return funcs


def run_test_function(func: Callable) -> bool:
    # Prepare fixtures if required
    kwargs = {}
    sig = inspect.signature(func)
    params = sig.parameters
    if 'tmp_path' in params:
        with TemporaryDirectory() as td:
            kwargs['tmp_path'] = Path(td)
            try:
                result = func(**kwargs)
            except Exception as e:
                print(f"Test {func.__name__} raised exception: {e}")
                return False
            return_value = result
    else:
        try:
            result = func(**kwargs)
        except Exception as e:
            print(f"Test {func.__name__} raised exception: {e}")
            return False
        return_value = result

    # Treat None as pass if no exception occurred
    if return_value is None:
        return True
    return bool(return_value)


def main():
    results = {}
    total = 0
    passes = 0
    for fname in sorted(TESTS_DIR.glob('test_*.py')):
        mod = load_module_from_path(fname)
        tests = get_test_functions(mod)
        for t in tests:
            total += 1
            ok = run_test_function(t)
            results[f"{fname.stem}.{t.__name__}"] = ok
            if ok:
                passes += 1
    print("==== Quick Check Summary ====")
    for k, v in results.items():
        print(f"{k}: {'PASS' if v else 'FAIL'}")
    print(f"Total: {total}, Pass: {passes}, Fail: {total - passes}")
    sys.exit(0 if passes == total else 1)


if __name__ == '__main__':
    main()
