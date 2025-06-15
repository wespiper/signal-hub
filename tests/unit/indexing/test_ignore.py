"""Unit tests for gitignore pattern handling."""

import pytest
from pathlib import Path
import tempfile

from signal_hub.indexing.ignore import IgnoreManager


class TestIgnoreManager:
    """Test IgnoreManager class."""
    
    def test_default_patterns(self):
        """Test that default patterns are loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            
            # Check some default patterns
            assert ".git/" in manager.patterns
            assert "__pycache__/" in manager.patterns
            assert "node_modules/" in manager.patterns
            assert ".DS_Store" in manager.patterns
    
    def test_should_ignore_default_patterns(self):
        """Test ignoring files matching default patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            
            # Test various default patterns
            assert manager.should_ignore(Path(".git/config"))
            assert manager.should_ignore(Path("__pycache__/module.pyc"))
            assert manager.should_ignore(Path("node_modules/package/index.js"))
            assert manager.should_ignore(Path(".DS_Store"))
            assert manager.should_ignore(Path("file.pyc"))
    
    def test_load_gitignore_file(self):
        """Test loading patterns from .gitignore file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create .gitignore
            gitignore = root / ".gitignore"
            gitignore.write_text("""
# Comment line
*.log
temp/
/build/
secret.txt
""")
            
            manager = IgnoreManager(root)
            
            # Check patterns were loaded
            assert "*.log" in manager.patterns
            assert "temp/" in manager.patterns
            assert "/build/" in manager.patterns
            assert "secret.txt" in manager.patterns
    
    def test_add_custom_patterns(self):
        """Test adding custom ignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            
            # Add custom patterns
            manager.add_patterns(["*.tmp", "custom/", "specific.file"])
            
            assert manager.should_ignore(Path("test.tmp"))
            assert manager.should_ignore(Path("custom/file.txt"))
            assert manager.should_ignore(Path("specific.file"))
    
    def test_pattern_matching_wildcards(self):
        """Test wildcard pattern matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            manager.patterns = []  # Clear defaults for testing
            
            # Test * wildcard (matches anything except /)
            manager.add_patterns(["*.txt", "test_*.py"])
            
            assert manager.should_ignore(Path("file.txt"))
            assert manager.should_ignore(Path("test_module.py"))
            assert not manager.should_ignore(Path("file.py"))
            assert not manager.should_ignore(Path("dir/file.txt"))  # * doesn't match /
    
    def test_pattern_matching_double_wildcard(self):
        """Test ** wildcard pattern matching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            manager.patterns = []  # Clear defaults
            
            # Test ** wildcard (matches anything including /)
            manager.add_patterns(["**/test.py", "logs/**"])
            
            assert manager.should_ignore(Path("test.py"))
            assert manager.should_ignore(Path("dir/test.py"))
            assert manager.should_ignore(Path("dir/sub/test.py"))
            assert manager.should_ignore(Path("logs/app.log"))
            assert manager.should_ignore(Path("logs/2023/app.log"))
    
    def test_directory_only_patterns(self):
        """Test patterns that only match directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            manager.patterns = []  # Clear defaults
            
            # Patterns ending with / only match directories
            manager.add_patterns(["temp/", "build/"])
            
            assert manager.should_ignore(Path("temp/file.txt"))
            assert manager.should_ignore(Path("build/output.o"))
            # In practice, we can't distinguish files vs dirs from path alone
            # So directory patterns will match anything with that prefix
    
    def test_anchored_patterns(self):
        """Test root-anchored patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            manager.patterns = []  # Clear defaults
            
            # Patterns starting with / are anchored to root
            manager.add_patterns(["/build/", "/config.txt"])
            
            assert manager.should_ignore(Path("build/output"))
            assert manager.should_ignore(Path("config.txt"))
            assert not manager.should_ignore(Path("src/build/output"))
            assert not manager.should_ignore(Path("src/config.txt"))
    
    def test_get_ignored_dirs(self):
        """Test getting simple directory names to ignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            
            ignored_dirs = manager.get_ignored_dirs()
            
            # Should include simple directory patterns from defaults
            assert ".git" in ignored_dirs
            assert "__pycache__" in ignored_dirs
            assert "node_modules" in ignored_dirs
            assert ".venv" in ignored_dirs
    
    def test_complex_gitignore_patterns(self):
        """Test more complex gitignore patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            manager.patterns = []  # Clear defaults
            
            # Add complex patterns
            manager.add_patterns([
                "!important.log",  # Negation (not implemented, but shouldn't crash)
                "*.py[cod]",       # Character class
                "temp?.txt",       # Single char wildcard
                "[Dd]ebug/",       # Character alternatives
            ])
            
            # Basic functionality should still work
            assert manager.should_ignore(Path("file.pyc"))
            assert manager.should_ignore(Path("temp1.txt"))
    
    def test_case_sensitivity(self):
        """Test that patterns are case-sensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manager = IgnoreManager(root)
            manager.patterns = []  # Clear defaults
            
            manager.add_patterns(["*.TXT", "Debug/"])
            
            assert manager.should_ignore(Path("file.TXT"))
            assert not manager.should_ignore(Path("file.txt"))
            assert manager.should_ignore(Path("Debug/log"))
            assert not manager.should_ignore(Path("debug/log"))