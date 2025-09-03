#!/usr/bin/env python3
"""Test TUI scanning and result handling."""

import asyncio
import logging
from pathlib import Path
from audithound.core.config import Config
from audithound.core.scanner import SecurityScanner

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_scan_results():
    """Test scanning and result parsing."""
    target = "/Users/r_hasan/Development/audithound"
    config = Config.load(None)  # Load default config
    config.use_docker = False  # Disable Docker
    scanner = SecurityScanner(config)
    
    logger.info("Starting scan...")
    results = scanner.scan(target)
    
    logger.info(f"Scan completed. Total findings: {results.total_findings}")
    logger.info(f"Results type: {type(results)}")
    logger.info(f"Results summary: {results.summary}")
    logger.info(f"Results by scanner: {list(results.results_by_scanner.keys())}")
    
    for scanner_name, result in results.results_by_scanner.items():
        findings_count = len(result.findings) if result.findings else 0
        logger.info(f"Scanner {scanner_name}: {result.status}, {findings_count} findings")
    
    return results

if __name__ == "__main__":
    results = test_scan_results()
    print(f"Final results: {results.total_findings} findings")
    print(f"Summary: {results.summary}")