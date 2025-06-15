"""Signal Hub CLI entry point."""

import sys
from signal_hub.cli import app

if __name__ == "__main__":
    sys.exit(app())