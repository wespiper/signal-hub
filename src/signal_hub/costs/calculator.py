"""Cost calculation utilities."""

import logging
from typing import Dict, Optional
from datetime import datetime

from signal_hub.routing.models import ModelType
from signal_hub.costs.models import ModelPricing, DEFAULT_PRICING

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculate costs for model usage."""
    
    def __init__(self, pricing: Optional[Dict[ModelType, ModelPricing]] = None):
        """Initialize cost calculator.
        
        Args:
            pricing: Custom pricing or use defaults
        """
        self.pricing = pricing or DEFAULT_PRICING
        
    def calculate_cost(
        self,
        model: ModelType,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for a model call.
        
        Args:
            model: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in USD
        """
        if model not in self.pricing:
            logger.warning(f"No pricing for model {model}, using Opus pricing")
            model = ModelType.OPUS
            
        pricing = self.pricing[model]
        return pricing.calculate_cost(input_tokens, output_tokens)
    
    def calculate_baseline_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        baseline_model: ModelType = ModelType.OPUS
    ) -> float:
        """Calculate baseline cost (if always using most expensive model).
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            baseline_model: Model to use as baseline
            
        Returns:
            Baseline cost in USD
        """
        return self.calculate_cost(baseline_model, input_tokens, output_tokens)
    
    def calculate_savings(
        self,
        actual_model: ModelType,
        input_tokens: int,
        output_tokens: int,
        baseline_model: ModelType = ModelType.OPUS
    ) -> Dict[str, float]:
        """Calculate cost savings from routing.
        
        Args:
            actual_model: Model actually used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            baseline_model: Model to compare against
            
        Returns:
            Dictionary with cost and savings information
        """
        actual_cost = self.calculate_cost(actual_model, input_tokens, output_tokens)
        baseline_cost = self.calculate_baseline_cost(
            input_tokens, output_tokens, baseline_model
        )
        
        savings = baseline_cost - actual_cost
        savings_percentage = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
        
        return {
            "actual_cost": actual_cost,
            "baseline_cost": baseline_cost,
            "savings": savings,
            "savings_percentage": savings_percentage,
            "model_used": actual_model.value,
            "baseline_model": baseline_model.value
        }
    
    def estimate_monthly_cost(
        self,
        daily_requests: int,
        model_distribution: Dict[ModelType, float],
        avg_input_tokens: int = 1000,
        avg_output_tokens: int = 500,
        cache_hit_rate: float = 0.0
    ) -> Dict[str, float]:
        """Estimate monthly costs based on usage patterns.
        
        Args:
            daily_requests: Average requests per day
            model_distribution: Percentage distribution across models
            avg_input_tokens: Average input tokens per request
            avg_output_tokens: Average output tokens per request
            cache_hit_rate: Percentage of cache hits (0-100)
            
        Returns:
            Monthly cost estimates
        """
        # Adjust for cache hits
        effective_requests = daily_requests * (1 - cache_hit_rate / 100)
        monthly_requests = effective_requests * 30
        
        # Calculate cost per model
        total_cost = 0.0
        model_costs = {}
        
        for model, percentage in model_distribution.items():
            requests_for_model = monthly_requests * (percentage / 100)
            cost = self.calculate_cost(
                model,
                int(avg_input_tokens * requests_for_model),
                int(avg_output_tokens * requests_for_model)
            )
            model_costs[model.value] = cost
            total_cost += cost
        
        # Calculate baseline (all Opus)
        baseline_cost = self.calculate_cost(
            ModelType.OPUS,
            int(avg_input_tokens * monthly_requests),
            int(avg_output_tokens * monthly_requests)
        )
        
        # Calculate savings
        total_savings = baseline_cost - total_cost
        cache_savings = self.calculate_cost(
            ModelType.OPUS,
            int(avg_input_tokens * daily_requests * 30 * (cache_hit_rate / 100)),
            int(avg_output_tokens * daily_requests * 30 * (cache_hit_rate / 100))
        )
        routing_savings = total_savings - cache_savings
        
        return {
            "estimated_monthly_cost": total_cost,
            "baseline_monthly_cost": baseline_cost,
            "total_monthly_savings": total_savings,
            "routing_monthly_savings": routing_savings,
            "cache_monthly_savings": cache_savings,
            "savings_percentage": (total_savings / baseline_cost * 100) if baseline_cost > 0 else 0,
            "model_costs": model_costs,
            "assumptions": {
                "daily_requests": daily_requests,
                "monthly_requests": monthly_requests,
                "cache_hit_rate": cache_hit_rate,
                "avg_input_tokens": avg_input_tokens,
                "avg_output_tokens": avg_output_tokens
            }
        }
    
    def get_pricing_info(self) -> Dict[str, Dict[str, float]]:
        """Get current pricing information.
        
        Returns:
            Pricing for all models
        """
        return {
            model.value: {
                "input_per_1m": pricing.input_cost_per_1m,
                "output_per_1m": pricing.output_cost_per_1m,
                "relative_cost": model.relative_cost
            }
            for model, pricing in self.pricing.items()
        }