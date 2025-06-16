#!/usr/bin/env python3
"""Minimal Signal Hub CLI without Rich/Typer issues."""

import sys
import os
from pathlib import Path

HELP_TEXT = """Signal Hub - Intelligent MCP server for RAG-enhanced development

Usage: signal-hub [OPTIONS] COMMAND [ARGS]...

Options:
  --version, -v  Show version and exit
  --help, -h     Show this help message

Commands:
  init      Initialize Signal Hub for a project
  index     Index a codebase for semantic search
  search    Search indexed codebase
  serve     Start the Signal Hub MCP server
  config    Show current configuration
  version   Show detailed version and edition info

Examples:
  signal-hub init                    # Initialize in current directory
  signal-hub init /path/to/project   # Initialize in specific directory
  signal-hub index .                 # Index current directory
  signal-hub search "function name"  # Search for code
  signal-hub serve                   # Start server with defaults
  signal-hub serve --port 4000       # Start server on custom port
"""

def show_help():
    """Show help message."""
    print(HELP_TEXT)
    sys.exit(0)

def show_version():
    """Show version."""
    try:
        from signal_hub import get_version_string
        print(get_version_string())
    except ImportError:
        print("Signal Hub 0.1.0")
    sys.exit(0)

def main():
    """Main CLI entry point."""
    args = sys.argv[1:]
    
    # Handle no arguments
    if not args:
        show_help()
    
    # Handle help flags
    if args[0] in ['--help', '-h', 'help']:
        show_help()
    
    # Handle version flags
    if args[0] in ['--version', '-v']:
        show_version()
    
    # Import Typer only when needed for commands
    try:
        # Set environment to disable Rich
        os.environ["_TYPER_STANDARD_TRACEBACK"] = "1"
        os.environ["_TYPER_COMPLETE_DISABLE_RICH"] = "1"
        
        import typer
        from signal_hub.cli.simple import app
        
        # Let Typer handle the actual commands
        app()
    except Exception as e:
        print(f"Error: {e}")
        print("\nRun 'signal-hub --help' for usage information")
        sys.exit(1)

if __name__ == "__main__":
    main()