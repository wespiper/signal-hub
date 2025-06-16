#!/usr/bin/env python3
"""Debug version of index command to find slowdown."""

import time
import sys
from pathlib import Path

# Add signal-hub to path
sys.path.insert(0, 'src')

def debug_index():
    """Run indexing with detailed debugging."""
    
    print("Starting debug indexing...\n")
    
    # Check which indexing is being used
    print("1. Checking which indexing method is active:")
    try:
        with open("src/signal_hub/cli/simple.py", "r") as f:
            content = f.read()
            if "minimal_index" in content and "# For large codebases, use minimal" in content:
                print("   ✓ Using minimal_index (JSON-based, no embeddings)")
                from signal_hub.cli.indexing_minimal import minimal_index
                
                # Run it with debug
                project_path = Path(".")
                signal_hub_dir = project_path / ".signal-hub"
                
                if not signal_hub_dir.exists():
                    print("\nCreating .signal-hub directory...")
                    signal_hub_dir.mkdir()
                    (signal_hub_dir / "db").mkdir()
                
                print("\nRunning minimal_index...")
                minimal_index(project_path, signal_hub_dir)
                
            elif "fast_index" in content:
                print("   ! Using fast_index (still uses ChromaDB)")
                print("   This might be the issue!")
            else:
                print("   ? Unknown indexing method")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run from signal-hub directory
    if not Path("src/signal_hub").exists():
        print("Error: Run this from the signal-hub directory")
        sys.exit(1)
        
    debug_index()