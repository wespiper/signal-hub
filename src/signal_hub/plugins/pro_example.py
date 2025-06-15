"""Example pro plugins for Signal Hub.

This module demonstrates how pro features would be implemented as plugins.
During early access, these are available to all users for testing and feedback.
"""

from typing import Any, Dict, List, Optional
import logging
import random
from datetime import datetime, timedelta

from signal_hub.core.plugins import Plugin, ModelRouter, AnalyticsProvider
from signal_hub.core.features import Feature, requires_feature

logger = logging.getLogger(__name__)


class MLModelRouter(Plugin, ModelRouter):
    """Machine learning-powered model router for Signal Hub Pro.
    
    This is a simplified example. The real implementation would use
    actual ML models trained on usage patterns and feedback.
    """
    
    name = "ml_router"
    version = "1.0.0"
    description = "ML-powered intelligent model routing"
    requires_pro = True
    
    def __init__(self):
        self.feedback_history: List[Dict[str, Any]] = []
        self.routing_model = None  # Would load actual ML model
    
    @requires_feature(Feature.ML_ROUTING)
    def route_query(self, query: str, context: Dict[str, Any]) -> str:
        """Route query using ML model based on complexity analysis."""
        # Extract features for ML model
        features = self._extract_features(query, context)
        
        # Predict complexity score (simplified for example)
        complexity_score = self._predict_complexity(features)
        
        # Add learning from feedback
        if self.feedback_history:
            complexity_score = self._adjust_from_feedback(query, complexity_score)
        
        # Select model based on score
        if complexity_score < 0.3:
            model = "claude-3-haiku-20240307"
        elif complexity_score < 0.7:
            model = "claude-3-sonnet-20240229"
        else:
            model = "claude-3-opus-20240229"
        
        logger.info(f"ML Router selected {model} (complexity: {complexity_score:.2f})")
        return model
    
    def record_feedback(self, query_id: str, feedback: Dict[str, Any]) -> None:
        """Record user feedback to improve routing."""
        self.feedback_history.append({
            "query_id": query_id,
            "feedback": feedback,
            "timestamp": datetime.now()
        })
        
        # In production, would retrain model periodically
        if len(self.feedback_history) % 100 == 0:
            logger.info("Would trigger model retraining with feedback")
    
    def _extract_features(self, query: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for ML model."""
        return {
            "query_length": len(query.split()),
            "query_complexity": len(set(query.split())) / len(query.split()),
            "context_size": len(str(context.get("retrieved_chunks", ""))),
            "code_files": len(context.get("files", [])),
            "has_error_keywords": any(word in query.lower() for word in ["error", "bug", "fix"]),
            "requires_analysis": any(word in query.lower() for word in ["analyze", "explain", "why"]),
            "requires_generation": any(word in query.lower() for word in ["create", "generate", "write"]),
        }
    
    def _predict_complexity(self, features: Dict[str, float]) -> float:
        """Predict complexity score using ML model (simplified)."""
        # Simplified scoring - real implementation would use trained model
        score = 0.0
        
        # Length-based scoring
        score += min(features["query_length"] / 100, 0.3)
        
        # Complexity indicators
        if features["has_error_keywords"]:
            score += 0.2
        if features["requires_analysis"]:
            score += 0.3
        if features["requires_generation"]:
            score += 0.2
        
        # Context size
        score += min(features["context_size"] / 10000, 0.3)
        
        return min(score, 1.0)
    
    def _adjust_from_feedback(self, query: str, base_score: float) -> float:
        """Adjust score based on historical feedback."""
        # Look for similar queries in feedback
        recent_feedback = [
            f for f in self.feedback_history
            if f["timestamp"] > datetime.now() - timedelta(days=7)
        ]
        
        if recent_feedback:
            # Simplified adjustment - real implementation would be more sophisticated
            positive_feedback = sum(1 for f in recent_feedback if f["feedback"].get("helpful", False))
            total_feedback = len(recent_feedback)
            
            if total_feedback > 0:
                adjustment = (positive_feedback / total_feedback - 0.5) * 0.1
                return max(0, min(1, base_score + adjustment))
        
        return base_score


class AdvancedAnalytics(Plugin, AnalyticsProvider):
    """Advanced analytics provider for Signal Hub Pro."""
    
    name = "advanced_analytics"
    version = "1.0.0"
    description = "Detailed analytics and cost optimization insights"
    requires_pro = True
    
    def __init__(self):
        self.query_history: List[Dict[str, Any]] = []
        self.model_costs = {
            "claude-3-haiku-20240307": 0.00025,  # per 1K tokens
            "claude-3-sonnet-20240229": 0.003,    # per 1K tokens
            "claude-3-opus-20240229": 0.015,      # per 1K tokens
        }
    
    @requires_feature(Feature.ADVANCED_ANALYTICS)
    def track_query(self, query: str, model: str, cost: float) -> None:
        """Track detailed query information."""
        self.query_history.append({
            "timestamp": datetime.now(),
            "query": query,
            "model": model,
            "actual_cost": cost,
            "opus_cost": self._calculate_opus_cost(query),
            "tokens": self._estimate_tokens(query),
            "response_time": random.uniform(0.5, 5.0),  # Simulated
        })
    
    @requires_feature(Feature.ADVANCED_ANALYTICS)
    def get_cost_savings(self, time_range: str = "7d") -> Dict[str, Any]:
        """Get detailed cost savings analytics."""
        # Filter by time range
        cutoff = self._parse_time_range(time_range)
        relevant_queries = [
            q for q in self.query_history
            if q["timestamp"] > cutoff
        ]
        
        if not relevant_queries:
            return self._empty_analytics()
        
        # Calculate metrics
        total_queries = len(relevant_queries)
        total_cost = sum(q["actual_cost"] for q in relevant_queries)
        opus_cost = sum(q["opus_cost"] for q in relevant_queries)
        savings = opus_cost - total_cost
        
        # Model distribution
        model_usage = {}
        for q in relevant_queries:
            model = q["model"].split("-")[2]  # Extract model name
            model_usage[model] = model_usage.get(model, 0) + 1
        
        # Average response time
        avg_response_time = sum(q["response_time"] for q in relevant_queries) / total_queries
        
        # Hourly distribution
        hourly_distribution = {}
        for q in relevant_queries:
            hour = q["timestamp"].hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
        
        return {
            "summary": {
                "total_queries": total_queries,
                "total_cost": f"${total_cost:.2f}",
                "potential_cost": f"${opus_cost:.2f}",
                "total_savings": f"${savings:.2f}",
                "savings_percentage": f"{(savings / opus_cost * 100):.1f}%",
                "avg_response_time": f"{avg_response_time:.2f}s",
            },
            "model_distribution": model_usage,
            "hourly_pattern": hourly_distribution,
            "cost_trend": self._calculate_trend(relevant_queries),
            "recommendations": self._generate_recommendations(relevant_queries),
        }
    
    def _calculate_opus_cost(self, query: str) -> float:
        """Calculate cost if Opus was used."""
        tokens = self._estimate_tokens(query)
        return (tokens / 1000) * self.model_costs["claude-3-opus-20240229"]
    
    def _estimate_tokens(self, query: str) -> int:
        """Estimate token count (simplified)."""
        # Rough estimation: 1 token ≈ 4 characters
        return len(query) // 4 + 500  # Add base for response
    
    def _parse_time_range(self, time_range: str) -> datetime:
        """Parse time range string to datetime."""
        if time_range.endswith("d"):
            days = int(time_range[:-1])
            return datetime.now() - timedelta(days=days)
        elif time_range.endswith("h"):
            hours = int(time_range[:-1])
            return datetime.now() - timedelta(hours=hours)
        else:
            # Default to all time
            return datetime.min
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            "summary": {
                "total_queries": 0,
                "total_cost": "$0.00",
                "potential_cost": "$0.00",
                "total_savings": "$0.00",
                "savings_percentage": "0.0%",
                "avg_response_time": "0.0s",
            },
            "model_distribution": {},
            "hourly_pattern": {},
            "cost_trend": [],
            "recommendations": [],
        }
    
    def _calculate_trend(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate cost trend over time."""
        if not queries:
            return []
        
        # Group by day
        daily_costs = {}
        daily_savings = {}
        
        for q in queries:
            day = q["timestamp"].date()
            daily_costs[day] = daily_costs.get(day, 0) + q["actual_cost"]
            daily_savings[day] = daily_savings.get(day, 0) + (q["opus_cost"] - q["actual_cost"])
        
        # Convert to list
        trend = []
        for day in sorted(daily_costs.keys()):
            trend.append({
                "date": day.isoformat(),
                "cost": round(daily_costs[day], 2),
                "savings": round(daily_savings[day], 2),
            })
        
        return trend
    
    def _generate_recommendations(self, queries: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if not queries:
            return ["Start using Signal Hub to see optimization recommendations"]
        
        # Check model distribution
        haiku_usage = sum(1 for q in queries if "haiku" in q["model"])
        total = len(queries)
        
        if haiku_usage / total < 0.3:
            recommendations.append(
                "Consider enabling more aggressive routing to Haiku for simple queries"
            )
        
        # Check response times
        slow_queries = sum(1 for q in queries if q["response_time"] > 3.0)
        if slow_queries / total > 0.2:
            recommendations.append(
                "Enable predictive caching to improve response times"
            )
        
        # Check time patterns
        # (Simplified - would analyze actual patterns)
        recommendations.append(
            "Peak usage detected during business hours - consider pre-warming cache"
        )
        
        return recommendations


# Example of how to register pro plugins

def register_pro_plugins(plugin_manager):
    """Register pro plugins if available."""
    try:
        # Register ML router
        ml_router = MLModelRouter()
        plugin_manager.register(ml_router)
        
        # Register advanced analytics
        analytics = AdvancedAnalytics()
        plugin_manager.register(analytics)
        
        logger.info("Pro plugins registered successfully")
    except Exception as e:
        logger.warning(f"Could not register pro plugins: {e}")