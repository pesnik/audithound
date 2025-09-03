#!/usr/bin/env python3
"""Simple debug script that can be run directly."""

import os
import sys
import subprocess

# Change to the project directory
project_dir = "/Users/r_hasan/Development/audithound"
os.chdir(project_dir)

# Set environment variables
os.environ["AUDITHOUND_LOG_LEVEL"] = "DEBUG"

# Run the TUI with uv
cmd = [
    "/Users/r_hasan/.local/bin/uv",
    "run", 
    "audithound",
    "tui",
    "/Users/r_hasan/Development/audithound/test-example"
]

print(f"Running: {' '.join(cmd)}")
print("🐞 Debug mode enabled - check /Users/r_hasan/.audithound/logs/audithound.log for logs")
print("⌨️  Press Ctrl+C to exit")

try:
    result = subprocess.run(cmd, cwd=project_dir)
    sys.exit(result.returncode)
except KeyboardInterrupt:
    print("\n👋 Debug interrupted by user")
    sys.exit(0)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)