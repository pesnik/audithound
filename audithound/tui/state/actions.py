"""Action system for TUI state management."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Dict
from pathlib import Path


class ActionType(Enum):
    """Types of actions that can modify state."""
    
    # Configuration actions
    UPDATE_CONFIG = auto()
    LOAD_CONFIG = auto()
    SAVE_CONFIG = auto()
    RESET_CONFIG = auto()
    
    # Scan actions
    START_SCAN = auto()
    CANCEL_SCAN = auto()
    PAUSE_SCAN = auto()
    RESUME_SCAN = auto()
    
    # UI actions
    CHANGE_TAB = auto()
    CHANGE_THEME = auto()
    TOGGLE_SIDEBAR = auto()
    SET_FILTER = auto()
    CLEAR_FILTER = auto()
    
    # Data actions
    SET_RESULTS = auto()
    CLEAR_RESULTS = auto()
    ADD_BOOKMARK = auto()
    REMOVE_BOOKMARK = auto()
    EXPORT_RESULTS = auto()
    
    # History actions
    ADD_TO_HISTORY = auto()
    CLEAR_HISTORY = auto()
    LOAD_FROM_HISTORY = auto()
    
    # Error actions
    SET_ERROR = auto()
    CLEAR_ERROR = auto()
    RETRY_OPERATION = auto()


@dataclass
class Action:
    """Base action class for state modifications."""
    
    action_type: ActionType
    payload: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    
    def get_payload_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the action payload."""
        if self.payload:
            return self.payload.get(key, default)
        return default
    
    def get_meta_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the action meta."""
        if self.meta:
            return self.meta.get(key, default)
        return default


# Action factory functions
def start_scan_action(target: str, tools: list[str] = None, config_overrides: Dict[str, Any] = None) -> Action:
    """Create a start scan action."""
    payload = {"target": target}
    if tools:
        payload["tools"] = tools
    if config_overrides:
        payload["config_overrides"] = config_overrides
    return Action(ActionType.START_SCAN, payload)


def update_config_action(config_updates: Dict[str, Any], save: bool = False) -> Action:
    """Create an update config action."""
    return Action(
        ActionType.UPDATE_CONFIG,
        {"updates": config_updates},
        {"save": save}
    )


def change_tab_action(tab_id: str) -> Action:
    """Create a change tab action."""
    return Action(ActionType.CHANGE_TAB, {"tab_id": tab_id})


def change_theme_action(theme_name: str) -> Action:
    """Create a change theme action."""
    return Action(ActionType.CHANGE_THEME, {"theme": theme_name})


def set_results_action(results, scan_id: str = None) -> Action:
    """Create a set results action."""
    payload = {"results": results}
    if scan_id:
        payload["scan_id"] = scan_id
    return Action(ActionType.SET_RESULTS, payload)


def set_filter_action(filter_type: str, filter_value: Any) -> Action:
    """Create a set filter action."""
    return Action(
        ActionType.SET_FILTER,
        {"filter_type": filter_type, "filter_value": filter_value}
    )


def add_bookmark_action(bookmark_name: str, bookmark_data: Dict[str, Any]) -> Action:
    """Create an add bookmark action."""
    return Action(
        ActionType.ADD_BOOKMARK,
        {"name": bookmark_name, "data": bookmark_data}
    )


def export_results_action(format_type: str, output_path: Path, options: Dict[str, Any] = None) -> Action:
    """Create an export results action."""
    payload = {"format": format_type, "output_path": str(output_path)}
    if options:
        payload["options"] = options
    return Action(ActionType.EXPORT_RESULTS, payload)


def set_error_action(error: Exception, context: str = None, recoverable: bool = True) -> Action:
    """Create a set error action."""
    payload = {
        "error": str(error),
        "error_type": type(error).__name__,
        "recoverable": recoverable
    }
    if context:
        payload["context"] = context
    return Action(ActionType.SET_ERROR, payload)