"""Results screen for displaying scan findings."""

from typing import Dict, Any, List
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, Select, Input, Tabs, TabPane, TabbedContent
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text

from ..components.base import BaseComponent
from ..components.data import FilterableTable
from ..components.progress import StreamingProgress
from ..state.events import EventType


class ResultsScreen(BaseComponent):
    """Screen for displaying and analyzing scan results."""
    
    def __init__(self, store, **kwargs):
        super().__init__(store, component_id="results", **kwargs)
        self.current_results = None
        self.filtered_results = []
    
    def compose(self) -> ComposeResult:
        with Vertical():
            # Results header with summary
            with Horizontal():
                yield Static("", id="results-summary", classes="summary-panel")
                yield Static("", id="severity-breakdown", classes="summary-panel")
            
            # Progress indicator (shown during scanning)
            yield StreamingProgress(self.store, id="scan-progress", classes="progress-section")
            
            # Results content
            with TabbedContent(initial="findings", id="results-tabs"):
                # Findings tab
                with TabPane("🔍 Findings", id="findings"):
                    with Vertical():
                        # Filter controls
                        with Horizontal(classes="filter-bar"):
                            yield Select(
                                [
                                    ("All Severities", "all"),
                                    ("Critical", "critical"),
                                    ("High", "high"),
                                    ("Medium", "medium"),
                                    ("Low", "low")
                                ],
                                value="all",
                                id="severity-filter"
                            )
                            yield Select(
                                [("All Scanners", "all")],
                                value="all",
                                id="scanner-filter"
                            )
                            yield Input(placeholder="Search findings...", id="findings-search")
                            yield Button("Clear", id="clear-filters", variant="default")
                        
                        # Findings table
                        yield FilterableTable(
                            self.store,
                            columns=["Severity", "Scanner", "Rule", "File", "Line", "Message"],
                            id="findings-table"
                        )
                
                # Summary tab
                with TabPane("📊 Summary", id="summary"):
                    with Horizontal():
                        yield Static("", id="summary-stats", classes="summary-panel")
                        yield Static("", id="scanner-stats", classes="summary-panel")
                
                # Timeline tab
                with TabPane("⏱️ Timeline", id="timeline"):
                    yield Static("", id="scan-timeline", classes="timeline-panel")
    
    def _setup_event_listeners(self) -> None:
        """Setup results screen event listeners."""
        self.listen_to_event(EventType.SCAN_STARTED, self._on_scan_started)
        self.listen_to_event(EventType.SCAN_PROGRESS, self._on_scan_progress)
        self.listen_to_event(EventType.SCAN_COMPLETED, self._on_scan_completed)
        self.listen_to_event(EventType.SCAN_FAILED, self._on_scan_failed)
        self.listen_to_event(EventType.RESULTS_UPDATED, self._on_results_updated)
    
    def on_component_mounted(self) -> None:
        """Initialize results screen."""
        self._update_results_display()
        self._hide_progress()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        # Update results if they changed
        if hasattr(new_state, 'current_results') and new_state.current_results != getattr(old_state, 'current_results', None):
            self.current_results = new_state.current_results
            self._update_results_display()
        
        # Show/hide progress based on scan state
        if hasattr(new_state, 'is_scanning'):
            if new_state.is_scanning:
                self._show_progress()
            else:
                self._hide_progress()
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter changes."""
        if event.select.id == "severity-filter":
            self._apply_severity_filter(event.value)
        elif event.select.id == "scanner-filter":
            self._apply_scanner_filter(event.value)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "findings-search":
            self._apply_text_filter(event.value)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "clear-filters":
            self._clear_all_filters()
    
    def _on_scan_started(self, event) -> None:
        """Handle scan started."""
        self._show_progress()
        self._update_progress_display("Scan started...")
    
    def _on_scan_progress(self, event) -> None:
        """Handle scan progress updates."""
        progress = event.get_payload_value("progress", 0)
        status = event.get_payload_value("status", "In progress...")
        current_tool = event.get_payload_value("current_tool")
        
        self._update_progress_display(f"{status} ({progress:.1f}%)")
    
    def _on_scan_completed(self, event) -> None:
        """Handle scan completion."""
        self._hide_progress()
        results = event.get_payload_value("results")
        if results:
            self.current_results = results
            self._update_results_display()
    
    def _on_scan_failed(self, event) -> None:
        """Handle scan failure."""
        self._hide_progress()
        error = event.get_payload_value("error", "Unknown error")
        self._show_error(f"Scan failed: {error}")
    
    def _on_results_updated(self, event) -> None:
        """Handle results updates."""
        results = event.get_payload_value("results")
        if results:
            self.current_results = results
            self._update_results_display()
    
    def _show_progress(self) -> None:
        """Show progress indicator."""
        try:
            progress_widget = self.query_one("#scan-progress", StreamingProgress)
            progress_widget.display = True
        except Exception as e:
            self.logger.debug(f"Error showing progress: {e}")
    
    def _hide_progress(self) -> None:
        """Hide progress indicator."""
        try:
            progress_widget = self.query_one("#scan-progress", StreamingProgress)
            progress_widget.display = False
        except Exception as e:
            self.logger.debug(f"Error hiding progress: {e}")
    
    def _update_progress_display(self, status: str) -> None:
        """Update progress display with status."""
        try:
            progress_widget = self.query_one("#scan-progress", StreamingProgress)
            # Progress widget would handle this internally
        except Exception as e:
            self.logger.debug(f"Error updating progress: {e}")
    
    def _update_results_display(self) -> None:
        """Update the entire results display."""
        if not self.current_results:
            self._show_no_results()
            return
        
        self._update_summary()
        self._update_severity_breakdown()
        self._update_findings_table()
        self._update_scanner_filters()
        self._update_summary_stats()
        self._update_timeline()
    
    def _show_no_results(self) -> None:
        """Show no results message."""
        try:
            summary_widget = self.query_one("#results-summary", Static)
            summary_widget.update(Panel(
                "No scan results available.\nStart a scan to see findings here.",
                title="No Results",
                border_style="dim"
            ))
            
            breakdown_widget = self.query_one("#severity-breakdown", Static)
            breakdown_widget.update("")
        except Exception as e:
            self.logger.debug(f"Error showing no results: {e}")
    
    def _update_summary(self) -> None:
        """Update results summary."""
        try:
            summary_widget = self.query_one("#results-summary", Static)
            
            if not self.current_results or not hasattr(self.current_results, 'total_findings'):
                return
            
            total = self.current_results.total_findings
            target = getattr(self.current_results, 'target', 'Unknown')
            scan_time = getattr(self.current_results, 'scan_time', None)
            
            summary_text = f"""
📊 Scan Results
Target: {target}
Total Findings: {total}
Scan Time: {scan_time.strftime('%Y-%m-%d %H:%M:%S') if scan_time else 'Unknown'}
Scanners: {len(getattr(self.current_results, 'results_by_scanner', {}))}
            """
            
            border_style = "red" if total > 0 else "green"
            summary_widget.update(Panel(
                summary_text.strip(),
                title="Results Summary",
                border_style=border_style
            ))
        
        except Exception as e:
            self.logger.debug(f"Error updating summary: {e}")
    
    def _update_severity_breakdown(self) -> None:
        """Update severity breakdown display."""
        try:
            breakdown_widget = self.query_one("#severity-breakdown", Static)
            
            if not self.current_results or not hasattr(self.current_results, 'summary'):
                return
            
            summary = self.current_results.summary
            critical = summary.get('critical', 0)
            high = summary.get('high', 0)
            medium = summary.get('medium', 0)
            low = summary.get('low', 0)
            
            # Create severity breakdown table
            table = Table(show_header=False, box=None)
            table.add_column("Severity", style="bold", width=10)
            table.add_column("Count", justify="right", width=8)
            table.add_column("Bar", width=20)
            
            total = max(1, critical + high + medium + low)  # Avoid division by zero
            
            def create_bar(count: int, color: str) -> Text:
                bar_length = int((count / total) * 15) if total > 0 else 0
                bar = "█" * bar_length + "░" * (15 - bar_length)
                return Text(bar, style=color)
            
            if critical > 0:
                table.add_row("Critical", str(critical), create_bar(critical, "bold red"))
            if high > 0:
                table.add_row("High", str(high), create_bar(high, "red"))
            if medium > 0:
                table.add_row("Medium", str(medium), create_bar(medium, "yellow"))
            if low > 0:
                table.add_row("Low", str(low), create_bar(low, "blue"))
            
            console = Console()
            with console.capture() as capture:
                console.print(table)
            
            breakdown_widget.update(Panel(
                capture.get(),
                title="Severity Breakdown",
                border_style="blue"
            ))
        
        except Exception as e:
            self.logger.debug(f"Error updating severity breakdown: {e}")
    
    def _update_findings_table(self) -> None:
        """Update the findings table."""
        try:
            table_widget = self.query_one("#findings-table", FilterableTable)
            
            if not self.current_results:
                return
            
            # Convert results to table data
            findings_data = []
            
            if hasattr(self.current_results, 'results_by_scanner'):
                for scanner_name, result in self.current_results.results_by_scanner.items():
                    if hasattr(result, 'findings') and result.status == "success":
                        for finding in result.findings:
                            findings_data.append({
                                "Severity": finding.get('severity', 'unknown'),
                                "Scanner": scanner_name,
                                "Rule": finding.get('rule_name', 'unknown'),
                                "File": finding.get('file', ''),
                                "Line": finding.get('line', 0),
                                "Message": finding.get('message', '')[:100] + "..." if len(finding.get('message', '')) > 100 else finding.get('message', '')
                            })
            
            table_widget.set_data(findings_data)
        
        except Exception as e:
            self.logger.debug(f"Error updating findings table: {e}")
    
    def _update_scanner_filters(self) -> None:
        """Update scanner filter options."""
        try:
            scanner_select = self.query_one("#scanner-filter", Select)
            
            if not self.current_results or not hasattr(self.current_results, 'results_by_scanner'):
                return
            
            # Get available scanners
            scanners = list(self.current_results.results_by_scanner.keys())
            scanner_options = [("All Scanners", "all")] + [(name, name) for name in scanners]
            
            # Update options (this is simplified - actual implementation would need to recreate the Select)
            # scanner_select.set_options(scanner_options)
        
        except Exception as e:
            self.logger.debug(f"Error updating scanner filters: {e}")
    
    def _update_summary_stats(self) -> None:
        """Update summary statistics tab."""
        try:
            stats_widget = self.query_one("#summary-stats", Static)
            scanner_stats_widget = self.query_one("#scanner-stats", Static)
            
            if not self.current_results:
                return
            
            # Overall statistics
            stats_text = "No statistics available yet."
            stats_widget.update(Panel(
                stats_text,
                title="Overall Statistics",
                border_style="blue"
            ))
            
            # Scanner-specific statistics  
            scanner_text = "No scanner statistics available yet."
            scanner_stats_widget.update(Panel(
                scanner_text,
                title="Scanner Statistics",
                border_style="green"
            ))
        
        except Exception as e:
            self.logger.debug(f"Error updating summary stats: {e}")
    
    def _update_timeline(self) -> None:
        """Update scan timeline display."""
        try:
            timeline_widget = self.query_one("#scan-timeline", Static)
            
            # This would show a timeline of the scan process
            timeline_text = "Scan timeline feature coming soon..."
            timeline_widget.update(timeline_text)
        
        except Exception as e:
            self.logger.debug(f"Error updating timeline: {e}")
    
    def _apply_severity_filter(self, severity: str) -> None:
        """Apply severity filter to results."""
        # This would filter the findings table
        pass
    
    def _apply_scanner_filter(self, scanner: str) -> None:
        """Apply scanner filter to results."""
        # This would filter the findings table  
        pass
    
    def _apply_text_filter(self, search_text: str) -> None:
        """Apply text filter to results."""
        # This would filter the findings table
        pass
    
    def _clear_all_filters(self) -> None:
        """Clear all active filters."""
        try:
            severity_select = self.query_one("#severity-filter", Select)
            scanner_select = self.query_one("#scanner-filter", Select) 
            search_input = self.query_one("#findings-search", Input)
            
            severity_select.value = "all"
            scanner_select.value = "all"
            search_input.value = ""
            
            # Clear filters in the table
            table_widget = self.query_one("#findings-table", FilterableTable)
            table_widget.clear_filters()
        
        except Exception as e:
            self.logger.debug(f"Error clearing filters: {e}")
    
    def _show_error(self, error_message: str) -> None:
        """Show error message in results area."""
        try:
            summary_widget = self.query_one("#results-summary", Static)
            summary_widget.update(Panel(
                error_message,
                title="Error",
                border_style="red"
            ))
        except Exception as e:
            self.logger.debug(f"Error showing error message: {e}")