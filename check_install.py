#!/usr/bin/env python3
"""Check what's installed in signal-hub."""

import os
import sys

print("Checking Signal Hub installation...\n")

# 1. Check if modules exist
print("1. Checking modules:")
try:
    import signal_hub.cli.indexing_minimal
    print("   ✓ indexing_minimal exists")
except ImportError:
    print("   ✗ indexing_minimal MISSING - THIS IS THE ISSUE!")

try:
    import signal_hub.cli.indexing_fast
    print("   ✓ indexing_fast exists")
except ImportError:
    print("   ✗ indexing_fast missing")

try:
    import signal_hub.cli.indexing_optimized
    print("   ✓ indexing_optimized exists")
except ImportError:
    print("   ✗ indexing_optimized missing")

# 2. Check what's in the CLI directory
print("\n2. Files in CLI directory:")
try:
    import signal_hub.cli
    cli_dir = os.path.dirname(signal_hub.cli.__file__)
    files = os.listdir(cli_dir)
    for f in sorted(files):
        print(f"   - {f}")
except Exception as e:
    print(f"   Error: {e}")

# 3. Check what indexing method is being used
print("\n3. Checking indexing method in simple.py:")
try:
    import signal_hub.cli.simple
    with open(signal_hub.cli.simple.__file__, 'r') as f:
        content = f.read()
        if 'minimal_index' in content:
            print("   ✓ Code references minimal_index")
        if 'fast_index' in content:
            print("   ! Code references fast_index")
        if 'indexing_optimized' in content:
            print("   ! Code references indexing_optimized")
            
        # Find the actual import line
        for line in content.split('\n'):
            if 'from signal_hub.cli.indexing' in line and 'import' in line:
                print(f"   Import line: {line.strip()}")
except Exception as e:
    print(f"   Error: {e}")

print("\n4. Installation location:")
import signal_hub
print(f"   Signal Hub installed at: {signal_hub.__file__}")
print(f"   Version: {getattr(signal_hub, '__version__', 'unknown')}")