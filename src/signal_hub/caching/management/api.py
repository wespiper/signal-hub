"""Cache management API."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from signal_hub.caching.semantic_cache import SemanticCache
from signal_hub.caching.management.manager import CacheManager

logger = logging.getLogger(__name__)


class CacheManagementAPI:
    """API for cache management operations."""
    
    def __init__(
        self,
        cache: SemanticCache,
        manager: CacheManager
    ):
        """Initialize management API.
        
        Args:
            cache: Semantic cache instance
            manager: Cache manager instance
        """
        self.cache = cache
        self.manager = manager
        
    async def clear_all(self) -> Dict[str, Any]:
        """Clear entire cache.
        
        Returns:
            Operation result
        """
        try:
            count = await self.cache.clear()
            return {
                "success": True,
                "message": f"Cleared {count} cache entries",
                "entries_cleared": count,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def clear_pattern(self, pattern: str) -> Dict[str, Any]:
        """Clear entries matching pattern.
        
        Args:
            pattern: Pattern to match in queries
            
        Returns:
            Operation result
        """
        try:
            count = await self.manager.evict_pattern(pattern)
            return {
                "success": True,
                "message": f"Cleared {count} entries matching '{pattern}'",
                "entries_cleared": count,
                "pattern": pattern,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error clearing pattern: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics.
        
        Returns:
            Cache statistics
        """
        try:
            cache_stats = await self.cache.get_stats()
            mgmt_stats = await self.manager.get_management_stats()
            
            return {
                "success": True,
                "cache": cache_stats,
                "management": mgmt_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def run_maintenance(self) -> Dict[str, Any]:
        """Manually trigger maintenance.
        
        Returns:
            Operation result
        """
        try:
            await self.manager.run_maintenance()
            return {
                "success": True,
                "message": "Maintenance completed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error running maintenance: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def export_cache(self, format: str = "json") -> Dict[str, Any]:
        """Export cache data.
        
        Args:
            format: Export format (json, csv)
            
        Returns:
            Exported data or error
        """
        try:
            if format != "json":
                return {
                    "success": False,
                    "error": f"Unsupported format: {format}"
                }
                
            # Get all cache entries (simplified)
            entries = []
            if hasattr(self.cache.storage, 'entries'):
                for entry in self.cache.storage.entries.values():
                    entries.append({
                        "id": entry.id,
                        "query": entry.query[:100],  # Truncate for export
                        "model": entry.model,
                        "timestamp": entry.timestamp.isoformat(),
                        "hit_count": entry.hit_count,
                        "expired": entry.is_expired
                    })
                    
            return {
                "success": True,
                "format": format,
                "entries": entries,
                "count": len(entries),
                "exported_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def import_cache(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Import cache data.
        
        Args:
            data: Cache data to import
            
        Returns:
            Operation result
        """
        try:
            if "entries" not in data:
                return {
                    "success": False,
                    "error": "Invalid import data: missing 'entries'"
                }
                
            imported = 0
            failed = 0
            
            for entry_data in data["entries"]:
                try:
                    # Reconstruct and add entry
                    success = await self.cache.put(
                        query=entry_data["query"],
                        response=entry_data.get("response", {"content": "Imported"}),
                        model=entry_data["model"],
                        metadata={"imported": True}
                    )
                    
                    if success:
                        imported += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to import entry: {e}")
                    failed += 1
                    
            return {
                "success": True,
                "message": f"Imported {imported} entries ({failed} failed)",
                "imported": imported,
                "failed": failed,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error importing cache: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def configure(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update cache configuration.
        
        Args:
            updates: Configuration updates
            
        Returns:
            Operation result
        """
        try:
            # Update configuration
            if "similarity_threshold" in updates:
                self.cache.config.similarity_threshold = float(updates["similarity_threshold"])
                
            if "ttl_hours" in updates:
                self.cache.config.ttl_hours = int(updates["ttl_hours"])
                self.cache.config.ttl_seconds = self.cache.config.ttl_hours * 3600
                
            if "max_entries" in updates:
                self.cache.config.max_entries = int(updates["max_entries"])
                
            # Validate new configuration
            self.cache.config.validate()
            
            return {
                "success": True,
                "message": "Configuration updated successfully",
                "config": {
                    "similarity_threshold": self.cache.config.similarity_threshold,
                    "ttl_hours": self.cache.config.ttl_hours,
                    "max_entries": self.cache.config.max_entries
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return {
                "success": False,
                "error": str(e)
            }