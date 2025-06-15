"""Main routing engine implementation."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from signal_hub.routing.models import (
    Query, ModelType, RoutingDecision, ModelSelection, RoutingMetrics
)
from signal_hub.routing.rules.base import RoutingRule
from signal_hub.routing.rules.length import LengthBasedRule
from signal_hub.routing.rules.complexity import ComplexityBasedRule
from signal_hub.routing.rules.task_type import TaskTypeRule
from signal_hub.routing.providers.base import ModelProvider
from signal_hub.routing.escalation.escalator import EscalationManager

logger = logging.getLogger(__name__)


class RoutingEngine:
    """Main routing engine that selects appropriate models for queries."""
    
    def __init__(
        self,
        provider: ModelProvider,
        rules: Optional[List[RoutingRule]] = None,
        default_model: ModelType = ModelType.OPUS,
        metrics: Optional[RoutingMetrics] = None,
        escalation_manager: Optional[EscalationManager] = None
    ):
        """Initialize routing engine.
        
        Args:
            provider: Model provider to use
            rules: List of routing rules (or use defaults)
            default_model: Default model when no rules match
            metrics: Metrics collector
            escalation_manager: Escalation manager (or create default)
        """
        self.provider = provider
        self.rules = rules or self._create_default_rules()
        self.default_model = default_model
        self.metrics = metrics or RoutingMetrics()
        self.escalation_manager = escalation_manager or EscalationManager()
        
        # Sort rules by priority
        self.rules.sort()
        
        logger.info(f"Initialized routing engine with {len(self.rules)} rules")
        
    def _create_default_rules(self) -> List[RoutingRule]:
        """Create default routing rules."""
        return [
            # Task type has highest priority
            TaskTypeRule(priority=30),
            # Then complexity
            ComplexityBasedRule(priority=20),
            # Then length
            LengthBasedRule(priority=10),
        ]
        
    def route(self, query: Query, session_id: Optional[str] = None) -> ModelSelection:
        """Route query to appropriate model.
        
        Args:
            query: Query to route
            session_id: Optional session identifier
            
        Returns:
            Model selection with reasoning
        """
        start_time = datetime.utcnow()
        
        # Check for escalation (includes preferred_model check)
        escalation = self.escalation_manager.check_escalation(query, session_id)
        if escalation:
            logger.info(f"Escalation: {escalation.model.display_name} from {escalation.source}")
            selection = ModelSelection(
                model=escalation.model,
                overridden=True,
                override_reason=escalation.reason or f"Escalation: {escalation.source}"
            )
            self.metrics.record_decision(selection)
            return selection
            
        # Apply routing rules
        routing_decision = self._apply_rules(query)
        
        if routing_decision:
            model = routing_decision.model
        else:
            # No rules matched, use default
            model = self.default_model
            routing_decision = RoutingDecision(
                model=model,
                reason="No routing rules matched, using default",
                confidence=0.5,
                rules_applied=[]
            )
            
        # Check model availability
        if not self.provider.is_available(model):
            logger.warning(f"Model {model} not available, falling back to default")
            model = self.default_model
            routing_decision.reason += f" (original model {routing_decision.model} unavailable)"
            routing_decision.model = model
            routing_decision.confidence *= 0.8
            
        # Create selection
        selection = ModelSelection(
            model=model,
            routing_decision=routing_decision
        )
        
        # Record metrics
        self.metrics.record_decision(selection)
        
        # Log routing decision
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(
            f"Routed query to {model.display_name} in {duration_ms:.1f}ms "
            f"(confidence: {routing_decision.confidence:.2f})"
        )
        
        return selection
        
    def _apply_rules(self, query: Query) -> Optional[RoutingDecision]:
        """Apply routing rules to query.
        
        Args:
            query: Query to evaluate
            
        Returns:
            Best routing decision or None
        """
        best_decision = None
        best_confidence = 0.0
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                decision = rule.evaluate(query)
                
                if decision and decision.confidence > best_confidence:
                    best_decision = decision
                    best_confidence = decision.confidence
                    
                    # If we have very high confidence, stop evaluating
                    if best_confidence >= 0.95:
                        break
                        
            except Exception as e:
                logger.error(f"Error in rule {rule.name}: {e}")
                continue
                
        return best_decision
        
    def add_rule(self, rule: RoutingRule):
        """Add a routing rule."""
        self.rules.append(rule)
        self.rules.sort()
        logger.info(f"Added routing rule: {rule.name}")
        
    def remove_rule(self, rule_name: str):
        """Remove a routing rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"Removed routing rule: {rule_name}")
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics."""
        return {
            "total_queries": self.metrics.total_queries,
            "model_distribution": self.metrics.get_distribution_percentages(),
            "override_rate": (self.metrics.override_count / max(1, self.metrics.total_queries)) * 100,
            "average_confidence": self.metrics.average_confidence,
            "rule_effectiveness": self.metrics.rule_hit_counts
        }
        
    def estimate_cost_savings(self) -> Dict[str, float]:
        """Estimate cost savings from routing.
        
        Returns:
            Dictionary with savings information
        """
        if self.metrics.total_queries == 0:
            return {"total_savings": 0.0, "savings_percentage": 0.0}
            
        # Calculate actual cost
        actual_cost = 0.0
        for model, count in self.metrics.model_distribution.items():
            # Assume average query size for estimation
            avg_input_tokens = 1000
            avg_output_tokens = 500
            
            if hasattr(self.provider, 'calculate_cost'):
                cost = self.provider.calculate_cost(model, avg_input_tokens, avg_output_tokens)
                actual_cost += cost * count
                
        # Calculate baseline (all Opus)
        baseline_cost = 0.0
        if hasattr(self.provider, 'calculate_cost'):
            opus_cost = self.provider.calculate_cost(
                ModelType.OPUS,
                avg_input_tokens,
                avg_output_tokens
            )
            baseline_cost = opus_cost * self.metrics.total_queries
            
        # Calculate savings
        total_savings = baseline_cost - actual_cost
        savings_percentage = (total_savings / baseline_cost * 100) if baseline_cost > 0 else 0
        
        return {
            "total_savings": total_savings,
            "savings_percentage": savings_percentage,
            "actual_cost": actual_cost,
            "baseline_cost": baseline_cost
        }