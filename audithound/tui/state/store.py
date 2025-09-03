"""Centralized state store for AuditHound TUI."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Set
from collections import defaultdict

from ...core.config import Config
from .actions import Action, ActionType
from .events import Event, EventType


logger = logging.getLogger(__name__)


@dataclass
class AppState:
    """Main application state."""
    
    # Configuration
    config: Config = field(default_factory=Config.default)
    config_file: Optional[Path] = None
    
    # Current scan state
    scan_target: Optional[str] = None
    scan_tools: List[str] = field(default_factory=list)
    scan_progress: float = 0.0
    scan_status: str = "idle"
    scan_id: Optional[str] = None
    is_scanning: bool = False
    current_scanner: Optional[str] = None
    
    # Results and data
    current_results = None
    scan_history: List[Dict[str, Any]] = field(default_factory=list)
    bookmarks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # UI state
    current_tab: str = "dashboard"
    theme: str = "default"
    sidebar_visible: bool = True
    filters: Dict[str, Any] = field(default_factory=dict)
    
    # Error state
    current_error: Optional[Dict[str, Any]] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    last_scan_duration: Optional[float] = None
    memory_usage: Optional[Dict[str, Any]] = None


class AppStore:
    """Centralized state store with event-driven architecture."""
    
    def __init__(self, initial_state: Optional[AppState] = None):
        self.state = initial_state or AppState()
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self._middleware: List[Callable] = []
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Action handlers mapping
        self._action_handlers = {
            ActionType.UPDATE_CONFIG: self._handle_update_config,
            ActionType.LOAD_CONFIG: self._handle_load_config,
            ActionType.SAVE_CONFIG: self._handle_save_config,
            ActionType.START_SCAN: self._handle_start_scan,
            ActionType.CANCEL_SCAN: self._handle_cancel_scan,
            ActionType.CHANGE_TAB: self._handle_change_tab,
            ActionType.CHANGE_THEME: self._handle_change_theme,
            ActionType.SET_RESULTS: self._handle_set_results,
            ActionType.SET_FILTER: self._handle_set_filter,
            ActionType.CLEAR_FILTER: self._handle_clear_filter,
            ActionType.ADD_BOOKMARK: self._handle_add_bookmark,
            ActionType.REMOVE_BOOKMARK: self._handle_remove_bookmark,
            ActionType.SET_ERROR: self._handle_set_error,
            ActionType.CLEAR_ERROR: self._handle_clear_error,
            ActionType.EXPORT_RESULTS: self._handle_export_results,
        }
    
    # Subscription and event handling
    
    def subscribe(self, path: str, callback: Callable) -> Callable:
        """Subscribe to state changes at a specific path."""
        self._subscribers[path].append(callback)
        return lambda: self.unsubscribe(path, callback)
    
    def unsubscribe(self, path: str, callback: Callable) -> None:
        """Unsubscribe from state changes."""
        if callback in self._subscribers[path]:
            self._subscribers[path].remove(callback)
    
    def listen_to_event(self, event_type: EventType, callback: Callable) -> Callable:
        """Listen to specific event types."""
        self._event_listeners[event_type].append(callback)
        return lambda: self.unlisten_to_event(event_type, callback)
    
    def unlisten_to_event(self, event_type: EventType, callback: Callable) -> None:
        """Stop listening to event types."""
        if callback in self._event_listeners[event_type]:
            self._event_listeners[event_type].remove(callback)
    
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware for action processing."""
        self._middleware.append(middleware)
    
    # State management
    
    def get_state(self) -> AppState:
        """Get the current state (read-only copy)."""
        return self.state
    
    def get_state_value(self, path: str, default: Any = None) -> Any:
        """Get a specific value from state using dot notation."""
        try:
            value = self.state
            for part in path.split('.'):
                value = getattr(value, part)
            return value
        except (AttributeError, KeyError):
            return default
    
    def dispatch_action(self, action: Action) -> None:
        """Dispatch an action to update state."""
        try:
            # Apply middleware
            for middleware in self._middleware:
                action = middleware(action, self.state) or action
            
            self._logger.debug(f"Dispatching action: {action.action_type.name}")
            
            # Handle the action
            if action.action_type in self._action_handlers:
                old_state = self._copy_state()
                self._action_handlers[action.action_type](action)
                self._notify_subscribers(old_state)
            else:
                self._logger.warning(f"No handler for action: {action.action_type}")
        
        except Exception as e:
            self._logger.error(f"Error dispatching action {action.action_type}: {e}")
            self.emit_event(Event(
                EventType.ERROR_OCCURRED,
                {"error": str(e), "action": action.action_type.name}
            ))
    
    def emit_event(self, event: Event) -> None:
        """Emit an event to all listeners."""
        self._logger.debug(f"Emitting event: {event.event_type.name}")
        
        # Notify event listeners
        for callback in self._event_listeners[event.event_type]:
            try:
                callback(event)
            except Exception as e:
                self._logger.error(f"Error in event listener: {e}")
    
    # Action handlers
    
    def _handle_update_config(self, action: Action) -> None:
        """Handle config updates."""
        updates = action.get_payload_value("updates", {})
        for key, value in updates.items():
            # Handle dotted notation for nested config updates
            if '.' in key:
                parts = key.split('.')
                target = self.state.config
                
                # Navigate to the parent object
                for part in parts[:-1]:
                    if hasattr(target, part):
                        target = getattr(target, part)
                    else:
                        self._logger.warning(f"Config path {key} not found - parent {part} missing")
                        break
                else:
                    # Set the final value
                    final_key = parts[-1]
                    if hasattr(target, final_key):
                        setattr(target, final_key, value)
                    else:
                        self._logger.warning(f"Config path {key} not found - final key {final_key} missing")
            else:
                # Handle direct attributes
                if hasattr(self.state.config, key):
                    setattr(self.state.config, key, value)
                else:
                    self._logger.warning(f"Config attribute {key} not found")
        
        if action.get_meta_value("save", False):
            self._save_config()
        
        self.emit_event(Event(EventType.CONFIG_CHANGED, {"updates": updates}))
    
    def _handle_load_config(self, action: Action) -> None:
        """Handle config loading."""
        config_path = action.get_payload_value("config_path")
        if config_path and Path(config_path).exists():
            self.state.config = Config.load(Path(config_path))
            self.state.config_file = Path(config_path)
            self.emit_event(Event(EventType.CONFIG_CHANGED, {"loaded": True}))
    
    def _handle_save_config(self, action: Action) -> None:
        """Handle config saving."""
        self._save_config()
    
    def _handle_start_scan(self, action: Action) -> None:
        """Handle scan start."""
        self.state.scan_target = action.get_payload_value("target")
        self.state.scan_tools = action.get_payload_value("tools", [])
        self.state.is_scanning = True
        self.state.scan_status = "initializing"
        self.state.scan_progress = 0.0
        self.state.scan_id = f"scan_{datetime.now().isoformat()}"
        
        self.emit_event(Event(
            EventType.SCAN_STARTED,
            {
                "target": self.state.scan_target,
                "tools": self.state.scan_tools,
                "scan_id": self.state.scan_id
            }
        ))
    
    def _handle_cancel_scan(self, action: Action) -> None:
        """Handle scan cancellation."""
        self.state.is_scanning = False
        self.state.scan_status = "cancelled"
        
        self.emit_event(Event(EventType.SCAN_CANCELLED))
    
    def _handle_change_tab(self, action: Action) -> None:
        """Handle tab changes."""
        old_tab = self.state.current_tab
        new_tab = action.get_payload_value("tab_id")
        self.state.current_tab = new_tab
        
        self.emit_event(Event(
            EventType.TAB_CHANGED,
            {"old_tab": old_tab, "new_tab": new_tab}
        ))
    
    def _handle_change_theme(self, action: Action) -> None:
        """Handle theme changes."""
        theme = action.get_payload_value("theme")
        self.state.theme = theme
        
        self.emit_event(Event(EventType.THEME_CHANGED, {"theme": theme}))
    
    def _handle_set_results(self, action: Action) -> None:
        """Handle results updates."""
        results = action.get_payload_value("results")
        scan_id = action.get_payload_value("scan_id")
        
        self.state.current_results = results
        self.state.is_scanning = False
        self.state.scan_status = "completed"
        
        # Add to history
        if results and scan_id:
            self.state.scan_history.append({
                "scan_id": scan_id,
                "target": self.state.scan_target,
                "timestamp": datetime.now(),
                "findings_count": getattr(results, 'total_findings', 0),
                "results": results
            })
        
        self.emit_event(Event(EventType.RESULTS_UPDATED, {"results": results}))
        self.emit_event(Event(EventType.SCAN_COMPLETED, {"results": results}))
    
    def _handle_set_filter(self, action: Action) -> None:
        """Handle filter updates."""
        filter_type = action.get_payload_value("filter_type")
        filter_value = action.get_payload_value("filter_value")
        self.state.filters[filter_type] = filter_value
    
    def _handle_clear_filter(self, action: Action) -> None:
        """Handle filter clearing."""
        filter_type = action.get_payload_value("filter_type")
        if filter_type in self.state.filters:
            del self.state.filters[filter_type]
        elif filter_type == "all":
            self.state.filters.clear()
    
    def _handle_add_bookmark(self, action: Action) -> None:
        """Handle bookmark addition."""
        name = action.get_payload_value("name")
        data = action.get_payload_value("data")
        self.state.bookmarks[name] = data
        
        self.emit_event(Event(EventType.BOOKMARK_ADDED, {"name": name, "data": data}))
    
    def _handle_remove_bookmark(self, action: Action) -> None:
        """Handle bookmark removal."""
        name = action.get_payload_value("name")
        if name in self.state.bookmarks:
            del self.state.bookmarks[name]
            self.emit_event(Event(EventType.BOOKMARK_REMOVED, {"name": name}))
    
    def _handle_set_error(self, action: Action) -> None:
        """Handle error state."""
        error_data = {
            "error": action.get_payload_value("error"),
            "error_type": action.get_payload_value("error_type"),
            "context": action.get_payload_value("context"),
            "recoverable": action.get_payload_value("recoverable", True),
            "timestamp": datetime.now()
        }
        
        self.state.current_error = error_data
        self.state.error_history.append(error_data)
        
        self.emit_event(Event(EventType.ERROR_OCCURRED, error_data))
    
    def _handle_clear_error(self, action: Action) -> None:
        """Handle error clearing."""
        self.state.current_error = None
        self.emit_event(Event(EventType.ERROR_RECOVERED))
    
    def _handle_export_results(self, action: Action) -> None:
        """Handle results export."""
        if not self.state.current_results:
            raise ValueError("No results to export")
        
        # This would typically delegate to a service
        # For now, just emit an event
        self.emit_event(Event(
            EventType.RESULTS_UPDATED,
            {
                "export_requested": True,
                "format": action.get_payload_value("format"),
                "output_path": action.get_payload_value("output_path")
            }
        ))
    
    # Helper methods
    
    def _copy_state(self) -> AppState:
        """Create a copy of current state."""
        # For now, return the state itself
        # In production, would create deep copy
        return self.state
    
    def _notify_subscribers(self, old_state: AppState) -> None:
        """Notify all subscribers of state changes."""
        # For now, notify all subscribers
        # In production, would diff states and notify only relevant subscribers
        for path, callbacks in self._subscribers.items():
            for callback in callbacks:
                try:
                    callback(self.state, old_state)
                except Exception as e:
                    self._logger.error(f"Error in state subscriber: {e}")
    
    def _save_config(self) -> None:
        """Save current configuration."""
        if self.state.config_file:
            self.state.config.save(self.state.config_file)
        else:
            # Save to default location
            config_path = Path("audithound.yaml")
            self.state.config.save(config_path)
            self.state.config_file = config_path