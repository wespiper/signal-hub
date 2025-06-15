"""Default routing configuration."""

from typing import Dict

from signal_hub.routing.models import ModelType
from .schema import (
    RoutingConfig,
    ModelConfig,
    RoutingRule,
    RuleOverride,
    ComplexityLevel,
    RuleThresholds,
    ComplexityIndicators,
    TaskMappings,
)


DEFAULT_CONFIG = RoutingConfig(
    models={
        ModelType.HAIKU: ModelConfig(
            max_tokens=1000,
            max_complexity=ComplexityLevel.SIMPLE,
            preferred_tasks=[
                "search", "simple_query", "list", "count",
                "find", "check", "verify", "lookup"
            ]
        ),
        ModelType.SONNET: ModelConfig(
            max_tokens=4000,
            max_complexity=ComplexityLevel.MODERATE,
            preferred_tasks=[
                "explain", "analyze", "summarize", "describe",
                "compare", "review", "suggest", "improve"
            ]
        ),
        ModelType.OPUS: ModelConfig(
            max_tokens=None,  # No limit
            max_complexity=ComplexityLevel.COMPLEX,
            preferred_tasks=[
                "debug", "architect", "refactor", "design",
                "optimize", "implement", "solve", "create"
            ]
        ),
    },
    rules=[
        # Length-based routing (highest priority)
        RoutingRule(
            name="length_based",
            enabled=True,
            priority=1,
            thresholds=RuleThresholds(
                haiku=500,
                sonnet=2000,
                # Opus: anything above sonnet threshold
            )
        ),
        
        # Complexity-based routing
        RoutingRule(
            name="complexity_based",
            enabled=True,
            priority=2,
            indicators=ComplexityIndicators(
                simple=[
                    "what", "when", "where", "who", "which",
                    "list", "show", "find", "get", "count",
                    "is", "are", "does", "check", "verify"
                ],
                moderate=[
                    "how", "why", "explain", "describe", "summarize",
                    "compare", "difference", "similar", "relate",
                    "understand", "clarify", "elaborate"
                ],
                complex=[
                    "analyze", "design", "architect", "optimize",
                    "refactor", "implement", "solve", "debug",
                    "performance", "scale", "distribute", "secure"
                ]
            )
        ),
        
        # Task type routing
        RoutingRule(
            name="task_type",
            enabled=True,
            priority=3,
            mappings=TaskMappings(
                search_code=ModelType.HAIKU,
                explain_code=ModelType.SONNET,
                find_similar=ModelType.HAIKU,
                get_context=ModelType.SONNET,
                analyze_architecture=ModelType.OPUS,
            )
        ),
    ],
    overrides=[
        # Security-related queries always use Opus
        RuleOverride(
            pattern=r"(?i)(security|vulnerability|exploit|injection|auth|cve)",
            model=ModelType.OPUS,
            reason="Security analysis requires maximum care and capability"
        ),
        
        # Performance optimization
        RuleOverride(
            pattern=r"(?i)(performance|optimize|bottleneck|profil|benchmark)",
            model=ModelType.OPUS,
            reason="Performance optimization needs deep technical analysis"
        ),
        
        # Architecture and design
        RuleOverride(
            pattern=r"(?i)(architect|design\s+pattern|scalab|distribut)",
            model=ModelType.OPUS,
            reason="System design requires comprehensive understanding"
        ),
        
        # Critical debugging
        RuleOverride(
            pattern=r"(?i)(debug|troubleshoot|root\s+cause|critical\s+bug)",
            model=ModelType.OPUS,
            reason="Complex debugging needs advanced reasoning"
        ),
    ],
    default_model=ModelType.HAIKU,
    cache_similarity_threshold=0.85,
    enable_escalation=True,
)


def get_default_config() -> RoutingConfig:
    """Get a copy of the default configuration."""
    return DEFAULT_CONFIG.copy(deep=True)