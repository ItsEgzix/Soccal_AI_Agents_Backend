"""
Path management utilities.

Provides centralized path management to avoid scattered path manipulations
throughout the codebase.
"""
from pathlib import Path
from typing import Optional


class PathManager:
    """
    Manages all path-related operations.
    
    Provides a single source of truth for all file and directory paths,
    making it easy to understand and modify path structures.
    """
    
    _project_root: Optional[Path] = None
    
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
    def get_agents_dir() -> Path:
        """
        Get agents directory.
        
        Returns:
            Path to 'Agents/Company Context Team' directory
        """
        return PathManager.get_project_root() / "Agents" / "Company Context Team"
    
    @staticmethod
    def get_scraper_path() -> Path:
        """
        Get web scraper module path.
        
        Returns:
            Path to 'Company_Context_Agent/tools/web scraper' directory
        """
        return (
            PathManager.get_agents_dir() 
            / "Company_Context_Agent" 
            / "tools" 
            / "web scraper"
        )
    
    @staticmethod
    def get_instagram_scraper_path() -> Path:
        """
        Get Instagram scraper module path.
        
        Returns:
            Path to 'Brand_Voice_Agent/tools/insgtram scraper' directory
        """
        return (
            PathManager.get_agents_dir()
            / "Brand_Voice_Agent"
            / "tools"
            / "insgtram scraper"
        )
    
    @staticmethod
    def get_utils_path() -> Path:
        """
        Get utils directory path.
        
        Returns:
            Path to 'Agents/Company Context Team/utils' directory
        """
        return PathManager.get_agents_dir() / "utils"
    
    @staticmethod
    def add_to_sys_path(path: Path) -> None:
        """
        Add a path to sys.path if not already present.
        
        Args:
            path: Path to add to sys.path
        """
        import sys
        path_str = str(path.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

