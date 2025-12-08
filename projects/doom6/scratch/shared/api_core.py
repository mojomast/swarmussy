import importlib.util
import os
from pathlib import Path

# Load the actual API core implementation from src/api_core.py
current_dir = Path(__file__).parent
src_path = current_dir / "src" / "api_core.py"
if not src_path.exists():
    raise FileNotFoundError(f"Expected source API core at {src_path}")

spec = importlib.util.spec_from_file_location("api_core_impl", str(src_path))
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)  # type: ignore

# Re-export the app object under the top-level module name for tests
app = getattr(_module, "app")
