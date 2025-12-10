"""
Tests for SessionController.

Verifies that the shared controller works correctly for both TUI and CLI modes.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock


class TestSessionController:
    """Tests for SessionController."""
    
    def test_import(self):
        """Test that SessionController can be imported."""
        from core.session_controller import SessionController, get_session_controller
        
        controller = SessionController()
        assert controller is not None
        assert controller.project is None
        assert controller.chatroom is None
        assert controller.is_devussy_mode == False
    
    def test_singleton(self):
        """Test get_session_controller returns same instance."""
        from core.session_controller import get_session_controller, reset_session_controller
        
        reset_session_controller()
        c1 = get_session_controller()
        c2 = get_session_controller()
        assert c1 is c2
        reset_session_controller()
    
    def test_get_status_no_chatroom(self):
        """Test get_status when no chatroom is initialized."""
        from core.session_controller import SessionController
        
        controller = SessionController()
        status = controller.get_status()
        
        assert status["is_running"] == False
        assert status["message_count"] == 0
        assert status["agent_count"] == 0
    
    def test_get_agents_no_chatroom(self):
        """Test get_agents when no chatroom is initialized."""
        from core.session_controller import SessionController
        
        controller = SessionController()
        agents = controller.get_agents()
        
        assert agents == []
    
    def test_get_tasks_empty(self):
        """Test get_tasks when no tasks exist."""
        from core.session_controller import SessionController
        
        controller = SessionController()
        tasks = controller.get_tasks()
        
        assert isinstance(tasks, list)
    
    def test_get_available_roles(self):
        """Test get_available_roles returns agent roles."""
        from core.session_controller import SessionController
        
        controller = SessionController()
        roles = controller.get_available_roles()
        
        assert isinstance(roles, list)
        assert len(roles) > 0
        assert "architect" in roles
        assert "backend_dev" in roles
    
    def test_get_token_stats(self):
        """Test get_token_stats returns valid dict."""
        from core.session_controller import SessionController
        
        controller = SessionController()
        stats = controller.get_token_stats()
        
        assert isinstance(stats, dict)
        assert "total_tokens" in stats or "prompt_tokens" in stats


class TestSwarmCLI:
    """Tests for the SwarmCLI class."""
    
    def test_import(self):
        """Test that SwarmCLI can be imported."""
        from main import SwarmCLI
        
        cli = SwarmCLI()
        assert cli is not None
        assert cli.controller is not None
        assert cli.running == True
    
    def test_colors_defined(self):
        """Test that ANSI colors are properly defined."""
        from main import Colors, AGENT_COLORS
        
        assert Colors.RESET is not None
        assert Colors.CYAN is not None
        assert len(AGENT_COLORS) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
