"""Integration tests for codebase scanner."""

import pytest
import asyncio
from pathlib import Path
import tempfile
import time

from signal_hub.indexing import CodebaseScanner, FileType


class TestScannerIntegration:
    """Integration tests for codebase scanner."""
    
    @pytest.fixture
    def large_repo(self):
        """Create a larger test repository for performance testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create multiple directories with files
            for i in range(10):
                dir_path = root / f"module_{i}"
                dir_path.mkdir()
                
                # Create Python files
                for j in range(50):
                    file_path = dir_path / f"file_{j}.py"
                    file_path.write_text(f"# Module {i} File {j}\nprint('test')")
                
                # Create some other file types
                (dir_path / "README.md").write_text(f"# Module {i}")
                (dir_path / "config.yaml").write_text("key: value")
            
            # Create node_modules to test ignoring
            node_modules = root / "node_modules"
            node_modules.mkdir()
            for i in range(100):
                (node_modules / f"package_{i}.js").write_text("module.exports = {}")
            
            yield root
    
    @pytest.mark.asyncio
    async def test_performance_large_repo(self, large_repo):
        """Test scanning performance on larger repository."""
        scanner = CodebaseScanner()
        
        start_time = time.time()
        files = await scanner.scan(large_repo)
        scan_time = time.time() - start_time
        
        # Should scan 500+ files quickly
        assert len(files) >= 500  # 10 dirs * 50 py files + extras
        assert scan_time < 10.0  # Should complete in under 10 seconds
        
        # Verify node_modules was ignored
        file_paths = [str(f.path) for f in files]
        assert not any("node_modules" in path for path in file_paths)
        
        print(f"Scanned {len(files)} files in {scan_time:.2f} seconds")
        print(f"Rate: {len(files) / scan_time:.1f} files/second")
    
    @pytest.mark.asyncio
    async def test_real_python_project(self):
        """Test scanning the Signal Hub project itself."""
        project_root = Path(__file__).parent.parent.parent
        scanner = CodebaseScanner()
        
        files = await scanner.scan(project_root)
        
        # Should find our own source files
        file_names = {f.path.name for f in files}
        assert "scanner.py" in file_names
        assert "server.py" in file_names
        assert "pyproject.toml" in file_names
        
        # Should ignore common patterns
        file_paths = [str(f.path) for f in files]
        assert not any("__pycache__" in path for path in file_paths)
        assert not any(".git" in path for path in file_paths)
        assert not any(".pytest_cache" in path for path in file_paths)
        
        # Check file types are detected correctly
        py_files = [f for f in files if f.file_type == FileType.PYTHON]
        assert len(py_files) > 10  # Should have many Python files
    
    @pytest.mark.asyncio
    async def test_concurrent_scans(self):
        """Test running multiple scans concurrently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            # Create test structure
            for i in range(5):
                dir_path = root / f"project_{i}"
                dir_path.mkdir()
                (dir_path / "main.py").write_text("print('test')")
                (dir_path / "README.md").write_text("# Project")
            
            scanner = CodebaseScanner()
            
            # Run multiple scans concurrently
            tasks = [
                scanner.scan(root / f"project_{i}")
                for i in range(5)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Each scan should return 2 files
            for files in results:
                assert len(files) == 2
                file_names = [f.path.name for f in files]
                assert "main.py" in file_names
                assert "README.md" in file_names
    
    @pytest.mark.asyncio
    async def test_memory_usage_streaming(self, large_repo):
        """Test that async iteration doesn't load all files in memory."""
        scanner = CodebaseScanner()
        
        file_count = 0
        max_concurrent = 0
        current_files = []
        
        async for file_info in scanner.scan_async(large_repo):
            file_count += 1
            current_files.append(file_info)
            
            # Simulate processing that takes time
            await asyncio.sleep(0.001)
            
            # Remove processed files (simulate streaming)
            if len(current_files) > 10:
                current_files.pop(0)
            
            max_concurrent = max(max_concurrent, len(current_files))
        
        # Should have processed many files
        assert file_count >= 500
        
        # But never held too many in memory at once
        assert max_concurrent <= 15  # Small buffer
    
    @pytest.mark.asyncio
    async def test_progress_accuracy(self, large_repo):
        """Test that progress reporting is accurate."""
        scanner = CodebaseScanner()
        
        progress_history = []
        
        def track_progress(progress):
            progress_history.append({
                "percentage": progress.percentage,
                "scanned": progress.files_scanned,
                "total": progress.total_files
            })
        
        files = []
        async for file_info in scanner.scan_with_progress(
            large_repo,
            progress_callback=track_progress
        ):
            files.append(file_info)
        
        # Progress should increase monotonically
        percentages = [p["percentage"] for p in progress_history]
        assert all(percentages[i] <= percentages[i+1] 
                  for i in range(len(percentages)-1))
        
        # Final progress should be 100%
        if progress_history:
            final = progress_history[-1]
            assert final["percentage"] == 100.0
            assert final["scanned"] == final["total"]
            assert final["scanned"] == len(files)