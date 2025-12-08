"""
Agents package for Multi-Agent Chatroom.

This package contains all AI agent implementations.
"""

from agents.base_agent import BaseAgent
from agents.architect import Architect
from agents.backend_dev import BackendDev
from agents.frontend_dev import FrontendDev
from agents.qa_engineer import QAEngineer
from agents.devops_engineer import DevOpsEngineer
from agents.project_manager import ProjectManager
from agents.tech_writer import TechWriter
from agents.database_specialist import DatabaseSpecialist
from agents.api_designer import APIDesigner
from agents.code_reviewer import CodeReviewer
from agents.research_agent import ResearchAgent

# All available agent classes
AGENT_CLASSES = {
    "architect": Architect,
    "backend_dev": BackendDev,
    "frontend_dev": FrontendDev,
    "qa_engineer": QAEngineer,
    "devops": DevOpsEngineer,
    "project_manager": ProjectManager,
    "tech_writer": TechWriter,
    "database_specialist": DatabaseSpecialist,
    "api_designer": APIDesigner,
    "code_reviewer": CodeReviewer,
    "research": ResearchAgent,
}

# Display name to role key mapping (lowercase)
DISPLAY_NAME_TO_ROLE = {
    "bossy mcarchitect": "architect",
    "codey mcbackend": "backend_dev",
    "pixel mcfrontend": "frontend_dev",
    "bugsy mctester": "qa_engineer",
    "deployo mcops": "devops",
    "checky mcmanager": "project_manager",
    "docy mcwriter": "tech_writer",
    "schema mcdatabase": "database_specialist",
    "swagger mcendpoint": "api_designer",
    "nitpick mcreviewer": "code_reviewer",
    "googly mcresearch": "research",
}

# Default set of agents for the chatroom
# Architect orchestrates, Checky tracks progress, others build/test.
DEFAULT_AGENTS = [
    "architect",
    "project_manager",
    "backend_dev",
    "frontend_dev",
    "qa_engineer",
]


def resolve_role(name_or_role: str) -> str:
    """
    Resolve a display name or role key to a valid role key.
    
    Args:
        name_or_role: Either a role key (e.g., "backend_dev") or 
                      display name (e.g., "Codey McBackend")
    
    Returns:
        Valid role key
        
    Raises:
        ValueError: If name cannot be resolved
    """
    # Try as role key first (case-insensitive)
    normalized = name_or_role.lower().strip()
    if normalized in AGENT_CLASSES:
        return normalized
    
    # Try as display name
    if normalized in DISPLAY_NAME_TO_ROLE:
        return DISPLAY_NAME_TO_ROLE[normalized]
    
    # Not found - provide helpful error message
    valid_roles = list(AGENT_CLASSES.keys())
    valid_names = list(DISPLAY_NAME_TO_ROLE.keys())
    raise ValueError(
        f"Unknown role: '{name_or_role}'. "
        f"Valid role keys: {valid_roles}. "
        f"Valid display names: {valid_names}"
    )


def create_agent(agent_type: str, model: str = None, name_suffix: str = None) -> BaseAgent:
    """
    Factory function to create an agent instance.
    
    Args:
        agent_type: Role key (e.g., "backend_dev") or display name (e.g., "Codey McBackend")
        model: Optional model override
        name_suffix: Optional suffix for the agent name (e.g., "2" -> "Backend Dev 2")
        
    Returns:
        Instance of the requested agent type
        
    Raises:
        ValueError: If agent_type is not recognized
    """
    # Resolve display name or role key to valid role key
    role_key = resolve_role(agent_type)
    agent_class = AGENT_CLASSES[role_key]
    
    # Create agent
    if model:
        agent = agent_class(model=model)
    else:
        agent = agent_class()
        
    # Apply name suffix if provided
    if name_suffix:
        # If name is "Backend Dev", it becomes "Backend Dev 2"
        agent.name = f"{agent.name} {name_suffix}"
        
    return agent


def create_all_default_agents() -> list[BaseAgent]:
    """
    Create instances of all default agents.
    
    Returns:
        List of agent instances
    """
    return [create_agent(agent_type) for agent_type in DEFAULT_AGENTS]


__all__ = [
    "BaseAgent",
    "Architect",
    "BackendDev",
    "FrontendDev",
    "QAEngineer",
    "DevOpsEngineer",
    "ProjectManager",
    "TechWriter",
    "DatabaseSpecialist",
    "APIDesigner",
    "CodeReviewer",
    "ResearchAgent",
    "AGENT_CLASSES",
    "DISPLAY_NAME_TO_ROLE",
    "DEFAULT_AGENTS",
    "resolve_role",
    "create_agent",
    "create_all_default_agents",
]
