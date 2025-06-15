"""Unit tests for codebase scanner."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from signal_hub.indexing.scanner import CodebaseScanner, ScanProgress
from signal_hub.indexing.file_info import FileType


class TestScanProgress:
    """Test ScanProgress class."""
    
    def test_progress_initialization(self):
        """Test progress object initialization."""
        progress = ScanProgress()
        
        assert progress.total_files == 0
        assert progress.files_scanned == 0
        assert progress.directories_scanned == 0
        assert progress.files_ignored == 0
        assert progress.errors == 0
        assert progress.current_path is None
    
    def test_progress_percentage(self):
        """Test percentage calculation."""
        progress = ScanProgress(total_files=100, files_scanned=25)
        assert progress.percentage == 25.0
        
        # Test zero total
        progress = ScanProgress(total_files=0, files_scanned=0)
        assert progress.percentage == 0.0


class TestCodebaseScanner:
    """Test CodebaseScanner class."""
    
    @pytest.fixture
    def scanner(self):
        """Create a scanner instance."""
        return CodebaseScanner(
            max_file_size=1024 * 1024,
            follow_symlinks=False,
            max_depth=None
        )
    
    @pytest.fixture
    def test_repo(self):
        """Create a test repository structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create directory structure
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("print('hello')")
            (root / "src" / "utils.py").write_text("def helper(): pass")
            
            (root / "tests").mkdir()
            (root / "tests" / "test_main.py").write_text("import pytest")
            
            (root / "docs").mkdir()
            (root / "docs" / "README.md").write_text("# Documentation")
            
            # Hidden directories
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("git config")
            
            # Binary file
            (root / "binary.dat").write_bytes(b"\x00\x01\x02\x03")
            
            # Large file
            (root / "large.txt").write_text("x" * (2 * 1024 * 1024))
            
            # Create .gitignore
            (root / ".gitignore").write_text("*.log\ntemp/\n")
            
            # Files to be ignored
            (root / "debug.log").write_text("log content")
            (root / "temp").mkdir()
            (root / "temp" / "cache.txt").write_text("temp file")
            
            yield root
    
    @pytest.mark.asyncio
    async def test_scan_basic(self, scanner, test_repo):
        """Test basic scanning functionality."""
        files = await scanner.scan(test_repo)
        
        # Check that we got some files
        assert len(files) > 0
        
        # Check file types
        file_paths = [f.path.name for f in files]
        assert "main.py" in file_paths
        assert "utils.py" in file_paths
        assert "test_main.py" in file_paths
        assert "README.md" in file_paths
        
        # Check that ignored files are not included
        assert "config" not in file_paths  # .git/config
        assert "debug.log" not in file_paths  # *.log pattern
        assert "cache.txt" not in file_paths  # temp/ pattern
        assert "binary.dat" not in file_paths  # Binary file
        assert "large.txt" not in file_paths  # Too large
    
    @pytest.mark.asyncio
    async def test_scan_async_iterator(self, scanner, test_repo):
        """Test async iteration over files."""
        files = []
        async for file_info in scanner.scan_async(test_repo):
            files.append(file_info)
        
        assert len(files) > 0
        
        # Verify file info objects
        for file_info in files:
            assert file_info.path.exists()
            assert file_info.size >= 0
            assert file_info.file_type != FileType.UNKNOWN
            assert file_info.should_index()
    
    @pytest.mark.asyncio
    async def test_scan_with_custom_ignore(self, scanner, test_repo):
        """Test scanning with custom ignore patterns."""
        files = await scanner.scan(test_repo, ignore_patterns=["*.py"])
        
        # Should only have non-Python files
        file_names = [f.path.name for f in files]
        assert "README.md" in file_names
        assert "main.py" not in file_names
        assert "utils.py" not in file_names
        assert "test_main.py" not in file_names
    
    @pytest.mark.asyncio
    async def test_scan_nonexistent_path(self, scanner):
        """Test scanning non-existent path."""
        with pytest.raises(ValueError) as exc_info:
            await scanner.scan("/nonexistent/path")
        assert "does not exist" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_scan_file_not_directory(self, scanner, test_repo):
        """Test scanning a file instead of directory."""
        file_path = test_repo / "src" / "main.py"
        
        with pytest.raises(ValueError) as exc_info:
            await scanner.scan(file_path)
        assert "not a directory" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_scan_with_progress(self, scanner, test_repo):
        """Test scanning with progress reporting."""
        progress_updates = []
        
        def progress_callback(progress: ScanProgress):
            progress_updates.append({
                "scanned": progress.files_scanned,
                "total": progress.total_files,
                "percentage": progress.percentage
            })
        
        files = []
        async for file_info in scanner.scan_with_progress(
            test_repo,
            progress_callback=progress_callback
        ):
            files.append(file_info)
        
        # Should have received progress updates
        assert len(progress_updates) > 0
        assert len(files) > 0
        
        # Final progress should be 100%
        if progress_updates:
            last_update = progress_updates[-1]
            assert last_update["scanned"] == len(files)
    
    @pytest.mark.asyncio
    async def test_scan_cancellation(self, scanner, test_repo):
        """Test cancelling a scan operation."""
        files_before_cancel = []
        
        async for file_info in scanner.scan_async(test_repo):
            files_before_cancel.append(file_info)
            if len(files_before_cancel) >= 2:
                scanner.cancel()
        
        # Should have stopped after cancellation
        assert len(files_before_cancel) <= 3  # May process a few more
    
    @pytest.mark.asyncio
    async def test_scan_with_max_depth(self, test_repo):
        """Test scanning with maximum depth limit."""
        scanner = CodebaseScanner(max_depth=1)
        files = await scanner.scan(test_repo)
        
        # Should only get files from root and immediate subdirs
        for file_info in files:
            path_parts = file_info.path.relative_to(test_repo).parts
            assert len(path_parts) <= 2  # At most one directory deep
    
    @pytest.mark.asyncio
    async def test_scan_symlinks(self, test_repo):
        """Test handling of symbolic links."""
        # Create a symlink
        link_target = test_repo / "src" / "main.py"
        link_path = test_repo / "link_to_main.py"
        
        try:
            os.symlink(link_target, link_path)
        except OSError:
            pytest.skip("Cannot create symlinks on this system")
        
        # Scanner with follow_symlinks=False (default)
        scanner = CodebaseScanner(follow_symlinks=False)
        files = await scanner.scan(test_repo)
        
        file_names = [f.path.name for f in files]
        assert "link_to_main.py" not in file_names
        
        # Scanner with follow_symlinks=True
        scanner = CodebaseScanner(follow_symlinks=True)
        files = await scanner.scan(test_repo)
        
        file_names = [f.path.name for f in files]
        assert "link_to_main.py" in file_names
    
    @pytest.mark.asyncio
    async def test_scan_permission_errors(self, scanner):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create a file
            (root / "readable.txt").write_text("content")
            
            # Create a directory with no read permissions
            restricted = root / "restricted"
            restricted.mkdir()
            (restricted / "secret.txt").write_text("secret")
            
            try:
                # Remove read permissions
                os.chmod(restricted, 0o000)
                
                # Should handle gracefully
                files = await scanner.scan(root)
                
                file_names = [f.path.name for f in files]
                assert "readable.txt" in file_names
                assert "secret.txt" not in file_names
                
            finally:
                # Restore permissions for cleanup
                try:
                    os.chmod(restricted, 0o755)
                except:
                    pass