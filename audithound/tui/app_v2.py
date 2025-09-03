"""Production-grade TUI Application for AuditHound."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, TabbedContent, TabPane, Static
from textual.screen import Screen

from ...core.config import Config
from ...core.scanner import SecurityScanner
from .state.store import AppStore, AppState
from .state.events import EventType, Event
from .state.actions import Action, ActionType, start_scan_action, change_tab_action
from .themes.theme_manager import ThemeManager
from .components.navigation import NavigationBar, CommandPalette, KeyboardShortcutManager
from .components.progress import ProgressIndicator, StreamingProgress
from .components.data import FilterableTable
from .screens.dashboard import DashboardScreen
from .screens.results import ResultsScreen
from .screens.configuration import ConfigurationScreen
from .services.scan_service import ScanService
from .services.persistence_service import PersistenceService


class ProductionTUI(App):
    """Production-grade TUI for AuditHound with advanced features."""
    
    CSS_PATH = None  # Will be set dynamically by theme manager
    
    # Global keyboard bindings
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+shift+p", "command_palette", "Command Palette", priority=True),
        Binding("f1", "help", "Help", priority=True),
        Binding("ctrl+1", "focus_dashboard", "Dashboard"),
        Binding("ctrl+2", "focus_results", "Results"),
        Binding("ctrl+3", "focus_configuration", "Configuration"),
        Binding("f5", "start_scan", "Start Scan"),
        Binding("ctrl+shift+t", "toggle_theme", "Toggle Theme"),
        Binding("ctrl+e", "export_results", "Export Results"),
    ]
    
    def __init__(
        self,
        target: str,
        config: Optional[Config] = None,
        config_file: Optional[Path] = None,
        output: Optional[Path] = None,
        tools: Optional[List[str]] = None,
        theme: str = "default"
    ):
        super().__init__()
        
        # Core configuration
        self.target = target
        self.config_file = config_file
        self.output = output
        self.tools = tools or []
        
        # Initialize config
        self.config = config if config is not None else Config.load(config_file)
        
        # Initialize state management
        initial_state = AppState(
            config=self.config,
            config_file=config_file,
            scan_target=target,
            scan_tools=tools or [],
            theme=theme
        )
        self.store = AppStore(initial_state)
        
        # Initialize services
        self.scanner_service = ScanService(self.store, self.config)
        self.persistence_service = PersistenceService(self.store)
        
        # Initialize theme management
        self.theme_manager = ThemeManager(self.store)
        self.theme_manager.set_theme(theme)
        self.theme_manager.register_theme_callback(self._on_theme_changed)
        
        # Initialize keyboard shortcuts
        self.shortcut_manager = KeyboardShortcutManager(self)
        
        # Component references
        self._navigation_bar = None
        self._dashboard_screen = None
        self._results_screen = None
        self._configuration_screen = None
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def compose(self) -> ComposeResult:
        """Create the main TUI layout."""
        # Apply current theme CSS
        self.CSS = self.theme_manager.get_theme_css()
        
        yield Header(show_clock=True)
        
        # Navigation bar
        self._navigation_bar = NavigationBar(self.store, component_id="main-nav")
        yield self._navigation_bar
        
        # Main content with tabs
        with TabbedContent(initial="dashboard", id="main-tabs"):
            # Dashboard Tab
            with TabPane("🏠 Dashboard", id="dashboard"):
                self._dashboard_screen = DashboardScreen(self.store)
                yield self._dashboard_screen
            
            # Results Tab
            with TabPane("📊 Results", id="results"):
                self._results_screen = ResultsScreen(self.store)
                yield self._results_screen
            
            # Configuration Tab
            with TabPane("⚙️ Configuration", id="configuration"):
                self._configuration_screen = ConfigurationScreen(self.store)
                yield self._configuration_screen
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application."""
        self.logger.info("Production TUI starting up")
        
        # Set app metadata
        self.title = "AuditHound - Security Audit Scanner"
        self.sub_title = f"Target: {self.target}"
        
        # Setup state event listeners
        self._setup_event_listeners()
        
        # Load persistent data
        self.persistence_service.load_session_data()
        
        # Show welcome notification
        self.notify(
            "Welcome to AuditHound! Press Ctrl+Shift+P for command palette.",
            title="Welcome",
            timeout=5
        )
        
        self.logger.info(f"TUI initialized for target: {self.target}")
    
    def on_unmount(self) -> None:
        """Cleanup when application closes."""
        self.logger.info("Production TUI shutting down")
        
        # Save session data
        self.persistence_service.save_session_data()
        
        # Cleanup services
        if hasattr(self, 'scanner_service'):
            self.scanner_service.cleanup()
    
    # Event listeners and state management
    
    def _setup_event_listeners(self) -> None:
        """Setup application-level event listeners."""
        self.store.listen_to_event(EventType.SCAN_STARTED, self._on_scan_started)
        self.store.listen_to_event(EventType.SCAN_COMPLETED, self._on_scan_completed)
        self.store.listen_to_event(EventType.SCAN_FAILED, self._on_scan_failed)
        self.store.listen_to_event(EventType.ERROR_OCCURRED, self._on_error_occurred)
        self.store.listen_to_event(EventType.TAB_CHANGED, self._on_tab_changed)
    
    def _on_scan_started(self, event: Event) -> None:
        """Handle scan start events."""
        target = event.get_payload_value("target")
        tools = event.get_payload_value("tools", [])
        
        self.notify(
            f"Starting scan of {target} with {len(tools)} tools",
            title="Scan Started",
            severity="information"
        )
        
        # Switch to results tab to show progress
        self.action_focus_results()
    
    def _on_scan_completed(self, event: Event) -> None:
        """Handle scan completion events."""
        results = event.get_payload_value("results")
        
        if results and hasattr(results, 'total_findings'):
            finding_count = results.total_findings
            if finding_count > 0:
                severity = "warning" if finding_count < 10 else "error"
                self.notify(
                    f"Scan completed: {finding_count} findings discovered",
                    title="Scan Complete",
                    severity=severity,
                    timeout=10
                )
            else:
                self.notify(
                    "Scan completed: No security issues found",
                    title="Scan Complete",
                    severity="information"
                )
        else:
            self.notify(
                "Scan completed successfully",
                title="Scan Complete",
                severity="information"
            )
    
    def _on_scan_failed(self, event: Event) -> None:
        """Handle scan failure events."""
        error = event.get_payload_value("error", "Unknown error")
        
        self.notify(
            f"Scan failed: {error}",
            title="Scan Failed",
            severity="error",
            timeout=15
        )
    
    def _on_error_occurred(self, event: Event) -> None:
        """Handle application errors."""
        error = event.get_payload_value("error", "Unknown error")
        context = event.get_payload_value("context", "")
        
        self.notify(
            f"Error{' in ' + context if context else ''}: {error}",
            title="Application Error", 
            severity="error",
            timeout=10
        )
    
    def _on_tab_changed(self, event: Event) -> None:
        """Handle tab change events."""
        new_tab = event.get_payload_value("new_tab")
        old_tab = event.get_payload_value("old_tab")
        
        self.logger.debug(f"Tab changed from {old_tab} to {new_tab}")
    
    def _on_theme_changed(self, new_theme) -> None:
        """Handle theme changes."""
        self.logger.info(f"Theme changed to: {new_theme.name}")
        
        # Apply new CSS
        self.CSS = new_theme.get_css()
        self.refresh_css()
        
        self.notify(
            f"Theme changed to {new_theme.name}",
            title="Theme Updated",
            timeout=3
        )
    
    # Action handlers
    
    def action_command_palette(self) -> None:
        """Open the command palette."""
        self.push_screen(CommandPalette(self.store))
    
    def action_focus_dashboard(self) -> None:
        """Focus the dashboard tab."""
        self._change_tab("dashboard")
    
    def action_focus_results(self) -> None:
        """Focus the results tab."""
        self._change_tab("results")
    
    def action_focus_configuration(self) -> None:
        """Focus the configuration tab."""
        self._change_tab("configuration")
    
    def action_start_scan(self) -> None:
        """Start a security scan."""
        if self.store.get_state_value("is_scanning", False):
            self.notify(
                "A scan is already in progress",
                title="Scan In Progress",
                severity="warning"
            )
            return
        
        # Start scan with current settings
        target = self.store.get_state_value("scan_target", self.target)
        tools = self.store.get_state_value("scan_tools", self.tools)
        
        self.store.dispatch_action(start_scan_action(target, tools))
    
    def action_toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        current_theme = self.store.get_state_value("theme", "default")
        new_theme = "light" if current_theme == "dark" else "dark"
        self.theme_manager.set_theme(new_theme)
    
    def action_export_results(self) -> None:
        """Export current results."""
        if not self.store.get_state_value("current_results"):
            self.notify(
                "No results to export",
                title="Export Failed",
                severity="warning"
            )
            return
        
        # Trigger export action
        from .state.actions import export_results_action
        output_path = self.output or Path("audithound_results.json")
        action = export_results_action("json", output_path)
        self.store.dispatch_action(action)
    
    def action_help(self) -> None:
        """Show help information."""
        # Would show help modal with keyboard shortcuts
        shortcuts = self.shortcut_manager.get_shortcut_help()
        help_text = "Keyboard Shortcuts:\n\n" + "\n".join(
            f"{key}: {desc}" for key, desc in shortcuts[:10]  # Show first 10
        )
        
        self.notify(
            help_text,
            title="Help - Keyboard Shortcuts",
            timeout=10
        )
    
    # Tab management
    
    def _change_tab(self, tab_id: str) -> None:
        """Change to a specific tab."""
        try:
            tabs = self.query_one("#main-tabs", TabbedContent)
            old_tab = tabs.active
            tabs.active = tab_id
            
            # Dispatch tab change action
            if old_tab != tab_id:
                self.store.dispatch_action(change_tab_action(tab_id))
        
        except Exception as e:
            self.logger.error(f"Error changing tab to {tab_id}: {e}")
    
    # Service integration
    
    def get_scanner_service(self) -> ScanService:
        """Get the scanner service instance."""
        return self.scanner_service
    
    def get_persistence_service(self) -> PersistenceService:
        """Get the persistence service instance."""
        return self.persistence_service
    
    def get_theme_manager(self) -> ThemeManager:
        """Get the theme manager instance."""
        return self.theme_manager
    
    # Utility methods
    
    def refresh_css(self) -> None:
        """Refresh CSS styling."""
        # Force CSS refresh - implementation depends on Textual version
        try:
            self.stylesheet.reparse()
        except AttributeError:
            # Fallback for older Textual versions
            pass
    
    def get_application_state(self) -> Dict[str, Any]:
        """Get current application state for debugging."""
        return {
            "target": self.target,
            "theme": self.store.get_state_value("theme"),
            "current_tab": self.store.get_state_value("current_tab"),
            "is_scanning": self.store.get_state_value("is_scanning"),
            "has_results": self.store.get_state_value("current_results") is not None,
            "config_file": str(self.config_file) if self.config_file else None
        }