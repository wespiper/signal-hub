"""Codebase scanner for traversing and analyzing repositories."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Callable, List, Optional, Set
import os
import logging

from signal_hub.indexing.file_info import FileInfo
from signal_hub.indexing.ignore import IgnoreManager


logger = logging.getLogger(__name__)


@dataclass
class ScanProgress:
    """Progress information for scanning operations."""
    
    total_files: int = 0
    files_scanned: int = 0
    directories_scanned: int = 0
    files_ignored: int = 0
    errors: int = 0
    current_path: Optional[Path] = None
    
    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.files_scanned / self.total_files) * 100


class CodebaseScanner:
    """Scans codebases and identifies files for indexing."""
    
    def __init__(
        self,
        max_file_size: int = 1024 * 1024,  # 1MB
        follow_symlinks: bool = False,
        max_depth: Optional[int] = None,
    ):
        """Initialize the scanner.
        
        Args:
            max_file_size: Maximum file size to process (bytes)
            follow_symlinks: Whether to follow symbolic links
            max_depth: Maximum directory depth to traverse
        """
        self.max_file_size = max_file_size
        self.follow_symlinks = follow_symlinks
        self.max_depth = max_depth
        self._cancelled = False
    
    async def scan(
        self,
        root_path: str | Path,
        ignore_patterns: Optional[List[str]] = None,
    ) -> List[FileInfo]:
        """Scan a codebase and return list of files.
        
        Args:
            root_path: Root directory to scan
            ignore_patterns: Additional ignore patterns
            
        Returns:
            List of FileInfo objects for indexable files
        """
        files = []
        async for file_info in self.scan_async(root_path, ignore_patterns):
            files.append(file_info)
        return files
    
    async def scan_async(
        self,
        root_path: str | Path,
        ignore_patterns: Optional[List[str]] = None,
    ) -> AsyncIterator[FileInfo]:
        """Scan a codebase asynchronously, yielding files as found.
        
        Args:
            root_path: Root directory to scan
            ignore_patterns: Additional ignore patterns
            
        Yields:
            FileInfo objects for indexable files
        """
        root_path = Path(root_path).resolve()
        
        # Verify root path exists
        if not root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")
        if not root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")
        
        # Initialize ignore manager
        ignore_manager = IgnoreManager(root_path)
        if ignore_patterns:
            ignore_manager.add_patterns(ignore_patterns)
        
        # Track visited paths to avoid loops
        visited: Set[Path] = set()
        
        # Scan recursively
        async for file_info in self._scan_directory(
            root_path, root_path, ignore_manager, visited, depth=0
        ):
            yield file_info
    
    async def scan_with_progress(
        self,
        root_path: str | Path,
        ignore_patterns: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None,
    ) -> AsyncIterator[FileInfo]:
        """Scan with progress reporting.
        
        Args:
            root_path: Root directory to scan
            ignore_patterns: Additional ignore patterns
            progress_callback: Optional callback for progress updates
            
        Yields:
            FileInfo objects for indexable files
        """
        root_path = Path(root_path).resolve()
        progress = ScanProgress()
        
        # First, count total files (quick scan)
        logger.info(f"Counting files in {root_path}")
        progress.total_files = await self._count_files(root_path)
        logger.info(f"Found {progress.total_files} total files")
        
        # Now scan with progress
        async for file_info in self.scan_async(root_path, ignore_patterns):
            progress.files_scanned += 1
            progress.current_path = file_info.path
            
            if progress_callback:
                progress_callback(progress)
            
            yield file_info
    
    def cancel(self) -> None:
        """Cancel the current scanning operation."""
        self._cancelled = True
    
    async def _scan_directory(
        self,
        directory: Path,
        root_path: Path,
        ignore_manager: IgnoreManager,
        visited: Set[Path],
        depth: int,
    ) -> AsyncIterator[FileInfo]:
        """Recursively scan a directory.
        
        Args:
            directory: Directory to scan
            root_path: Root path of the scan
            ignore_manager: Ignore pattern manager
            visited: Set of visited paths
            depth: Current depth
            
        Yields:
            FileInfo objects for files in directory
        """
        if self._cancelled:
            return
        
        # Check depth limit
        if self.max_depth is not None and depth > self.max_depth:
            return
        
        # Avoid loops
        try:
            real_path = directory.resolve()
            if real_path in visited:
                logger.warning(f"Skipping already visited path: {directory}")
                return
            visited.add(real_path)
        except OSError as e:
            logger.error(f"Error resolving path {directory}: {e}")
            return
        
        # Get ignored directory names for optimization
        ignored_dirs = ignore_manager.get_ignored_dirs()
        
        # List directory contents
        try:
            entries = list(directory.iterdir())
        except PermissionError:
            logger.warning(f"Permission denied: {directory}")
            return
        except OSError as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return
        
        # Process entries
        for entry in entries:
            if self._cancelled:
                return
            
            # Get relative path for ignore checking
            try:
                relative_path = entry.relative_to(root_path)
            except ValueError:
                relative_path = entry
            
            # Check if should ignore
            if ignore_manager.should_ignore(relative_path):
                continue
            
            try:
                # Handle symbolic links
                if entry.is_symlink() and not self.follow_symlinks:
                    continue
                
                if entry.is_dir():
                    # Skip ignored directories
                    if entry.name in ignored_dirs:
                        continue
                    
                    # Recurse into subdirectory
                    async for file_info in self._scan_directory(
                        entry, root_path, ignore_manager, visited, depth + 1
                    ):
                        yield file_info
                
                elif entry.is_file():
                    # Create file info
                    file_info = FileInfo.from_path(entry)
                    
                    # Skip files that are too large
                    if file_info.size > self.max_file_size:
                        continue
                    
                    # Skip files that shouldn't be indexed
                    if not file_info.should_index():
                        continue
                    
                    # Set relative path
                    file_info.path = entry
                    
                    yield file_info
            
            except OSError as e:
                logger.error(f"Error processing {entry}: {e}")
                continue
        
        # Yield control to allow other tasks
        await asyncio.sleep(0)
    
    async def _count_files(self, root_path: Path) -> int:
        """Quick count of total files in directory tree.
        
        Args:
            root_path: Root directory to count
            
        Returns:
            Total number of files
        """
        count = 0
        
        for root, dirs, files in os.walk(root_path):
            if self._cancelled:
                break
            
            # Remove hidden directories from traversal
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            
            count += len(files)
            
            # Yield control periodically
            if count % 1000 == 0:
                await asyncio.sleep(0)
        
        return count