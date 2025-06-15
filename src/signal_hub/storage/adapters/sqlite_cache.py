"""SQLite adapter for CacheStore interface."""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from signal_hub.storage.interfaces import CacheStore

logger = logging.getLogger(__name__)


class SQLiteCacheAdapter(CacheStore):
    """SQLite implementation of CacheStore interface."""
    
    def __init__(self, db_path: str = "./cache.db"):
        """Initialize SQLite cache adapter.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure database is initialized."""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
            """)
            await db.commit()
            
        self._initialized = True
        
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clean up expired entries
            await self._cleanup_expired(db)
            
            cursor = await db.execute(
                "SELECT value FROM cache WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)",
                (key, datetime.utcnow())
            )
            row = await cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return row[0]  # Return as string if not JSON
                    
        return None
        
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        await self._ensure_initialized()
        
        # Calculate expiration time
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
        # Serialize value
        serialized = json.dumps(value) if not isinstance(value, str) else value
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, expires_at)
                VALUES (?, ?, ?)
                """,
                (key, serialized, expires_at)
            )
            await db.commit()
            
        return True
        
    async def delete(self, key: str) -> bool:
        """Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM cache WHERE key = ?",
                (key,)
            )
            await db.commit()
            
            return cursor.rowcount > 0
            
    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM cache WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)",
                (key, datetime.utcnow())
            )
            row = await cursor.fetchone()
            
            return row is not None
            
    async def clear(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if successful
        """
        await self._ensure_initialized()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM cache")
            await db.commit()
            
        return True
        
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs (only existing keys)
        """
        await self._ensure_initialized()
        
        if not keys:
            return {}
            
        results = {}
        placeholders = ",".join("?" * len(keys))
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clean up expired entries
            await self._cleanup_expired(db)
            
            cursor = await db.execute(
                f"""
                SELECT key, value FROM cache 
                WHERE key IN ({placeholders}) 
                AND (expires_at IS NULL OR expires_at > ?)
                """,
                keys + [datetime.utcnow()]
            )
            
            async for row in cursor:
                key, value = row
                try:
                    results[key] = json.loads(value)
                except json.JSONDecodeError:
                    results[key] = value
                    
        return results
        
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache.
        
        Args:
            items: Dictionary of key-value pairs
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        await self._ensure_initialized()
        
        if not items:
            return True
            
        # Calculate expiration time
        expires_at = None
        if ttl:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
        # Prepare values
        values = []
        for key, value in items.items():
            serialized = json.dumps(value) if not isinstance(value, str) else value
            values.append((key, serialized, expires_at))
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """
                INSERT OR REPLACE INTO cache (key, value, expires_at)
                VALUES (?, ?, ?)
                """,
                values
            )
            await db.commit()
            
        return True
        
    async def _cleanup_expired(self, db: aiosqlite.Connection):
        """Clean up expired cache entries.
        
        Args:
            db: Database connection
        """
        await db.execute(
            "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
            (datetime.utcnow(),)
        )
        await db.commit()
        
    async def health_check(self) -> bool:
        """Check if SQLite cache is healthy and accessible.
        
        Returns:
            True if healthy
        """
        try:
            await self._ensure_initialized()
            
            # Try a simple operation
            test_key = "_health_check_"
            await self.set(test_key, "ok", ttl=1)
            result = await self.get(test_key)
            await self.delete(test_key)
            
            return result == "ok"
        except Exception as e:
            logger.error(f"SQLite cache health check failed: {e}")
            return False