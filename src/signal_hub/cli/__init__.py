"""Signal Hub CLI module."""

import sys
import os

# Detect if we need help handling
if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
    # Use minimal CLI for help to avoid Rich issues
    from signal_hub.cli.minimal import main
    main()
else:
    # Use the simple CLI for actual commands
    from signal_hub.cli.simple import app

__all__ = ["app"]