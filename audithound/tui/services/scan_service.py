"""Scan execution service with real-time updates."""

import asyncio
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future

from ...core.config import Config
from ...core.scanner import SecurityScanner
from ..state.store import AppStore
from ..state.events import (
    Event, EventType, scan_started_event, scan_progress_event,
    scan_completed_event, scan_failed_event, error_occurred_event
)
from ..state.actions import Action, ActionType, set_results_action


class ScanService:
    """Service for managing security scans with real-time updates."""
    
    def __init__(self, store: AppStore, config: Config):
        self.store = store
        self.config = config
        self.scanner = SecurityScanner(config)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Scan state
        self._current_scan: Optional[Future] = None
        self._scan_thread_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="scan")
        self._cancel_event = threading.Event()
        
        # Progress tracking
        self._progress_callback: Optional[Callable] = None
        self._scan_start_time: Optional[datetime] = None
        
        # Setup event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners for scan management."""
        self.store.listen_to_event(EventType.SCAN_STARTED, self._on_scan_started)
        self.store.listen_to_event(EventType.SCAN_CANCELLED, self._on_scan_cancelled)
    
    def _on_scan_started(self, event: Event) -> None:
        """Handle scan started events."""
        target = event.get_payload_value("target")
        tools = event.get_payload_value("tools", [])
        config_overrides = event.get_payload_value("config_overrides", {})
        
        # Start the actual scan
        self.start_scan_async(target, tools, config_overrides)
    
    def _on_scan_cancelled(self, event: Event) -> None:
        """Handle scan cancellation events."""
        self.cancel_current_scan()
    
    def start_scan_async(
        self,
        target: str,
        tools: Optional[List[str]] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Start a scan asynchronously."""
        if self.is_scan_running():
            self.logger.warning("Scan already in progress")
            return False
        
        try:
            # Reset cancel event
            self._cancel_event.clear()
            self._scan_start_time = datetime.now()
            
            # Submit scan task
            self._current_scan = self._scan_thread_pool.submit(
                self._run_scan,
                target,
                tools or [],
                config_overrides or {}
            )
            
            # Monitor scan progress
            asyncio.create_task(self._monitor_scan_progress())
            
            self.logger.info(f"Started scan for target: {target}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to start scan: {e}")
            self.store.emit_event(error_occurred_event(e, "scan_start"))
            return False
    
    def cancel_current_scan(self) -> bool:
        """Cancel the currently running scan."""
        if not self.is_scan_running():
            return False
        
        try:
            # Set cancel event
            self._cancel_event.set()
            
            # Cancel the future
            if self._current_scan and not self._current_scan.done():
                self._current_scan.cancel()
            
            self.logger.info("Scan cancellation requested")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to cancel scan: {e}")
            return False
    
    def is_scan_running(self) -> bool:
        """Check if a scan is currently running."""
        return (
            self._current_scan is not None and
            not self._current_scan.done()
        )
    
    def get_scan_progress(self) -> float:
        """Get current scan progress (0-100)."""
        # This would return actual progress from the scanner
        # For now, return state value
        return self.store.get_state_value("scan_progress", 0.0)
    
    def cleanup(self) -> None:
        """Cleanup scan service resources."""
        try:
            # Cancel any running scan
            self.cancel_current_scan()
            
            # Shutdown thread pool
            self._scan_thread_pool.shutdown(wait=True, timeout=30)
            
            self.logger.info("Scan service cleanup completed")
        
        except Exception as e:
            self.logger.error(f"Error during scan service cleanup: {e}")
    
    def _run_scan(
        self,
        target: str,
        tools: List[str],
        config_overrides: Dict[str, Any]
    ) -> None:
        """Run the actual scan in a separate thread."""
        scan_id = f"scan_{datetime.now().isoformat()}"
        
        try:
            self.logger.info(f"Starting scan execution: {scan_id}")
            
            # Apply config overrides if any
            scan_config = self.config
            if config_overrides:
                # Create modified config (simplified)
                scan_config = self.config
            
            # Update scanner with new config
            scanner = SecurityScanner(scan_config)
            
            # Set up progress callback
            self._setup_progress_callback(scan_id, tools)
            
            # Execute scan with progress monitoring
            results = self._execute_scan_with_progress(scanner, target, tools, scan_id)
            
            if self._cancel_event.is_set():
                self.logger.info(f"Scan cancelled: {scan_id}")
                return
            
            # Emit completion event
            self.store.emit_event(scan_completed_event(results))
            
            # Update state with results
            self.store.dispatch_action(set_results_action(results, scan_id))
            
            self.logger.info(f"Scan completed successfully: {scan_id}")
        
        except Exception as e:
            self.logger.error(f"Scan failed: {e}")
            self.store.emit_event(scan_failed_event(str(e), {"scan_id": scan_id}))
        
        finally:
            self._current_scan = None
            self._progress_callback = None
    
    def _execute_scan_with_progress(
        self,
        scanner: SecurityScanner,
        target: str,
        tools: List[str],
        scan_id: str
    ):
        """Execute scan with progress monitoring."""
        # This is a simplified implementation
        # In production, would integrate with actual scanner progress
        
        total_steps = len(tools) if tools else len(scanner.available_scanners)
        current_step = 0
        
        # Simulate scan progress
        for i in range(total_steps):
            if self._cancel_event.is_set():
                break
            
            current_tool = tools[i] if i < len(tools) else f"tool_{i}"
            
            # Emit progress event
            progress = (i / total_steps) * 100
            self.store.emit_event(scan_progress_event(
                progress,
                f"Scanning with {current_tool}...",
                current_tool
            ))
            
            current_step += 1
            
            # Simulate some work (replace with actual scanner calls)
            import time
            time.sleep(0.5)  # Simulate scanner execution time
        
        # Final progress
        if not self._cancel_event.is_set():
            self.store.emit_event(scan_progress_event(100.0, "Finalizing results..."))
            
            # Execute actual scan
            results = scanner.scan(target, tools)
            return results
        
        return None
    
    def _setup_progress_callback(self, scan_id: str, tools: List[str]) -> None:
        """Setup progress monitoring callback."""
        def progress_callback(current_tool: str, progress: float, status: str):
            """Callback for scan progress updates."""
            if not self._cancel_event.is_set():
                self.store.emit_event(scan_progress_event(
                    progress,
                    status,
                    current_tool
                ))
        
        self._progress_callback = progress_callback
    
    async def _monitor_scan_progress(self) -> None:
        """Monitor scan progress and emit events."""
        while self.is_scan_running() and not self._cancel_event.is_set():
            try:
                # Check if scan completed
                if self._current_scan.done():
                    break
                
                # Emit periodic progress updates (if needed)
                await asyncio.sleep(1)
            
            except Exception as e:
                self.logger.error(f"Error monitoring scan progress: {e}")
                break
    
    def get_scan_history(self) -> List[Dict[str, Any]]:
        """Get scan history from state."""
        return self.store.get_state_value("scan_history", [])
    
    def get_current_scan_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the current scan."""
        if not self.is_scan_running():
            return None
        
        state = self.store.get_state()
        return {
            "scan_id": state.scan_id,
            "target": state.scan_target,
            "tools": state.scan_tools,
            "progress": state.scan_progress,
            "status": state.scan_status,
            "current_scanner": state.current_scanner,
            "start_time": self._scan_start_time
        }
    
    def export_scan_results(
        self,
        results,
        output_path: Path,
        format_type: str = "json",
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Export scan results to file."""
        try:
            # Use the scanner's export functionality
            if hasattr(self.scanner, 'export_results'):
                self.scanner.export_results(results, output_path, format_type, options)
            else:
                # Fallback export implementation
                self._export_results_fallback(results, output_path, format_type)
            
            self.logger.info(f"Results exported to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to export results: {e}")
            self.store.emit_event(error_occurred_event(e, "export"))
            return False
    
    def _export_results_fallback(
        self,
        results,
        output_path: Path,
        format_type: str
    ) -> None:
        """Fallback export implementation."""
        if format_type.lower() == "json":
            import json
            
            # Convert results to dict
            if hasattr(results, '__dict__'):
                data = results.__dict__
            else:
                data = {"results": str(results)}
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        else:
            # Simple text export
            with open(output_path, 'w') as f:
                f.write(str(results))


class MockScanner:
    """Mock scanner for development and testing."""
    
    def __init__(self, config: Config):
        self.config = config
        self.available_scanners = ["bandit", "safety", "semgrep"]
    
    def scan(self, target: str, tools: List[str] = None):
        """Mock scan implementation."""
        import random
        from ...core.types import AggregatedResults
        
        # Create mock results
        mock_findings = []
        severities = ["critical", "high", "medium", "low"]
        
        # Generate some mock findings
        for i in range(random.randint(0, 10)):
            mock_findings.append({
                "severity": random.choice(severities),
                "rule_name": f"mock_rule_{i}",
                "file": f"src/file_{i}.py",
                "line": random.randint(1, 100),
                "message": f"Mock security finding {i}"
            })
        
        # Create mock aggregated results
        class MockResult:
            def __init__(self):
                self.total_findings = len(mock_findings)
                self.target = target
                self.scan_time = datetime.now()
                self.results_by_scanner = {
                    "mock_scanner": MockScannerResult(mock_findings)
                }
                self.summary = self._calculate_summary()
            
            def _calculate_summary(self):
                summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                for finding in mock_findings:
                    severity = finding.get("severity", "low")
                    if severity in summary:
                        summary[severity] += 1
                return summary
        
        class MockScannerResult:
            def __init__(self, findings):
                self.status = "success"
                self.findings = findings
        
        return MockResult()