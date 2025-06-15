"""Main cost tracking implementation."""

import uuid
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import asyncio

from signal_hub.routing.models import ModelType, ModelSelection
from signal_hub.costs.models import ModelUsage, CostSummary, CostPeriod
from signal_hub.costs.calculator import CostCalculator
from signal_hub.costs.storage.base import CostStorage

logger = logging.getLogger(__name__)


class CostTracker:
    """Track costs for all model API calls."""
    
    def __init__(
        self,
        storage: CostStorage,
        calculator: Optional[CostCalculator] = None
    ):
        """Initialize cost tracker.
        
        Args:
            storage: Storage backend for cost data
            calculator: Cost calculator (or use default)
        """
        self.storage = storage
        self.calculator = calculator or CostCalculator()
        self._initialized = False
        
    async def initialize(self):
        """Initialize tracker and storage."""
        if self._initialized:
            return
            
        await self.storage.initialize()
        self._initialized = True
        logger.info("Cost tracker initialized")
        
    async def track_usage(
        self,
        model: ModelType,
        input_tokens: int,
        output_tokens: int,
        routing_reason: str,
        cache_hit: bool,
        latency_ms: int,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ModelUsage:
        """Track a model API call.
        
        Args:
            model: Model used
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            routing_reason: Why this model was selected
            cache_hit: Whether response was from cache
            latency_ms: Response latency in milliseconds
            tool_name: Optional MCP tool name
            user_id: Optional user identifier
            metadata: Optional additional metadata
            
        Returns:
            Usage record
        """
        # Calculate cost
        cost = 0.0
        if not cache_hit:
            cost = self.calculator.calculate_cost(model, input_tokens, output_tokens)
        
        # Create usage record
        usage = ModelUsage(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            model=model,
            input_tokens=input_tokens if not cache_hit else 0,
            output_tokens=output_tokens if not cache_hit else 0,
            cost=cost,
            routing_reason=routing_reason,
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            tool_name=tool_name,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Store usage
        await self.storage.add_usage(usage)
        
        logger.debug(
            f"Tracked usage: {model.display_name}, "
            f"cost=${cost:.4f}, cache_hit={cache_hit}"
        )
        
        return usage
    
    async def track_from_selection(
        self,
        selection: ModelSelection,
        input_tokens: int,
        output_tokens: int,
        cache_hit: bool,
        latency_ms: int,
        **kwargs
    ) -> ModelUsage:
        """Track usage from a routing selection.
        
        Args:
            selection: Model selection from routing
            input_tokens: Input tokens consumed
            output_tokens: Output tokens generated
            cache_hit: Whether response was from cache
            latency_ms: Response latency
            **kwargs: Additional tracking parameters
            
        Returns:
            Usage record
        """
        routing_reason = "User preference"
        if selection.routing_decision:
            routing_reason = selection.routing_decision.reason
            
        return await self.track_usage(
            model=selection.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            routing_reason=routing_reason,
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            **kwargs
        )
    
    async def get_summary(
        self,
        period: CostPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> CostSummary:
        """Get cost summary for a period.
        
        Args:
            period: Period to summarize
            start_time: Start of period (or auto-calculate)
            end_time: End of period (or use now)
            
        Returns:
            Cost summary
        """
        # Calculate time range
        if not end_time:
            end_time = datetime.utcnow()
            
        if not start_time:
            if period == CostPeriod.HOURLY:
                start_time = end_time - timedelta(hours=1)
            elif period == CostPeriod.DAILY:
                start_time = end_time - timedelta(days=1)
            elif period == CostPeriod.WEEKLY:
                start_time = end_time - timedelta(weeks=1)
            else:  # MONTHLY
                start_time = end_time - timedelta(days=30)
        
        # Get usage records
        usage_records = await self.storage.get_usage_range(start_time, end_time)
        
        # Calculate summary
        total_cost = 0.0
        total_saved = 0.0
        routing_savings = 0.0
        cache_savings = 0.0
        total_requests = len(usage_records)
        cache_hits = 0
        model_distribution = {}
        total_latency = 0.0
        
        for usage in usage_records:
            total_cost += usage.cost
            total_latency += usage.latency_ms
            
            # Track cache hits
            if usage.cache_hit:
                cache_hits += 1
                # Calculate what would have been spent
                baseline_cost = self.calculator.calculate_baseline_cost(
                    usage.input_tokens or 1000,  # Estimate if cached
                    usage.output_tokens or 500
                )
                cache_savings += baseline_cost
            else:
                # Calculate routing savings
                savings_info = self.calculator.calculate_savings(
                    usage.model,
                    usage.input_tokens,
                    usage.output_tokens
                )
                routing_savings += savings_info["savings"]
            
            # Track model distribution
            if usage.model in model_distribution:
                model_distribution[usage.model] += 1
            else:
                model_distribution[usage.model] = 1
        
        total_saved = routing_savings + cache_savings
        avg_latency = total_latency / total_requests if total_requests > 0 else 0
        
        return CostSummary(
            period=period,
            start_time=start_time,
            end_time=end_time,
            total_cost=total_cost,
            total_saved=total_saved,
            routing_savings=routing_savings,
            cache_savings=cache_savings,
            total_requests=total_requests,
            cache_hits=cache_hits,
            model_distribution=model_distribution,
            average_latency_ms=avg_latency
        )
    
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
        return await self.storage.get_recent_usage(limit, user_id)
    
    async def get_cost_by_model(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[ModelType, float]:
        """Get costs broken down by model.
        
        Args:
            start_time: Start of period
            end_time: End of period
            
        Returns:
            Costs per model
        """
        usage_records = await self.storage.get_usage_range(start_time, end_time)
        
        costs = {}
        for usage in usage_records:
            if usage.model in costs:
                costs[usage.model] += usage.cost
            else:
                costs[usage.model] = usage.cost
                
        return costs
    
    async def get_cost_trends(
        self,
        period: CostPeriod,
        num_periods: int = 7
    ) -> List[Dict[str, Any]]:
        """Get cost trends over multiple periods.
        
        Args:
            period: Period granularity
            num_periods: Number of periods to include
            
        Returns:
            List of period summaries
        """
        trends = []
        end_time = datetime.utcnow()
        
        for i in range(num_periods):
            if period == CostPeriod.HOURLY:
                start_time = end_time - timedelta(hours=1)
            elif period == CostPeriod.DAILY:
                start_time = end_time - timedelta(days=1)
            elif period == CostPeriod.WEEKLY:
                start_time = end_time - timedelta(weeks=1)
            else:  # MONTHLY
                start_time = end_time - timedelta(days=30)
            
            summary = await self.get_summary(period, start_time, end_time)
            trends.append(summary.to_dict())
            
            # Move to previous period
            end_time = start_time
            
        return list(reversed(trends))  # Oldest first
    
    async def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """Clean up old usage records.
        
        Args:
            days_to_keep: Number of days of records to keep
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted = await self.storage.cleanup_before(cutoff_date)
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old cost records")
            
        return deleted