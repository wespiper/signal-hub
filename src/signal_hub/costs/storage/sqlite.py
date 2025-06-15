"""SQLite storage for cost tracking."""

import json
import sqlite3
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import asyncio

from signal_hub.routing.models import ModelType
from signal_hub.costs.models import ModelUsage
from signal_hub.costs.storage.base import CostStorage

logger = logging.getLogger(__name__)


class SQLiteCostStorage(CostStorage):
    """SQLite-based cost storage."""
    
    def __init__(self, db_path: str = "~/.signal-hub/costs.db"):
        """Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize database schema."""
        if self._initialized:
            return
            
        async with self._lock:
            # Create tables
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        model TEXT NOT NULL,
                        input_tokens INTEGER NOT NULL,
                        output_tokens INTEGER NOT NULL,
                        cost REAL NOT NULL,
                        routing_reason TEXT NOT NULL,
                        cache_hit INTEGER NOT NULL,
                        latency_ms INTEGER NOT NULL,
                        tool_name TEXT,
                        user_id TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_timestamp 
                    ON usage(timestamp)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_user 
                    ON usage(user_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_model 
                    ON usage(model)
                """)
                
                conn.commit()
                
        self._initialized = True
        logger.info(f"Initialized SQLite cost storage at {self.db_path}")
        
    async def add_usage(self, usage: ModelUsage) -> bool:
        """Add usage record."""
        async with self._lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute("""
                        INSERT INTO usage (
                            id, timestamp, model, input_tokens, output_tokens,
                            cost, routing_reason, cache_hit, latency_ms,
                            tool_name, user_id, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        usage.id,
                        usage.timestamp.isoformat(),
                        usage.model.value,
                        usage.input_tokens,
                        usage.output_tokens,
                        usage.cost,
                        usage.routing_reason,
                        1 if usage.cache_hit else 0,
                        usage.latency_ms,
                        usage.tool_name,
                        usage.user_id,
                        json.dumps(usage.metadata)
                    ))
                    conn.commit()
                    
                return True
                
            except Exception as e:
                logger.error(f"Error adding usage record: {e}")
                return False
                
    async def get_usage_range(
        self,
        start_time: datetime,
        end_time: datetime,
        user_id: Optional[str] = None
    ) -> List[ModelUsage]:
        """Get usage records in time range."""
        async with self._lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT * FROM usage 
                    WHERE timestamp >= ? AND timestamp <= ?
                """
                params = [start_time.isoformat(), end_time.isoformat()]
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                    
                query += " ORDER BY timestamp DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_usage(row) for row in rows]
                
    async def get_recent_usage(
        self,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[ModelUsage]:
        """Get recent usage records."""
        async with self._lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM usage"
                params = []
                
                if user_id:
                    query += " WHERE user_id = ?"
                    params.append(user_id)
                    
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_usage(row) for row in rows]
                
    async def cleanup_before(self, cutoff_date: datetime) -> int:
        """Delete records before cutoff date."""
        async with self._lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "DELETE FROM usage WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
                
                return cursor.rowcount
                
    async def get_total_cost(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> float:
        """Get total cost for period."""
        async with self._lock:
            with sqlite3.connect(str(self.db_path)) as conn:
                query = "SELECT SUM(cost) FROM usage"
                params = []
                
                conditions = []
                if start_time:
                    conditions.append("timestamp >= ?")
                    params.append(start_time.isoformat())
                if end_time:
                    conditions.append("timestamp <= ?")
                    params.append(end_time.isoformat())
                    
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                    
                cursor = conn.execute(query, params)
                result = cursor.fetchone()[0]
                
                return result or 0.0
                
    def _row_to_usage(self, row: sqlite3.Row) -> ModelUsage:
        """Convert database row to ModelUsage."""
        return ModelUsage(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            model=ModelType(row["model"]),
            input_tokens=row["input_tokens"],
            output_tokens=row["output_tokens"],
            cost=row["cost"],
            routing_reason=row["routing_reason"],
            cache_hit=bool(row["cache_hit"]),
            latency_ms=row["latency_ms"],
            tool_name=row["tool_name"],
            user_id=row["user_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )