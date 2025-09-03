"""Dashboard screen for AuditHound TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, ProgressBar
from rich.panel import Panel
from rich.table import Table
from rich.console import Console

from ..components.base import BaseComponent
from ..state.events import EventType


class DashboardScreen(BaseComponent):
    """Main dashboard showing overview and quick actions."""
    
    def __init__(self, store, **kwargs):
        super().__init__(store, component_id="dashboard", **kwargs)
    
    def compose(self) -> ComposeResult:
        with Vertical():
            # Status overview
            with Horizontal():
                yield Static("🎯 Target: Ready to scan", id="target-info", classes="summary-panel")
                yield Static("🔍 Status: No scan running", id="scan-status", classes="summary-panel")
            
            # Quick actions
            with Horizontal():
                yield Static("⚡ Quick Actions", classes="summary-panel")
                with Vertical(classes="summary-panel"):
                    yield Button("🚀 Start Scan", variant="primary", id="quick-scan")
                    yield Button("📊 View Results", variant="default", id="quick-results")
                    yield Button("⚙️ Configure", variant="default", id="quick-config")
                    yield Button("📤 Export", variant="default", id="quick-export")
            
            # Recent activity
            yield Static("📈 Recent Activity", classes="section-title")
            yield Static("No recent scans. Start a scan to see activity here.", id="recent-activity", classes="activity-panel")
    
    def _setup_event_listeners(self) -> None:
        """Setup dashboard event listeners."""
        self.listen_to_event(EventType.SCAN_STARTED, self._on_scan_started)
        self.listen_to_event(EventType.SCAN_COMPLETED, self._on_scan_completed)
        self.listen_to_event(EventType.SCAN_FAILED, self._on_scan_failed)
        self.listen_to_event(EventType.RESULTS_UPDATED, self._on_results_updated)
    
    def on_component_mounted(self) -> None:
        """Initialize dashboard."""
        self._update_dashboard()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        self._update_dashboard()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "quick-scan":
            self._start_scan()
        elif event.button.id == "quick-results":
            self._view_results()
        elif event.button.id == "quick-config":
            self._open_config()
        elif event.button.id == "quick-export":
            self._export_results()
    
    def _update_dashboard(self) -> None:
        """Update dashboard display."""
        state = self.store.get_state()
        
        # Update target info
        self._update_target_info(state)
        
        # Update scan status
        self._update_scan_status(state)
        
        # Update recent activity
        self._update_recent_activity(state)
    
    def _update_target_info(self, state) -> None:
        """Update target information panel."""
        try:
            target_widget = self.query_one("#target-info", Static)
            
            info_text = f"""
🎯 Scan Target
Path: {state.scan_target or 'Not set'}
Tools: {len(state.scan_tools)} configured
Config: {'✅ Loaded' if state.config else '❌ Default'}
            """
            
            target_widget.update(Panel(info_text.strip(), title="Target Info", border_style="blue"))
        
        except Exception as e:
            self.logger.debug(f"Error updating target info: {e}")
    
    def _update_scan_status(self, state) -> None:
        """Update scan status panel."""
        try:
            status_widget = self.query_one("#scan-status", Static)
            
            if state.is_scanning:
                status_text = f"""
📊 Scan Status: Running
Progress: {state.scan_progress:.1f}%
Current: {state.current_scanner or 'Initializing...'}
Status: {state.scan_status}
                """
                border_style = "yellow"
            elif state.current_results:
                findings = getattr(state.current_results, 'total_findings', 0)
                status_text = f"""
📊 Last Scan: Complete
Findings: {findings}
Duration: {state.last_scan_duration or 'Unknown'}
Status: ✅ Ready
                """
                border_style = "green" if findings == 0 else "red"
            else:
                status_text = f"""
📊 Scan Status: Ready
Last scan: Never
Status: Waiting for scan
Progress: Press 'Start Scan'
                """
                border_style = "blue"
            
            status_widget.update(Panel(status_text.strip(), title="Scan Status", border_style=border_style))
        
        except Exception as e:
            self.logger.debug(f"Error updating scan status: {e}")
    
    def _update_recent_activity(self, state) -> None:
        """Update recent activity display."""
        try:
            activity_widget = self.query_one("#recent-activity", Static)
            
            if state.scan_history:
                # Show recent scans
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Time", style="dim", width=12)
                table.add_column("Target", style="cyan", width=20)
                table.add_column("Findings", justify="right", style="red")
                table.add_column("Status", style="green")
                
                # Show last 5 scans
                for scan in state.scan_history[-5:]:
                    timestamp = scan.get('timestamp', 'Unknown')
                    target = scan.get('target', 'Unknown')[:18] + '...' if len(scan.get('target', '')) > 20 else scan.get('target', 'Unknown')
                    findings = str(scan.get('findings_count', 0))
                    status = "✅ Complete"
                    
                    table.add_row(
                        timestamp.strftime('%H:%M:%S') if hasattr(timestamp, 'strftime') else str(timestamp),
                        target,
                        findings,
                        status
                    )
                
                console = Console()
                with console.capture() as capture:
                    console.print(table)
                
                activity_widget.update(capture.get())
            else:
                activity_widget.update("No recent scans. Start your first scan to see activity here.")
        
        except Exception as e:
            self.logger.debug(f"Error updating recent activity: {e}")
    
    def _on_scan_started(self, event) -> None:
        """Handle scan started event."""
        self._update_dashboard()
    
    def _on_scan_completed(self, event) -> None:
        """Handle scan completed event."""
        self._update_dashboard()
    
    def _on_scan_failed(self, event) -> None:
        """Handle scan failed event."""
        self._update_dashboard()
    
    def _on_results_updated(self, event) -> None:
        """Handle results updated event."""
        self._update_dashboard()
    
    def _start_scan(self) -> None:
        """Start a scan from dashboard."""
        from ..state.actions import start_scan_action
        
        state = self.store.get_state()
        target = state.scan_target
        tools = state.scan_tools
        
        if not target:
            # Could show error or prompt for target
            return
        
        self.dispatch_action(start_scan_action(target, tools))
    
    def _view_results(self) -> None:
        """Switch to results view."""
        from ..state.actions import change_tab_action
        self.dispatch_action(change_tab_action("results"))
    
    def _open_config(self) -> None:
        """Switch to configuration view."""
        from ..state.actions import change_tab_action
        self.dispatch_action(change_tab_action("configuration"))
    
    def _export_results(self) -> None:
        """Export current results."""
        state = self.store.get_state()
        if not state.current_results:
            return
        
        from ..state.actions import export_results_action
        from pathlib import Path
        
        output_path = Path("audithound_dashboard_export.json")
        self.dispatch_action(export_results_action("json", output_path))