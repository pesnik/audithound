#!/usr/bin/env python3
"""Debug TUI scan issue."""

import asyncio
from pathlib import Path
from audithound.core.config import Config
from audithound.core.scanner import SecurityScanner

async def debug_scan():
    """Debug the exact same scan that TUI would run."""
    target = "/Users/r_hasan/Development/audithound"
    
    # Load config exactly like TUI does
    config = Config.load(None)  # No config file, use defaults
    config.use_docker = False  # Simulate --no-docker
    
    scanner = SecurityScanner(config)
    
    print(f"Config use_docker: {config.use_docker}")
    print(f"Docker runner: {scanner.docker_runner}")
    
    print("Starting scan...")
    
    # Run scan like TUI does - in executor
    results = await asyncio.get_event_loop().run_in_executor(
        None, scanner.scan, target, None
    )
    
    print(f"Scan completed!")
    print(f"Results type: {type(results)}")
    print(f"Total findings: {results.total_findings if results else 0}")
    print(f"Summary: {results.summary if results else 'None'}")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(debug_scan())