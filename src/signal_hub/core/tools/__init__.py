"""MCP tools for Signal Hub."""

from signal_hub.core.tools.base import Tool, ToolRegistry

__all__ = [
    "Tool",
    "ToolRegistry"
]

# Import tool implementations conditionally to avoid circular imports
try:
    from signal_hub.core.tools.search_code import SearchCodeTool
    from signal_hub.core.tools.explain_code import ExplainCodeTool
    from signal_hub.core.tools.find_similar import FindSimilarTool
    from signal_hub.core.tools.get_context import GetContextTool
    
    __all__.extend([
        "SearchCodeTool",
        "ExplainCodeTool",
        "FindSimilarTool",
        "GetContextTool"
    ])
except ImportError:
    # Tools not available yet, likely during initial setup
    pass