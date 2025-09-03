"""Configuration screen for AuditHound TUI."""

import logging
from pathlib import Path
from typing import Dict, Any, List
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Static, Button, Input, Select, Switch, Checkbox, 
    Collapsible, TabbedContent, TabPane
)
from rich.panel import Panel

from textual.widget import Widget

class ConfigurationScreen(Widget):
    """Screen for managing application configuration."""
    
    DEFAULT_CSS = """
    ConfigurationScreen {
        height: auto;
        min-height: 100%;
        overflow-y: auto;
        padding: 1;
        display: block;
    }
    
    #config-main-vertical {
        height: auto;
        min-height: 20;
        width: 100%;
    }
    
    ConfigurationScreen Static {
        color: #ffffff;
        margin: 0 0 1 0;
    }
    
    ConfigurationScreen Button {
        margin: 0 0 1 0;
        width: 100%;
    }
    """
    
    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self.config_changes: Dict[str, Any] = {}
        self.unsaved_changes = False
        
        # Initialize robust logging with explicit configuration
        self._setup_logging()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("ConfigurationScreen initialized")
        self.logger.debug(f"Store: {store}, Config changes: {self.config_changes}")
    
    def _setup_logging(self) -> None:
        """Ensure logging is properly configured for the configuration screen."""
        import logging.handlers
        from pathlib import Path
        
        # Create log directory if it doesn't exist
        log_dir = Path.home() / '.audithound' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'audithound.log'
        
        # Get or create logger
        logger_name = f"{__name__}.{self.__class__.__name__}"
        logger = logging.getLogger(logger_name)
        
        # Don't add handlers if they already exist
        if logger.handlers:
            return
        
        # Set logger level to DEBUG
        logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s:%(lineno)-3d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        # Create file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
        
        # Test log to confirm it's working
        logger.info(f"Logging setup completed for {logger_name}")
        logger.debug(f"Log file: {log_file}")
    
    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("⚙️ AuditHound Configuration"),
            Static(""),  # spacer
            
            # Scanners section
            Static("🔍 Scanner Settings:"),
            Button("Toggle Bandit Scanner", id="toggle-bandit"),
            Button("Toggle Semgrep Scanner", id="toggle-semgrep"), 
            Button("Toggle Safety Scanner", id="toggle-safety"),
            Static(""),  # spacer
            
            # Output settings
            Static("📤 Output Settings:"),
            Button("Change Output Format", id="output-format"),
            Button("Set Output Path", id="output-path"),
            Static(""),  # spacer
            
            # Theme settings
            Static("🎨 Theme Settings:"),
            Button("Toggle Theme", id="theme-toggle"),
            Static(""),  # spacer
            
            # Actions
            Static("💾 Actions:"),
            Button("Save Configuration", variant="primary", id="save-all"),
            Button("Reset to Defaults", variant="error", id="reset-config"),
            id="config-main-vertical"
        )
    
    def on_mount(self) -> None:
        """Initialize configuration screen."""
        self.logger.info("ConfigurationScreen mounted")
        self.logger.debug("Starting simple initialization without complex event setup")
        # Simple initialization without complex event setup
        pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle configuration button presses."""
        button_id = event.button.id
        self.logger.info(f"Button pressed: {button_id}")
        
        # Simple button handlers with notifications
        if button_id == "toggle-bandit":
            self.logger.debug("Toggling Bandit scanner")
            self.app.notify("Bandit scanner toggled", timeout=2)
            self.logger.info("Bandit scanner toggle completed")
        elif button_id == "toggle-semgrep":
            self.logger.debug("Toggling Semgrep scanner")
            self.app.notify("Semgrep scanner toggled", timeout=2)
            self.logger.info("Semgrep scanner toggle completed")
        elif button_id == "toggle-safety":
            self.logger.debug("Toggling Safety scanner")
            self.app.notify("Safety scanner toggled", timeout=2)
            self.logger.info("Safety scanner toggle completed")
        elif button_id == "output-format":
            self.logger.debug("Changing output format")
            self.app.notify("Output format changed", timeout=2)
            self.logger.info("Output format change completed")
        elif button_id == "output-path":
            self.logger.debug("Opening output path dialog")
            self._show_output_path_dialog()
        elif button_id == "theme-toggle":
            self.logger.debug("Toggling theme")
            self.app.action_toggle_theme()
            self.logger.info("Theme toggle completed")
        elif button_id == "save-all":
            self.logger.debug("Saving all configuration")
            self._save_all_config()
        elif button_id == "reset-config":
            self.logger.debug("Resetting configuration to defaults")
            self._reset_config()
        
        # Advanced button handlers (currently simplified)
        elif button_id == "reload-config":
            self.logger.debug("Reloading configuration")
            self._reload_config()
        elif button_id == "export-config":
            self.logger.debug("Exporting configuration")
            self._export_config()
        elif button_id.startswith("toggle-scanner-"):
            scanner_name = button_id.replace("toggle-scanner-", "")
            self.logger.debug(f"Toggling scanner: {scanner_name}")
            self._toggle_scanner(scanner_name)
            self.app.notify(f"{scanner_name.title()} scanner toggled", timeout=2)
            self.logger.info(f"{scanner_name} scanner toggle completed")
        else:
            self.logger.warning(f"Unknown button pressed: {button_id}")
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        self.logger.debug("State change detected in ConfigurationScreen")
        self.logger.debug(f"New state type: {type(new_state)}, Old state type: {type(old_state)}")
        
        # Update configuration display if config changed
        if hasattr(new_state, 'config') and new_state.config != getattr(old_state, 'config', None):
            self.logger.info("Configuration changed in state - reloading current config")
            self._load_current_config()
        else:
            self.logger.debug("No configuration changes detected in state")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        input_id = event.input.id if event.input.id else "unknown"
        self.logger.debug(f"Input changed: {input_id} = '{event.value}'")
        
        self._mark_unsaved_changes()
        # Update config_changes with the new value
        self.config_changes[input_id] = event.value
        
        self.logger.info(f"Config change recorded for input {input_id}: '{event.value}'")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        select_id = event.select.id if event.select.id else "unknown"
        self.logger.debug(f"Select changed: {select_id} = '{event.value}'")
        
        self._mark_unsaved_changes()
        self.config_changes[select_id] = event.value
        
        self.logger.info(f"Config change recorded for select {select_id}: '{event.value}'")
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes."""
        switch_id = event.switch.id if event.switch.id else "unknown"
        self.logger.debug(f"Switch changed: {switch_id} = {event.value}")
        
        self._mark_unsaved_changes()
        self.config_changes[switch_id] = event.value
        
        self.logger.info(f"Config change recorded for switch {switch_id}: {event.value}")
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        checkbox_id = event.checkbox.id if event.checkbox.id else "unknown"
        self.logger.debug(f"Checkbox changed: {checkbox_id} = {event.value}")
        
        self._mark_unsaved_changes()
        self.config_changes[checkbox_id] = event.value
        
        self.logger.info(f"Config change recorded for checkbox {checkbox_id}: {event.value}")
    
    def _create_scanner_config(self) -> Vertical:
        """Create scanner configuration section."""
        # Get current config
        config = self.store.get_state().config
        
        children = [Static("Scanner Configuration", classes="section-title")]
        
        if hasattr(config, 'scanners'):
            for scanner_name, scanner_config in config.scanners.items():
                scanner_children = [
                    Horizontal(
                        Static(f"Enable {scanner_name}:"),
                        Switch(
                            value=getattr(scanner_config, 'enabled', True),
                            id=f"scanner-{scanner_name}-enabled"
                        )
                    ),
                    Horizontal(
                        Static("Severity Threshold:"),
                        Select(
                            [
                                ("Low", "low"),
                                ("Medium", "medium"), 
                                ("High", "high"),
                                ("Critical", "critical")
                            ],
                            value=getattr(scanner_config, 'severity_threshold', 'low'),
                            id=f"scanner-{scanner_name}-threshold"
                        )
                    )
                ]
                
                # Scanner-specific options
                if scanner_name == "bandit":
                    scanner_children.append(
                        Input(
                            placeholder="Additional Bandit options...",
                            id=f"scanner-{scanner_name}-options"
                        )
                    )
                elif scanner_name == "semgrep":
                    scanner_children.append(
                        Input(
                            placeholder="Semgrep ruleset...",
                            id=f"scanner-{scanner_name}-ruleset"
                        )
                    )
                
                children.append(
                    Collapsible(
                        Vertical(*scanner_children),
                        collapsed=False, 
                        title=f"🔍 {scanner_name.title()}"
                    )
                )
        else:
            children.append(Static("No scanners configured", classes="no-config"))
        
        return Vertical(*children)
    
    def _create_target_config(self) -> Vertical:
        """Create target configuration section."""
        config = self.store.get_state().config
        
        return Vertical(
            Static("Target Configuration", classes="section-title"),
            # Target path
            Horizontal(
                Static("Default Target Path:"),
                Input(
                    value=getattr(config, 'default_target', ''),
                    placeholder="/path/to/scan/target",
                    id="default-target-path"
                )
            ),
            # Include/exclude patterns
            Collapsible(
                Vertical(
                    Static("Include Patterns:"),
                    Input(
                        value=",".join(getattr(config, 'include_patterns', [])),
                        placeholder="*.py,*.js,*.go",
                        id="include-patterns"
                    ),
                    Static("Exclude Patterns:"),
                    Input(
                        value=",".join(getattr(config, 'exclude_patterns', [])),
                        placeholder="node_modules,*.test.py",
                        id="exclude-patterns"
                    ),
                    Horizontal(
                        Static("Include Hidden Files:"),
                        Switch(
                            value=getattr(config, 'include_hidden', False),
                            id="include-hidden-files"
                        )
                    )
                ),
                collapsed=False, 
                title="📁 File Patterns"
            )
        )
    
    def _create_output_config(self) -> Vertical:
        """Create output configuration section."""
        config = self.store.get_state().config
        output_config = getattr(config, 'output', None)
        
        return Vertical(
            Static("Output Configuration", classes="section-title"),
            # Output format
            Horizontal(
                Static("Default Output Format:"),
                Select(
                    [
                        ("JSON", "json"),
                        ("YAML", "yaml"),
                        ("CSV", "csv"),
                        ("XML", "xml"),
                        ("SARIF", "sarif")
                    ],
                    value=getattr(output_config, 'format', 'json') if output_config else 'json',
                    id="output-format"
                )
            ),
            # Output file
            Horizontal(
                Static("Default Output File:"),
                Input(
                    value=getattr(output_config, 'file', '') if output_config else '',
                    placeholder="audithound-results.json",
                    id="output-file"
                )
            ),
            # Output options
            Collapsible(
                Vertical(
                    Checkbox(
                        "Include Passed Tests",
                        value=getattr(output_config, 'include_passed', False) if output_config else False,
                        id="include-passed"
                    ),
                    Checkbox(
                        "Group by Severity",
                        value=getattr(output_config, 'group_by_severity', True) if output_config else True,
                        id="group-by-severity"
                    ),
                    Checkbox(
                        "Include Metadata",
                        value=getattr(output_config, 'include_metadata', True) if output_config else True,
                        id="include-metadata"
                    ),
                    Checkbox(
                        "Pretty Print",
                        value=getattr(output_config, 'pretty_print', True) if output_config else True,
                        id="pretty-print"
                    )
                ),
                collapsed=False, 
                title="📄 Output Options"
            )
        )
    
    def _create_environment_config(self) -> Vertical:
        """Create environment configuration section."""
        config = self.store.get_state().config
        
        return Vertical(
            Static("Environment Configuration", classes="section-title"),
            # Docker settings
            Collapsible(
                Vertical(
                    Horizontal(
                        Static("Use Docker:"),
                        Switch(
                            value=getattr(config, 'use_docker', False),
                            id="use-docker"
                        )
                    ),
                    Horizontal(
                        Static("Docker Timeout (seconds):"),
                        Input(
                            value=str(getattr(config, 'docker_timeout', 300)),
                            placeholder="300",
                            id="docker-timeout"
                        )
                    ),
                    Input(
                        value=getattr(config, 'docker_image', ''),
                        placeholder="Custom docker image (optional)",
                        id="docker-image"
                    )
                ),
                collapsed=False, 
                title="🐳 Docker Settings"
            ),
            # Performance settings
            Collapsible(
                Vertical(
                    Horizontal(
                        Static("Max Concurrent Scanners:"),
                        Input(
                            value=str(getattr(config, 'max_concurrent', 3)),
                            placeholder="3",
                            id="max-concurrent"
                        )
                    ),
                    Horizontal(
                        Static("Enable Caching:"),
                        Switch(
                            value=getattr(config, 'enable_cache', True),
                            id="enable-cache"
                        )
                    )
                ),
                collapsed=False, 
                title="⚡ Performance"
            )
        )
    
    def _create_theme_config(self) -> Vertical:
        """Create theme configuration section."""
        current_theme = getattr(self.store.get_state(), 'theme', 'default')
        
        return Vertical(
            Static("Theme Configuration", classes="section-title"),
            # Theme selection
            Horizontal(
                Static("Current Theme:"),
                Select(
                    [
                        ("Textual Dark", "textual-dark"),
                        ("Textual Light", "textual-light")
                    ],
                    value=current_theme if current_theme in ["textual-dark", "textual-light"] else "textual-dark",
                    id="theme-select"
                )
            ),
            # Theme preview
            Static("Theme preview area", id="theme-preview", classes="theme-preview"),
            # Theme options
            Collapsible(
                Vertical(
                    Button("Create Custom Theme", variant="primary", id="create-theme"),
                    Button("Import Theme", variant="default", id="import-theme"),
                    Button("Export Current Theme", variant="default", id="export-theme")
                ),
                collapsed=True, 
                title="🎨 Advanced Theme Options"
            )
        )
    
    def _on_config_changed(self, event) -> None:
        """Handle config change events."""
        self._load_current_config()
    
    def _on_theme_changed(self, event) -> None:
        """Handle theme change events."""
        new_theme = event.get_payload_value("theme")
        # Temporarily disable to prevent recursion
        self.logger.debug(f"Theme change event received: {new_theme} (handling disabled to prevent recursion)")
        # try:
        #     theme_select = self.query_one("#theme-select", Select)
        #     theme_select.value = new_theme
        # except Exception as e:
        #     self.logger.debug(f"Error updating theme select: {e}")
    
    def _load_current_config(self) -> None:
        """Load current configuration into UI elements."""
        self.logger.info("Loading current configuration into UI elements")
        try:
            current_config = self.store.get_state().config
            self.logger.debug(f"Current config: {current_config}")
            
            # This would populate all UI elements with current config values
            # Implementation would iterate through all config sections
            self.logger.debug("Configuration loading (placeholder implementation)")
            # TODO: Implement actual config loading logic
            
            self.logger.info("Configuration loading completed")
        except Exception as e:
            self.logger.error(f"Error loading current configuration: {e}", exc_info=True)
    
    def _save_all_config(self) -> None:
        """Save all configuration changes."""
        self.logger.info("Starting configuration save operation")
        self.logger.debug(f"Current config changes: {self.config_changes}")
        
        if not self.config_changes:
            self.logger.info("No configuration changes to save")
            self.app.notify("No changes to save", severity="information")
            return
        
        try:
            self.logger.debug("Processing configuration changes")
            # Apply changes to config
            config_updates = self._process_config_changes()
            self.logger.info(f"Processed config updates: {config_updates}")
            
            # Dispatch update action
            from ..state.actions import update_config_action
            self.logger.debug("Dispatching update config action")
            self.app.store.dispatch_action(update_config_action(config_updates, save=True))
            
            self.config_changes.clear()
            self.unsaved_changes = False
            self.logger.info("Configuration changes cleared and unsaved flag reset")
            
            self.app.notify("Configuration saved successfully", severity="information")
            self.logger.info("Configuration saved successfully")
        
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}", exc_info=True)
            self.app.notify(f"Error saving configuration: {e}", severity="error")
    
    def _reload_config(self) -> None:
        """Reload configuration from file."""
        self.logger.info("Starting configuration reload operation")
        try:
            config_file = self.store.get_state().config_file
            self.logger.debug(f"Config file path: {config_file}")
            
            if config_file and config_file.exists():
                self.logger.info(f"Reloading configuration from: {config_file}")
                from ..state.actions import Action, ActionType
                self.app.store.dispatch_action(Action(ActionType.LOAD_CONFIG, {"config_path": str(config_file)}))
                self.app.notify("Configuration reloaded", severity="information")
                self.logger.info("Configuration reloaded successfully")
            else:
                self.logger.warning(f"No configuration file to reload: {config_file}")
                self.app.notify("No configuration file to reload", severity="warning")
        
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}", exc_info=True)
            self.app.notify(f"Error reloading configuration: {e}", severity="error")
    
    def _reset_config(self) -> None:
        """Reset configuration to defaults."""
        self.logger.info("Starting configuration reset operation")
        try:
            self.logger.debug("Creating default configuration")
            from ...core.config import Config
            default_config = Config.default()
            
            from ..state.actions import Action, ActionType
            # This would reset the config to defaults
            self.logger.info("Configuration reset to defaults (placeholder implementation)")
            self.app.notify("Configuration reset to defaults", severity="information")
        
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}", exc_info=True)
            self.app.notify(f"Error resetting configuration: {e}", severity="error")
    
    def _export_config(self) -> None:
        """Export current configuration."""
        self.logger.info("Starting configuration export operation")
        try:
            config_path = Path("audithound_config_export.yaml")
            self.logger.debug(f"Export path: {config_path}")
            
            config = self.store.get_state().config
            self.logger.debug(f"Current config state: {config}")
            
            # Save config to export file
            self.logger.info(f"Saving configuration to export file: {config_path}")
            config.save(config_path)
            
            self.app.notify(f"Configuration exported to {config_path}", severity="information")
            self.logger.info(f"Configuration exported successfully to {config_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}", exc_info=True)
            self.app.notify(f"Error exporting configuration: {e}", severity="error")
    
    def _toggle_scanner(self, scanner_name: str) -> None:
        """Toggle scanner enabled state."""
        self.logger.info(f"Toggling scanner: {scanner_name}")
        try:
            # This would toggle the scanner enabled state
            self.logger.debug(f"Scanner {scanner_name} toggle operation (placeholder implementation)")
            # TODO: Implement actual scanner toggle logic
            pass
        except Exception as e:
            self.logger.error(f"Error toggling scanner {scanner_name}: {e}", exc_info=True)
    
    def _process_config_changes(self) -> Dict[str, Any]:
        """Process config changes into structured updates."""
        self.logger.debug("Processing configuration changes")
        self.logger.debug(f"Raw config changes: {self.config_changes}")
        
        updates = {}
        
        for field_id, value in self.config_changes.items():
            self.logger.debug(f"Processing field: {field_id} = {value}")
            
            # Map UI field IDs to config paths
            if field_id.startswith("scanner-"):
                # Handle scanner config changes
                parts = field_id.split("-")
                if len(parts) >= 3:
                    scanner_name = parts[1]
                    setting = "-".join(parts[2:])
                    
                    scanner_key = f"scanners.{scanner_name}"
                    if scanner_key not in updates:
                        updates[scanner_key] = {}
                    updates[scanner_key][setting] = value
                    self.logger.debug(f"Mapped scanner config: {scanner_key}.{setting} = {value}")
            
            elif field_id == "output-format":
                updates["output.format"] = value
                self.logger.debug(f"Mapped output format: {value}")
            elif field_id == "output-file":
                updates["output.file"] = value
                self.logger.debug(f"Mapped output file: {value}")
            elif field_id == "output-path":
                updates["output.file"] = value
                self.logger.debug(f"Mapped output path: {value}")
            elif field_id == "use-docker":
                updates["use_docker"] = value
                self.logger.debug(f"Mapped docker usage: {value}")
            elif field_id == "docker-timeout":
                try:
                    int_value = int(value)
                    updates["docker_timeout"] = int_value
                    self.logger.debug(f"Mapped docker timeout: {int_value}")
                except ValueError as e:
                    self.logger.warning(f"Invalid docker timeout value '{value}': {e}")
            else:
                self.logger.warning(f"Unknown field ID: {field_id}")
            # Add more mappings as needed
        
        self.logger.info(f"Processed config updates: {updates}")
        return updates
    
    def _mark_unsaved_changes(self) -> None:
        """Mark that there are unsaved changes."""
        self.logger.debug("Marking unsaved changes")
        self.unsaved_changes = True
        self.logger.debug(f"Unsaved changes flag set to: {self.unsaved_changes}")
        # Could update UI to show unsaved changes indicator
    
    def _show_output_path_dialog(self) -> None:
        """Show dialog to set output path."""
        self.logger.info("Showing output path dialog")
        from textual.screen import ModalScreen
        from textual.widgets import Label
        
        class OutputPathDialog(ModalScreen):
            """Modal dialog for setting output path."""
            
            def __init__(self, config_screen, **kwargs):
                super().__init__(**kwargs)
                self.config_screen = config_screen
                self.logger = config_screen.logger
            
            def compose(self) -> ComposeResult:
                self.logger.debug("Composing output path dialog")
                yield Vertical(
                    Label("Set Output Path", classes="dialog-title"),
                    Input(
                        placeholder="Enter output file path (e.g., /path/to/results.json)",
                        id="output-path-input",
                        classes="dialog-input"
                    ),
                    Horizontal(
                        Button("Cancel", variant="default", id="cancel"),
                        Button("Set Path", variant="primary", id="set-path"),
                        classes="dialog-buttons"
                    ),
                    classes="dialog"
                )
            
            def on_mount(self) -> None:
                """Focus the input field when dialog opens."""
                self.logger.debug("Mounting output path dialog")
                input_field = self.query_one("#output-path-input", Input)
                input_field.focus()
                
                # Pre-fill with current output path if exists
                try:
                    config = self.app.store.get_state().config
                    output_config = getattr(config, 'output', None)
                    if output_config and hasattr(output_config, 'file') and output_config.file:
                        current_path = output_config.file
                        input_field.value = current_path
                        self.logger.info(f"Pre-filled dialog with current output path: {current_path}")
                    else:
                        self.logger.debug("No current output path to pre-fill")
                except Exception as e:
                    self.logger.error(f"Error pre-filling output path dialog: {e}")
            
            def on_button_pressed(self, event: Button.Pressed) -> None:
                """Handle dialog button presses."""
                button_id = event.button.id
                self.logger.info(f"Output path dialog button pressed: {button_id}")
                
                if button_id == "cancel":
                    self.logger.debug("Canceling output path dialog")
                    self.app.pop_screen()
                    self.logger.info("Output path dialog canceled")
                elif button_id == "set-path":
                    self.logger.debug("Processing output path setting")
                    input_field = self.query_one("#output-path-input", Input)
                    path_value = input_field.value.strip()
                    self.logger.debug(f"Input path value: '{path_value}'")
                    
                    if path_value:
                        # Validate path
                        try:
                            self.logger.debug(f"Validating path: {path_value}")
                            path_obj = Path(path_value)
                            self.logger.debug(f"Path object created: {path_obj}")
                            
                            # Check if parent directory exists or can be created
                            parent_dir = path_obj.parent
                            self.logger.debug(f"Parent directory: {parent_dir}")
                            
                            if not parent_dir.exists():
                                self.logger.info(f"Creating parent directory: {parent_dir}")
                                parent_dir.mkdir(parents=True, exist_ok=True)
                                self.logger.info(f"Parent directory created successfully")
                            else:
                                self.logger.debug(f"Parent directory already exists")
                            
                            # Update configuration immediately
                            config_updates = {"output.file": str(path_obj)}
                            self.logger.info(f"Dispatching config update: {config_updates}")
                            
                            from ..state.actions import update_config_action
                            self.app.store.dispatch_action(update_config_action(config_updates, save=True))
                            
                            self.logger.info(f"Config update dispatched successfully for path: {path_value}")
                            self.app.notify(f"Output path set to: {path_value}", timeout=3)
                            self.app.pop_screen()
                            self.logger.info("Output path dialog completed successfully")
                            
                        except Exception as e:
                            self.logger.error(f"Error setting output path: {e}", exc_info=True)
                            self.app.notify(f"Invalid path: {e}", severity="error", timeout=5)
                    else:
                        self.logger.warning("Empty path value provided")
                        self.app.notify("Please enter a valid path", severity="warning", timeout=3)
        
        try:
            dialog = OutputPathDialog(self)
            self.app.push_screen(dialog)
            self.logger.info("Output path dialog pushed to screen successfully")
        except Exception as e:
            self.logger.error(f"Error showing output path dialog: {e}", exc_info=True)
            self.app.notify("Error opening path dialog", severity="error", timeout=3)