"""
Swarm Anchors - Standardized markers for DevUssY ↔ SwarmUssY communication.

These anchors ensure consistent parsing between:
- DevUssY (plan generation) 
- SwarmUssY (plan execution)

Both systems should import from this file to stay in sync.
"""

# =============================================================================
# PHASE ANCHORS - Mark phase boundaries and status
# =============================================================================

# Phase status block (HTML comments for invisibility in markdown rendering)
PHASE_STATUS_START = "<!-- PHASE_{n}_STATUS_START -->"
PHASE_STATUS_END = "<!-- PHASE_{n}_STATUS_END -->"

# Example:
# <!-- PHASE_1_STATUS_START -->
# status: in_progress
# completed: 3/10
# next_task: 1.4
# <!-- PHASE_1_STATUS_END -->

# =============================================================================
# TASK ANCHORS - Mark individual task metadata
# =============================================================================

# Task header format
TASK_HEADER = "### Task {phase}.{task}: {title}"  # e.g., "### Task 1.1: Setup Project"

# Task metadata tags (inline, parseable)
TASK_AGENT = "@agent:"           # @agent: backend_dev
TASK_PRIORITY = "@priority:"     # @priority: high
TASK_DEPENDS = "@depends:"       # @depends: 1.1, 1.2 OR @depends: none
TASK_STATUS = "@status:"         # @status: pending | in_progress | completed | blocked
TASK_FILES = "@files:"           # @files: (multiline list follows)
TASK_DONE_WHEN = "@done_when:"   # @done_when: Tests pass, exports X

# Task section headers (within task block)
TASK_GOAL = "**Goal:**"
TASK_STEPS = "**Implementation Steps:**"
TASK_CRITERIA = "**Acceptance Criteria:**"
TASK_TOOLS = "**Tool Calls:**"
TASK_HANDOFF = "**Handoff Notes:**"

# =============================================================================
# AGENT ROLE KEYS - Canonical agent identifiers
# =============================================================================

AGENT_ROLES = {
    "backend_dev": "Codey McBackend",
    "frontend_dev": "Pixel McFrontend",
    "qa_engineer": "Bugsy McTester",
    "devops": "Deployo McOps",
    "tech_writer": "Docy McWriter",
    "database_specialist": "Schema McDatabase",
    "api_designer": "Swagger McEndpoint",
}

# Reverse lookup
AGENT_NAMES = {v: k for k, v in AGENT_ROLES.items()}

# =============================================================================
# TOOL CALL FORMAT - Standardized tool suggestions
# =============================================================================

# Tools should be suggested in this format (no brackets around args)
TOOL_FORMAT = {
    "read_file": 'read_file("path/to/file")',
    "write_file": 'write_file("path/to/file", content)',
    "run_command": 'run_command("command")',
    "search_code": 'search_code("query", file_pattern="*.py")',
    "complete_my_task": 'complete_my_task(result="summary")',
    "read_multiple_files": 'read_multiple_files(["path1", "path2"])',
    "replace_in_file": 'replace_in_file("path", old_str, new_str)',
    "append_file": 'append_file("path", content)',
}

# =============================================================================
# DISPATCH COMMAND FORMAT - Ready-to-copy task assignments
# =============================================================================

DISPATCH_TEMPLATE = '''assign_task("{agent_name}", """Task {task_number}: {task_title}

GOAL: {goal}

FILES:
{files}

REQUIREMENTS:
{requirements}

DONE_WHEN: {done_when}
""")'''

# =============================================================================
# STATUS VALUES - Task/Phase status tracking
# =============================================================================

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"  
STATUS_COMPLETED = "completed"
STATUS_BLOCKED = "blocked"
STATUS_SKIPPED = "skipped"

# Status emoji mappings for display
STATUS_EMOJI = {
    STATUS_PENDING: "⏳",
    STATUS_IN_PROGRESS: "🔄",
    STATUS_COMPLETED: "✅",
    STATUS_BLOCKED: "❌",
    STATUS_SKIPPED: "⏭️",
}

# =============================================================================
# FILE PATH CONVENTIONS
# =============================================================================

# All swarm work happens in these paths (relative to project scratch/)
SHARED_DIR = "shared/"                    # Main work directory
SHARED_SRC = "shared/src/"                # Source code
SHARED_TESTS = "shared/tests/"            # Test files
SHARED_DOCS = "shared/docs/"              # Documentation
SHARED_CONFIG = "shared/config/"          # Config files

# Key files the swarm looks for
MASTER_PLAN = "shared/master_plan.md"     # Architect's high-level plan
PROJECT_DESIGN = "shared/project_design.md"  # Full design from devussy
DEVPLAN = "shared/devplan.md"             # Step-by-step dev plan
TASK_QUEUE = "shared/task_queue.md"       # Pre-assigned task queue
CONTEXT = "shared/context.md"             # Shared memory/decisions

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def phase_status_anchor(phase_num: int, start: bool = True) -> str:
    """Generate phase status anchor.
    
    Args:
        phase_num: Phase number (1, 2, 3...)
        start: True for start anchor, False for end
        
    Returns:
        Anchor string like "<!-- PHASE_1_STATUS_START -->"
    """
    template = PHASE_STATUS_START if start else PHASE_STATUS_END
    return template.format(n=phase_num)


def format_task_header(phase: int, task: int, title: str) -> str:
    """Format a task header line.
    
    Args:
        phase: Phase number
        task: Task number within phase
        title: Task title
        
    Returns:
        Formatted header like "### Task 1.1: Setup Project"
    """
    return TASK_HEADER.format(phase=phase, task=task, title=title)


def get_agent_name(role_key: str) -> str:
    """Get agent display name from role key.
    
    Args:
        role_key: Role like "backend_dev"
        
    Returns:
        Display name like "Codey McBackend"
    """
    return AGENT_ROLES.get(role_key, role_key)


def get_role_key(agent_name: str) -> str:
    """Get role key from agent display name.
    
    Args:
        agent_name: Display name like "Codey McBackend"
        
    Returns:
        Role key like "backend_dev"
    """
    return AGENT_NAMES.get(agent_name, "backend_dev")


def format_dispatch_command(
    agent_name: str,
    task_number: str,
    task_title: str,
    goal: str,
    files: list,
    requirements: list,
    done_when: str
) -> str:
    """Format a complete dispatch command for the Architect.
    
    Args:
        agent_name: Agent display name
        task_number: Task number like "1.1"
        task_title: Task title
        goal: One-line goal description
        files: List of file paths
        requirements: List of requirements
        done_when: Acceptance criteria
        
    Returns:
        Ready-to-copy assign_task() call
    """
    files_str = "\n".join(f"- {f}" for f in files) if files else "- (see task details)"
    reqs_str = "\n".join(f"- {r}" for r in requirements) if requirements else "- (see task details)"
    
    return DISPATCH_TEMPLATE.format(
        agent_name=agent_name,
        task_number=task_number,
        task_title=task_title,
        goal=goal,
        files=files_str,
        requirements=reqs_str,
        done_when=done_when
    )
