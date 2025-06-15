"""Signal Hub: Intelligent developer assistant that extends Claude's context through MCP+RAG.

Signal Hub Basic is the open source edition providing core RAG and MCP functionality.
Signal Hub Pro/Enterprise editions add advanced ML-powered routing and analytics.
"""

__version__ = "0.1.0"
__edition__ = "basic"  # basic, pro, or enterprise

from signal_hub.core import (
    Edition,
    Feature,
    get_edition,
    get_feature_flags,
    is_feature_enabled,
)

# Check early access mode
import os
if os.getenv("SIGNAL_HUB_EARLY_ACCESS", "false").lower() == "true":
    __edition__ = "early_access"


def get_version_string() -> str:
    """Get full version string including edition."""
    edition = get_edition().value.title()
    if __edition__ == "early_access":
        return f"Signal Hub {__version__} (Early Access - All Features Enabled)"
    elif edition == "Basic":
        return f"Signal Hub Basic {__version__}"
    else:
        return f"Signal Hub {edition} {__version__}"


__all__ = [
    "__version__",
    "__edition__",
    "get_version_string",
    "Edition",
    "Feature",
    "get_edition",
    "get_feature_flags",
    "is_feature_enabled",
]