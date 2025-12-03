"""
Path Manager

Centralized path management for all agents, teams, and tools.
Single source of truth for all path operations - no more scattered sys.path.append()!
"""

from pathlib import Path
from typing import Optional
import sys


class AgentPathManager:
    """
    Manages all agent-related paths.
    
    Provides a single source of truth for all path operations,
    making it easy to understand and modify path structures.
    """
    
    _agents_root: Optional[Path] = None
    
    @staticmethod
    def get_agents_root() -> Path:
        """
        Get Agents directory root.
        
        Returns:
            Path to Agents directory
        """
        if AgentPathManager._agents_root is None:
            # This file is at Agents/core/path_manager.py
            AgentPathManager._agents_root = Path(__file__).parent.parent
        return AgentPathManager._agents_root
    
    @staticmethod
    def get_teams_dir() -> Path:
        """
        Get teams directory.
        
        Returns:
            Path to teams directory
        """
        return AgentPathManager.get_agents_root() / "teams"
    
    @staticmethod
    def get_shared_dir() -> Path:
        """
        Get shared utilities directory.
        
        Returns:
            Path to shared directory
        """
        return AgentPathManager.get_agents_root() / "shared"
    
    @staticmethod
    def get_team_path(team_name: str) -> Path:
        """
        Get path to a team directory.
        
        Args:
            team_name: Name of the team (e.g., "company_context")
        
        Returns:
            Path to team directory
        """
        return AgentPathManager.get_teams_dir() / team_name
    
    @staticmethod
    def get_agent_path(team_name: str, agent_name: str) -> Path:
        """
        Get path to an agent directory.
        
        Args:
            team_name: Name of the team
            agent_name: Name of the agent
        
        Returns:
            Path to agent directory
        """
        return (
            AgentPathManager.get_team_path(team_name)
            / "agents"
            / agent_name
        )
    
    @staticmethod
    def get_tool_path(team_name: str, tool_name: str) -> Path:
        """
        Get path to a tool directory.
        
        Args:
            team_name: Name of the team
            tool_name: Name of the tool
        
        Returns:
            Path to tool directory
        """
        return (
            AgentPathManager.get_team_path(team_name)
            / "tools"
            / tool_name
        )
    
    @staticmethod
    def get_team_utils_path(team_name: str) -> Path:
        """
        Get path to team-specific utils directory.
        
        Args:
            team_name: Name of the team
        
        Returns:
            Path to team utils directory
        """
        return AgentPathManager.get_team_path(team_name) / "utils"
    
    @staticmethod
    def setup_imports(
        team_name: str,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> None:
        """
        Setup Python imports for a team/agent/tool.
        
        Automatically adds necessary paths to sys.path in the correct order.
        
        Args:
            team_name: Name of the team
            agent_name: Optional agent name
            tool_name: Optional tool name
        """
        # Add shared utilities first (highest priority)
        shared_path = AgentPathManager.get_shared_dir()
        AgentPathManager._add_to_path(shared_path)
        
        # Add team path
        team_path = AgentPathManager.get_team_path(team_name)
        AgentPathManager._add_to_path(team_path)
        
        # Add team utils
        team_utils_path = AgentPathManager.get_team_utils_path(team_name)
        AgentPathManager._add_to_path(team_utils_path)
        
        # Add agent path if specified
        if agent_name:
            agent_path = AgentPathManager.get_agent_path(team_name, agent_name)
            AgentPathManager._add_to_path(agent_path)
        
        # Add tool path if specified
        if tool_name:
            tool_path = AgentPathManager.get_tool_path(team_name, tool_name)
            AgentPathManager._add_to_path(tool_path)
    
    @staticmethod
    def _add_to_path(path: Path) -> None:
        """
        Add path to sys.path if not already present.
        
        Args:
            path: Path to add
        """
        if not path.exists():
            return
        
        path_str = str(path.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

