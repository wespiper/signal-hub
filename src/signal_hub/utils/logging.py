"""Logging configuration for Signal Hub."""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback


# Install rich traceback handler for better error display
install_rich_traceback(show_locals=True)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
    rich_console: bool = True,
) -> None:
    """
    Configure logging for Signal Hub.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
        json_format: Whether to use JSON format for logs
        rich_console: Whether to use rich console handler
    """
    # Convert string level to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatters
    if json_format:
        import json
        
        class JsonFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
                
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'created', 'filename',
                                  'funcName', 'levelname', 'levelno', 'lineno',
                                  'module', 'msecs', 'message', 'pathname', 'process',
                                  'processName', 'relativeCreated', 'thread',
                                  'threadName', 'exc_info', 'exc_text', 'stack_info']:
                        log_data[key] = value
                
                return json.dumps(log_data)
        
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    if rich_console:
        console = Console(stderr=True)
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
            log_time_format="[%Y-%m-%d %H:%M:%S]"
        )
        rich_handler.setLevel(log_level)
        root_logger.addHandler(rich_handler)
    else:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Set specific loggers
    logging.getLogger("signal_hub").setLevel(log_level)
    
    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for adding context to log messages."""
    
    def __init__(self, logger: logging.Logger, **context: Any):
        self.logger = logger
        self.context = context
        self._original_extras: Dict[str, Any] = {}
    
    def __enter__(self):
        # Store original extras
        for key in self.context:
            if hasattr(self.logger, key):
                self._original_extras[key] = getattr(self.logger, key)
        
        # Add context as logger attributes
        for key, value in self.context.items():
            setattr(self.logger, key, value)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original extras
        for key in self.context:
            if key in self._original_extras:
                setattr(self.logger, key, self._original_extras[key])
            else:
                delattr(self.logger, key)


def log_performance(logger: logging.Logger, operation: str):
    """
    Decorator to log operation performance.
    
    Args:
        logger: Logger instance
        operation: Name of the operation being measured
    """
    import functools
    import time
    
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.debug(
                    f"{operation} completed",
                    extra={"duration_ms": elapsed, "status": "success"}
                )
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    extra={"duration_ms": elapsed, "status": "error", "error": str(e)}
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.debug(
                    f"{operation} completed",
                    extra={"duration_ms": elapsed, "status": "success"}
                )
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"{operation} failed",
                    extra={"duration_ms": elapsed, "status": "error", "error": str(e)}
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator