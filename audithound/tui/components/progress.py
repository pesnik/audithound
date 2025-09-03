"""Progress indicators and real-time updates."""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ProgressBar, Static, Label
from textual.reactive import reactive
from rich.text import Text
from rich.progress import Progress as RichProgress
from rich.console import Console

from .base import BaseComponent
from ..state.events import EventType, Event
from ..state.actions import Action


class ProgressIndicator(BaseComponent):
    """Enhanced progress indicator with real-time updates."""
    
    progress = reactive(0.0)
    total = reactive(100.0)
    status = reactive("Ready")
    show_eta = reactive(True)
    show_rate = reactive(True)
    
    def __init__(self, store, show_details: bool = True, **kwargs):
        super().__init__(store, **kwargs)
        self.show_details = show_details
        self.start_time: Optional[datetime] = None
        self.last_update: Optional[datetime] = None
        self.update_count = 0
        self.rate_history: List[float] = []
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(self.status, id="progress-status")
            yield ProgressBar(
                total=self.total,
                progress=self.progress,
                show_eta=self.show_eta,
                id="main-progress"
            )
            if self.show_details:
                with Horizontal():
                    yield Label("", id="progress-details")
                    yield Label("", id="progress-eta")
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners for progress updates."""
        self.listen_to_event(EventType.SCAN_STARTED, self._on_scan_started)
        self.listen_to_event(EventType.SCAN_PROGRESS, self._on_scan_progress)
        self.listen_to_event(EventType.SCAN_COMPLETED, self._on_scan_completed)
        self.listen_to_event(EventType.SCAN_FAILED, self._on_scan_failed)
        self.listen_to_event(EventType.SCAN_CANCELLED, self._on_scan_cancelled)
    
    def on_component_mounted(self) -> None:
        """Initialize progress indicator."""
        self.reset()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        # Update progress from state
        self.progress = new_state.scan_progress
        self.status = new_state.scan_status
    
    def _on_scan_started(self, event: Event) -> None:
        """Handle scan start."""
        self.start_time = datetime.now()
        self.last_update = self.start_time
        self.update_count = 0
        self.rate_history.clear()
        
        self.progress = 0.0
        self.status = "Starting scan..."
        
        target = event.get_payload_value("target", "unknown")
        self.set_status(f"Scanning {target}")
    
    def _on_scan_progress(self, event: Event) -> None:
        """Handle progress updates."""
        now = datetime.now()
        progress_value = event.get_payload_value("progress", 0.0)
        status_msg = event.get_payload_value("status", "In progress...")
        current_tool = event.get_payload_value("current_tool")
        
        self.progress = progress_value
        
        # Update status with current tool info
        if current_tool:
            self.status = f"Running {current_tool}: {status_msg}"
        else:
            self.status = status_msg
        
        # Calculate rate
        if self.last_update:
            time_delta = (now - self.last_update).total_seconds()
            if time_delta > 0:
                rate = (progress_value - self.progress) / time_delta
                self.rate_history.append(rate)
                if len(self.rate_history) > 10:  # Keep last 10 measurements
                    self.rate_history.pop(0)
        
        self.last_update = now
        self.update_count += 1
        
        # Update details
        self._update_details()
    
    def _on_scan_completed(self, event: Event) -> None:
        """Handle scan completion."""
        self.progress = 100.0
        self.status = "Scan completed successfully"
        self.set_loading(False)
        
        # Show completion details
        results = event.get_payload_value("results")
        if results and hasattr(results, 'total_findings'):
            self.status = f"Completed - {results.total_findings} findings"
    
    def _on_scan_failed(self, event: Event) -> None:
        """Handle scan failure."""
        error = event.get_payload_value("error", "Unknown error")
        self.status = f"Scan failed: {error}"
        self.set_error(Exception(error), "scan_failed")
        self.set_loading(False)
    
    def _on_scan_cancelled(self, event: Event) -> None:
        """Handle scan cancellation."""
        self.status = "Scan cancelled by user"
        self.set_loading(False)
    
    def _update_details(self) -> None:
        """Update progress details display."""
        if not self.show_details:
            return
        
        try:
            details_widget = self.query_one("#progress-details", Label)
            eta_widget = self.query_one("#progress-eta", Label)
            
            # Calculate and show details
            details_text = f"{self.progress:.1f}% ({self.update_count} updates)"
            
            # Calculate ETA
            if self.start_time and self.progress > 0:
                elapsed = datetime.now() - self.start_time
                if self.progress < 100:
                    estimated_total = elapsed * (100 / self.progress)
                    remaining = estimated_total - elapsed
                    eta_text = f"ETA: {self._format_duration(remaining)}"
                else:
                    eta_text = f"Duration: {self._format_duration(elapsed)}"
            else:
                eta_text = "ETA: calculating..."
            
            details_widget.update(details_text)
            eta_widget.update(eta_text)
            
        except Exception as e:
            self.logger.debug(f"Error updating progress details: {e}")
    
    def _format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def set_status(self, status: str) -> None:
        """Set the status message."""
        self.status = status
        try:
            status_widget = self.query_one("#progress-status", Static)
            status_widget.update(status)
        except Exception as e:
            self.logger.debug(f"Error updating status: {e}")
    
    def set_progress(self, progress: float, status: str = None) -> None:
        """Set progress value and optional status."""
        self.progress = min(100.0, max(0.0, progress))
        if status:
            self.set_status(status)
        
        try:
            progress_bar = self.query_one("#main-progress", ProgressBar)
            progress_bar.update(progress=self.progress)
        except Exception as e:
            self.logger.debug(f"Error updating progress bar: {e}")
    
    def reset(self) -> None:
        """Reset progress indicator."""
        self.progress = 0.0
        self.status = "Ready"
        self.start_time = None
        self.last_update = None
        self.update_count = 0
        self.rate_history.clear()
        self.clear_error()
        self.set_loading(False)


class StreamingProgress(BaseComponent):
    """Advanced progress indicator with streaming updates and multiple progress bars."""
    
    def __init__(self, store, max_scanners: int = 5, **kwargs):
        super().__init__(store, **kwargs)
        self.max_scanners = max_scanners
        self.scanner_progress: Dict[str, float] = {}
        self.scanner_status: Dict[str, str] = {}
        self.overall_progress = 0.0
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Overall Progress", classes="progress-title")
            yield ProgressBar(total=100, progress=0, id="overall-progress")
            yield Static("", id="overall-status")
            
            # Individual scanner progress bars
            yield Static("Scanner Progress", classes="progress-title")
            with Vertical(id="scanner-progress-container"):
                pass
    
    def _setup_event_listeners(self) -> None:
        """Setup streaming progress event listeners."""
        self.listen_to_event(EventType.SCAN_STARTED, self._on_scan_started)
        self.listen_to_event(EventType.SCAN_PROGRESS, self._on_progress_update)
        self.listen_to_event(EventType.SCAN_COMPLETED, self._on_scan_completed)
    
    def on_component_mounted(self) -> None:
        """Initialize streaming progress."""
        self.reset_progress()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes for streaming progress."""
        self.overall_progress = new_state.scan_progress
        self._update_overall_progress()
    
    def _on_scan_started(self, event: Event) -> None:
        """Handle scan start for streaming progress."""
        tools = event.get_payload_value("tools", [])
        self.scanner_progress = {tool: 0.0 for tool in tools}
        self.scanner_status = {tool: "Initializing..." for tool in tools}
        self._setup_scanner_bars()
    
    def _on_progress_update(self, event: Event) -> None:
        """Handle streaming progress updates."""
        current_tool = event.get_payload_value("current_tool")
        progress = event.get_payload_value("progress", 0.0)
        status = event.get_payload_value("status", "Running...")
        
        if current_tool and current_tool in self.scanner_progress:
            self.scanner_progress[current_tool] = progress
            self.scanner_status[current_tool] = status
            self._update_scanner_progress(current_tool)
        
        # Update overall progress
        self.overall_progress = progress
        self._update_overall_progress()
    
    def _on_scan_completed(self, event: Event) -> None:
        """Handle scan completion for streaming progress."""
        # Mark all scanners as complete
        for scanner in self.scanner_progress:
            self.scanner_progress[scanner] = 100.0
            self.scanner_status[scanner] = "Completed"
            self._update_scanner_progress(scanner)
        
        self.overall_progress = 100.0
        self._update_overall_progress()
    
    def _setup_scanner_bars(self) -> None:
        """Setup individual scanner progress bars."""
        try:
            container = self.query_one("#scanner-progress-container", Vertical)
            container.remove_children()
            
            for scanner_name in self.scanner_progress:
                with container:
                    with Horizontal(classes="scanner-progress-row"):
                        yield Static(f"{scanner_name}:", classes="scanner-label")
                        yield ProgressBar(
                            total=100,
                            progress=0,
                            id=f"progress-{scanner_name}"
                        )
                        yield Static(
                            self.scanner_status.get(scanner_name, "Ready"),
                            id=f"status-{scanner_name}",
                            classes="scanner-status"
                        )
        except Exception as e:
            self.logger.error(f"Error setting up scanner bars: {e}")
    
    def _update_overall_progress(self) -> None:
        """Update overall progress display."""
        try:
            overall_bar = self.query_one("#overall-progress", ProgressBar)
            overall_status = self.query_one("#overall-status", Static)
            
            overall_bar.update(progress=self.overall_progress)
            
            if self.overall_progress >= 100:
                status_text = "All scanners completed"
            else:
                active_scanners = sum(1 for p in self.scanner_progress.values() if 0 < p < 100)
                status_text = f"Running {active_scanners} scanner(s) - {self.overall_progress:.1f}%"
            
            overall_status.update(status_text)
            
        except Exception as e:
            self.logger.debug(f"Error updating overall progress: {e}")
    
    def _update_scanner_progress(self, scanner_name: str) -> None:
        """Update individual scanner progress."""
        try:
            progress_bar = self.query_one(f"#progress-{scanner_name}", ProgressBar)
            status_label = self.query_one(f"#status-{scanner_name}", Static)
            
            progress = self.scanner_progress[scanner_name]
            status = self.scanner_status[scanner_name]
            
            progress_bar.update(progress=progress)
            status_label.update(status)
            
        except Exception as e:
            self.logger.debug(f"Error updating scanner progress for {scanner_name}: {e}")
    
    def reset_progress(self) -> None:
        """Reset all progress indicators."""
        self.scanner_progress.clear()
        self.scanner_status.clear()
        self.overall_progress = 0.0
        
        try:
            container = self.query_one("#scanner-progress-container", Vertical)
            container.remove_children()
        except Exception as e:
            self.logger.debug(f"Error resetting progress: {e}")