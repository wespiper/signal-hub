"""Progress tracking utilities for indexing operations."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
import time


@dataclass
class ProgressTracker:
    """Tracks progress of long-running operations."""
    
    total_items: int = 0
    completed_items: int = 0
    start_time: float = field(default_factory=time.time)
    current_item: Optional[str] = None
    errors: int = 0
    
    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def estimated_time_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds."""
        if self.completed_items == 0:
            return None
        
        rate = self.completed_items / self.elapsed_time
        remaining_items = self.total_items - self.completed_items
        
        if rate == 0:
            return None
        
        return remaining_items / rate
    
    @property
    def items_per_second(self) -> float:
        """Calculate processing rate."""
        if self.elapsed_time == 0:
            return 0.0
        return self.completed_items / self.elapsed_time
    
    def increment(self, current_item: Optional[str] = None) -> None:
        """Increment completed items counter."""
        self.completed_items += 1
        self.current_item = current_item
    
    def add_error(self) -> None:
        """Increment error counter."""
        self.errors += 1
    
    def format_time(self, seconds: Optional[float]) -> str:
        """Format time duration as human-readable string."""
        if seconds is None:
            return "Unknown"
        
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def get_status(self) -> str:
        """Get formatted status string."""
        eta = self.estimated_time_remaining
        eta_str = self.format_time(eta) if eta else "calculating..."
        
        return (
            f"Progress: {self.completed_items}/{self.total_items} "
            f"({self.percentage:.1f}%) | "
            f"Rate: {self.items_per_second:.1f}/s | "
            f"ETA: {eta_str}"
        )


class ProgressReporter:
    """Reports progress at regular intervals."""
    
    def __init__(
        self,
        tracker: ProgressTracker,
        callback: Callable[[ProgressTracker], None],
        interval: float = 1.0,
    ):
        """Initialize the progress reporter.
        
        Args:
            tracker: Progress tracker to monitor
            callback: Function to call with progress updates
            interval: Update interval in seconds
        """
        self.tracker = tracker
        self.callback = callback
        self.interval = interval
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start progress reporting."""
        if self._task is not None:
            return
        
        self._task = asyncio.create_task(self._report_loop())
    
    async def stop(self) -> None:
        """Stop progress reporting."""
        if self._task is None:
            return
        
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
    
    async def _report_loop(self) -> None:
        """Report progress at regular intervals."""
        while True:
            try:
                self.callback(self.tracker)
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                # Final report
                self.callback(self.tracker)
                raise