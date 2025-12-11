
import asyncio
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime

# Add devussy to sys.path if needed
import sys
DEVUSSY_PATH = Path(__file__).parent.parent / "devussy"
if str(DEVUSSY_PATH) not in sys.path:
    sys.path.insert(0, str(DEVUSSY_PATH))

from src.config import AppConfig, load_config
from src.llm_interview import LLMInterviewManager
from src.pipeline.compose import PipelineOrchestrator
from src.clients.factory import create_llm_client
from src.concurrency import ConcurrencyManager
from src.file_manager import FileManager
from src.state_manager import StateManager
from src.markdown_output_manager import MarkdownOutputManager
from src.models import ProjectDesign, DevPlan

logger = logging.getLogger("web_devussy")

class WebDevussyRunner:
    """
    Manages the Devussy pipeline for a web session.
    Handles the state machine: Interview -> Design -> DevPlan -> Handoff.
    """
    
    def __init__(self, project_path: Path, config: Optional[AppConfig] = None):
        self.project_path = Path(project_path)
        self.config = config or self._create_config_from_env()
        self.interview_manager: Optional[LLMInterviewManager] = None
        self.orchestrator: Optional[PipelineOrchestrator] = None
        self.stage = "config"  # config, interview, processing, complete
        self.on_message: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.extracted_inputs: Dict[str, Any] = {}
        
        # Output directories
        self.scratch_shared = self.project_path / "scratch" / "shared"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = self.scratch_shared.parent / "devussy" / f"run_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure output for devussy
        self.config.output_dir = self.output_dir
        
        # Setup markdown manager
        self.markdown_mgr = MarkdownOutputManager(base_output_dir=str(self.output_dir))
        # Force set run_dir since we already created the specific timestamped dir
        self.markdown_mgr.run_dir = self.output_dir
        # Create metadata.json to signal valid run dir
        self.markdown_mgr.save_run_metadata({"source": "web_session"})

    def _create_config_from_env(self) -> AppConfig:
        """Create AppConfig with correct provider settings from environment."""
        from config.settings import REQUESTY_API_KEY, ZAI_API_KEY
        
        # Determine which provider to use based on available keys
        # Priority: Requesty > Z.AI > OpenAI
        if REQUESTY_API_KEY:
            provider = "requesty"
            api_key = REQUESTY_API_KEY
            base_url = "https://router.requesty.ai/v1"
        elif ZAI_API_KEY:
            provider = "generic"  # Z.AI uses OpenAI-compatible API
            api_key = ZAI_API_KEY
            base_url = "https://api.z.ai/api/paas/v4"
        else:
            # Fallback to OpenAI if configured
            provider = "openai"
            api_key = os.environ.get("OPENAI_API_KEY", "")
            base_url = None
        
        logger.info(f"WebDevussyRunner using provider: {provider}")
        
        # Create config with correct provider settings
        config = AppConfig()
        config.llm.provider = provider
        config.llm.api_key = api_key
        if base_url:
            config.llm.base_url = base_url
        
        return config

    async def start_interview(self, models: Dict[str, str]):
        """Start the interview stage."""
        self.stage = "interview"
        
        # Configure models
        if models.get("interview_model"):
            self.config.llm.model = models["interview_model"]
        
        # Store other model choices for later
        self.design_model = models.get("design_model") or self.config.llm.model
        self.devplan_model = models.get("devplan_model") or self.config.llm.model
        
        # Initialize Interview Manager
        # We assume no repo analysis for web mode for simplicity initially, 
        # or we could add it later.
        self.interview_manager = LLMInterviewManager(
            config=self.config,
            verbose=True,
            markdown_output_manager=self.markdown_mgr
        )
        
        # Generate initial greeting
        # We manually trigger the first message logic from LLMInterviewManager.run()
        greeting = "Hi! I'm excited to help you plan your project. Let's start with the basics - what would you like to name your project?"
        
        # Send greeting to UI
        await self._emit_message(greeting, "assistant")
        
        # We don't actually send this to LLM history yet, mirroring CLI behavior 
        # where it prompts user first? 
        # Actually LLMInterviewManager.run() sends a prompt to LLM to generate greeting 
        # OR uses a hardcoded one.
        # In llm_interview.py: 
        # initial_response = self._send_to_llm("Hi! ...") 
        # So it does send to LLM history.
        
        # Let's just manually inject the greeting into history and send it to UI.
        self.interview_manager.conversation_history.append({
            "role": "assistant",
            "content": greeting
        })
        # Note: We skipped the "User: Hi..." fake message. 
        # This is cleaner.
        
        # But `run()` does:
        # self._display_llm_response(initial_response)
        
        # Let's assume the greeting I defined above is what we want the user to see.

    async def handle_input(self, text: str):
        """Handle user input during interview."""
        if self.stage != "interview":
            logger.warning(f"Received input in wrong stage: {self.stage}")
            return

        if not self.interview_manager:
            return

        # Handle commands
        if text.startswith("/"):
            # We don't support all CLI commands, but we should handle /done
            if text.strip() == "/done":
                await self._try_finalize()
                return
            # Ignore other commands for now
            return

        # Send to LLM
        # This blocks in the original code, but we're async. 
        # However `_send_to_llm` uses `generate_completion_sync` unless streaming.
        # We should use `_send_to_llm_streaming` if possible or run in thread.
        # `llm_interview.py` has `_send_to_llm_streaming` (async).
        
        # We need to pass a callback to `_send_to_llm_streaming` to stream tokens to UI.
        response = await self.interview_manager._send_to_llm_streaming(
            text, 
            callback=self._stream_callback
        )
        
        # Send full message event to ensure UI has complete text (and stop typing indicator)
        await self._emit_message(response, "assistant")
        
        # Check for extraction
        extracted = self.interview_manager._extract_structured_data(response)
        if extracted:
            self.interview_manager.extracted_data = extracted
            if self.interview_manager._validate_extracted_data(extracted):
                # We have enough info.
                # In CLI it prompts: "Required info collected. Type /done..."
                await self._emit_message("✓ Required info collected. Type /done to finalize and generate, or continue to refine.", "system")

    async def _stream_callback(self, token: str):
        """Callback for streaming tokens."""
        # For now, we might not stream every token to websocket to avoid traffic jam,
        # or we can. React handles it okay usually.
        # Let's just accumulate or rely on the final message for now to keep it simple,
        # OR implement a proper streaming event.
        pass

    async def _try_finalize(self):
        """Attempt to finalize the interview."""
        await self._emit_message("Finalizing interview...", "system")

        if not self.interview_manager:
            logger.error("Cannot finalize interview: interview_manager is None")
            await self._emit_message("Internal error: interview manager not ready.", "system")
            return

        # 1) Prefer already-extracted structured data from the conversation
        existing = getattr(self.interview_manager, "extracted_data", None)
        if existing:
            try:
                if self.interview_manager._validate_extracted_data(existing):
                    logger.info("Finalizing interview using previously extracted data (no extra LLM call).")
                    self.interview_manager.extracted_data = existing
                    self.extracted_inputs = existing

                    # Save interview summary to markdown, mirroring CLI behavior
                    try:
                        if self.interview_manager.markdown_output_manager:
                            self.interview_manager.markdown_output_manager.save_interview_summary(
                                conversation_history=self.interview_manager.conversation_history,
                                extracted_data=self.interview_manager.extracted_data,
                            )
                    except Exception as e:
                        logger.warning(f"Failed to save interview summary during finalize: {e}")

                    await self._emit_message("Interview complete! Starting generation...", "system")
                    await self._run_generation_pipeline()
                    return
            except Exception as e:
                logger.warning(f"Error validating existing extracted_data: {e}")

        # 2) Fall back to the direct JSON extraction helper as a last resort
        # Some frontier / reasoning models (e.g., gpt-5-nano) can occasionally
        # return empty content while still burning a lot of tokens. To make
        # /done more robust, switch to a more stable general-purpose model
        # for the JSON extraction step only.
        try:
            current_model = getattr(self.config.llm, "model", "") or ""
            if "gpt-5" in current_model:
                fallback_model = "openai/gpt-4o-mini"
                logger.info(
                    "Switching finalize model from %s to %s for JSON extraction.",
                    current_model,
                    fallback_model,
                )
                self.config.llm.model = fallback_model
                # Recreate the interview LLM client with the fallback model
                self.interview_manager.llm_client = create_llm_client(self.config)
        except Exception as e:
            logger.warning(f"Failed to adjust finalize model for /done: {e}")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        extracted = None
        if loop is not None:
            try:
                extracted = await loop.run_in_executor(
                    None, self.interview_manager._finalize_via_direct_prompt
                )
            except Exception as e:
                logger.error(f"_finalize_via_direct_prompt failed: {e}", exc_info=True)

        if extracted and self.interview_manager._validate_extracted_data(extracted):
            logger.info("Finalizing interview using direct JSON extraction helper.")
            self.interview_manager.extracted_data = extracted
            self.extracted_inputs = extracted

            try:
                if self.interview_manager.markdown_output_manager:
                    self.interview_manager.markdown_output_manager.save_interview_summary(
                        conversation_history=self.interview_manager.conversation_history,
                        extracted_data=self.interview_manager.extracted_data,
                    )
            except Exception as e:
                logger.warning(f"Failed to save interview summary during finalize: {e}")

            await self._emit_message("Interview complete! Starting generation...", "system")
            await self._run_generation_pipeline()
        else:
            await self._emit_message(
                "Could not finalize yet. Please provide more details, then type /done again.",
                "system",
            )

    async def _run_generation_pipeline(self):
        """Run the rest of the pipeline (Design -> DevPlan -> Handoff)."""
        self.stage = "processing"
        await self._emit_stage_update("interview", "complete")
        
        try:
            # 1. Prepare inputs
            # Map extracted data to design inputs
            inputs = self.interview_manager.to_generate_design_inputs()
            
            # Setup Orchestrator
            # We need to switch models if configured
            if self.design_model:
                self.config.llm.model = self.design_model
            
            # Create orchestrator
            self.orchestrator = PipelineOrchestrator(
                llm_client=create_llm_client(self.config),
                concurrency_manager=ConcurrencyManager(self.config.max_concurrent_requests),
                file_manager=FileManager(),
                git_config=self.config.git,
                config=self.config,
                markdown_output_manager=self.markdown_mgr
            )
            
            # 2. Generate Design
            await self._emit_stage_update("design", "active")
            await self._emit_message("Generating Project Design...", "system")
            
            design = await self.orchestrator.project_design_gen.generate(
                project_name=inputs["name"],
                languages=[l.strip() for l in inputs["languages"].split(",")],
                requirements=inputs["requirements"],
                frameworks=[f.strip() for f in inputs.get("frameworks", "").split(",")] if inputs.get("frameworks") else None,
                apis=[a.strip() for a in inputs.get("apis", "").split(",")] if inputs.get("apis") else None,
            )
            
            # Save Design
            design_file = self.output_dir / "project_design.md"
            with open(design_file, "w", encoding="utf-8") as f:
                f.write(f"# Project Design: {inputs['name']}\n\n")
                f.write(f"## Architecture Overview\n\n{design.architecture_overview}\n\n")
                # ... (simplified save for now, assume orchestrator saves artifacts too)
            
            await self._emit_stage_update("design", "complete")
            
            # 3. Generate DevPlan
            if self.devplan_model:
                self.config.llm.model = self.devplan_model
                # Recreate client with new model
                self.orchestrator.llm_client = create_llm_client(self.config)
            
            await self._emit_stage_update("devplan", "active")
            await self._emit_message("Generating Development Plan...", "system")
            
            devplan = await self.orchestrator.run_devplan_only(
                design,
                pre_review=False
            )
            
            # Save DevPlan
            devplan_md = self.orchestrator._devplan_to_markdown(devplan)
            (self.output_dir / "devplan.md").write_text(devplan_md, encoding="utf-8")
            
            # Save Phases
            await self._emit_stage_update("devplan", "complete")
            await self._emit_stage_update("phases", "active")
            
            for phase in devplan.phases:
                phase_md = self.orchestrator._phase_to_markdown(phase, devplan)
                (self.output_dir / f"phase{phase.number}.md").write_text(phase_md, encoding="utf-8")
            
            await self._emit_stage_update("phases", "complete")
            
            # 4. Generate Handoff
            await self._emit_stage_update("handoff", "active")
            await self._emit_message("Preparing Handoff...", "system")
            
            handoff = await self.orchestrator.run_handoff_only(devplan, inputs["name"])
            (self.output_dir / "handoff_prompt.md").write_text(handoff.content, encoding="utf-8")
            
            await self._emit_stage_update("handoff", "complete")
            
            # 5. Copy to Shared
            self._copy_to_project_shared()
            
            self.stage = "complete"
            await self._emit_event("complete", {})
            await self._emit_message("Pipeline completed successfully!", "system")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            await self._emit_message(f"Error during processing: {str(e)}", "system")

    def _copy_to_project_shared(self):
        """Copy generated files to project scratch/shared."""
        import shutil
        self.scratch_shared.mkdir(parents=True, exist_ok=True)
        
        # Copy key files
        for filename in ["project_design.md", "devplan.md"]:
            if (self.output_dir / filename).exists():
                shutil.copy2(self.output_dir / filename, self.scratch_shared / filename)
        
        # Copy handoff to handoff.md
        if (self.output_dir / "handoff_prompt.md").exists():
            shutil.copy2(self.output_dir / "handoff_prompt.md", self.scratch_shared / "handoff.md")
            
        # Copy phases
        phases_dir = self.scratch_shared / "phases"
        phases_dir.mkdir(exist_ok=True)
        for phase_file in self.output_dir.glob("phase*.md"):
            shutil.copy2(phase_file, phases_dir / phase_file.name)

    async def _emit_message(self, content: str, role: str):
        if self.on_message:
            await self.on_message({
                "type": "message", 
                "content": content, 
                "role": role
            })

    async def _emit_stage_update(self, stage_id: str, status: str):
        if self.on_message:
            await self.on_message({
                "type": "stage_update", 
                "stage_id": stage_id, 
                "status": status
            })

    async def _emit_event(self, type_name: str, data: Dict[str, Any]):
        if self.on_message:
            payload = {"type": type_name}
            payload.update(data)
            await self.on_message(payload)
