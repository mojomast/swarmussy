"""
Project Bootstrap - Automatic project setup before swarm work begins.

Handles:
1. Python .venv creation and activation
2. requirements.txt installation
3. Node.js node_modules installation  
4. Basic directory structure creation
5. .gitignore setup

This runs as "Phase 0" before any devplan tasks execute.
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class ProjectBootstrap:
    """
    Handles automatic project environment setup.
    
    Called after devussy pipeline completes but before swarm tasks start.
    
    NOTE: .venv is created at PROJECT ROOT (not in shared/) so that agent tools
    operating inside shared/ don't see it and bloat their context with dependency trees.
    """
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.shared_dir = self.project_path / "scratch" / "shared"
        # Place .venv at project root, NOT in shared/ - keeps it out of agent view
        self.venv_path = self.project_path / ".venv"
        self._log_callback = None
        
    def set_log_callback(self, callback):
        """Set callback for status messages."""
        self._log_callback = callback
    
    def _log(self, message: str):
        """Log a message."""
        logger.info(f"[Bootstrap] {message}")
        if self._log_callback:
            try:
                self._log_callback(f"🔧 Bootstrap: {message}")
            except:
                pass
    
    def detect_project_type(self) -> Dict[str, bool]:
        """
        Detect what kind of project this is based on devplan/design files.
        
        Returns dict with flags for different project types.
        """
        flags = {
            "python": False,
            "node": False,
            "typescript": False,
            "react": False,
            "fastapi": False,
            "flask": False,
            "django": False,
            "godot": False,
            "unity": False,
        }
        
        # Check design file
        design_file = self.shared_dir / "project_design.md"
        devplan_file = self.shared_dir / "devplan.md"
        
        content = ""
        if design_file.exists():
            content += design_file.read_text(encoding="utf-8").lower()
        if devplan_file.exists():
            content += devplan_file.read_text(encoding="utf-8").lower()
        
        # Detect project types
        if any(kw in content for kw in ["python", "pip", "pytest", "fastapi", "flask", "django", ".py"]):
            flags["python"] = True
        if any(kw in content for kw in ["fastapi", "fast api"]):
            flags["fastapi"] = True
        if any(kw in content for kw in ["flask"]):
            flags["flask"] = True
        if any(kw in content for kw in ["django"]):
            flags["django"] = True
        if any(kw in content for kw in ["node", "npm", "yarn", "package.json", "javascript"]):
            flags["node"] = True
        if any(kw in content for kw in ["typescript", ".ts", ".tsx"]):
            flags["typescript"] = True
        if any(kw in content for kw in ["react", "jsx", "tsx", "next.js", "nextjs"]):
            flags["react"] = True
        if any(kw in content for kw in ["godot", "gdscript", ".gd"]):
            flags["godot"] = True
        if any(kw in content for kw in ["unity", "c#", ".cs"]):
            flags["unity"] = True
        
        return flags
    
    def create_directory_structure(self, project_types: Dict[str, bool]) -> List[str]:
        """Create basic directory structure based on project type."""
        created = []
        
        # Always create these
        base_dirs = ["src", "tests", "docs", "config"]
        
        for d in base_dirs:
            dir_path = self.shared_dir / d
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created.append(str(d))
        
        # Python-specific
        if project_types.get("python"):
            for d in ["src/__pycache__", "tests/__pycache__"]:
                (self.shared_dir / d).mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py files
            for init_path in [self.shared_dir / "src" / "__init__.py", 
                             self.shared_dir / "tests" / "__init__.py"]:
                if not init_path.exists():
                    init_path.write_text("", encoding="utf-8")
        
        # Node-specific
        if project_types.get("node") or project_types.get("react"):
            for d in ["src/components", "src/lib", "public"]:
                dir_path = self.shared_dir / d
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created.append(str(d))
        
        return created
    
    def setup_python_venv(self) -> Tuple[bool, str]:
        """
        Create Python virtual environment and install dependencies.
        
        The .venv is created at PROJECT ROOT (not shared/) so agents don't see it.
        Requirements are still installed from shared/requirements.txt.
        
        Returns (success, message).
        """
        if self.venv_path.exists():
            self._log(f".venv already exists at {self.venv_path}, skipping creation")
            return True, "venv already exists"
        
        self._log(f"Creating Python virtual environment at {self.venv_path}...")
        
        try:
            # Create venv at project root (not in shared/)
            result = subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_path),  # Run from project root
            )
            
            if result.returncode != 0:
                return False, f"Failed to create venv: {result.stderr}"
            
            self._log(f"✅ Created .venv at project root (outside shared/)")
            
            # Determine pip path
            if os.name == 'nt':  # Windows
                pip_path = self.venv_path / "Scripts" / "pip.exe"
                python_path = self.venv_path / "Scripts" / "python.exe"
            else:  # Unix
                pip_path = self.venv_path / "bin" / "pip"
                python_path = self.venv_path / "bin" / "python"
            
            # Upgrade pip
            subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                timeout=120,
                cwd=str(self.project_path),
            )
            
            # Ensure requirements.txt in shared/ exists and includes pytest
            requirements_file = self.shared_dir / "requirements.txt"
            if requirements_file.exists():
                try:
                    existing = requirements_file.read_text(encoding="utf-8")
                except Exception:
                    existing = ""
                if "pytest" not in existing:
                    self._log("Ensuring pytest is present in requirements.txt...")
                    # Preserve existing content, just append pytest on its own line
                    updated = (existing.rstrip() + "\npytest\n") if existing else "pytest\n"
                    requirements_file.write_text(updated, encoding="utf-8")
            else:
                # Create basic requirements.txt in shared/ with pytest included
                self._log("Creating basic requirements.txt in shared/... (with pytest)")
                requirements_file.write_text(
                    "# Project requirements\n# Add your dependencies here\npytest\n",
                    encoding="utf-8"
                )

            # Install requirements from shared/
            self._log("Installing requirements.txt...")
            result = subprocess.run(
                [str(pip_path), "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.shared_dir),  # Run from shared/ for relative paths
            )
            if result.returncode == 0:
                self._log("✅ Installed requirements (including pytest)")
            else:
                self._log(f"⚠️ Some requirements failed: {result.stderr[:200]}")
            
            return True, f"venv created at {self.venv_path}"
            
        except subprocess.TimeoutExpired:
            return False, "Timeout creating venv"
        except Exception as e:
            return False, f"Error creating venv: {e}"
    
    def setup_node_project(self) -> Tuple[bool, str]:
        """
        Initialize Node.js project if needed.
        
        Returns (success, message).
        """
        package_json = self.shared_dir / "package.json"
        node_modules = self.shared_dir / "node_modules"
        
        if node_modules.exists():
            self._log("node_modules already exists, skipping npm install")
            return True, "node_modules exists"
        
        if not package_json.exists():
            self._log("No package.json found, skipping Node setup")
            return True, "no package.json"
        
        self._log("Installing npm dependencies...")
        
        try:
            # Check if npm is available
            npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
            
            result = subprocess.run(
                [npm_cmd, "install"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.shared_dir),
            )
            
            if result.returncode == 0:
                self._log("✅ Installed npm dependencies")
                return True, "npm install completed"
            else:
                self._log(f"⚠️ npm install had issues: {result.stderr[:200]}")
                return False, result.stderr[:200]
                
        except FileNotFoundError:
            self._log("⚠️ npm not found, skipping Node setup")
            return False, "npm not found"
        except subprocess.TimeoutExpired:
            return False, "npm install timeout"
        except Exception as e:
            return False, f"npm error: {e}"
    
    def create_gitignore(self) -> bool:
        """Create .gitignore if it doesn't exist."""
        gitignore_path = self.shared_dir / ".gitignore"
        
        if gitignore_path.exists():
            return True
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/
dist/
build/
.eggs/

# Node
node_modules/
npm-debug.log
yarn-error.log

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Build artifacts
*.log
*.tmp
"""
        
        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        self._log("Created .gitignore")
        return True
    
    def run_bootstrap(self) -> Dict[str, Any]:
        """
        Run the full bootstrap process.
        
        Returns dict with results.
        """
        self._log("Starting project bootstrap...")
        
        results = {
            "success": True,
            "project_types": {},
            "dirs_created": [],
            "venv_status": "",
            "node_status": "",
            "errors": [],
        }
        
        # Ensure shared dir exists
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        
        # Detect project type
        results["project_types"] = self.detect_project_type()
        self._log(f"Detected project types: {[k for k, v in results['project_types'].items() if v]}")
        
        # Create directory structure
        results["dirs_created"] = self.create_directory_structure(results["project_types"])
        if results["dirs_created"]:
            self._log(f"Created directories: {', '.join(results['dirs_created'])}")
        
        # Python setup
        if results["project_types"].get("python"):
            success, msg = self.setup_python_venv()
            results["venv_status"] = msg
            if not success:
                results["errors"].append(f"venv: {msg}")
        
        # Node setup
        if results["project_types"].get("node") or results["project_types"].get("react"):
            success, msg = self.setup_node_project()
            results["node_status"] = msg
            if not success and "not found" not in msg.lower():
                results["errors"].append(f"node: {msg}")
        
        # Create gitignore
        self.create_gitignore()
        
        results["success"] = len(results["errors"]) == 0
        
        if results["success"]:
            self._log("✅ Bootstrap complete!")
        else:
            self._log(f"⚠️ Bootstrap completed with issues: {results['errors']}")
        
        return results


async def run_project_bootstrap(project_path: Path, log_callback=None) -> Dict[str, Any]:
    """
    Async wrapper to run project bootstrap.
    
    Call this after devussy pipeline but before dispatching tasks.
    """
    import asyncio
    
    bootstrap = ProjectBootstrap(project_path)
    if log_callback:
        bootstrap.set_log_callback(log_callback)
    
    # Run in thread to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, bootstrap.run_bootstrap)
    
    return result
