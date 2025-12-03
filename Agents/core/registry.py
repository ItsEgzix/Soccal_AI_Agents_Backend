"""
Agent Registry

Auto-discovery system for agents, teams, and tools.
Makes it easy to find and use components without hardcoding.
"""

from pathlib import Path
from typing import Dict, List, Type, Optional
import importlib
import sys

from .base_agent import BaseAgent
from .base_tool import BaseTool
from .path_manager import AgentPathManager


class AgentRegistry:
    """
    Registry for auto-discovering agents, teams, and tools.
    
    Automatically finds all components, making it easy to:
    - List available agents
    - Get agent by name
    - Discover tools
    - Find teams
    
    Usage:
        # Discover all components
        AgentRegistry.discover_all()
        
        # Get an agent
        agent_class = AgentRegistry.get_agent("company_context", "CompanyContextAgent")
        
        # List all agents
        agents = AgentRegistry.list_agents()
    """
    
    _agents: Dict[str, Type[BaseAgent]] = {}
    _tools: Dict[str, Type[BaseTool]] = {}
    _teams: List[str] = []
    _initialized = False
    
    @classmethod
    def discover_all(cls) -> None:
        """
        Discover all agents, teams, and tools.
        
        Scans the teams directory and automatically registers all components.
        Safe to call multiple times - only discovers once.
        """
        if cls._initialized:
            return
        
        teams_dir = AgentPathManager.get_teams_dir()
        
        if not teams_dir.exists():
            print(f"Warning: Teams directory not found: {teams_dir}")
            return
        
        # Discover teams
        for team_dir in teams_dir.iterdir():
            if team_dir.is_dir() and not team_dir.name.startswith('_'):
                cls._teams.append(team_dir.name)
                cls._discover_team(team_dir)
        
        cls._initialized = True
        print(f"AgentRegistry: Discovered {len(cls._teams)} teams, "
              f"{len(cls._agents)} agents, {len(cls._tools)} tools")
    
    @classmethod
    def _discover_team(cls, team_dir: Path) -> None:
        """
        Discover agents and tools in a team.
        
        Args:
            team_dir: Path to team directory
        """
        team_name = team_dir.name
        
        # Discover agents
        agents_dir = team_dir / "agents"
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir() and not agent_dir.name.startswith('_'):
                    cls._discover_agent(agent_dir, team_name)
        
        # Discover tools
        tools_dir = team_dir / "tools"
        if tools_dir.exists():
            for tool_dir in tools_dir.iterdir():
                if tool_dir.is_dir() and not tool_dir.name.startswith('_'):
                    cls._discover_tool(tool_dir, team_name)
    
    @classmethod
    def _discover_agent(cls, agent_dir: Path, team_name: str) -> None:
        """
        Discover and register an agent.
        
        Args:
            agent_dir: Path to agent directory
            team_name: Name of the team
        """
        agent_file = agent_dir / "agent.py"
        if not agent_file.exists():
            return
        
        agent_name = agent_dir.name
        
        try:
            # Setup imports
            AgentPathManager.setup_imports(team_name, agent_name)
            
            # Try to import
            # Format: teams.team_name.agents.agent_name.agent
            module_path = f"teams.{team_name}.agents.{agent_name}.agent"
            
            # Add parent directory to path for relative imports
            parent_path = str(agent_dir.parent.parent.parent)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)
            
            module = importlib.import_module(module_path)
            
            # Find agent class (class ending with 'Agent' or inheriting from BaseAgent)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseAgent) and 
                    attr != BaseAgent):
                    agent_key = f"{team_name}.{agent_name}"
                    cls._agents[agent_key] = attr
                    print(f"  Registered agent: {agent_key} -> {attr_name}")
                    break
        except Exception as e:
            print(f"Warning: Could not register agent {team_name}.{agent_name}: {e}")
    
    @classmethod
    def _discover_tool(cls, tool_dir: Path, team_name: str) -> None:
        """
        Discover and register a tool.
        
        Args:
            tool_dir: Path to tool directory
            team_name: Name of the team
        """
        tool_name = tool_dir.name
        
        # Look for tool files (could be scraper.py, processor.py, etc.)
        tool_files = list(tool_dir.glob("*.py"))
        if not tool_files:
            return
        
        # Try to find a class that inherits from BaseTool
        try:
            AgentPathManager.setup_imports(team_name, tool_name=tool_name)
            
            # Import the first Python file
            tool_file = tool_files[0]
            module_name = tool_file.stem
            
            # Add parent directory to path
            parent_path = str(tool_dir.parent.parent.parent)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)
            
            # Try to import
            module_path = f"teams.{team_name}.tools.{tool_name}.{module_name}"
            module = importlib.import_module(module_path)
            
            # Find tool class
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseTool) and 
                    attr != BaseTool):
                    tool_key = f"{team_name}.{tool_name}"
                    cls._tools[tool_key] = attr
                    print(f"  Registered tool: {tool_key} -> {attr_name}")
                    break
        except Exception as e:
            # Tools are optional, so just warn
            pass
    
    @classmethod
    def get_agent(cls, team_name: str, agent_name: str) -> Optional[Type[BaseAgent]]:
        """
        Get agent class by team and agent name.
        
        Args:
            team_name: Name of the team
            agent_name: Name of the agent
        
        Returns:
            Agent class or None if not found
        """
        cls.discover_all()
        key = f"{team_name}.{agent_name}"
        return cls._agents.get(key)
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """
        List all available agents.
        
        Returns:
            List of agent keys in format "team_name.agent_name"
        """
        cls.discover_all()
        return list(cls._agents.keys())
    
    @classmethod
    def list_teams(cls) -> List[str]:
        """
        List all available teams.
        
        Returns:
            List of team names
        """
        cls.discover_all()
        return cls._teams.copy()
    
    @classmethod
    def get_tool(cls, team_name: str, tool_name: str) -> Optional[Type[BaseTool]]:
        """
        Get tool class by team and tool name.
        
        Args:
            team_name: Name of the team
            tool_name: Name of the tool
        
        Returns:
            Tool class or None if not found
        """
        cls.discover_all()
        key = f"{team_name}.{tool_name}"
        return cls._tools.get(key)
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """
        List all available tools.
        
        Returns:
            List of tool keys in format "team_name.tool_name"
        """
        cls.discover_all()
        return list(cls._tools.keys())
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset registry (useful for testing).
        """
        cls._agents.clear()
        cls._tools.clear()
        cls._teams.clear()
        cls._initialized = False

