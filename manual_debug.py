#!/usr/bin/env python3
"""Manual debugging with pdb."""

import pdb
import sys
import os

# Add project to path
sys.path.insert(0, '/Users/r_hasan/Development/audithound')

# Set up environment
os.environ["AUDITHOUND_LOG_LEVEL"] = "DEBUG"

# Import and setup logging
from audithound.utils.logging_config import configure_for_tui
configure_for_tui()

from audithound.tui.screens.configuration import ConfigurationScreen
from audithound.tui.state.store import AppStore, AppState
from audithound.core.config import Config
from pathlib import Path

print("🐞 Manual Debug Session Started")
print("📝 Setting up configuration screen...")

# Create store and config
config = Config.default()
initial_state = AppState(
    config=config,
    config_file=Path("test-config.yaml"),
    scan_target="/Users/r_hasan/Development/audithound/test-example",
    theme="default"
)
store = AppStore(initial_state)

# Create configuration screen
config_screen = ConfigurationScreen(store)

print("✅ Configuration screen created")
print("🔍 You can now inspect variables:")
print("   - config_screen: The configuration screen instance")  
print("   - store: The application store")
print("   - config: The configuration object")
print("📍 Set breakpoint with: pdb.set_trace()")

# Start interactive debugging
pdb.set_trace()

print("🏁 Debug session ended")