"""
Devussy Pipeline Integration for Swarm Chat.

This module integrates the Devussy development planning pipeline with the
multi-agent swarm system. When enabled, Devussy generates a devplan and phases
that the swarm treats as its work specification.

The Architect (Bossy McArchitect) becomes a pure orchestrator - it doesn't
decide what to build, it only delegates work based on the devplan.

In SWARM MODE, the devplan is generated with:
- Pre-assigned agent roles for each task
- Tool call suggestions for agents
- Dependency graphs for parallel execution
- Acceptance criteria for task completion
"""

import asyncio
import threading
import shutil
import sys
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

# Add devussy to path
DEVUSSY_PATH = Path(__file__).parent.parent / "devussy"
if str(DEVUSSY_PATH) not in sys.path:
    sys.path.insert(0, str(DEVUSSY_PATH))

# Agent role definitions for swarm mode
SWARM_AGENTS = {
    "backend_dev": {
        "name": "Codey McBackend",
        "specialization": "Python, APIs, server logic, databases",
        "tools": ["write_file", "read_file", "run_command", "search_code"],
    },
    "frontend_dev": {
        "name": "Pixel McFrontend", 
        "specialization": "React, UI/UX, CSS, components",
        "tools": ["write_file", "read_file", "run_command"],
    },
    "qa_engineer": {
        "name": "Bugsy McTester",
        "specialization": "Testing, pytest, security, code review",
        "tools": ["read_file", "write_file", "run_command"],
    },
    "devops": {
        "name": "Deployo McOps",
        "specialization": "Docker, CI/CD, deployment",
        "tools": ["write_file", "run_command"],
    },
    "tech_writer": {
        "name": "Docy McWriter",
        "specialization": "Documentation, README, guides",
        "tools": ["write_file", "read_file"],
    },
    "database_specialist": {
        "name": "Schema McDatabase",
        "specialization": "DB design, migrations, SQL",
        "tools": ["write_file", "run_command"],
    },
    "api_designer": {
        "name": "Swagger McEndpoint",
        "specialization": "API specs, OpenAPI, contracts",
        "tools": ["write_file", "read_file"],
    },
}


class DevussyPipelineRunner:
    """Runs the Devussy pipeline and integrates outputs with swarm projects."""
    
    def __init__(self, project_path: Path, model: Optional[str] = None):
        """Initialize with target project path.
        
        Args:
            project_path: Path to the swarm project (e.g., projects/my_project/)
            model: Optional model override for devussy pipeline (e.g., "anthropic/claude-sonnet-4-20250514")
        """
        self.project_path = Path(project_path)
        self.scratch_shared = self.project_path / "scratch" / "shared"
        self.output_dir: Optional[Path] = None
        self.model = model
        
    def ensure_directories(self):
        """Create required directories."""
        self.scratch_shared.mkdir(parents=True, exist_ok=True)
        
    def run_interactive_pipeline(self, verbose: bool = False) -> Tuple[bool, str]:
        """Run the Devussy interactive pipeline.
        
        This runs the full devussy interview and planning pipeline:
        1. Interactive Q&A about the project
        2. Complexity analysis
        3. Design generation
        4. DevPlan generation with phases
        5. Handoff document creation
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            from src.cli import (
                _load_app_config,
                _resolve_requesty_api_key,
                interactive_design,
                _render_splash,
            )
            from src.config import load_config

            # Suppress splash in integrated mode
            os.environ["DEVUSSY_NO_SPLASH"] = "1"

            # Output directly to the project's scratch folder
            self.ensure_directories()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = self.project_path.name or "project"

            # Use project's scratch/devussy folder for outputs
            self.output_dir = self.scratch_shared.parent / "devussy" / f"{project_name}_{timestamp}"
            self.output_dir.mkdir(parents=True, exist_ok=True)

            print("\n" + "=" * 60)
            print("🔮 DEVUSSY PIPELINE - Project Planning")
            print("=" * 60)
            print(f"\nProject: {project_name}")
            print(f"Output: {self.output_dir}")
            print("\nThis will guide you through defining your project.")
            print("The swarm will then execute the generated plan.\n")

            if self.model:
                print(f"📡 Using model: {self.model}\n")

            original_cwd = os.getcwd()
            error: Optional[BaseException] = None

            def _run_interactive() -> None:
                nonlocal error
                try:
                    os.chdir(DEVUSSY_PATH)
                    # Run the interactive design command (may use asyncio.run() internally)
                    interactive_design(
                        config_path=str(DEVUSSY_PATH / "config" / "config.yaml"),
                        provider="requesty" if self.model else None,
                        model=self.model,
                        output_dir=str(self.output_dir),
                        temperature=None,
                        max_tokens=None,
                        select_model=False,
                        save_session=None,
                        resume_session=None,
                        llm_interview=True,
                        scripted=False,
                        streaming=True,  # Enable streaming for better UX
                        verbose=verbose,
                        debug=False,
                    )
                except BaseException as e:  # Capture all exceptions to re-raise in caller
                    error = e
                finally:
                    os.chdir(original_cwd)

            # If an event loop is already running (e.g. inside the swarm TUI),
            # run the blocking Devussy CLI in a background thread so its internal
            # asyncio.run() calls are not nested inside the main loop.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                thread = threading.Thread(target=_run_interactive, daemon=True)
                thread.start()
                thread.join()
            else:
                _run_interactive()

            if error is not None:
                raise error

            # Find and copy the generated files to scratch/shared
            return self._copy_outputs_to_project()

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Devussy pipeline failed: {e}"
    
    def _find_devussy_output_folder(self) -> Optional[Path]:
        """Find the most recent devussy output folder.
        
        Search priority:
        1. Explicit output_dir set during run
        2. Project's scratch/devussy folder
        3. Devussy's own outputs folder (fallback)
        """
        search_locations = [
            # Priority 1: Explicit output dir
            self.output_dir,
            # Priority 2: Project's scratch folder
            self.scratch_shared.parent / "devussy",
            self.scratch_shared,
            # Priority 3: Devussy's outputs (fallback for older runs)
            DEVUSSY_PATH / "outputs",
            # Priority 4: CWD locations (legacy)
            Path.cwd() / "devussy_output",
        ]
        
        all_candidates = []
        
        for base in search_locations:
            if not base or not base.exists():
                continue
                
            # Check for devplan.md directly in this folder
            if (base / "devplan.md").exists():
                all_candidates.append(base)
                
            # Check subdirectories
            for subdir in base.iterdir():
                if subdir.is_dir() and not subdir.name.startswith("."):
                    if (subdir / "devplan.md").exists():
                        all_candidates.append(subdir)
                    # Check one level deeper
                    for subsubdir in subdir.iterdir():
                        if subsubdir.is_dir() and (subsubdir / "devplan.md").exists():
                            all_candidates.append(subsubdir)
        
        if not all_candidates:
            return None
            
        # Return most recently modified
        return max(all_candidates, key=lambda p: p.stat().st_mtime)
    
    def _copy_outputs_to_project(self) -> Tuple[bool, str]:
        """Copy devussy outputs to the project's scratch/shared folder.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        self.ensure_directories()
        
        # Find the devussy output folder
        project_folder = self._find_devussy_output_folder()
        
        if not project_folder:
            return False, "No devussy output folder with devplan.md found"
        
        print(f"[COPY] Found devussy output at: {project_folder}")
        
        copied_files = []
        
        # Files to copy
        files_to_copy = {
            "devplan.md": "devplan.md",
            "project_design.md": "project_design.md", 
            "handoff_prompt.md": "handoff.md",
        }
        
        for src_name, dst_name in files_to_copy.items():
            src_file = project_folder / src_name
            if src_file.exists():
                dst_file = self.scratch_shared / dst_name
                shutil.copy2(src_file, dst_file)
                copied_files.append(dst_name)
                print(f"[COPY] {src_name} -> {dst_name}")
        
        # Copy phase files
        phase_files = list(project_folder.glob("phase*.md"))
        if phase_files:
            phases_dir = self.scratch_shared / "phases"
            phases_dir.mkdir(exist_ok=True)
            
            for phase_file in phase_files:
                dst_file = phases_dir / phase_file.name
                shutil.copy2(phase_file, dst_file)
                copied_files.append(f"phases/{phase_file.name}")
            
            # Also create a combined phases.md for easy reference
            combined_phases = self.scratch_shared / "phases.md"
            with open(combined_phases, "w", encoding="utf-8") as f:
                f.write("# Implementation Phases\n\n")
                f.write("This file combines all phase documents for reference.\n\n")
                f.write("---\n\n")
                for phase_file in sorted(phase_files):
                    f.write(f"## {phase_file.stem.replace('_', ' ').title()}\n\n")
                    content = phase_file.read_text(encoding="utf-8")
                    # Skip the first heading if it exists
                    lines = content.split("\n")
                    if lines and lines[0].startswith("#"):
                        content = "\n".join(lines[1:])
                    f.write(content.strip())
                    f.write("\n\n---\n\n")
            copied_files.append("phases.md")
            print(f"[COPY] {len(phase_files)} phase files + combined phases.md")
        
        if copied_files:
            return True, f"Copied to project: {', '.join(copied_files)}"
        else:
            return False, "No devussy output files found to copy"


# =============================================================================
# PIPELINE RESUME FUNCTIONALITY
# =============================================================================

# Pipeline stages in order (for resume selection)
PIPELINE_STAGES = [
    ("interview", "Interview / Q&A", ["interview_data.json"]),
    ("project_design", "Project Design", ["project_design.md"]),
    ("design_review", "Design Review", ["design_review.md"]),
    ("basic_devplan", "Basic DevPlan", ["devplan.md"]),
    ("detailed_devplan", "Detailed DevPlan", ["phase1.md", "phase2.md"]),
    ("handoff", "Handoff Prompt", ["handoff_prompt.md"]),
]


def list_devussy_artifacts(project_path: Path) -> Dict[str, Any]:
    """List all available devussy artifacts from a project.
    
    Searches the project's scratch/devussy folder for previous pipeline runs.
    
    Args:
        project_path: Path to the swarm project
        
    Returns:
        Dict with:
        - runs: List of previous runs with their artifacts
        - checkpoints: List of available checkpoints
    """
    result = {
        "runs": [],
        "checkpoints": [],
        "latest_run": None,
    }
    
    devussy_dir = project_path / "scratch" / "devussy"
    
    # Find all runs (timestamped folders)
    if devussy_dir.exists():
        for run_dir in sorted(devussy_dir.iterdir(), reverse=True):
            if not run_dir.is_dir() or run_dir.name.startswith("."):
                continue
            
            run_info = {
                "path": str(run_dir),
                "name": run_dir.name,
                "artifacts": [],
                "stages_complete": [],
            }
            
            # Check which artifacts exist
            artifact_files = [
                ("project_design.md", "project_design", "Project Design"),
                ("design_review.md", "design_review", "Design Review"),
                ("devplan.md", "basic_devplan", "Basic DevPlan"),
                ("handoff_prompt.md", "handoff", "Handoff Prompt"),
                ("complexity_profile.md", "complexity", "Complexity Profile"),
            ]
            
            for filename, stage, display_name in artifact_files:
                if (run_dir / filename).exists():
                    run_info["artifacts"].append(filename)
                    run_info["stages_complete"].append(stage)
            
            # Check for phase files
            phase_files = list(run_dir.glob("phase*.md"))
            if phase_files:
                run_info["artifacts"].extend([p.name for p in phase_files])
                run_info["stages_complete"].append("detailed_devplan")
                run_info["phase_count"] = len(phase_files)
            
            if run_info["artifacts"]:
                result["runs"].append(run_info)
                if not result["latest_run"]:
                    result["latest_run"] = run_info
    
    # Find checkpoints from StateManager
    try:
        from src.state_manager import StateManager
        sm = StateManager(str(project_path / ".devussy_state"))
        checkpoints = sm.list_checkpoints()
        result["checkpoints"] = checkpoints
    except Exception as e:
        print(f"[WARN] Could not load checkpoints: {e}")
    
    return result


def select_resume_stage(artifacts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Interactive selection of which stage to resume from.
    
    Args:
        artifacts: Result from list_devussy_artifacts()
        
    Returns:
        Dict with resume info (run, stage) or None if cancelled
    """
    runs = artifacts.get("runs", [])
    checkpoints = artifacts.get("checkpoints", [])
    
    if not runs and not checkpoints:
        print("\n❌ No previous devussy runs found.")
        return None
    
    print("\n" + "=" * 60)
    print("🔄 RESUME DEVUSSY PIPELINE")
    print("=" * 60)
    
    options = []
    
    # List runs with their available stages
    print("\n📁 Previous Runs:")
    for i, run in enumerate(runs[:5], 1):  # Show last 5 runs
        print(f"\n  {i}. {run['name']}")
        stages = run.get("stages_complete", [])
        print(f"     Stages: {', '.join(stages)}")
        if "phase_count" in run:
            print(f"     Phases: {run['phase_count']} files")
        options.append(("run", run))
    
    # List checkpoints
    if checkpoints:
        print("\n💾 Checkpoints:")
        for j, ckpt in enumerate(checkpoints[:5], len(runs) + 1):
            print(f"  {j}. {ckpt['key']} ({ckpt['stage']}) - {ckpt['timestamp'][:16]}")
            options.append(("checkpoint", ckpt))
    
    print(f"\n  0. Cancel / Start fresh")
    print()
    
    choice = input("Select run/checkpoint to resume from [0]: ").strip()
    
    if not choice or choice == "0":
        return None
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            option_type, option_data = options[idx]
            
            if option_type == "run":
                # Ask which stage to resume from
                run = option_data
                stages = run.get("stages_complete", [])
                
                print(f"\n📍 Resume from which stage?")
                for s_idx, stage in enumerate(stages, 1):
                    print(f"  {s_idx}. After {stage}")
                print(f"  0. Cancel")
                
                stage_choice = input("Stage [1]: ").strip() or "1"
                s_idx = int(stage_choice) - 1
                
                if 0 <= s_idx < len(stages):
                    return {
                        "type": "run",
                        "run_path": run["path"],
                        "resume_after": stages[s_idx],
                    }
            else:
                # Checkpoint
                return {
                    "type": "checkpoint",
                    "checkpoint_key": option_data["key"],
                    "stage": option_data["stage"],
                }
    except (ValueError, IndexError):
        pass
    
    return None


def resume_devussy_pipeline(
    project_path: Path,
    resume_info: Dict[str, Any],
    model: Optional[str] = None,
    verbose: bool = False,
) -> Tuple[bool, str]:
    """Resume devussy pipeline from a previous stage.
    
    Args:
        project_path: Path to the swarm project
        resume_info: Resume info from select_resume_stage()
        model: Optional model override
        verbose: Enable verbose output
        
    Returns:
        Tuple of (success, message)
    """
    try:
        from src.config import load_config
        from src.state_manager import StateManager
        from src.pipeline.compose import PipelineOrchestrator
        from src.clients.factory import create_llm_client
        from src.concurrency import ConcurrencyManager
        from src.file_manager import FileManager
        from src.models import DevPlan, ProjectDesign
        
        # Output to project's scratch folder
        scratch_shared = project_path / "scratch" / "shared"
        scratch_shared.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = scratch_shared.parent / "devussy" / f"resume_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 60)
        print("🔄 RESUMING DEVUSSY PIPELINE")
        print("=" * 60)
        print(f"\nOutput: {output_dir}")
        
        # Change to devussy directory
        original_cwd = os.getcwd()
        os.chdir(DEVUSSY_PATH)
        
        try:
            # Load config and create components
            config = load_config()
            if model:
                config.model = model
            
            llm_client = create_llm_client(config)
            conc = ConcurrencyManager(config.max_concurrent_requests)
            file_mgr = FileManager()
            
            orch = PipelineOrchestrator(
                llm_client=llm_client,
                concurrency_manager=conc,
                file_manager=file_mgr,
                git_config=config.git,
                config=config,
            )
            
            resume_type = resume_info.get("type")
            
            if resume_type == "checkpoint":
                # Load from checkpoint
                checkpoint_key = resume_info["checkpoint_key"]
                sm = StateManager()
                ckpt = sm.load_checkpoint(checkpoint_key)
                
                if not ckpt:
                    return False, f"Checkpoint not found: {checkpoint_key}"
                
                data = ckpt.get("data", {})
                stage = ckpt.get("stage", "")
                
                print(f"📍 Loaded checkpoint from stage: {stage}")
                
                # Resume based on stage
                return _resume_from_checkpoint_data(
                    orch, file_mgr, data, stage, output_dir, scratch_shared
                )
                
            elif resume_type == "run":
                # Load from artifacts
                run_path = Path(resume_info["run_path"])
                resume_after = resume_info["resume_after"]
                
                print(f"📍 Resuming after stage: {resume_after}")
                print(f"📂 Loading from: {run_path}")
                
                return _resume_from_artifacts(
                    orch, file_mgr, run_path, resume_after, output_dir, scratch_shared
                )
                
        finally:
            os.chdir(original_cwd)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Resume failed: {e}"


def _resume_from_checkpoint_data(
    orch, file_mgr, data: Dict, stage: str, output_dir: Path, scratch_shared: Path
) -> Tuple[bool, str]:
    """Resume from checkpoint data based on stage."""
    import asyncio
    from src.models import DevPlan, ProjectDesign
    
    try:
        if stage == "project_design":
            # Have design, need devplan
            design = ProjectDesign.model_validate(data["project_design"])
            print("✅ Loaded project design, generating devplan...")
            
            # Generate basic devplan
            basic = asyncio.run(orch.basic_devplan_gen.generate(
                design.project_name,
                design.summary or "",
                design.tech_stack,
            ))
            
            # Generate detailed devplan
            detailed = asyncio.run(orch.detailed_devplan_gen.generate(
                basic,
                project_name=design.project_name,
                tech_stack=design.tech_stack,
            ))
            
            # Write outputs
            _write_devplan_outputs(orch, file_mgr, detailed, design, output_dir)
            _copy_to_shared(output_dir, scratch_shared)
            
            return True, "Resumed from project_design, generated devplan"
            
        elif stage == "basic_devplan":
            # Have basic devplan, need detailed
            design = ProjectDesign.model_validate(data["project_design"])
            basic = DevPlan.model_validate(data["basic_devplan"])
            
            print("✅ Loaded basic devplan, generating detailed phases...")
            
            detailed = asyncio.run(orch.detailed_devplan_gen.generate(
                basic,
                project_name=design.project_name,
                tech_stack=design.tech_stack,
            ))
            
            _write_devplan_outputs(orch, file_mgr, detailed, design, output_dir)
            _copy_to_shared(output_dir, scratch_shared)
            
            return True, "Resumed from basic_devplan, generated detailed phases"
            
        elif stage == "detailed_devplan":
            # Have detailed devplan, just need handoff
            design = ProjectDesign.model_validate(data["project_design"])
            detailed = DevPlan.model_validate(data["detailed_devplan"])
            
            print("✅ Loaded detailed devplan, generating handoff...")
            
            handoff = orch.handoff_gen.generate(
                devplan=detailed,
                project_name=design.project_name,
                project_summary=detailed.summary or "",
                architecture_notes=design.architecture_overview or "",
            )
            
            file_mgr.write_markdown(str(output_dir / "handoff_prompt.md"), handoff.content)
            
            # Also write devplan outputs
            _write_devplan_outputs(orch, file_mgr, detailed, design, output_dir)
            _copy_to_shared(output_dir, scratch_shared)
            
            return True, "Resumed from detailed_devplan, generated handoff"
            
        else:
            return False, f"Unknown stage: {stage}"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Resume from checkpoint failed: {e}"


def _resume_from_artifacts(
    orch, file_mgr, run_path: Path, resume_after: str, output_dir: Path, scratch_shared: Path
) -> Tuple[bool, str]:
    """Resume from artifact files."""
    import asyncio
    import json
    
    try:
        # Try to load project design from markdown (parse key fields)
        design_file = run_path / "project_design.md"
        if not design_file.exists():
            return False, "project_design.md not found in run folder"
        
        design_content = design_file.read_text(encoding="utf-8")
        
        # Extract project name from title
        import re
        name_match = re.search(r'^#\s+(.+?)(?:\n|$)', design_content, re.MULTILINE)
        project_name = name_match.group(1).strip() if name_match else "Project"
        
        # Copy existing artifacts to output
        print(f"📋 Copying existing artifacts from {run_path.name}...")
        for src_file in run_path.glob("*.md"):
            dst_file = output_dir / src_file.name
            shutil.copy2(src_file, dst_file)
        
        if resume_after == "project_design":
            # Need to regenerate from design
            print("🔄 Regenerating devplan from project design...")
            
            # Try to load from checkpoint if available
            try:
                from src.state_manager import StateManager
                sm = StateManager()
                ckpt = sm.load_checkpoint(f"{project_name}_pipeline")
                if ckpt and "project_design" in ckpt.get("data", {}):
                    return _resume_from_checkpoint_data(
                        orch, file_mgr, ckpt["data"], "project_design", output_dir, scratch_shared
                    )
            except:
                pass
            
            # Fallback: just copy artifacts
            _copy_to_shared(output_dir, scratch_shared)
            return True, "Copied artifacts - manual devplan regeneration may be needed"
            
        elif resume_after in ("basic_devplan", "detailed_devplan"):
            # Just copy the existing files
            _copy_to_shared(output_dir, scratch_shared)
            return True, f"Copied artifacts from {resume_after} stage"
            
        elif resume_after == "handoff":
            # Everything is done, just copy
            _copy_to_shared(output_dir, scratch_shared)
            return True, "Copied all artifacts (pipeline was complete)"
            
        else:
            _copy_to_shared(output_dir, scratch_shared)
            return True, "Copied available artifacts"
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Resume from artifacts failed: {e}"


def _write_devplan_outputs(orch, file_mgr, devplan, design, output_dir: Path):
    """Write devplan and phase files to output directory."""
    # Write devplan.md
    devplan_md = orch._devplan_to_markdown(devplan)
    file_mgr.write_markdown(str(output_dir / "devplan.md"), devplan_md)
    
    # Write phase files
    for phase in devplan.phases:
        phase_md = orch._phase_to_markdown(phase, devplan)
        file_mgr.write_markdown(str(output_dir / f"phase{phase.number}.md"), phase_md)
    
    print(f"✅ Wrote devplan.md + {len(devplan.phases)} phase files")


def _copy_to_shared(output_dir: Path, scratch_shared: Path):
    """Copy outputs to project's scratch/shared folder."""
    scratch_shared.mkdir(parents=True, exist_ok=True)
    
    files_to_copy = {
        "devplan.md": "devplan.md",
        "project_design.md": "project_design.md",
        "handoff_prompt.md": "handoff.md",
    }
    
    copied = []
    for src_name, dst_name in files_to_copy.items():
        src = output_dir / src_name
        if src.exists():
            shutil.copy2(src, scratch_shared / dst_name)
            copied.append(dst_name)
    
    # Copy phase files
    phases_dir = scratch_shared / "phases"
    phases_dir.mkdir(exist_ok=True)
    for phase_file in output_dir.glob("phase*.md"):
        shutil.copy2(phase_file, phases_dir / phase_file.name)
        copied.append(f"phases/{phase_file.name}")
    
    print(f"📋 Copied to shared: {', '.join(copied)}")


def run_devussy_pipeline_sync(
    project_path: Path, 
    verbose: bool = False,
    model: Optional[str] = None,
    run_bootstrap: bool = True,
) -> Tuple[bool, str]:
    """Synchronous wrapper to run the devussy pipeline.
    
    Args:
        project_path: Path to the swarm project
        verbose: Enable verbose output
        model: Optional model override (e.g., "anthropic/claude-sonnet-4-20250514")
        run_bootstrap: If True, run project bootstrap (venv, npm, etc.)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    runner = DevussyPipelineRunner(project_path, model=model)
    success, message = runner.run_interactive_pipeline(verbose)
    
    if success:
        # Generate swarm task queue after successful pipeline
        try:
            generate_swarm_task_queue(project_path)
            message += " + task_queue.md generated"
        except Exception as e:
            print(f"[WARN] Could not generate task queue: {e}")
        
        # Run project bootstrap (venv, npm install, etc.)
        if run_bootstrap:
            try:
                from core.project_bootstrap import ProjectBootstrap
                print("\n" + "=" * 60)
                print("🔧 PHASE 0: Project Bootstrap")
                print("=" * 60)
                bootstrap = ProjectBootstrap(project_path)
                bootstrap.set_log_callback(lambda msg: print(f"  {msg}"))
                result = bootstrap.run_bootstrap()
                
                if result["success"]:
                    message += " + bootstrap complete"
                    types = [k for k, v in result["project_types"].items() if v]
                    if types:
                        print(f"\n  Project types: {', '.join(types)}")
                    if result.get("venv_status") and "created" in result["venv_status"]:
                        print("  ✅ Python .venv created")
                    if result.get("node_status") and "completed" in result["node_status"]:
                        print("  ✅ npm dependencies installed")
                else:
                    message += f" + bootstrap issues: {result['errors']}"
            except Exception as e:
                print(f"[WARN] Bootstrap failed: {e}")
                message += f" + bootstrap failed: {e}"
    
    return success, message


def run_devussy_with_resume_option(
    project_path: Path,
    verbose: bool = False,
    model: Optional[str] = None,
    run_bootstrap: bool = True,
) -> Tuple[bool, str]:
    """Run devussy pipeline with option to resume from previous run.
    
    This is the recommended entry point - it checks for previous runs
    and offers the user a choice to resume or start fresh.
    
    Args:
        project_path: Path to the swarm project
        verbose: Enable verbose output
        model: Optional model override
        run_bootstrap: Run project bootstrap after pipeline
        
    Returns:
        Tuple of (success, message)
    """
    # Check for existing artifacts
    artifacts = list_devussy_artifacts(project_path)
    
    if artifacts.get("runs") or artifacts.get("checkpoints"):
        # Offer choice
        print("\n" + "=" * 60)
        print("🔮 DEVUSSY PIPELINE")
        print("=" * 60)
        print("\nPrevious runs detected!")
        print()
        print("  1. Start fresh (new interview)")
        print("  2. Resume from previous run/checkpoint")
        print("  3. Cancel")
        print()
        
        choice = input("Choice [1]: ").strip() or "1"
        
        if choice == "2":
            # Resume flow
            resume_info = select_resume_stage(artifacts)
            if resume_info:
                success, message = resume_devussy_pipeline(
                    project_path, resume_info, model=model, verbose=verbose
                )
                
                if success:
                    # Generate task queue and run bootstrap
                    try:
                        generate_swarm_task_queue(project_path)
                        message += " + task_queue.md generated"
                    except Exception as e:
                        print(f"[WARN] Could not generate task queue: {e}")
                    
                    if run_bootstrap:
                        try:
                            from core.project_bootstrap import ProjectBootstrap
                            print("\n" + "=" * 60)
                            print("🔧 PHASE 0: Project Bootstrap")
                            print("=" * 60)
                            bootstrap = ProjectBootstrap(project_path)
                            bootstrap.set_log_callback(lambda msg: print(f"  {msg}"))
                            result = bootstrap.run_bootstrap()
                            if result["success"]:
                                message += " + bootstrap complete"
                        except Exception as e:
                            print(f"[WARN] Bootstrap failed: {e}")
                
                return success, message
            else:
                print("\n📋 Resume cancelled, starting fresh...")
        elif choice == "3":
            return False, "Cancelled by user"
    
    # Start fresh
    return run_devussy_pipeline_sync(
        project_path, 
        verbose=verbose, 
        model=model, 
        run_bootstrap=run_bootstrap
    )


def copy_artifacts_to_new_project(
    source_run_path: Path,
    target_project_path: Path,
    stages_to_copy: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """Copy devussy artifacts from one project/run to a new project.
    
    This allows creating a new project based on artifacts from a previous run.
    
    Args:
        source_run_path: Path to the source devussy run folder
        target_project_path: Path to the target project
        stages_to_copy: Optional list of stages to copy (defaults to all)
        
    Returns:
        Tuple of (success, message)
    """
    try:
        target_devussy = target_project_path / "scratch" / "devussy"
        target_devussy.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_run = target_devussy / f"imported_{timestamp}"
        target_run.mkdir()
        
        copied = []
        
        # Copy all markdown files
        for src_file in source_run_path.glob("*.md"):
            shutil.copy2(src_file, target_run / src_file.name)
            copied.append(src_file.name)
        
        # Copy any JSON files (interview data, etc.)
        for src_file in source_run_path.glob("*.json"):
            shutil.copy2(src_file, target_run / src_file.name)
            copied.append(src_file.name)
        
        print(f"✅ Copied {len(copied)} files to {target_run}")
        
        # Also copy to shared folder
        _copy_to_shared(target_run, target_project_path / "scratch" / "shared")
        
        return True, f"Imported artifacts: {', '.join(copied)}"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Import failed: {e}"


# Fallback models if API fetch fails
DEVUSSY_MODEL_FALLBACK = [
    ("anthropic/claude-sonnet-4-20250514", "Claude Sonnet 4"),
    ("openai/gpt-4o", "GPT-4o"),
    ("openai/gpt-4o-mini", "GPT-4o Mini"),
]


def fetch_requesty_models() -> List[tuple]:
    """Fetch available models from Requesty API.
    
    Returns:
        List of (model_id, display_name) tuples
    """
    import requests
    import os
    
    api_key = os.environ.get("REQUESTY_API_KEY")
    if not api_key:
        print("   [WARN] REQUESTY_API_KEY not set, using fallback models")
        return DEVUSSY_MODEL_FALLBACK
    
    try:
        response = requests.get(
            "https://router.requesty.ai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        models = []
        seen = set()
        
        # Priority patterns for planning-capable models
        priority_high = ["claude-sonnet", "claude-opus", "gpt-4o", "gpt-4-turbo", "gpt-5", "o1", "o3", "gemini-pro", "gemini-2"]
        priority_med = ["claude-3", "gpt-4", "deepseek", "gemini"]
        
        for model in data.get("data", []):
            model_id = model.get("id", "")
            if not model_id or model_id in seen:
                continue
            seen.add(model_id)
            
            # Create display name from model ID
            parts = model_id.split("/")
            if len(parts) == 2:
                provider, name = parts
                display = f"{provider.title()}: {name}"
            else:
                display = model_id
            
            # Calculate priority score
            model_lower = model_id.lower()
            if any(p in model_lower for p in priority_high):
                priority = 0
            elif any(p in model_lower for p in priority_med):
                priority = 1
            else:
                priority = 2
            
            models.append((model_id, display, priority))
        
        # Sort by priority then alphabetically
        models.sort(key=lambda x: (x[2], x[0]))
        
        # Return up to 20 models
        result = [(m[0], m[1]) for m in models[:20]]
        
        if not result:
            return DEVUSSY_MODEL_FALLBACK
        return result
        
    except Exception as e:
        print(f"   [WARN] Could not fetch models: {e}")
        return DEVUSSY_MODEL_FALLBACK


def select_devussy_model() -> Optional[str]:
    """Interactive model selection for devussy pipeline.
    
    Fetches available models from Requesty API.
    
    Returns:
        Selected model string or None for default
    """
    print("\n📡 Select model for Devussy pipeline:")
    print("   (Fetching available models from Requesty...)")
    
    models = fetch_requesty_models()
    
    print()
    for i, (model_id, desc) in enumerate(models, 1):
        print(f"   {i}. {desc}")
        print(f"      [{model_id}]")
    print(f"   {len(models) + 1}. Enter custom model")
    print(f"   Enter. Use default from config")
    print()
    
    choice = input("Choice [Enter for default]: ").strip()
    
    if not choice:
        return None  # Use default
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            return models[idx][0]
        elif idx == len(models):
            custom = input("Enter model (e.g., openai/gpt-4o): ").strip()
            return custom if custom else None
    
    # Assume they entered a model name directly
    if "/" in choice:
        return choice
    
    return None


def generate_swarm_task_queue(project_path: Path) -> None:
    """Generate a swarm-ready task queue from the devplan.
    
    Creates task_queue.md with pre-formatted tasks ready for dispatch.
    
    Args:
        project_path: Path to the swarm project
    """
    scratch_shared = project_path / "scratch" / "shared"
    devplan_file = scratch_shared / "devplan.md"
    phases_dir = scratch_shared / "phases"
    
    if not devplan_file.exists():
        return
    
    # Load project context for smart agent assignment
    project_context = None
    
    # Try to load from project_design.md
    design_file = scratch_shared / "project_design.md"
    if design_file.exists():
        design_content = design_file.read_text(encoding="utf-8").lower()
        project_context = {
            "project_type": "",
            "primary_language": "",
            "frameworks": "",
        }
        # Extract key info from design
        if "godot" in design_content:
            project_context["frameworks"] = "godot"
        if "gdscript" in design_content:
            project_context["primary_language"] = "gdscript"
        if "unity" in design_content:
            project_context["frameworks"] = "unity"
        if "game" in design_content or "fps" in design_content or "rpg" in design_content:
            project_context["project_type"] = "game"
        if "react" in design_content:
            project_context["frameworks"] += " react"
        if "fastapi" in design_content or "flask" in design_content:
            project_context["frameworks"] += " python-web"
            
        print(f"[CONTEXT] Project type detected: {project_context}")
    
    devplan_content = devplan_file.read_text(encoding="utf-8")
    
    # Parse tasks and assign agents with project context
    tasks = parse_devplan_tasks(devplan_content, project_context)
    
    # Also parse phase files for more detailed tasks
    if phases_dir.exists():
        for phase_file in sorted(phases_dir.glob("phase*.md")):
            phase_content = phase_file.read_text(encoding="utf-8")
            tasks.extend(parse_devplan_tasks(phase_content, project_context))
    
    # Generate task queue markdown
    queue_content = generate_task_queue_markdown(tasks)
    
    # Write task queue
    queue_file = scratch_shared / "task_queue.md"
    with open(queue_file, "w", encoding="utf-8") as f:
        f.write(queue_content)
    
    print(f"[QUEUE] Generated task_queue.md with {len(tasks)} tasks")


def parse_devplan_tasks(content: str, project_context: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Parse tasks from devplan/phase content.

    Handles multiple formats:
    - "### Task 1.1: Title"
    - "### Step 1.1: Title"
    - "## 1.1: Title"
    - "## Phase 1.1: Title"
    - "1.1: Title" (at line start)
    - "- [ ] 1.1: Title" checklist bullets (new Devussy phase format)

    Also overlays status/agent information from TASK_ anchors like:

        <!-- TASK_1_1_START -->
        task: 1.1
        status: pending
        agent: backend_dev
        <!-- TASK_1_1_END -->

    Args:
        content: Markdown content
        project_context: Optional dict with project_type, primary_language, frameworks
        
    Returns:
        List of task dictionaries
    """
    import re

    tasks: List[Dict[str, Any]] = []
    seen_task_ids = set()  # Prevent duplicates

    # ---------------------------------------------------------------------
    # 1) Heading-style task formats (backwards compatible)
    # ---------------------------------------------------------------------
    heading_patterns = [
        # Format: ### Task 1.1: Title (with content until next header)
        (r"###?\s*Task\s+(\d+)\.(\d+)[:\s]+(.+?)(?=\n###|\n##|\Z)", "task"),
        # Format: ### Step 1.1: Title
        (r"###?\s*Step\s+(\d+)\.(\d+)[:\s]+(.+?)(?=\n###|\n##|\Z)", "step"),
        # Format: ## 1.1: Title (common in older phase files)
        (r"^##\s*(\d+)\.(\d+)[:\s]+(.+?)(?=\n##|\Z)", "section"),
        # Format: ## Phase 1.1: Title
        (r"##\s*Phase\s+(\d+)\.(\d+)[:\s]+(.+?)(?=\n##|\Z)", "phase_section"),
        # Format: 1.1: Title (standalone, less greedy)
        (r"^(\d+)\.(\d+):\s*(.+?)(?=\n\d+\.\d+:|\n##|\n###|\Z)", "bare"),
    ]

    def _add_task(phase_num: str, task_num: str, task_content: str) -> None:
        """Helper to normalize and append a task if not already seen."""
        task_id = f"{phase_num}.{task_num}"
        if task_id in seen_task_ids:
            return
        seen_task_ids.add(task_id)

        # Extract title (first line, clean up trailing ### and link artifacts)
        lines = task_content.split("\n")
        title = lines[0].strip() if lines else f"Task {task_id}"
        title = re.sub(r"\s*#+\s*$", "", title)  # Remove trailing ###
        title = re.sub(r"\[.*?\]", "", title).strip()  # Remove [link] artifacts

        if not title or title.startswith("|") or len(title) < 3:
            return

        # Try to find @agent: inline
        agent_match = re.search(r"@agent:\s*(\w+)", task_content, re.IGNORECASE)
        agent = agent_match.group(1).lower() if agent_match else None

        # Infer agent if not assigned, using project context and content
        if not agent:
            agent = infer_agent_from_content(task_content, project_context)

        # Priority / depends / done_when / goal
        priority_match = re.search(r"@priority:\s*(high|medium|low)", task_content, re.IGNORECASE)
        priority = priority_match.group(1).lower() if priority_match else "medium"

        depends_match = re.search(r"@depends:\s*([^\n]+)", task_content, re.IGNORECASE)
        depends: List[str] = []
        if depends_match:
            deps_text = depends_match.group(1).strip()
            if deps_text.lower() != "none":
                depends = [d.strip() for d in deps_text.split(",") if d.strip()]

        goal_match = re.search(r"\*\*Goal:\*\*\s*(.+?)(?:\n\n|\n\*\*|$)", task_content, re.DOTALL)
        goal = goal_match.group(1).strip() if goal_match else title

        done_match = re.search(r"@done_when:\s*([^\n]+)", task_content, re.IGNORECASE)
        done_when = done_match.group(1).strip() if done_match else "Task completed as specified"

        # NEW: Parse complexity for task batching
        complexity_match = re.search(r"@complexity:\s*(trivial|simple|medium|complex)", task_content, re.IGNORECASE)
        complexity = complexity_match.group(1).lower() if complexity_match else infer_task_complexity(task_content)
        
        # NEW: Parse parallel_safe flag
        parallel_match = re.search(r"@parallel_safe:\s*(true|false)", task_content, re.IGNORECASE)
        parallel_safe = parallel_match.group(1).lower() == "true" if parallel_match else True
        
        # NEW: Parse batch_with for task grouping
        batch_match = re.search(r"@batch_with:\s*([^\n]+)", task_content, re.IGNORECASE)
        batch_with: List[str] = []
        if batch_match:
            batch_text = batch_match.group(1).strip()
            if batch_text.lower() != "none":
                batch_with = [b.strip() for b in batch_text.split(",") if b.strip()]

        # Extract file paths mentioned
        files: List[str] = []
        file_paths = re.findall(r"shared/[\w/.-]+\.\w+", task_content)
        files.extend(file_paths)

        tasks.append(
            {
                "number": task_id,
                "title": title,
                "agent": agent,
                "priority": priority,
                "depends": depends,
                "goal": goal,
                "done_when": done_when,
                "files": files,
                "content": task_content,
                "status": "pending",
                # NEW: Batching/parallel fields
                "complexity": complexity,
                "parallel_safe": parallel_safe,
                "batch_with": batch_with,
            }
        )

    # Parse heading-style tasks first
    for pattern, fmt_type in heading_patterns:
        flags = re.DOTALL | re.MULTILINE
        for match in re.finditer(pattern, content, flags):
            phase_num = match.group(1)
            task_num = match.group(2)
            task_content = match.group(3).strip()
            _add_task(phase_num, task_num, task_content)

    # ---------------------------------------------------------------------
    # 2) Checklist-style tasks: "- [ ] 1.1: Title" (new Devussy format)
    # ---------------------------------------------------------------------
    checklist_pattern = re.compile(
        r"^\s*-\s*\[[ xX]\]\s*(\d+)\.(\d+):\s*(.+?)(?=^\s*-\s*\[[ xX]\]\s*\d+\.\d+:|\Z)",
        re.MULTILINE | re.DOTALL,
    )

    for match in checklist_pattern.finditer(content):
        phase_num = match.group(1)
        task_num = match.group(2)
        body = match.group(3).rstrip()

        # Normalize content: first line is the title, rest is detailed steps
        lines = body.split("\n")
        title_line = lines[0].strip() if lines else ""
        rest = "\n".join(lines[1:]) if len(lines) > 1 else ""
        task_content = title_line + ("\n" + rest if rest else "")

        _add_task(phase_num, task_num, task_content)

    # ---------------------------------------------------------------------
    # 3) Overlay TASK_ anchors for status / explicit agent assignments
    # ---------------------------------------------------------------------
    if tasks:
        task_by_id = {t["number"]: t for t in tasks}

        anchor_pattern = re.compile(
            r"<!--\s*TASK_(\d+)_(\d+)_START\s*-->"  # opening anchor
            r"(.*?)"  # inner block
            r"<!--\s*TASK_\\1_\\2_END\s*-->",  # closing anchor
            re.DOTALL | re.IGNORECASE,
        )

        for match in anchor_pattern.finditer(content):
            phase_num = match.group(1)
            task_num = match.group(2)
            inner = match.group(3)
            task_id = f"{phase_num}.{task_num}"

            task = task_by_id.get(task_id)
            if not task:
                continue

            status_match = re.search(r"status:\s*([a-z_]+)", inner, re.IGNORECASE)
            agent_match = re.search(r"agent:\s*([a-zA-Z_]+)", inner, re.IGNORECASE)

            if status_match:
                task["status"] = status_match.group(1).lower()

            if agent_match:
                agent_val = agent_match.group(1).lower()
                if agent_val and agent_val != "unassigned":
                    task["agent"] = agent_val

    # Sort by task number for deterministic ordering
    tasks.sort(key=lambda t: (int(t["number"].split(".")[0]), int(t["number"].split(".")[1])))

    return tasks


def infer_agent_from_content(content: str, project_context: Optional[Dict] = None) -> str:
    """Infer agent from task content and project context.
    
    Args:
        content: Task description text
        project_context: Optional dict with project_type, primary_language, frameworks
        
    Returns:
        Agent role key
    """
    content_lower = content.lower()
    
    # Check project context for game engines / non-web projects
    is_game_project = False
    is_godot = False
    is_unity = False
    primary_lang = ""
    
    if project_context:
        project_type = str(project_context.get("project_type", "")).lower()
        primary_lang = str(project_context.get("primary_language", "")).lower()
        frameworks = str(project_context.get("frameworks", "")).lower()
        
        # Detect game engine projects
        is_godot = "godot" in frameworks or "gdscript" in primary_lang or "godot" in project_type
        is_unity = "unity" in frameworks or "c#" in primary_lang and "game" in project_type
        is_game_project = is_godot or is_unity or any(kw in project_type for kw in ["game", "fps", "rpg", "engine"])
    
    # GAME ENGINE PROJECTS - All code goes to backend_dev (who handles GDScript/C#)
    if is_game_project:
        # Game dev = backend_dev handles all code (GDScript, C#, etc.)
        if any(kw in content_lower for kw in ["script", "code", "implement", "class", "function", "gdscript", 
                                               "scene", "node", "signal", "autoload", "resource", "shader",
                                               "physics", "collision", "mesh", "geometry", "ai", "fsm",
                                               "player", "enemy", "weapon", "level", "spawn", "entity"]):
            return "backend_dev"  # GDScript/game code
        
        # UI in game engines is still code, not React
        if any(kw in content_lower for kw in ["ui", "hud", "menu", "control", "panel", "button", "label"]):
            return "backend_dev"  # Godot UI = GDScript, not React
        
        # Only assign frontend_dev if explicitly web-related
        if any(kw in content_lower for kw in ["html", "css", "react", "web page", "browser"]):
            return "frontend_dev"
    
    # WEB PROJECTS - Normal assignment
    else:
        # Frontend indicators (only for web projects)
        if any(kw in content_lower for kw in ["component", "react", "vue", "angular", "css", "frontend", 
                                               "page", "style", "tailwind", "html", "jsx", "tsx"]):
            return "frontend_dev"
    
    # Backend indicators (always valid)
    if any(kw in content_lower for kw in ["api", "endpoint", "server", "database", "model", "backend", 
                                           "python", "fastapi", "flask", "django", "node", "express"]):
        return "backend_dev"
    
    # QA indicators
    if any(kw in content_lower for kw in ["test", "pytest", "jest", "gut", "gdunit", "coverage", "lint", "quality"]):
        return "qa_engineer"
    
    # DevOps indicators
    if any(kw in content_lower for kw in ["docker", "deploy", "ci/cd", "pipeline", "kubernetes", "github action", "export"]):
        return "devops"
    
    # Tech writer indicators
    if any(kw in content_lower for kw in ["documentation", "readme", "docs", "guide", "comment"]):
        return "tech_writer"
    
    # Database indicators
    if any(kw in content_lower for kw in ["schema", "migration", "sql", "database design"]):
        return "database_specialist"
    
    return "backend_dev"  # Default


def infer_task_complexity(content: str) -> str:
    """Infer task complexity from content if not explicitly specified.
    
    Complexity levels:
    - trivial: <5 min, single file, config/import changes
    - simple: <15 min, 1-2 files, single function
    - medium: 15-60 min, multiple files, full module
    - complex: >1h, architectural changes
    
    Args:
        content: Task content to analyze
        
    Returns:
        Complexity level string
    """
    import re
    content_lower = content.lower()
    
    # Count files mentioned
    file_count = len(re.findall(r"shared/[\w/.-]+\.\w+", content))
    
    # Count implementation steps
    step_count = len(re.findall(r"^\s*\d+\.", content, re.MULTILINE))
    
    # Trivial indicators - quick config/setup changes
    trivial_words = ["config", "import", "update", "fix", "tweak", "add line", "rename", 
                     "set ", "change ", "modify setting"]
    if any(w in content_lower for w in trivial_words) and file_count <= 1 and step_count <= 2:
        return "trivial"
    
    # Complex indicators - major architectural work
    complex_words = ["architecture", "refactor", "redesign", "migrate", "overhaul", 
                     "system", "entire", "complete rewrite", "from scratch"]
    if any(w in content_lower for w in complex_words) or file_count > 5:
        return "complex"
    
    # Simple vs medium based on scope
    if file_count <= 2 and step_count <= 3:
        return "simple"
    
    return "medium"


def generate_task_queue_markdown(tasks: List[Dict[str, Any]], max_phase: int = 1) -> str:
    """Generate markdown task queue for the Architect.
    
    Creates a simple, copy-paste ready task dispatch file.
    The Architect just needs to spawn workers and copy the commands.
    
    IMPORTANT: Only includes tasks up to max_phase to keep context small.
    Default is Phase 1 only (~5KB instead of 60KB for 153 tasks).
    
    Args:
        tasks: List of parsed task dictionaries
        max_phase: Maximum phase to include (default 1 to keep context small)
        
    Returns:
        Markdown content
    """
    from core.swarm_anchors import AGENT_ROLES, STATUS_PENDING
    
    # Agent emoji mapping
    AGENT_EMOJI = {
        "backend_dev": "⚙️",
        "frontend_dev": "🎨",
        "qa_engineer": "🐛",
        "devops": "🚀",
        "tech_writer": "📝",
    }
    
    # Filter to only include tasks up to max_phase
    filtered_tasks = [
        t for t in tasks 
        if int(t["number"].split(".")[0]) <= max_phase
    ]
    
    lines = [
        "# 🚀 Swarm Task Queue",
        "",
        "## ⚠️ IMPORTANT: Execute assign_task() tool calls!",
        "The code blocks below are NOT just documentation - you must EXECUTE them as tool calls.",
        "",
        "## How to Use",
        "1. `spawn_worker(role)` for each needed agent type",
        "2. **EXECUTE** each `assign_task()` below as a tool call (don't just read it!)",
        "3. Say 'Dispatched N tasks.' then STOP",
        "",
        "---",
        "",
    ]
    
    # Count tasks per agent (for ALL tasks - show full picture)
    all_agent_counts = {}
    for task in tasks:
        agent = task.get("agent", "backend_dev")
        all_agent_counts[agent] = all_agent_counts.get(agent, 0) + 1
    
    # Count phases
    all_phases = set(int(t["number"].split(".")[0]) for t in tasks)
    total_phases = len(all_phases)
    
    lines.append("## Project Summary")
    lines.append(f"**Total:** {len(tasks)} tasks across {total_phases} phases")
    lines.append(f"**This file shows:** Phase 1 only ({len(filtered_tasks)} tasks)")
    lines.append("")
    lines.append("### Agents Needed:")
    for agent, count in sorted(all_agent_counts.items()):
        agent_info = SWARM_AGENTS.get(agent, {"name": agent})
        emoji = AGENT_EMOJI.get(agent, "🤖")
        lines.append(f"- {emoji} **{agent_info.get('name', agent)}**: {count} total tasks")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Group filtered tasks by phase (Phase 1 only by default)
    phases = {}
    for task in filtered_tasks:
        phase_num = task["number"].split(".")[0]
        if phase_num not in phases:
            phases[phase_num] = []
        phases[phase_num].append(task)
    
    for phase_num in sorted(phases.keys(), key=int):
        phase_tasks = phases[phase_num]
        lines.append(f"## Phase {phase_num}")
        lines.append("")
        
        for task in phase_tasks:
            agent = task.get("agent", "backend_dev")
            agent_info = SWARM_AGENTS.get(agent, {"name": agent})
            agent_name = agent_info.get("name", agent)
            emoji = AGENT_EMOJI.get(agent, "🤖")
            
            # Get task details
            goal = task.get("goal") or task.get("title", "Complete the task")
            files = task.get("files", [])
            done_when = task.get("done_when", "Task completed as specified")
            
            # Build files string
            if files:
                files_str = "\n".join(f"- {f}" for f in files[:5])
            else:
                files_str = "- (see task description)"
            
            # Build requirements from task content
            content = task.get("content", "")
            reqs = []
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("- ") and len(line) > 10:
                    reqs.append(line)
                    if len(reqs) >= 3:
                        break
            reqs_str = "\n".join(reqs) if reqs else "- See task description above"
            
            # Task header with emoji
            lines.append(f"### {emoji} Task {task['number']}: {task['title']}")
            lines.append(f"**Agent:** {agent_name} (`{agent}`)")
            lines.append(f"**Status:** `{task['status']}`")
            if task.get('depends'):
                lines.append(f"**Depends:** {', '.join(task['depends'])}")
            lines.append("")
            
            # Dispatch command - ready to copy
            dispatch = f'''```python
assign_task("{agent_name}", """Task {task['number']}: {task['title']}

GOAL: {goal}

FILES:
{files_str}

REQUIREMENTS:
{reqs_str}

DONE_WHEN: {done_when}
""")
```'''
            lines.append(dispatch)
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Add note about additional phases
    if total_phases > max_phase:
        lines.append("## 📄 Additional Phases")
        lines.append(f"Phases 2-{total_phases} will be loaded after Phase 1 completes.")
        lines.append("The Auto Orchestrator will trigger you to assign more tasks.")
        lines.append("")
    
    return "\n".join(lines)


def check_devussy_available() -> bool:
    """Check if devussy is available for import."""
    try:
        if str(DEVUSSY_PATH) not in sys.path:
            sys.path.insert(0, str(DEVUSSY_PATH))
        from src.cli import interactive_design
        return True
    except ImportError:
        return False


def load_devplan_for_swarm(project_path: Path) -> Optional[dict]:
    """Load the devplan and phases for use by the swarm.
    
    Args:
        project_path: Path to the swarm project
        
    Returns:
        Dictionary with devplan info, or None if not found
    """
    scratch_shared = project_path / "scratch" / "shared"
    
    devplan_file = scratch_shared / "devplan.md"
    phases_file = scratch_shared / "phases.md"
    handoff_file = scratch_shared / "handoff.md"
    
    result = {
        "has_devplan": False,
        "devplan_content": None,
        "phases_content": None,
        "handoff_content": None,
        "phase_files": [],
    }
    
    if devplan_file.exists():
        result["has_devplan"] = True
        result["devplan_content"] = devplan_file.read_text(encoding="utf-8")
    
    if phases_file.exists():
        result["phases_content"] = phases_file.read_text(encoding="utf-8")
    
    if handoff_file.exists():
        result["handoff_content"] = handoff_file.read_text(encoding="utf-8")
    
    # Load individual phase files
    phases_dir = scratch_shared / "phases"
    if phases_dir.exists():
        for phase_file in sorted(phases_dir.glob("phase*.md")):
            result["phase_files"].append({
                "name": phase_file.stem,
                "path": str(phase_file),
                "content": phase_file.read_text(encoding="utf-8"),
            })
    
    return result if result["has_devplan"] else None


def recover_project_state(project_path: Path) -> Dict[str, Any]:
    """Analyze project state and determine what work remains.
    
    This is used when resuming a project to understand:
    1. What files already exist (completed work)
    2. What phases are incomplete
    3. What the next tasks should be
    
    Args:
        project_path: Path to the swarm project
        
    Returns:
        Dictionary with project state analysis
    """
    import re
    
    scratch_shared = project_path / "scratch" / "shared"
    
    state = {
        "existing_files": [],
        "phases": [],
        "current_phase": 1,
        "completed_tasks": 0,
        "total_tasks": 0,
        "next_work": [],
        "can_resume": False,
    }
    
    # Find all existing source files
    src_dir = scratch_shared / "src"
    if src_dir.exists():
        for f in src_dir.rglob("*"):
            if f.is_file() and f.suffix in [".ts", ".js", ".py", ".gd", ".cs", ".md"]:
                state["existing_files"].append(str(f.relative_to(scratch_shared)))
    
    # Also check root level files
    for f in scratch_shared.glob("*"):
        if f.is_file() and f.suffix in [".ts", ".js", ".json", ".html", ".css"]:
            state["existing_files"].append(f.name)
    
    # Parse devplan for phase information
    devplan_file = scratch_shared / "devplan.md"
    if devplan_file.exists():
        content = devplan_file.read_text(encoding="utf-8")
        
        # Find phase status anchors
        phase_pattern = re.compile(
            r'<!-- PHASE_(\d+)_STATUS_START -->\s*'
            r'(?:phase:\s*\d+\s*)?'
            r'(?:name:\s*([^\n]+)\s*)?'
            r'completed:\s*(\d+)/(\d+)',
            re.IGNORECASE
        )
        
        for match in phase_pattern.finditer(content):
            phase_num = int(match.group(1))
            phase_name = match.group(2) or f"Phase {phase_num}"
            completed = int(match.group(3))
            total = int(match.group(4))
            
            state["phases"].append({
                "number": phase_num,
                "name": phase_name.strip(),
                "completed": completed,
                "total": total,
            })
            
            state["total_tasks"] += total
            state["completed_tasks"] += completed
            
            # Find first incomplete phase
            if completed < total and state["current_phase"] == 1:
                state["current_phase"] = phase_num
        
        # If phases found, we can resume
        if state["phases"]:
            state["can_resume"] = True
            
            # Determine next work from current phase
            current = next((p for p in state["phases"] if p["completed"] < p["total"]), None)
            if current:
                next_task_num = current["completed"] + 1
                state["next_work"].append({
                    "phase": current["number"],
                    "task": f"{current['number']}.{next_task_num}",
                    "description": f"Continue Phase {current['number']}: {current['name']}",
                })
    
    return state


def regenerate_task_queue_from_devplan(project_path: Path) -> bool:
    """Regenerate task_queue.md from devplan when phase files are corrupted.
    
    This creates a minimal task queue based on the devplan's phase information,
    allowing the swarm to continue even when detailed phase files are missing.
    
    Args:
        project_path: Path to the swarm project
        
    Returns:
        True if successful
    """
    import re
    
    scratch_shared = project_path / "scratch" / "shared"
    devplan_file = scratch_shared / "devplan.md"
    
    if not devplan_file.exists():
        return False
    
    content = devplan_file.read_text(encoding="utf-8")
    
    # Parse phase overview table
    # Format: | 1 | Project Setup | [WAIT] Not Started | 16 | [phase1.md] |
    table_pattern = re.compile(
        r'\|\s*(\d+)\s*\|\s*([^|]+)\|\s*\[(?:WAIT|DONE|WIP)\][^|]*\|\s*(\d+)\s*\|',
        re.IGNORECASE
    )
    
    phases = []
    for match in table_pattern.finditer(content):
        phase_num = int(match.group(1))
        phase_name = match.group(2).strip()
        task_count = int(match.group(3))
        phases.append({
            "number": phase_num,
            "name": phase_name,
            "tasks": task_count,
        })
    
    if not phases:
        return False
    
    # Generate minimal task queue
    lines = [
        "# 🚀 Swarm Task Queue (Recovered)",
        "",
        "⚠️ **Note:** This queue was regenerated from devplan.md because phase files were incomplete.",
        "The Architect should read this and dispatch work based on what remains.",
        "",
        "---",
        "",
        "## Phases Overview",
        "",
    ]
    
    for phase in phases:
        lines.append(f"### Phase {phase['number']}: {phase['name']}")
        lines.append(f"- **Total Tasks:** {phase['tasks']}")
        lines.append(f"- **Status:** Check existing files to determine progress")
        lines.append("")
        lines.append("**To dispatch work for this phase:**")
        lines.append("1. Use `get_project_structure()` to see what files exist")
        lines.append("2. Read `shared/phases/phase{}.md` if it has task details".format(phase['number']))
        lines.append("3. Assign tasks for files that don't exist yet")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.extend([
        "## Recovery Instructions for Architect",
        "",
        "Since task details may be incomplete, use this workflow:",
        "",
        "1. `get_project_structure()` - See what's already built",
        "2. `read_file('shared/devplan.md')` - Get phase overview",
        "3. `read_file('shared/project_design.md')` - Understand the project",
        "4. For each incomplete phase:",
        "   - Spawn workers: `spawn_worker('backend_dev')`, etc.",
        "   - Assign work based on what's missing",
        "   - Include clear GOAL, FILES, REQUIREMENTS, DONE criteria",
        "",
    ])
    
    # Write recovered queue
    queue_file = scratch_shared / "task_queue.md"
    queue_file.write_text("\n".join(lines), encoding="utf-8")
    
    print(f"[RECOVER] Regenerated task_queue.md with {len(phases)} phases")
    return True
