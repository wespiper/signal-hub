"""Signal Hub CLI module."""

# Use the simple CLI to avoid Rich/Typer compatibility issues
from signal_hub.cli.simple import app

__all__ = ["app"]