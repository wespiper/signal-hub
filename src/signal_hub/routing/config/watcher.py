"""Configuration file watcher for hot reload support."""

import asyncio
from pathlib import Path
from typing import Callable, Optional

from signal_hub.utils.logging import get_logger
from .loader import RoutingConfigLoader


logger = get_logger(__name__)


class ConfigWatcher:
    """Watches configuration file for changes and triggers reload."""
    
    def __init__(
        self,
        loader: RoutingConfigLoader,
        callback: Optional[Callable] = None,
        poll_interval: float = 1.0
    ):
        """
        Initialize configuration watcher.
        
        Args:
            loader: Configuration loader
            callback: Function to call on config change
            poll_interval: How often to check for changes (seconds)
        """
        self.loader = loader
        self.callback = callback
        self.poll_interval = poll_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_mtime: Optional[float] = None
    
    async def start(self) -> None:
        """Start watching for configuration changes."""
        if self._running:
            logger.warning("ConfigWatcher already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._watch_loop())
        logger.info(f"Started watching {self.loader.config_path}")
    
    async def stop(self) -> None:
        """Stop watching for changes."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped configuration watcher")
    
    async def _watch_loop(self) -> None:
        """Main watch loop."""
        while self._running:
            try:
                await self._check_for_changes()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in config watcher: {e}")
                await asyncio.sleep(self.poll_interval * 5)  # Back off on error
    
    async def _check_for_changes(self) -> None:
        """Check if configuration file has changed."""
        if not self.loader.config_path.exists():
            return
        
        current_mtime = self.loader.config_path.stat().st_mtime
        
        # First run - just record the mtime
        if self._last_mtime is None:
            self._last_mtime = current_mtime
            return
        
        # Check if file has changed
        if current_mtime != self._last_mtime:
            logger.info("Configuration file changed, reloading...")
            self._last_mtime = current_mtime
            
            try:
                # Reload configuration
                new_config = self.loader.reload()
                
                # Call callback if provided
                if self.callback:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(new_config)
                    else:
                        self.callback(new_config)
                
                logger.info("Configuration reloaded successfully")
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running