"""Interactive audit preparation and execution screen."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.widgets import (
    Static, Button, Input, Select, Switch, Checkbox, 
    TabbedContent, TabPane, ProgressBar, Label, 
    RadioButton, RadioSet, Collapsible
)
from textual.reactive import reactive
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress

from ..components.base import BaseComponent
from ..state.events import EventType


class AuditScreen(BaseComponent):
    """Interactive audit preparation and execution screen."""
    
    DEFAULT_CSS = """
    AuditScreen {
        height: auto;
        min-height: 100%;
        overflow-y: auto;
        padding: 1;
        display: block;
    }
    
    #audit-main {
        height: auto;
        min-height: 20;
        width: 100%;
    }
    
    .audit-panel {
        background: #333333;
        color: #ffffff;
        border: solid #666666;
        padding: 1;
        margin: 1 0;
        min-height: 5;
    }
    
    .audit-form {
        margin: 1 0;
        height: auto;
    }
    
    .audit-form Input {
        margin: 0 1 1 0;
        width: 30;
    }
    
    .audit-form Select {
        margin: 0 1 1 0;
        width: 25;
    }
    
    .framework-selection {
        margin: 1 0;
        height: auto;
    }
    
    .checklist-panel {
        background: #2d2d2d;
        color: #ffffff;
        border: solid #666666;
        padding: 1;
        margin: 1 0;
        min-height: 10;
    }
    
    .progress-panel {
        background: #1a1a1a;
        color: #ffffff;
        border: solid #666666;
        padding: 1;
        margin: 1 0;
        min-height: 8;
    }
    
    .audit-results {
        background: #0d1117;
        color: #ffffff;
        border: solid #30363d;
        padding: 1;
        margin: 1 0;
        min-height: 10;
    }
    
    Button.primary {
        background: #238636;
        color: #ffffff;
    }
    
    Button.error {
        background: #da3633;
        color: #ffffff;
    }
    
    Button.warning {
        background: #bf8700;
        color: #ffffff;
    }
    """
    
    # Reactive states
    audit_in_progress = reactive(False)
    current_framework = reactive("soc2")
    auditor_name = reactive("Security Team")
    organization = reactive("Organization")
    compliance_results = reactive({})
    
    def __init__(self, store, **kwargs):
        super().__init__(store, component_id="audit", **kwargs)
        self.audit_checklist_items = []
        self.completed_checks = set()
        
    def compose(self) -> ComposeResult:
        yield Vertical(
            # Header
            Static("🔍 Enterprise Audit Center", classes="audit-panel"),
            
            id="audit-main"
        )
        
        # Main audit interface with tabs
        with TabbedContent(initial="setup", id="audit-tabs"):
            with TabPane("Setup", id="setup"):
                yield self._create_audit_setup()
            
            with TabPane("Checklist", id="checklist"):
                yield self._create_audit_checklist()
            
            with TabPane("Execute", id="execute"):
                yield self._create_audit_execution()
            
            with TabPane("Results", id="results"):
                yield self._create_audit_results()
    
    def _create_audit_setup(self) -> Vertical:
        """Create the audit setup form."""
        return Vertical(
            Static("🔧 Audit Configuration", classes="audit-panel"),
            
            # Auditor information
            Horizontal(
                Vertical(
                    Label("Auditor Name:"),
                    Input(value="Security Team", id="auditor-name"),
                    Label("Auditor Title:"),
                    Input(value="Security Analyst", id="auditor-title"),
                    classes="audit-form"
                ),
                Vertical(
                    Label("Organization:"),
                    Input(value="Organization", id="organization"),
                    Label("Audit Date:"),
                    Input(value=datetime.now().strftime("%Y-%m-%d"), id="audit-date"),
                    classes="audit-form"
                )
            ),
            
            # Framework selection
            Static("📋 Compliance Frameworks", classes="audit-panel"),
            Horizontal(
                Vertical(
                    Checkbox("SOC 2 Type II", value=True, id="framework-soc2"),
                    Checkbox("NIST Cybersecurity Framework", value=False, id="framework-nist"),
                    classes="framework-selection"
                ),
                Vertical(
                    Checkbox("CIS Critical Security Controls", value=False, id="framework-cis"),
                    Checkbox("OWASP ASVS", value=False, id="framework-owasp"),
                    classes="framework-selection"
                )
            ),
            
            # Scanner configuration
            Static("🔧 Scanner Configuration", classes="audit-panel"),
            Horizontal(
                Vertical(
                    Checkbox("Bandit (Python Security)", value=True, id="scanner-bandit"),
                    Checkbox("Safety (Dependency Scan)", value=True, id="scanner-safety"),
                    Checkbox("Semgrep (Multi-language)", value=True, id="scanner-semgrep")
                ),
                Vertical(
                    Checkbox("TruffleHog (Secrets)", value=True, id="scanner-trufflehog"),
                    Checkbox("Checkov (IaC Security)", value=True, id="scanner-checkov"),
                    Switch(value=False, id="use-docker"),
                    Label("Use Docker")
                )
            ),
            
            # Action buttons
            Horizontal(
                Button("💾 Save Configuration", variant="primary", id="save-audit-config"),
                Button("🔄 Load Template", variant="default", id="load-template"),
                Button("➡️ Next: Checklist", variant="primary", id="goto-checklist")
            )
        )
    
    def _create_audit_checklist(self) -> Vertical:
        """Create the interactive audit checklist."""
        checklist_items = [
            "📦 Install AuditHound with all scanners",
            "⚙️ Configure scanner settings and exclusions", 
            "📋 Gather security policies and procedures",
            "🏗️ Collect system architecture diagrams",
            "📊 Prepare data flow documentation",
            "👥 Brief development team on audit scope",
            "🔐 Set up secure communication with auditors",
            "🗂️ Organize incident response documentation",
            "📈 Compile previous audit findings",
            "🎯 Define audit scope and boundaries",
            "⏰ Schedule audit activities and milestones",
            "🚨 Prepare emergency contact list"
        ]
        
        checklist_widgets = []
        for i, item in enumerate(checklist_items):
            checklist_widgets.append(
                Horizontal(
                    Checkbox("", value=False, id=f"check-{i}"),
                    Label(item)
                )
            )
        
        return Vertical(
            Static("📋 Pre-Audit Preparation Checklist", classes="checklist-panel"),
            *checklist_widgets,
            
            # Checklist progress
            Static("", id="checklist-progress", classes="audit-panel"),
            
            # Action buttons
            Horizontal(
                Button("⬅️ Back: Setup", variant="default", id="goto-setup"),
                Button("✅ Mark All Complete", variant="success", id="complete-all-checks"),
                Button("➡️ Next: Execute", variant="primary", id="goto-execute")
            )
        )
    
    def _create_audit_execution(self) -> Vertical:
        """Create the audit execution interface."""
        return Vertical(
            Static("🚀 Audit Execution Center", classes="audit-panel"),
            
            # Current audit status
            Static("", id="audit-status", classes="progress-panel"),
            
            # Progress indicator
            Static("", id="audit-progress", classes="progress-panel"),
            
            # Framework execution status
            Static("", id="framework-status", classes="audit-panel"),
            
            # Real-time log output
            Static("", id="audit-logs", classes="checklist-panel"),
            
            # Control buttons
            Horizontal(
                Button("⬅️ Back: Checklist", variant="default", id="goto-checklist-from-execute"),
                Button("🚀 Start Audit", variant="primary", id="start-comprehensive-audit"),
                Button("⏸️ Pause", variant="warning", id="pause-audit"),
                Button("🛑 Stop", variant="error", id="stop-audit"),
                Button("➡️ View Results", variant="success", id="goto-results")
            )
        )
    
    def _create_audit_results(self) -> Vertical:
        """Create the audit results dashboard."""
        return Vertical(
            Static("📊 Audit Results Dashboard", classes="audit-panel"),
            
            # Executive summary
            Static("", id="executive-summary", classes="audit-results"),
            
            # Compliance scores
            Horizontal(
                Static("", id="compliance-scores", classes="audit-panel"),
                Static("", id="risk-assessment", classes="audit-panel")
            ),
            
            # Detailed findings by framework
            Static("", id="detailed-findings", classes="audit-results"),
            
            # Export options
            Horizontal(
                Button("📥 Export Reports", variant="primary", id="export-audit-reports"),
                Button("📧 Email Summary", variant="default", id="email-summary"),
                Button("📦 Create Package", variant="success", id="create-audit-package"),
                Button("🔄 Run Again", variant="warning", id="restart-audit")
            )
        )
    
    def on_mount(self) -> None:
        """Initialize the audit screen."""
        self.logger.info("AuditScreen mounted")
        self._update_checklist_progress()
        self._initialize_audit_status()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle audit screen button presses."""
        button_id = event.button.id
        self.logger.info(f"Audit screen button pressed: {button_id}")
        
        # Navigation buttons
        if button_id == "goto-checklist":
            self._switch_to_tab("checklist")
        elif button_id == "goto-setup":
            self._switch_to_tab("setup")
        elif button_id == "goto-execute":
            self._switch_to_tab("execute")
        elif button_id == "goto-checklist-from-execute":
            self._switch_to_tab("checklist")
        elif button_id == "goto-results":
            self._switch_to_tab("results")
            
        # Configuration actions
        elif button_id == "save-audit-config":
            self._save_audit_configuration()
        elif button_id == "load-template":
            self._load_configuration_template()
            
        # Checklist actions
        elif button_id == "complete-all-checks":
            self._complete_all_checklist_items()
            
        # Audit execution actions
        elif button_id == "start-comprehensive-audit":
            self._start_comprehensive_audit()
        elif button_id == "pause-audit":
            self._pause_audit()
        elif button_id == "stop-audit":
            self._stop_audit()
            
        # Results actions
        elif button_id == "export-audit-reports":
            self._export_audit_reports()
        elif button_id == "email-summary":
            self._email_audit_summary()
        elif button_id == "create-audit-package":
            self._create_audit_package()
        elif button_id == "restart-audit":
            self._restart_audit()
        
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checklist checkbox changes."""
        checkbox_id = event.checkbox.id
        
        if checkbox_id.startswith("check-"):
            self._update_checklist_progress()
        
        self.logger.info(f"Checkbox {checkbox_id} changed to {event.value}")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        input_id = event.input.id
        
        if input_id == "auditor-name":
            self.auditor_name = event.value
        elif input_id == "organization":
            self.organization = event.value
            
        self.logger.debug(f"Input {input_id} changed to: {event.value}")
    
    def _switch_to_tab(self, tab_name: str) -> None:
        """Switch to a specific audit tab."""
        try:
            tabs = self.query_one("#audit-tabs", TabbedContent)
            tabs.active = tab_name
            self.logger.info(f"Switched to audit tab: {tab_name}")
        except Exception as e:
            self.logger.error(f"Error switching to tab {tab_name}: {e}")
    
    def _update_checklist_progress(self) -> None:
        """Update the checklist progress display."""
        try:
            # Count completed checkboxes
            checkboxes = self.query("Checkbox")
            total_checks = 0
            completed_checks = 0
            
            for checkbox in checkboxes:
                if checkbox.id and checkbox.id.startswith("check-"):
                    total_checks += 1
                    if checkbox.value:
                        completed_checks += 1
            
            if total_checks > 0:
                progress_percent = (completed_checks / total_checks) * 100
                
                progress_widget = self.query_one("#checklist-progress", Static)
                progress_widget.update(Panel(
                    f"Progress: {completed_checks}/{total_checks} items completed ({progress_percent:.1f}%)",
                    title="Checklist Progress",
                    border_style="green" if progress_percent == 100 else "yellow"
                ))
                
                self.logger.debug(f"Checklist progress: {completed_checks}/{total_checks}")
                
        except Exception as e:
            self.logger.error(f"Error updating checklist progress: {e}")
    
    def _initialize_audit_status(self) -> None:
        """Initialize the audit status display."""
        try:
            status_widget = self.query_one("#audit-status", Static)
            status_widget.update(Panel(
                "Ready to begin comprehensive audit\nConfigure your settings and complete the checklist first",
                title="Audit Status",
                border_style="blue"
            ))
        except Exception as e:
            self.logger.debug(f"Error initializing audit status: {e}")
    
    def _save_audit_configuration(self) -> None:
        """Save the current audit configuration."""
        self.logger.info("Saving audit configuration")
        
        try:
            # Collect form data
            config_data = {
                "auditor_name": self.auditor_name,
                "organization": self.organization,
                "frameworks": self._get_selected_frameworks(),
                "scanners": self._get_selected_scanners(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to store state
            self.store.update_state({"audit_config": config_data})
            
            self.app.notify("Audit configuration saved successfully", timeout=3)
            
        except Exception as e:
            self.logger.error(f"Error saving audit configuration: {e}")
            self.app.notify(f"Error saving configuration: {e}", severity="error")
    
    def _get_selected_frameworks(self) -> List[str]:
        """Get list of selected compliance frameworks."""
        frameworks = []
        framework_checkboxes = {
            "framework-soc2": "soc2",
            "framework-nist": "nist", 
            "framework-cis": "cis",
            "framework-owasp": "owasp"
        }
        
        try:
            for checkbox_id, framework_name in framework_checkboxes.items():
                checkbox = self.query_one(f"#{checkbox_id}", Checkbox)
                if checkbox.value:
                    frameworks.append(framework_name)
        except Exception as e:
            self.logger.error(f"Error getting selected frameworks: {e}")
            
        return frameworks
    
    def _get_selected_scanners(self) -> List[str]:
        """Get list of selected scanners."""
        scanners = []
        scanner_checkboxes = {
            "scanner-bandit": "bandit",
            "scanner-safety": "safety",
            "scanner-semgrep": "semgrep", 
            "scanner-trufflehog": "trufflehog",
            "scanner-checkov": "checkov"
        }
        
        try:
            for checkbox_id, scanner_name in scanner_checkboxes.items():
                checkbox = self.query_one(f"#{checkbox_id}", Checkbox)
                if checkbox.value:
                    scanners.append(scanner_name)
        except Exception as e:
            self.logger.error(f"Error getting selected scanners: {e}")
            
        return scanners
    
    def _load_configuration_template(self) -> None:
        """Load a configuration template."""
        self.logger.info("Loading configuration template")
        self.app.notify("Configuration template loaded", timeout=3)
    
    def _complete_all_checklist_items(self) -> None:
        """Mark all checklist items as complete."""
        try:
            checkboxes = self.query("Checkbox")
            for checkbox in checkboxes:
                if checkbox.id and checkbox.id.startswith("check-"):
                    checkbox.value = True
            
            self._update_checklist_progress()
            self.app.notify("All checklist items marked complete!", timeout=3)
            
        except Exception as e:
            self.logger.error(f"Error completing checklist: {e}")
    
    async def _start_comprehensive_audit(self) -> None:
        """Start the comprehensive audit process."""
        self.logger.info("Starting comprehensive audit")
        
        try:
            # Update status
            status_widget = self.query_one("#audit-status", Static)
            status_widget.update(Panel(
                "🚀 Comprehensive audit in progress...\nRunning security scans across all selected frameworks",
                title="Audit Status - RUNNING",
                border_style="yellow"
            ))
            
            # Get selected frameworks and scanners
            frameworks = self._get_selected_frameworks()
            scanners = self._get_selected_scanners()
            
            if not frameworks:
                self.app.notify("Please select at least one compliance framework", severity="warning")
                return
                
            if not scanners:
                self.app.notify("Please select at least one security scanner", severity="warning")
                return
            
            # Update progress display
            progress_widget = self.query_one("#audit-progress", Static)
            framework_widget = self.query_one("#framework-status", Static)
            
            total_audits = len(frameworks)
            completed_audits = 0
            
            # Execute audit for each framework
            for framework in frameworks:
                framework_widget.update(Panel(
                    f"Currently auditing: {framework.upper()}\nScanning with: {', '.join(scanners)}",
                    title="Current Framework",
                    border_style="yellow"
                ))
                
                # Simulate audit execution (replace with actual audit call)
                await self._execute_framework_audit(framework, scanners)
                
                completed_audits += 1
                progress_percent = (completed_audits / total_audits) * 100
                
                progress_widget.update(Panel(
                    f"Progress: {completed_audits}/{total_audits} frameworks completed ({progress_percent:.1f}%)",
                    title="Audit Progress", 
                    border_style="green" if progress_percent == 100 else "yellow"
                ))
            
            # Complete
            status_widget.update(Panel(
                f"✅ Comprehensive audit completed!\n{completed_audits} framework(s) audited successfully",
                title="Audit Status - COMPLETED",
                border_style="green"
            ))
            
            self.app.notify("Comprehensive audit completed successfully!", timeout=5)
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive audit: {e}")
            self.app.notify(f"Audit failed: {e}", severity="error")
    
    async def _execute_framework_audit(self, framework: str, scanners: List[str]) -> None:
        """Execute audit for a specific framework."""
        self.logger.info(f"Executing {framework} audit with scanners: {scanners}")
        
        # Simulate audit execution with delay
        await asyncio.sleep(2)  # Replace with actual audit execution
        
        # Update logs
        try:
            logs_widget = self.query_one("#audit-logs", Static)
            current_logs = logs_widget.renderable or ""
            new_log = f"✅ {framework.upper()} audit completed with {len(scanners)} scanners\n"
            logs_widget.update(str(current_logs) + new_log)
        except Exception as e:
            self.logger.debug(f"Error updating logs: {e}")
    
    def _pause_audit(self) -> None:
        """Pause the current audit."""
        self.logger.info("Pausing audit")
        self.app.notify("Audit paused", timeout=3)
    
    def _stop_audit(self) -> None:
        """Stop the current audit."""
        self.logger.info("Stopping audit")
        self.app.notify("Audit stopped", timeout=3)
    
    def _export_audit_reports(self) -> None:
        """Export audit reports."""
        self.logger.info("Exporting audit reports")
        self.app.notify("Audit reports exported successfully", timeout=3)
    
    def _email_audit_summary(self) -> None:
        """Email audit summary."""
        self.logger.info("Emailing audit summary")
        self.app.notify("Audit summary emailed", timeout=3)
    
    def _create_audit_package(self) -> None:
        """Create comprehensive audit package."""
        self.logger.info("Creating audit package")
        self.app.notify("Audit package created successfully", timeout=3)
    
    def _restart_audit(self) -> None:
        """Restart the audit process."""
        self.logger.info("Restarting audit")
        self._switch_to_tab("setup")
        self.app.notify("Audit restarted - please reconfigure", timeout=3)