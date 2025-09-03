"""Advanced navigation components with keyboard shortcuts and command palette."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, Tuple
import time
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Input, Static, ListView, ListItem, Label, Button
from textual.reactive import reactive
from rich.text import Text

from .base import BaseComponent
from ..state.events import EventType, Event
from ..state.actions import Action, ActionType


class NavigationBar(BaseComponent):
    """Navigation bar with breadcrumbs and quick actions."""
    
    current_path = reactive("")
    show_breadcrumbs = reactive(True)
    
    def __init__(self, store, show_actions: bool = True, **kwargs):
        super().__init__(store, **kwargs)
        self.show_actions = show_actions
        self.breadcrumbs: List[Dict[str, str]] = []
        self.quick_actions: List[Dict[str, Any]] = []
        
        self._setup_default_actions()
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="navigation-bar"):
            # Breadcrumbs section
            if self.show_breadcrumbs:
                with Horizontal(classes="breadcrumbs", id="breadcrumbs-container"):
                    yield Static("🏠 Home", classes="breadcrumb-item")
            
            # Quick actions section
            if self.show_actions:
                with Horizontal(classes="quick-actions", id="actions-container"):
                    for action in self.quick_actions:
                        yield Button(
                            action["label"],
                            variant=action.get("variant", "default"),
                            id=f"action-{action['key']}",
                            classes="quick-action-btn"
                        )
    
    def _setup_subscriptions(self) -> None:
        """Setup state subscriptions."""
        self.subscribe_to_state("current_tab")
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners."""
        self.listen_to_event(EventType.TAB_CHANGED, self._on_tab_changed)
    
    def on_component_mounted(self) -> None:
        """Initialize navigation bar."""
        self._update_breadcrumbs()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        if new_state.current_tab != getattr(old_state, 'current_tab', None):
            self._update_breadcrumbs()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id and button_id.startswith("action-"):
            action_key = button_id.replace("action-", "")
            self._execute_quick_action(action_key)
        elif button_id and button_id.startswith("breadcrumb-"):
            # Extract target from ID format: breadcrumb-{target}-{i}-{timestamp}
            parts = button_id.replace("breadcrumb-", "").split("-")
            if len(parts) >= 3:
                target = "-".join(parts[:-2])  # Everything except index and timestamp
            else:
                target = parts[0]  # Fallback for simpler format
            self._navigate_to_breadcrumb(target)
    
    def _on_tab_changed(self, event: Event) -> None:
        """Handle tab changes."""
        new_tab = event.get_payload_value("new_tab")
        self._update_breadcrumbs_for_tab(new_tab)
    
    def _setup_default_actions(self) -> None:
        """Setup default quick actions."""
        self.quick_actions = [
            {
                "key": "scan",
                "label": "🚀 Scan",
                "variant": "primary",
                "action": self._start_scan_action
            },
            {
                "key": "export",
                "label": "📤 Export",
                "variant": "default",
                "action": self._export_action
            },
            {
                "key": "config",
                "label": "⚙️ Config",
                "variant": "default",
                "action": self._config_action
            },
            {
                "key": "help",
                "label": "❓ Help",
                "variant": "default",
                "action": self._help_action
            }
        ]
    
    def _update_breadcrumbs(self) -> None:
        """Update breadcrumbs based on current state."""
        current_tab = self.get_state_value("current_tab", "dashboard")
        self._update_breadcrumbs_for_tab(current_tab)
    
    def _update_breadcrumbs_for_tab(self, tab: str) -> None:
        """Update breadcrumbs for a specific tab."""
        self.breadcrumbs = [{"label": "🏠 Home", "target": "dashboard"}]
        
        if tab == "results":
            self.breadcrumbs.append({"label": "📊 Results", "target": "results"})
        elif tab == "configuration":
            self.breadcrumbs.append({"label": "⚙️ Configuration", "target": "configuration"})
        elif tab != "dashboard":
            self.breadcrumbs.append({"label": tab.title(), "target": tab})
        
        self._refresh_breadcrumbs_display()
    
    def _refresh_breadcrumbs_display(self) -> None:
        """Refresh the breadcrumbs display."""
        try:
            container = self.query_one("#breadcrumbs-container", Horizontal)
            
            # Force remove all children and wait
            for child in list(container.children):
                child.remove()
            
            # Use timestamp to ensure unique IDs
            timestamp = int(time.time() * 1000000)  # microseconds for uniqueness
            
            for i, crumb in enumerate(self.breadcrumbs):
                if i > 0:
                    container.mount(Static(" > ", classes="breadcrumb-separator"))
                
                container.mount(
                    Button(
                        crumb["label"],
                        variant="default",
                        id=f"breadcrumb-{crumb['target']}-{i}-{timestamp}",
                        classes="breadcrumb-item"
                    )
                )
        except Exception as e:
            self.logger.debug(f"Error updating breadcrumbs: {e}")
    
    def _execute_quick_action(self, action_key: str) -> None:
        """Execute a quick action."""
        for action in self.quick_actions:
            if action["key"] == action_key:
                if callable(action.get("action")):
                    action["action"]()
                break
    
    def _start_scan_action(self) -> None:
        """Quick scan action."""
        from ..state.actions import start_scan_action
        target = self.get_state_value("scan_target") or "."
        self.dispatch_action(start_scan_action(target))
    
    def _export_action(self) -> None:
        """Quick export action."""
        # Would trigger export modal or direct export
        pass
    
    def _config_action(self) -> None:
        """Quick config action."""
        from ..state.actions import change_tab_action
        self.dispatch_action(change_tab_action("configuration"))
    
    def _help_action(self) -> None:
        """Quick help action."""
        # Would show help modal or switch to help tab
        pass

    def _navigate_to_breadcrumb(self, target: str) -> None:
        """Navigate to breadcrumb target."""
        from ..state.actions import change_tab_action
        self.dispatch_action(change_tab_action(target))


class CommandPalette(ModalScreen):
    """Command palette for quick navigation and actions."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("enter", "execute_command", "Execute"),
        Binding("up", "cursor_up", "Up"),
        Binding("down", "cursor_down", "Down"),
    ]
    
    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self.commands: List[Dict[str, Any]] = []
        self.filtered_commands: List[Dict[str, Any]] = []
        self.selected_index = 0
        
        self._setup_commands()
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="command-palette"):
            yield Static("Command Palette", classes="palette-title")
            yield Input(placeholder="Type a command...", id="command-input")
            with Vertical(id="commands-list"):
                pass
            yield Static("Press Enter to execute, Escape to close", classes="palette-help")
    
    def on_mount(self) -> None:
        """Initialize command palette."""
        self._update_command_list()
        self.query_one("#command-input", Input).focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "command-input":
            self._filter_commands(event.value)
    
    def on_key(self, event: Key) -> None:
        """Handle keyboard navigation."""
        if event.key == "up":
            self.selected_index = max(0, self.selected_index - 1)
            self._update_selection()
        elif event.key == "down":
            self.selected_index = min(len(self.filtered_commands) - 1, self.selected_index + 1)
            self._update_selection()
    
    def action_execute_command(self) -> None:
        """Execute the selected command."""
        if 0 <= self.selected_index < len(self.filtered_commands):
            command = self.filtered_commands[self.selected_index]
            self._execute_command(command)
        self.dismiss()
    
    def action_cursor_up(self) -> None:
        """Move cursor up."""
        self.selected_index = max(0, self.selected_index - 1)
        self._update_selection()
    
    def action_cursor_down(self) -> None:
        """Move cursor down."""
        self.selected_index = min(len(self.filtered_commands) - 1, self.selected_index + 1)
        self._update_selection()
    
    def _setup_commands(self) -> None:
        """Setup available commands."""
        self.commands = [
            # Navigation commands
            {
                "id": "nav_dashboard",
                "title": "Go to Dashboard",
                "description": "Navigate to the main dashboard",
                "category": "Navigation",
                "keywords": ["dashboard", "home", "main"],
                "action": lambda: self._navigate_to("dashboard")
            },
            {
                "id": "nav_results", 
                "title": "Go to Results",
                "description": "Navigate to scan results",
                "category": "Navigation",
                "keywords": ["results", "findings", "vulnerabilities"],
                "action": lambda: self._navigate_to("results")
            },
            {
                "id": "nav_config",
                "title": "Go to Configuration", 
                "description": "Navigate to configuration settings",
                "category": "Navigation",
                "keywords": ["config", "settings", "preferences"],
                "action": lambda: self._navigate_to("configuration")
            },
            
            # Scan commands
            {
                "id": "scan_start",
                "title": "Start Scan",
                "description": "Start a new security scan",
                "category": "Scan",
                "keywords": ["scan", "start", "run", "execute"],
                "action": self._start_scan
            },
            {
                "id": "scan_cancel",
                "title": "Cancel Scan",
                "description": "Cancel the current scan",
                "category": "Scan", 
                "keywords": ["cancel", "stop", "abort"],
                "action": self._cancel_scan
            },
            
            # Theme commands
            {
                "id": "theme_dark",
                "title": "Switch to Dark Theme",
                "description": "Change to dark theme",
                "category": "Appearance",
                "keywords": ["theme", "dark", "appearance"],
                "action": lambda: self._change_theme("dark")
            },
            {
                "id": "theme_light",
                "title": "Switch to Light Theme",
                "description": "Change to light theme",
                "category": "Appearance",
                "keywords": ["theme", "light", "appearance"],
                "action": lambda: self._change_theme("light")
            },
            {
                "id": "theme_high_contrast",
                "title": "Switch to High Contrast Theme",
                "description": "Change to high contrast theme",
                "category": "Appearance",
                "keywords": ["theme", "high", "contrast", "accessibility"],
                "action": lambda: self._change_theme("high_contrast")
            },
            
            # Export commands
            {
                "id": "export_json",
                "title": "Export Results as JSON",
                "description": "Export scan results in JSON format",
                "category": "Export",
                "keywords": ["export", "json", "save", "results"],
                "action": lambda: self._export_results("json")
            },
            {
                "id": "export_csv",
                "title": "Export Results as CSV",
                "description": "Export scan results in CSV format", 
                "category": "Export",
                "keywords": ["export", "csv", "save", "results"],
                "action": lambda: self._export_results("csv")
            },
            
            # Help commands
            {
                "id": "help_shortcuts",
                "title": "Show Keyboard Shortcuts",
                "description": "Display all available keyboard shortcuts",
                "category": "Help",
                "keywords": ["help", "shortcuts", "keys", "hotkeys"],
                "action": self._show_shortcuts
            },
            {
                "id": "help_about",
                "title": "About AuditHound",
                "description": "Show application information",
                "category": "Help",
                "keywords": ["about", "info", "version"],
                "action": self._show_about
            }
        ]
        
        self.filtered_commands = self.commands.copy()
    
    def _filter_commands(self, search_text: str) -> None:
        """Filter commands based on search text."""
        if not search_text:
            self.filtered_commands = self.commands.copy()
        else:
            search_lower = search_text.lower()
            self.filtered_commands = [
                cmd for cmd in self.commands
                if (search_lower in cmd["title"].lower() or
                    search_lower in cmd["description"].lower() or
                    any(search_lower in kw for kw in cmd["keywords"]))
            ]
        
        self.selected_index = 0
        self._update_command_list()
    
    def _update_command_list(self) -> None:
        """Update the command list display."""
        try:
            container = self.query_one("#commands-list", Vertical)
            container.remove_children()
            
            for i, command in enumerate(self.filtered_commands):
                classes = "command-item"
                if i == self.selected_index:
                    classes += " selected"
                
                container.mount(
                    Static(
                        f"{command['title']}\n{command['description']}",
                        classes=classes,
                        id=f"cmd-{command['id']}"
                    )
                )
        
        except Exception as e:
            self.logger.error(f"Error updating command list: {e}")
    
    def _update_selection(self) -> None:
        """Update the visual selection."""
        try:
            container = self.query_one("#commands-list", Vertical)
            for i, child in enumerate(container.children):
                if hasattr(child, 'classes'):
                    if i == self.selected_index:
                        child.add_class("selected")
                    else:
                        child.remove_class("selected")
        except Exception as e:
            self.logger.debug(f"Error updating selection: {e}")
    
    def _execute_command(self, command: Dict[str, Any]) -> None:
        """Execute a command."""
        try:
            if callable(command.get("action")):
                command["action"]()
        except Exception as e:
            self.logger.error(f"Error executing command {command['id']}: {e}")
    
    def _navigate_to(self, tab: str) -> None:
        """Navigate to a specific tab."""
        from ..state.actions import change_tab_action
        self.store.dispatch_action(change_tab_action(tab))
    
    def _start_scan(self) -> None:
        """Start a scan."""
        from ..state.actions import start_scan_action
        target = self.store.get_state_value("scan_target", ".")
        self.store.dispatch_action(start_scan_action(target))
    
    def _cancel_scan(self) -> None:
        """Cancel current scan."""
        from ..state.actions import Action, ActionType
        self.store.dispatch_action(Action(ActionType.CANCEL_SCAN))
    
    def _change_theme(self, theme_name: str) -> None:
        """Change theme."""
        from ..state.actions import change_theme_action
        self.store.dispatch_action(change_theme_action(theme_name))
    
    def _export_results(self, format_type: str) -> None:
        """Export results."""
        from ..state.actions import Action, ActionType
        from pathlib import Path
        
        output_path = Path(f"audithound_results.{format_type}")
        self.store.dispatch_action(Action(
            ActionType.EXPORT_RESULTS,
            {"format": format_type, "output_path": str(output_path)}
        ))
    
    def _show_shortcuts(self) -> None:
        """Show keyboard shortcuts."""
        # Would open shortcuts modal
        pass
    
    def _show_about(self) -> None:
        """Show about information."""
        # Would open about modal
        pass


class KeyboardShortcutManager:
    """Manages global keyboard shortcuts."""
    
    def __init__(self, app):
        self.app = app
        self.shortcuts: Dict[str, Dict[str, Any]] = {}
        self.global_shortcuts: Dict[str, Callable] = {}
        
        self._setup_default_shortcuts()
    
    def _setup_default_shortcuts(self) -> None:
        """Setup default keyboard shortcuts."""
        self.shortcuts = {
            # Global application shortcuts
            "ctrl+q": {
                "description": "Quit application",
                "action": "quit",
                "global": True
            },
            "ctrl+shift+p": {
                "description": "Open command palette",
                "action": self._open_command_palette,
                "global": True
            },
            "f1": {
                "description": "Show help",
                "action": self._show_help,
                "global": True
            },
            
            # Navigation shortcuts
            "ctrl+1": {
                "description": "Go to dashboard",
                "action": lambda: self._navigate_to("dashboard"),
                "global": True
            },
            "ctrl+2": {
                "description": "Go to results",
                "action": lambda: self._navigate_to("results"),
                "global": True
            },
            "ctrl+3": {
                "description": "Go to configuration",
                "action": lambda: self._navigate_to("configuration"),
                "global": True
            },
            
            # Scan shortcuts
            "f5": {
                "description": "Start/refresh scan",
                "action": self._start_scan,
                "global": True
            },
            "ctrl+s": {
                "description": "Start scan",
                "action": self._start_scan,
                "global": False
            },
            "escape": {
                "description": "Cancel scan",
                "action": self._cancel_scan,
                "global": False
            },
            
            # Theme shortcuts
            "ctrl+shift+t": {
                "description": "Toggle theme",
                "action": self._toggle_theme,
                "global": True
            },
            
            # Export shortcuts
            "ctrl+e": {
                "description": "Export results",
                "action": self._export_results,
                "global": False
            },
            "ctrl+shift+e": {
                "description": "Export with options",
                "action": self._export_with_options,
                "global": False
            }
        }
    
    def register_shortcut(
        self,
        key_combination: str,
        action: Callable,
        description: str = "",
        global_shortcut: bool = False
    ) -> None:
        """Register a new keyboard shortcut."""
        self.shortcuts[key_combination] = {
            "description": description,
            "action": action,
            "global": global_shortcut
        }
    
    def unregister_shortcut(self, key_combination: str) -> None:
        """Unregister a keyboard shortcut."""
        if key_combination in self.shortcuts:
            del self.shortcuts[key_combination]
    
    def get_shortcuts(self, global_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """Get all shortcuts or only global ones."""
        if global_only:
            return {
                key: shortcut for key, shortcut in self.shortcuts.items()
                if shortcut.get("global", False)
            }
        return self.shortcuts.copy()
    
    def execute_shortcut(self, key_combination: str) -> bool:
        """Execute a keyboard shortcut."""
        if key_combination in self.shortcuts:
            shortcut = self.shortcuts[key_combination]
            try:
                if callable(shortcut["action"]):
                    shortcut["action"]()
                elif hasattr(self.app, shortcut["action"]):
                    getattr(self.app, shortcut["action"])()
                return True
            except Exception as e:
                self.app.logger.error(f"Error executing shortcut {key_combination}: {e}")
        return False
    
    def get_shortcut_help(self) -> List[Tuple[str, str]]:
        """Get help text for all shortcuts."""
        return [
            (key, shortcut["description"])
            for key, shortcut in self.shortcuts.items()
            if shortcut["description"]
        ]
    
    def _open_command_palette(self) -> None:
        """Open the command palette."""
        if hasattr(self.app, 'store'):
            palette = CommandPalette(self.app.store)
            self.app.push_screen(palette)
    
    def _show_help(self) -> None:
        """Show help information."""
        # Would show help modal with shortcuts
        pass
    
    def _navigate_to(self, tab: str) -> None:
        """Navigate to a specific tab."""
        if hasattr(self.app, 'store'):
            from ..state.actions import change_tab_action
            self.app.store.dispatch_action(change_tab_action(tab))
    
    def _start_scan(self) -> None:
        """Start a scan."""
        if hasattr(self.app, 'store'):
            from ..state.actions import start_scan_action
            target = self.app.store.get_state_value("scan_target", ".")
            self.app.store.dispatch_action(start_scan_action(target))
    
    def _cancel_scan(self) -> None:
        """Cancel current scan."""
        if hasattr(self.app, 'store'):
            from ..state.actions import Action, ActionType
            self.app.store.dispatch_action(Action(ActionType.CANCEL_SCAN))
    
    def _toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        if hasattr(self.app, 'store'):
            current_theme = self.app.store.get_state_value("theme", "default")
            new_theme = "light" if current_theme == "dark" else "dark"
            
            from ..state.actions import change_theme_action
            self.app.store.dispatch_action(change_theme_action(new_theme))
    
    def _export_results(self) -> None:
        """Export results."""
        if hasattr(self.app, 'store'):
            from ..state.actions import Action, ActionType
            from pathlib import Path
            
            output_path = Path("audithound_results.json")
            self.app.store.dispatch_action(Action(
                ActionType.EXPORT_RESULTS,
                {"format": "json", "output_path": str(output_path)}
            ))
    
    def _export_with_options(self) -> None:
        """Export results with options dialog."""
        # Would show export options modal
        pass