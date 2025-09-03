"""Configuration screen for AuditHound TUI."""

from pathlib import Path
from typing import Dict, Any, List
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Static, Button, Input, Select, Switch, Checkbox, 
    Collapsible, TabbedContent, TabPane
)
from rich.panel import Panel

from ..components.base import BaseComponent
from ..state.events import EventType
from ..state.actions import Action, ActionType


class ConfigurationScreen(BaseComponent):
    """Screen for managing application configuration."""
    
    def __init__(self, store, **kwargs):
        super().__init__(store, component_id="configuration", **kwargs)
        self.config_changes: Dict[str, Any] = {}
        self.unsaved_changes = False
    
    def compose(self) -> ComposeResult:
        with Vertical():
            # Configuration header
            with Horizontal(classes="config-header"):
                yield Static("⚙️ Configuration", classes="tab-title")
                with Horizontal(classes="config-actions"):
                    yield Button("💾 Save All", variant="primary", id="save-all")
                    yield Button("↻ Reload", variant="default", id="reload-config")
                    yield Button("🔄 Reset", variant="error", id="reset-config")
                    yield Button("📤 Export", variant="default", id="export-config")
            
            # Configuration tabs
            with TabbedContent(initial="scanners", id="config-tabs"):
                # Scanner Configuration
                with TabPane("🔍 Scanners", id="scanners"):
                    yield self._create_scanner_config()
                
                # Target Configuration
                with TabPane("🎯 Targets", id="targets"):
                    yield self._create_target_config()
                
                # Output Configuration
                with TabPane("📤 Output", id="output"):
                    yield self._create_output_config()
                
                # Environment Configuration
                with TabPane("🐳 Environment", id="environment"):
                    yield self._create_environment_config()
                
                # Themes Configuration
                with TabPane("🎨 Themes", id="themes"):
                    yield self._create_theme_config()
    
    def _setup_event_listeners(self) -> None:
        """Setup configuration event listeners."""
        self.listen_to_event(EventType.CONFIG_CHANGED, self._on_config_changed)
        # Disabled theme listener to prevent recursion
        # self.listen_to_event(EventType.THEME_CHANGED, self._on_theme_changed)
    
    def on_component_mounted(self) -> None:
        """Initialize configuration screen."""
        self._load_current_config()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        # Update configuration display if config changed
        if hasattr(new_state, 'config') and new_state.config != getattr(old_state, 'config', None):
            self._load_current_config()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle configuration button presses."""
        if event.button.id == "save-all":
            self._save_all_config()
        elif event.button.id == "reload-config":
            self._reload_config()
        elif event.button.id == "reset-config":
            self._reset_config()
        elif event.button.id == "export-config":
            self._export_config()
        elif event.button.id.startswith("toggle-scanner-"):
            scanner_name = event.button.id.replace("toggle-scanner-", "")
            self._toggle_scanner(scanner_name)
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        self._mark_unsaved_changes()
        # Update config_changes with the new value
        self.config_changes[event.input.id] = event.value
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        self._mark_unsaved_changes()
        self.config_changes[event.select.id] = event.value
    
    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch changes."""
        self._mark_unsaved_changes()
        self.config_changes[event.switch.id] = event.value
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        self._mark_unsaved_changes()
        self.config_changes[event.checkbox.id] = event.value
    
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
        # This would populate all UI elements with current config values
        # Implementation would iterate through all config sections
        pass
    
    def _save_all_config(self) -> None:
        """Save all configuration changes."""
        if not self.config_changes:
            self.app.notify("No changes to save", severity="information")
            return
        
        try:
            # Apply changes to config
            config_updates = self._process_config_changes()
            
            # Dispatch update action
            from ..state.actions import update_config_action
            self.dispatch_action(update_config_action(config_updates, save=True))
            
            self.config_changes.clear()
            self.unsaved_changes = False
            
            self.app.notify("Configuration saved successfully", severity="information")
        
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            self.app.notify(f"Error saving configuration: {e}", severity="error")
    
    def _reload_config(self) -> None:
        """Reload configuration from file."""
        try:
            config_file = self.store.get_state().config_file
            if config_file and config_file.exists():
                from ..state.actions import Action, ActionType
                self.dispatch_action(Action(ActionType.LOAD_CONFIG, {"config_path": str(config_file)}))
                self.app.notify("Configuration reloaded", severity="information")
            else:
                self.app.notify("No configuration file to reload", severity="warning")
        
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            self.app.notify(f"Error reloading configuration: {e}", severity="error")
    
    def _reset_config(self) -> None:
        """Reset configuration to defaults."""
        try:
            from ..core.config import Config
            default_config = Config.default()
            
            from ..state.actions import Action, ActionType
            # This would reset the config to defaults
            self.app.notify("Configuration reset to defaults", severity="information")
        
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            self.app.notify(f"Error resetting configuration: {e}", severity="error")
    
    def _export_config(self) -> None:
        """Export current configuration."""
        try:
            config_path = Path("audithound_config_export.yaml")
            config = self.store.get_state().config
            
            # Save config to export file
            config.save(config_path)
            
            self.app.notify(f"Configuration exported to {config_path}", severity="information")
        
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            self.app.notify(f"Error exporting configuration: {e}", severity="error")
    
    def _toggle_scanner(self, scanner_name: str) -> None:
        """Toggle scanner enabled state."""
        # This would toggle the scanner enabled state
        pass
    
    def _process_config_changes(self) -> Dict[str, Any]:
        """Process config changes into structured updates."""
        updates = {}
        
        for field_id, value in self.config_changes.items():
            # Map UI field IDs to config paths
            if field_id.startswith("scanner-"):
                # Handle scanner config changes
                parts = field_id.split("-")
                if len(parts) >= 3:
                    scanner_name = parts[1]
                    setting = "-".join(parts[2:])
                    
                    if f"scanners.{scanner_name}" not in updates:
                        updates[f"scanners.{scanner_name}"] = {}
                    updates[f"scanners.{scanner_name}"][setting] = value
            
            elif field_id == "output-format":
                updates["output.format"] = value
            elif field_id == "output-file":
                updates["output.file"] = value
            elif field_id == "use-docker":
                updates["use_docker"] = value
            elif field_id == "docker-timeout":
                try:
                    updates["docker_timeout"] = int(value)
                except ValueError:
                    pass
            # Add more mappings as needed
        
        return updates
    
    def _mark_unsaved_changes(self) -> None:
        """Mark that there are unsaved changes."""
        self.unsaved_changes = True
        # Could update UI to show unsaved changes indicator