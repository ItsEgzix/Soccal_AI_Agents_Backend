"""
Path management utilities for test framework.

Uses Agents/core/path_manager for consistency.
Provides backward compatibility with old structure.
"""
from pathlib import Path
from typing import Optional
import sys


class PathManager:
    """
    Manages all path-related operations for test framework.
    
    Uses Agents/core/path_manager for agent paths to ensure consistency.
    Provides backward compatibility with old structure.
    """
    
    _project_root: Optional[Path] = None
    _agents_path_manager = None
    
    @staticmethod
    def get_project_root() -> Path:
        """
        Get AI_Backend root directory.
        
        Returns:
            Path to AI_Backend directory
        """
        if PathManager._project_root is None:
            # Go up from test/config/paths.py -> test -> AI_Backend
            PathManager._project_root = Path(__file__).parent.parent.parent
        return PathManager._project_root
    
    @staticmethod
    def _get_agents_path_manager():
        """Get Agents PathManager instance (lazy import)."""
        if PathManager._agents_path_manager is None:
            agents_root = PathManager.get_project_root() / "Agents"
            sys.path.insert(0, str(agents_root))
            try:
                from core.path_manager import AgentPathManager
                PathManager._agents_path_manager = AgentPathManager
            except ImportError:
                # Fallback if core not available
                PathManager._agents_path_manager = None
        return PathManager._agents_path_manager
    
    @staticmethod
    def get_agents_dir() -> Path:
        """
        Get agents directory.
        
        Returns:
            Path to 'Agents' directory
        """
        return PathManager.get_project_root() / "Agents"
    
    @staticmethod
    def get_scraper_path() -> Path:
        """
        Get web scraper module path.
        
        Returns:
            Path to web scraper directory
        """
        agents_root = PathManager.get_project_root() / "Agents"
        return agents_root / "teams" / "company_context" / "tools" / "web_scraper"
    
    @staticmethod
    def get_instagram_scraper_path() -> Path:
        """
        Get Instagram scraper module path.
        
        Returns:
            Path to Instagram scraper directory
        """
        agents_root = PathManager.get_project_root() / "Agents"
        return agents_root / "teams" / "company_context" / "tools" / "instagram_scraper"
    
    @staticmethod
    def get_utils_path() -> Path:
        """
        Get utils directory path.
        
        Returns:
            Path to utils directory
        """
        agents_root = PathManager.get_project_root() / "Agents"
        return agents_root / "teams" / "company_context" / "utils"
    
    @staticmethod
    def get_tool_path(team_name: str, tool_name: str) -> Path:
        """
        Get tool path using Agents path manager (new structure).
        
        Args:
            team_name: Name of the team
            tool_name: Name of the tool
        
        Returns:
            Path to tool directory
        """
        path_mgr = PathManager._get_agents_path_manager()
        if path_mgr:
            return path_mgr.get_tool_path(team_name, tool_name)
        
        # Fallback
        return PathManager.get_project_root() / "Agents" / "teams" / team_name / "tools" / tool_name
    
    @staticmethod
    def add_to_sys_path(path: Path) -> None:
        """
        Add a path to sys.path if not already present.
        
        Args:
            path: Path to add to sys.path
        """
        if not path.exists():
            return
        
        path_str = str(path.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

