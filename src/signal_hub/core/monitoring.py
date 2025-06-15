"""Monitoring endpoints for Signal Hub."""

from typing import Dict, Any, Optional
import json
import time
import platform
import psutil
import sys

from ..utils.logging import get_logger
from ..utils.metrics import get_collector, active_connections

logger = get_logger(__name__)


class MonitoringService:
    """Service for monitoring and health checks."""
    
    def __init__(self):
        self.start_time = time.time()
        self.logger = get_logger(__name__)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime": time.time() - self.start_time,
            "version": "0.1.0",  # TODO: Get from package
        }
    
    async def readiness_check(self) -> Dict[str, Any]:
        """Check if service is ready to handle requests."""
        checks = {
            "server": True,
            "embeddings": await self._check_embeddings(),
            "vector_store": await self._check_vector_store(),
            "cache": await self._check_cache(),
        }
        
        all_ready = all(checks.values())
        
        return {
            "ready": all_ready,
            "checks": checks,
            "timestamp": time.time(),
        }
    
    async def get_metrics(self, format: str = "prometheus") -> str:
        """Get metrics in specified format."""
        collector = get_collector()
        
        if format == "prometheus":
            return collector.format_prometheus()
        elif format == "json":
            metrics = collector.collect_all()
            return json.dumps(
                [
                    {
                        "name": m.name,
                        "labels": m.labels,
                        "value": m.value,
                        "timestamp": m.timestamp,
                    }
                    for m in metrics
                ],
                indent=2
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        try:
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage("/")
            
            # Process info
            process = psutil.Process()
            process_info = {
                "pid": process.pid,
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            }
            
            return {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "python": sys.version,
                },
                "cpu": {
                    "count": cpu_count,
                    "percent": cpu_percent,
                },
                "memory": {
                    "total_mb": memory.total / 1024 / 1024,
                    "available_mb": memory.available / 1024 / 1024,
                    "percent": memory.percent,
                },
                "disk": {
                    "total_gb": disk.total / 1024 / 1024 / 1024,
                    "free_gb": disk.free / 1024 / 1024 / 1024,
                    "percent": disk.percent,
                },
                "process": process_info,
                "connections": {
                    "active": active_connections.get(),
                },
            }
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}
    
    async def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information (only in debug mode)."""
        # TODO: Check if debug mode is enabled
        
        return {
            "config": {
                "edition": "basic",  # TODO: Get from settings
                "debug": True,
                "early_access": True,
            },
            "loaded_plugins": [],  # TODO: Get from plugin manager
            "feature_flags": {},  # TODO: Get from feature flags
            "cache_stats": await self._get_cache_stats(),
            "recent_errors": [],  # TODO: Implement error tracking
        }
    
    async def _check_embeddings(self) -> bool:
        """Check if embeddings service is available."""
        # TODO: Implement actual check
        return True
    
    async def _check_vector_store(self) -> bool:
        """Check if vector store is available."""
        # TODO: Implement actual check
        return True
    
    async def _check_cache(self) -> bool:
        """Check if cache is available."""
        # TODO: Implement actual check
        return True
    
    async def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        # TODO: Implement actual stats
        return {
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
            "size": 0,
        }


# Global monitoring service
_monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service."""
    return _monitoring_service


# MCP Tool definitions for monitoring
MONITORING_TOOLS = [
    {
        "name": "signal_hub_health",
        "description": "Check Signal Hub health status",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "signal_hub_metrics",
        "description": "Get Signal Hub metrics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["prometheus", "json"],
                    "default": "json",
                    "description": "Output format for metrics",
                },
            },
        },
    },
    {
        "name": "signal_hub_system_info",
        "description": "Get Signal Hub system information",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


async def handle_monitoring_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """Handle monitoring tool requests."""
    service = get_monitoring_service()
    
    if tool_name == "signal_hub_health":
        return await service.health_check()
    elif tool_name == "signal_hub_metrics":
        format = arguments.get("format", "json")
        metrics = await service.get_metrics(format)
        if format == "json":
            return json.loads(metrics)
        else:
            return {"metrics": metrics, "format": format}
    elif tool_name == "signal_hub_system_info":
        return await service.get_system_info()
    else:
        raise ValueError(f"Unknown monitoring tool: {tool_name}")