"""Gitignore pattern handling for file filtering."""

import re
from pathlib import Path
from typing import List, Optional, Set
import fnmatch


class IgnoreManager:
    """Manages gitignore patterns and file filtering."""
    
    # Default patterns to always ignore
    DEFAULT_PATTERNS = [
        # Version control
        ".git/",
        ".svn/",
        ".hg/",
        
        # Python
        "__pycache__/",
        "*.pyc",
        "*.pyo",
        ".venv/",
        "venv/",
        "env/",
        ".env",
        
        # Node.js
        "node_modules/",
        "npm-debug.log",
        
        # IDE
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        ".DS_Store",
        
        # Build outputs
        "dist/",
        "build/",
        "target/",
        "*.o",
        "*.so",
        "*.dylib",
        
        # Misc
        ".coverage",
        "*.log",
        ".cache/",
    ]
    
    def __init__(self, root_path: Path):
        """Initialize the ignore manager.
        
        Args:
            root_path: Root directory of the codebase
        """
        self.root_path = root_path
        self.patterns: List[str] = []
        self._regex_cache: dict[str, re.Pattern] = {}
        
        # Load default patterns
        self.patterns.extend(self.DEFAULT_PATTERNS)
        
        # Load .gitignore if exists
        gitignore_path = root_path / ".gitignore"
        if gitignore_path.exists():
            self._load_gitignore(gitignore_path)
    
    def _load_gitignore(self, gitignore_path: Path) -> None:
        """Load patterns from a .gitignore file."""
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        self.patterns.append(line)
        except Exception:
            # Ignore errors reading .gitignore
            pass
    
    def add_patterns(self, patterns: List[str]) -> None:
        """Add custom ignore patterns."""
        self.patterns.extend(patterns)
    
    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored.
        
        Args:
            path: Path to check (relative to root)
            
        Returns:
            True if the path should be ignored
        """
        # Convert to string for pattern matching
        path_str = str(path)
        
        # Check each pattern
        for pattern in self.patterns:
            if self._matches_pattern(path_str, pattern):
                return True
        
        return False
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a gitignore pattern.
        
        This implements basic gitignore pattern matching:
        - Patterns ending with / only match directories
        - Patterns starting with / are anchored to root
        - * matches any characters except /
        - ** matches any characters including /
        - ? matches any single character except /
        """
        # Normalize path separators
        path = path.replace("\\", "/")
        pattern = pattern.replace("\\", "/")
        
        # Handle directory-only patterns
        is_dir_pattern = pattern.endswith("/")
        if is_dir_pattern:
            pattern = pattern[:-1]
        
        # Handle root-anchored patterns
        is_anchored = pattern.startswith("/")
        if is_anchored:
            pattern = pattern[1:]
        
        # Convert gitignore pattern to regex
        regex_pattern = self._pattern_to_regex(pattern)
        
        # Check if pattern matches
        if is_anchored:
            # Anchored patterns must match from start
            match = re.match(regex_pattern, path)
        else:
            # Non-anchored patterns can match anywhere
            match = re.search(regex_pattern, path)
        
        if match and is_dir_pattern:
            # Directory patterns should only match directories
            # For simplicity, we assume paths ending with pattern are directories
            return True
        
        return bool(match)
    
    def _pattern_to_regex(self, pattern: str) -> str:
        """Convert a gitignore pattern to a regex pattern."""
        # Check cache
        if pattern in self._regex_cache:
            return self._regex_cache[pattern]
        
        # Escape special regex characters except * and ?
        regex_pattern = re.escape(pattern)
        
        # Replace gitignore wildcards with regex equivalents
        regex_pattern = regex_pattern.replace(r"\*\*", ".*")  # ** matches anything
        regex_pattern = regex_pattern.replace(r"\*", "[^/]*")  # * matches anything except /
        regex_pattern = regex_pattern.replace(r"\?", "[^/]")   # ? matches any single char except /
        
        # Cache the compiled pattern
        self._regex_cache[pattern] = regex_pattern
        
        return regex_pattern
    
    def get_ignored_dirs(self) -> Set[str]:
        """Get a set of directory names that should be ignored.
        
        This is an optimization to skip entire directories during traversal.
        """
        ignored_dirs = set()
        
        for pattern in self.patterns:
            # Only consider simple directory patterns
            if pattern.endswith("/") and "/" not in pattern[:-1] and "*" not in pattern:
                ignored_dirs.add(pattern[:-1])
        
        return ignored_dirs