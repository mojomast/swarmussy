"""
Slim Tool Definitions for Efficient Agent Operation.

This module provides compressed tool definitions that reduce input tokens
by ~80% compared to verbose definitions. Use SLIM_WORKER_TOOLS and 
SLIM_ORCHESTRATOR_TOOLS instead of the full definitions.

Token savings: ~15k -> ~3k per API call with tools.
"""

# =============================================================================
# CORE WORKER TOOLS - Minimal descriptions, maximum efficiency
# =============================================================================

SLIM_TOOL_DEFINITIONS = [
    # FILE OPERATIONS - The essentials
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "OVERWRITES entire file. Read first if updating! No placeholders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "read_file",
            "description": "Read file contents with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_multiple_files",
            "description": "Batch-read up to 10 files. Split larger lists into multiple calls of ≤10.",
            "parameters": {
                "type": "object",
                "properties": {
                    "paths": {"type": "array", "items": {"type": "string"}, "maxItems": 10}
                },
                "required": ["paths"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": "Find & replace string in file. old_string must match exactly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_string": {"type": "string"},
                    "new_string": {"type": "string"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List directory contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Default: ."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search files for text/regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "file_pattern": {"type": "string", "description": "e.g. *.py"},
                    "regex": {"type": "boolean"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "indexed_search_code",
            "description": "Fast FTS search. Use FIRST for code discovery. Cached.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "file_pattern": {"type": "string", "description": "e.g. *.py"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "indexed_related_files",
            "description": "Find related files: same dir, tests, similar names.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_results": {"type": "integer"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run shell cmd. Allowed: python/pip/pytest/npm/node/git status/ls/cat/grep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_structure",
            "description": "Get file tree. Excludes .venv/node_modules/.git. Capped at 150 lines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "max_depth": {"type": "integer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_my_task",
            "description": "REQUIRED when done. Marks task complete, frees you for new work.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "result": {"type": "string", "description": "Brief summary of accomplishment"}
                },
                "required": ["result"]
            }
        }
    },
    # Shared context - lightweight memory
    {
        "type": "function",
        "function": {
            "name": "log_context",
            "description": "Log key decision/progress to shared context file. Replaces DB memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry": {"type": "string", "description": "What to log"},
                    "category": {"type": "string", "enum": ["decision", "progress", "blocker"]}
                },
                "required": ["entry"]
            }
        }
    },
    # Less common but useful
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create directory (with parents).",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Append to file end.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
]

# =============================================================================
# ORCHESTRATOR TOOLS - For Architect only
# =============================================================================

SLIM_ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "spawn_worker",
            "description": "Spawn worker. Singletons - reuses existing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["backend_dev", "frontend_dev", "qa_engineer", "devops", "tech_writer"]
                    }
                },
                "required": ["role"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assign_task",
            "description": "Assign task to worker. Include: goal, files, requirements, done-when.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["agent_name", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_task",
            "description": "Get next pending task with dispatch command. Use instead of reading task_queue.md.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_swarm_state",
            "description": "Get all agents/tasks status.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "OVERWRITES file. Read first if updating! Plans only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_structure",
            "description": "Get file tree view.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Add to end of file without overwriting. Use for updating plans.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    },
]


# =============================================================================
# MINIMAL SYSTEM PROMPT ADDITIONS
# =============================================================================

SLIM_TOOLS_PROMPT = """
## TOOLS
- indexed_search_code(query) - FAST FTS search. Use FIRST for discovery!
- indexed_related_files(path) - Find tests, same-dir files, similar names
- read_file(path) / read_multiple_files(paths) - Read files
- write_file(path, content) - OVERWRITES file! Read first if updating
- replace_in_file(path, old, new) - Edit existing file (preferred for updates)
- append_file(path, content) - Add to end without overwriting
- run_command(cmd) - Run tests: pytest/npm test
- complete_my_task(result) - REQUIRED when done

## WORKFLOW
1. indexed_search_code(query) - Find relevant files
2. indexed_related_files(path) - Find tests/related
3. read_multiple_files([paths]) - Read only what you need
4. write_file / replace_in_file - Implement
5. complete_my_task(result) - REQUIRED

## RULES
- Use indexed_search_code BEFORE reading files
- Paths relative to shared/
- Write COMPLETE implementations
"""

SLIM_ORCHESTRATOR_PROMPT = """
## TOOLS  
- spawn_worker(role) - Roles: backend_dev, frontend_dev, qa_engineer, devops, tech_writer
- assign_task(agent_name, description) - Give detailed task
- get_swarm_state() - Check status
- write_file - For plans only

## WORKFLOW
1. Write plan to shared/master_plan.md
2. Spawn workers: spawn_worker("backend_dev")
3. Assign tasks with: goal, files, requirements, done-when
4. STOP and let workers work
"""


def get_slim_tools_for_agent(agent_name: str) -> list:
    """Get minimal tool set for agent.
    
    Architect gets orchestration tools (spawn, assign, etc.)
    PM gets read-only tools (no complete_my_task - they don't get assigned tasks!)
    Workers get full tool set including complete_my_task
    """
    if "Architect" in agent_name:
        return SLIM_ORCHESTRATOR_TOOLS
    
    # PM gets reduced tools - they observe/track, NOT execute tasks
    if "Manager" in agent_name or "Checky" in agent_name:
        # Filter out complete_my_task - PM doesn't get assigned tasks
        return [
            tool for tool in SLIM_TOOL_DEFINITIONS
            if tool.get("function", {}).get("name") != "complete_my_task"
        ]
    
    return SLIM_TOOL_DEFINITIONS


def get_slim_tools_prompt(agent_name: str) -> str:
    """Get minimal tools prompt for agent."""
    if "Architect" in agent_name:
        return SLIM_ORCHESTRATOR_PROMPT
    return SLIM_TOOLS_PROMPT
