"""Main TUI Application for AuditHound."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List

from textual.app import App, ComposeResult

# Setup logging for TUI debugging
log_dir = Path.home() / '.audithound' / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'tui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TUI')
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Static, Button, ProgressBar, DataTable, Tree, 
    Checkbox, Select, Input, Collapsible, Tabs, TabPane, Label,
    Rule, TabbedContent, ContentSwitcher, Switch, RadioButton, RadioSet
)
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.align import Align

from ..core.config import Config
from ..core.scanner import SecurityScanner
from ..core.types import AggregatedResults


class ScanProgressScreen(ModalScreen[None]):
    """Modal screen showing scan progress."""
    
    def __init__(self, scanner: SecurityScanner, target: str, tools: Optional[List[str]] = None):
        super().__init__()
        logger.info(f"ScanProgressScreen.__init__ called with target={target}, tools={tools}")
        self.scanner = scanner
        self.target = target
        self.tools = tools
        self.results = None
        
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("🔍 Running Security Scan")
            yield Static(f"Target: {self.target}")
            yield ProgressBar(show_eta=False)
            yield Static("Initializing...", id="progress-status")
            yield Button("Cancel", variant="error")
    
    async def on_mount(self) -> None:
        """Start the scan when screen is mounted."""
        logger.info("ScanProgressScreen.on_mount called - starting scan task")
        asyncio.create_task(self.run_scan())
    
    async def run_scan(self) -> None:
        """Run the security scan."""
        logger.info("ScanProgressScreen.run_scan started")
        progress_bar = self.query_one(ProgressBar)
        status = self.query_one("#progress-status", Static)
        
        try:
            logger.info("Setting up progress bar")
            progress_bar.update(total=100)
            status.update("Starting scan...")
            
            logger.info(f"Scanner info: has_scanner={hasattr(self, 'scanner')}, target={self.target}")
            status.update(f"Scanner available: {hasattr(self, 'scanner')}, Target: {self.target}")
            await asyncio.sleep(1)
            
            # Run actual scan
            logger.info("Starting actual scan execution")
            status.update("Running security scanners...")
            self.results = await asyncio.get_event_loop().run_in_executor(
                None, self.scanner.scan, self.target, self.tools
            )
            
            logger.info(f"Scan completed with {self.results.total_findings if self.results else 0} findings")
            progress_bar.update(progress=100)
            status.update(f"Scan completed! Found {self.results.total_findings if self.results else 0} findings")
            
            # Close modal and return results to main screen
            await asyncio.sleep(2)  # Give user time to see the result count
            logger.info(f"Dismissing modal with results: {type(self.results)}")
            self.dismiss(self.results)
            
        except Exception as e:
            logger.error(f"Scan failed with error: {e}")
            status.update(f"Error: {str(e)}")
            await asyncio.sleep(3)
            self.dismiss(None)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel button."""
        self.app.pop_screen()


class ResultsTable(DataTable):
    """Table widget for displaying scan results."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_type = "row"
        
    def populate_results(self, results: AggregatedResults) -> None:
        """Populate table with scan results."""
        self.clear()
        
        # Add columns
        self.add_columns("Severity", "Scanner", "Rule", "File", "Line", "Message")
        
        # Add rows
        for scanner_name, result in results.results_by_scanner.items():
            if result.status == "success":
                for finding in result.findings:
                    severity = finding.get('severity', 'unknown')
                    rule_name = finding.get('rule_name', 'unknown')
                    file_path = finding.get('file', '')
                    line = finding.get('line', 0)
                    message = finding.get('message', '')[:100] + "..." if len(finding.get('message', '')) > 100 else finding.get('message', '')
                    
                    # Style severity cell based on level
                    severity_text = Text(severity.upper())
                    if severity == 'critical':
                        severity_text.stylize("bold red")
                    elif severity == 'high':
                        severity_text.stylize("red")
                    elif severity == 'medium':
                        severity_text.stylize("yellow")
                    elif severity == 'low':
                        severity_text.stylize("blue")
                    else:
                        severity_text.stylize("dim")
                    
                    self.add_row(
                        severity_text,
                        scanner_name,
                        rule_name,
                        file_path,
                        str(line) if line > 0 else "",
                        message
                    )


class SummaryWidget(Static):
    """Widget showing scan summary statistics."""
    
    def update_summary(self, results: AggregatedResults) -> None:
        """Update summary with scan results."""
        summary = results.summary
        
        # Create summary text
        total = summary.get('total', 0)
        critical = summary.get('critical', 0)
        high = summary.get('high', 0)
        medium = summary.get('medium', 0)
        low = summary.get('low', 0)
        
        summary_text = f"""
📊 Scan Summary
Target: {results.target}
Total Findings: {total}

Severity Breakdown:
  Critical: {critical}
  High: {high}
  Medium: {medium}
  Low: {low}

Scanners: {len(results.results_by_scanner)}
Scan Time: {results.scan_time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.update(Panel(summary_text.strip(), title="Summary", border_style="blue"))


class ConfigProfilesWidget(Static):
    """Configuration profiles management widget."""
    
    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.profiles = self._load_profiles()
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Configuration Profiles", classes="section-title")
            with Horizontal():
                yield Select(
                    [(name, name) for name in self.profiles.keys()] + [("Create New", "new")],
                    value=list(self.profiles.keys())[0] if self.profiles else "new",
                    id="profile-select"
                )
                yield Button("Load", variant="primary", id="load-profile")
                yield Button("Save As...", variant="success", id="save-profile")
                yield Button("Delete", variant="error", id="delete-profile")
    
    def _load_profiles(self) -> dict:
        """Load configuration profiles from disk."""
        # For now, return some example profiles
        return {
            "Default": Config.default(),
            "Quick Scan": Config.default(),
            "Deep Analysis": Config.default(),
            "CI/CD Pipeline": Config.default()
        }


class ScannerConfigWidget(Static):
    """Advanced scanner configuration widget."""
    
    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Scanner Configuration", classes="section-title")
            yield Input(placeholder="Search scanners...", id="scanner-search")
            
            # Create a table-like layout for scanners
            with Vertical():
                # Header
                with Horizontal(classes="scanner-header"):
                    yield Static("Scanner", classes="col-scanner")
                    yield Static("Status", classes="col-status")
                    yield Static("Threshold", classes="col-threshold")
                    yield Static("Options", classes="col-options")
                
                yield Rule()
                
                # Scanner rows
                for scanner_name, scanner_config in self.config.scanners.items():
                    with Horizontal(classes="scanner-row"):
                        yield Static(f"🔍 {scanner_name.title()}", classes="col-scanner")
                        yield Switch(
                            value=scanner_config.enabled,
                            id=f"switch-{scanner_name}"
                        )
                        yield Select(
                            [("Low", "low"), ("Medium", "medium"), ("High", "high"), ("Critical", "critical")],
                            value=scanner_config.severity_threshold,
                            id=f"threshold-{scanner_name}"
                        )
                        yield Button("Configure", id=f"config-{scanner_name}")
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle scanner enable/disable."""
        if event.switch.id and event.switch.id.startswith("switch-"):
            scanner_name = event.switch.id.replace("switch-", "")
            if scanner_name in self.config.scanners:
                self.config.scanners[scanner_name].enabled = event.value
                self.app.call_later(self._update_parent_config)
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle threshold changes."""
        if event.select.id and event.select.id.startswith("threshold-"):
            scanner_name = event.select.id.replace("threshold-", "")
            if scanner_name in self.config.scanners:
                self.config.scanners[scanner_name].severity_threshold = event.value
                self.app.call_later(self._update_parent_config)
    
    def _update_parent_config(self) -> None:
        """Notify parent of config changes."""
        if hasattr(self.app, '_on_config_changed'):
            self.app._on_config_changed()


class EnvironmentConfigWidget(Static):
    """Environment and runtime configuration widget."""
    
    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Runtime Environment", classes="section-title")
            
            # Docker Configuration
            with Collapsible(collapsed=False, title="🐳 Docker Settings"):
                with Vertical():
                    with Horizontal():
                        yield Label("Use Docker:")
                        yield Switch(value=self.config.use_docker, id="docker-enabled")
                    
                    with Horizontal():
                        yield Label("Timeout (seconds):")
                        yield Input(
                            value=str(self.config.docker_timeout),
                            placeholder="300",
                            id="docker-timeout"
                        )
            
            # Path Configuration
            with Collapsible(collapsed=False, title="📁 Path Settings"):
                with Vertical():
                    with Horizontal():
                        yield Label("Include Hidden Files:")
                        yield Switch(value=self.config.include_hidden, id="include-hidden")
                    
                    yield Label("Exclude Patterns:")
                    for i, pattern in enumerate(self.config.exclude_paths):
                        with Horizontal():
                            yield Input(value=pattern, id=f"exclude-{i}")
                            yield Button("✖", classes="remove-btn", id=f"remove-{i}")
                    
                    yield Button("+ Add Pattern", variant="primary", id="add-exclude")
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes."""
        if event.switch.id == "docker-enabled":
            self.config.use_docker = event.value
        elif event.switch.id == "include-hidden":
            self.config.include_hidden = event.value
        self.app.call_later(self._update_parent_config)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "docker-timeout":
            try:
                self.config.docker_timeout = int(event.value)
                self.app.call_later(self._update_parent_config)
            except ValueError:
                pass
    
    def _update_parent_config(self) -> None:
        """Notify parent of config changes."""
        if hasattr(self.app, '_on_config_changed'):
            self.app._on_config_changed()


class OutputConfigWidget(Static):
    """Output and reporting configuration widget."""
    
    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Output & Reporting", classes="section-title")
            
            with Horizontal():
                with Vertical(classes="output-column"):
                    yield Label("Output Format:")
                    yield RadioSet(
                        "JSON", "YAML", "XML", "SARIF", "CSV",
                        id="output-format"
                    )
                
                with Vertical(classes="output-column"):
                    yield Label("Report Options:")
                    yield Checkbox("Include Passed Tests", value=self.config.output.include_passed, id="include-passed")
                    yield Checkbox("Group by Severity", value=self.config.output.group_by_severity, id="group-severity")
                    yield Checkbox("Detailed Descriptions", value=True, id="detailed-desc")
                    yield Checkbox("Include Remediation", value=True, id="include-remediation")
            
            with Horizontal():
                yield Label("Output File:")
                yield Input(
                    value=self.config.output.file or "",
                    placeholder="audithound-report.json",
                    id="output-file"
                )
                yield Button("Browse...", id="browse-output")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        if event.checkbox.id == "include-passed":
            self.config.output.include_passed = event.value
        elif event.checkbox.id == "group-severity":
            self.config.output.group_by_severity = event.value
        self.app.call_later(self._update_parent_config)
    
    def _update_parent_config(self) -> None:
        """Notify parent of config changes."""
        if hasattr(self.app, '_on_config_changed'):
            self.app._on_config_changed()


class ConfigurationTab(Static):
    """Professional configuration tab with organized sections."""
    
    def __init__(self, config: Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        with Vertical():
            # Configuration header with actions
            with Horizontal(classes="config-header"):
                yield Static("⚙️ Configuration", classes="tab-title")
                with Horizontal(classes="config-actions"):
                    yield Button("💾 Save", variant="primary", id="save-all-config")
                    yield Button("↻ Reload", variant="default", id="reload-config")
                    yield Button("🔄 Validate", variant="success", id="validate-config")
            
            yield Rule()
            
            # Configuration sections
            with Horizontal():
                # Left column
                with Vertical(classes="config-left"):
                    yield ConfigProfilesWidget(self.config)
                    yield Rule()
                    yield EnvironmentConfigWidget(self.config)
                
                # Right column
                with Vertical(classes="config-right"):
                    yield ScannerConfigWidget(self.config)
                    yield Rule()
                    yield OutputConfigWidget(self.config)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle configuration actions."""
        if event.button.id == "save-all-config":
            self._save_configuration()
        elif event.button.id == "reload-config":
            self._reload_configuration()
        elif event.button.id == "validate-config":
            self._validate_configuration()
    
    def _save_configuration(self) -> None:
        """Save current configuration to file."""
        try:
            config_path = Path("audithound.yaml")
            self.config.save(config_path)
            self.app.notify(f"✅ Configuration saved to {config_path}", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Failed to save configuration: {str(e)}", severity="error")
    
    def _reload_configuration(self) -> None:
        """Reload configuration from file."""
        try:
            config_path = Path("audithound.yaml")
            if config_path.exists():
                new_config = Config.load(config_path)
                self.config.__dict__.update(new_config.__dict__)
                self.app.notify("✅ Configuration reloaded", severity="information")
            else:
                self.app.notify("⚠️ No configuration file found", severity="warning")
        except Exception as e:
            self.app.notify(f"❌ Failed to reload configuration: {str(e)}", severity="error")
    
    def _validate_configuration(self) -> None:
        """Validate current configuration."""
        try:
            # Basic validation logic
            issues = []
            
            if not any(scanner.enabled for scanner in self.config.scanners.values()):
                issues.append("No scanners are enabled")
            
            if self.config.docker_timeout <= 0:
                issues.append("Docker timeout must be positive")
            
            if issues:
                self.app.notify(f"⚠️ Configuration issues: {', '.join(issues)}", severity="warning")
            else:
                self.app.notify("✅ Configuration is valid", severity="information")
        except Exception as e:
            self.app.notify(f"❌ Validation failed: {str(e)}", severity="error")


class AuditHoundTUI(App):
    """Main TUI application for AuditHound."""
    
    CSS = """
    /* Main layout */
    .summary-panel {
        width: 50%;
        margin: 1;
        padding: 1;
        border: solid $primary;
    }
    
    .results-panel {
        width: 50%;
        margin: 1;
        padding: 1;
    }
    
    /* Tab styling */
    Tabs {
        dock: top;
    }
    
    TabPane {
        padding: 1;
    }
    
    /* Configuration tab styling */
    .tab-title {
        text-style: bold;
        color: $accent;
    }
    
    .section-title {
        text-style: bold;
        color: $primary;
        background: $surface;
        padding: 1;
        margin-bottom: 1;
    }
    
    .config-header {
        align: center middle;
        height: 5;
        background: $surface;
        margin-bottom: 1;
    }
    
    .config-actions {
        align: right middle;
    }
    
    .config-left, .config-right {
        width: 50%;
        margin: 0 1;
        padding: 1;
    }
    
    /* Scanner table styling */
    .scanner-header {
        background: $primary;
        color: $text;
        text-style: bold;
        height: 3;
        padding: 1;
    }
    
    .scanner-row {
        height: 3;
        padding: 0 1;
        border-bottom: solid $accent;
    }
    
    .col-scanner { width: 30%; }
    .col-status { width: 20%; }
    .col-threshold { width: 25%; }
    .col-options { width: 25%; }
    
    /* Output configuration */
    .output-column {
        width: 50%;
        margin: 0 2;
    }
    
    /* Form controls */
    Input {
        margin: 0 1;
        width: auto;
    }
    
    Select {
        margin: 0 1;
        width: auto;
    }
    
    Switch {
        margin: 0 1;
    }
    
    Button {
        margin: 0 1;
    }
    
    .remove-btn {
        background: $error;
        color: $text;
        width: 4;
    }
    
    /* Collapsible sections */
    Collapsible {
        border: solid $primary;
        margin: 1 0;
    }
    
    Collapsible > Contents {
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "scan", "Start Scan"),
        Binding("r", "refresh", "Refresh Results"),
        Binding("e", "export", "Export Results"),
        Binding("c", "focus_config", "Configuration"),
        Binding("1", "focus_dashboard", "Dashboard"),
        Binding("2", "focus_results", "Results"),
        Binding("3", "focus_config", "Configuration"),
        Binding("ctrl+s", "save_config", "Save Config"),
        Binding("f5", "reload_config", "Reload Config"),
    ]
    
    def __init__(self, target: str, config: Optional[Config] = None, 
                 config_file: Optional[Path] = None, output: Optional[Path] = None, tools: Optional[List[str]] = None):
        super().__init__()
        self.target = target
        self.config_file = config_file
        self.output = output
        self.tools = tools
        self.results = None
        
        # Use provided config or load from file
        self.config = config if config is not None else Config.load(config_file)
        self.scanner = SecurityScanner(self.config)
    
    def compose(self) -> ComposeResult:
        """Create the professional TUI layout with tabs."""
        yield Header()
        
        with TabbedContent(initial="dashboard"):
            # Dashboard Tab
            with TabPane("🏠 Dashboard", id="dashboard"):
                with Vertical():
                    # Quick status overview
                    with Horizontal():
                        yield Static("🎯 Target", classes="summary-panel")
                        yield Static(f"📁 {self.target}", classes="summary-panel")
                    
                    with Horizontal():
                        yield Static("⚡ Quick Actions", classes="summary-panel")
                        with Vertical(classes="summary-panel"):
                            yield Button("🚀 Start Scan", variant="primary", id="quick-scan")
                            yield Button("📤 Export Results", variant="default", id="quick-export")
                            yield Button("⚙️ Configure", variant="default", id="quick-config")
                    
                    # Recent activity or scan status
                    yield Static("📊 Scan Status", classes="section-title")
                    yield Static("No recent scans. Press 's' or click 'Start Scan' to begin.", id="scan-status")
            
            # Results Tab
            with TabPane("📊 Results", id="results"):
                with Vertical():
                    with Horizontal():
                        yield SummaryWidget(id="summary-widget", classes="summary-panel")
                        yield Static("Filter & Search", classes="summary-panel")
                    
                    yield Rule()
                    yield ResultsTable(id="results-table")
            
            # Configuration Tab  
            with TabPane("⚙️ Configuration", id="configuration"):
                yield ConfigurationTab(self.config, id="config-tab")
        
        yield Footer()
    
    def _on_config_changed(self) -> None:
        """Handle configuration changes from interactive widget."""
        # Update the scanner instance with new config
        self.scanner = SecurityScanner(self.config)
        self.notify("Configuration updated", timeout=2)
    
    def action_scan(self) -> None:
        """Start a security scan."""
        logger.info("action_scan triggered - user pressed 's'")
        self.push_screen(ScanProgressScreen(self.scanner, self.target, self.tools), self._handle_scan_results)
    
    def action_focus_dashboard(self) -> None:
        """Focus the dashboard tab."""
        self.query_one(TabbedContent).active = "dashboard"
    
    def action_focus_results(self) -> None:
        """Focus the results tab."""
        self.query_one(TabbedContent).active = "results"
    
    def action_focus_config(self) -> None:
        """Focus the configuration tab."""
        self.query_one(TabbedContent).active = "configuration"
    
    def action_save_config(self) -> None:
        """Save configuration using keyboard shortcut."""
        try:
            config_path = Path("audithound.yaml")
            self.config.save(config_path)
            self.notify(f"✅ Configuration saved to {config_path}", severity="information")
        except Exception as e:
            self.notify(f"❌ Failed to save configuration: {str(e)}", severity="error")
    
    def action_reload_config(self) -> None:
        """Reload configuration using keyboard shortcut."""
        try:
            config_path = Path("audithound.yaml")
            if config_path.exists():
                new_config = Config.load(config_path)
                self.config.__dict__.update(new_config.__dict__)
                self.scanner = SecurityScanner(self.config)
                self.notify("✅ Configuration reloaded", severity="information")
            else:
                self.notify("⚠️ No configuration file found", severity="warning")
        except Exception as e:
            self.notify(f"❌ Failed to reload configuration: {str(e)}", severity="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses from dashboard quick actions."""
        if event.button.id == "quick-scan":
            self.action_scan()
        elif event.button.id == "quick-export":
            self.action_export()
        elif event.button.id == "quick-config":
            self.action_focus_config()
    
    def _handle_scan_results(self, results) -> None:
        """Handle scan results returned from modal screen."""
        logger.info(f"_handle_scan_results called with results type: {type(results)}")
        if results:
            logger.info(f"Results received: {results.total_findings} findings")
            self.results = results
            self._update_results_display()
            self.notify(f"✅ Scan completed! Found {results.total_findings} findings.")
            # Switch to results tab to show findings
            self.query_one(TabbedContent).active = "results"
        else:
            logger.warning("No results received from scan modal")
            self.notify("❌ Scan failed or was cancelled.", severity="error")
    
    def action_refresh(self) -> None:
        """Refresh the display."""
        if self.results:
            self._update_results_display()
    
    def action_export(self) -> None:
        """Export results to file."""
        if not self.results:
            self.notify("No results to export", severity="warning")
            return
        
        try:
            output_path = self.output or Path("audithound_results.json")
            self.scanner.export_results(self.results, output_path)
            self.notify(f"Results exported to {output_path}", severity="information")
        except Exception as e:
            self.notify(f"Export failed: {str(e)}", severity="error")
    
    
    def _update_results_display(self) -> None:
        """Update the results display with scan data."""
        logger.info("_update_results_display called")
        if not self.results:
            logger.warning("No results to display")
            return
        
        logger.info(f"Updating display with {self.results.total_findings} findings")
        
        # Create summary text
        summary_text = f"""
📊 Scan Summary
Target: {self.results.target}
Total Findings: {self.results.total_findings}

Severity Breakdown:
  Critical: {self.results.summary.get('critical', 0)}
  High: {self.results.summary.get('high', 0)}
  Medium: {self.results.summary.get('medium', 0)}
  Low: {self.results.summary.get('low', 0)}

Scanners: {len(self.results.results_by_scanner)}
Scan Time: {self.results.scan_time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        try:
            # Update summary widget in results tab
            logger.info("Updating summary widget")
            summary_widget = self.query_one("#summary-widget", SummaryWidget)
            summary_widget.update_summary(self.results)
            
            # Update dashboard status
            status_widget = self.query_one("#scan-status", Static)
            status_widget.update(f"✅ Last scan: {self.results.total_findings} findings found")
            
            # Update results table
            logger.info("Updating results table")
            results_table = self.query_one("#results-table", ResultsTable)
            results_table.populate_results(self.results)
            logger.info("Results display update completed successfully")
            
        except Exception as e:
            logger.error(f"Error updating results display: {e}")
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        logger.info("TUI app mounted - initializing interface")
        self.title = "AuditHound - Security Audit Scanner"
        self.sub_title = f"Target: {self.target}"
        
        # Show welcome message
        self.notify("Welcome to AuditHound! Press 's' to start scanning.")
        logger.info(f"TUI ready for target: {self.target}")
    
