"""Base interface for cost storage."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from signal_hub.costs.models import ModelUsage


class CostStorage(ABC):
    """Abstract base class for cost data storage."""
    
    @abstractmethod
    async def initialize(self):
        """Initialize storage backend."""
        pass
    
    @abstractmethod
    async def add_usage(self, usage: ModelUsage) -> bool:
        """Add usage record.
        
        Args:
            usage: Usage record to store
            
        Returns:
            True if stored successfully
        """
        pass
    
    @abstractmethod
    async def get_usage_range(
        self,
        start_time: datetime,
        end_time: datetime,
        user_id: Optional[str] = None
    ) -> List[ModelUsage]:
        """Get usage records in time range.
        
        Args:
            start_time: Start of range
            end_time: End of range
            user_id: Optional filter by user
            
        Returns:
            List of usage records
        """
        pass
    
    @abstractmethod
    async def get_recent_usage(
        self,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[ModelUsage]:
        """Get recent usage records.
        
        Args:
            limit: Maximum records to return
            user_id: Optional filter by user
            
        Returns:
            Recent usage records
        """
        pass
    
    @abstractmethod
    async def cleanup_before(self, cutoff_date: datetime) -> int:
        """Delete records before cutoff date.
        
        Args:
            cutoff_date: Delete records before this date
            
        Returns:
            Number of records deleted
        """
        pass
    
    @abstractmethod
    async def get_total_cost(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> float:
        """Get total cost for period.
        
        Args:
            start_time: Start of period (or all time)
            end_time: End of period (or now)
            
        Returns:
            Total cost
        """
        pass