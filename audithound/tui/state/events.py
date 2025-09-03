"""Event system for TUI state management."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Dict
from datetime import datetime


class EventType(Enum):
    """Types of events in the TUI."""
    
    # Application events
    APP_STARTED = auto()
    APP_SHUTDOWN = auto()
    CONFIG_CHANGED = auto()
    
    # Scan events
    SCAN_STARTED = auto()
    SCAN_PROGRESS = auto()
    SCAN_COMPLETED = auto()
    SCAN_FAILED = auto()
    SCAN_CANCELLED = auto()
    
    # UI events
    TAB_CHANGED = auto()
    THEME_CHANGED = auto()
    LAYOUT_CHANGED = auto()
    
    # Data events
    RESULTS_UPDATED = auto()
    HISTORY_UPDATED = auto()
    BOOKMARK_ADDED = auto()
    BOOKMARK_REMOVED = auto()
    
    # Error events
    ERROR_OCCURRED = auto()
    ERROR_RECOVERED = auto()


@dataclass
class Event:
    """Base event class for the TUI state system."""
    
    event_type: EventType
    payload: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    source: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def get_payload_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the event payload."""
        if self.payload:
            return self.payload.get(key, default)
        return default
    
    def has_payload_key(self, key: str) -> bool:
        """Check if a key exists in the event payload."""
        return self.payload is not None and key in self.payload


# Event factory functions
def scan_started_event(target: str, tools: list[str]) -> Event:
    """Create a scan started event."""
    return Event(
        EventType.SCAN_STARTED,
        {"target": target, "tools": tools},
        source="scanner"
    )


def scan_progress_event(progress: float, status: str, current_tool: str = None) -> Event:
    """Create a scan progress event."""
    payload = {"progress": progress, "status": status}
    if current_tool:
        payload["current_tool"] = current_tool
    return Event(EventType.SCAN_PROGRESS, payload, source="scanner")


def scan_completed_event(results) -> Event:
    """Create a scan completed event."""
    return Event(
        EventType.SCAN_COMPLETED,
        {"results": results},
        source="scanner"
    )


def scan_failed_event(error: str, details: Dict[str, Any] = None) -> Event:
    """Create a scan failed event."""
    payload = {"error": error}
    if details:
        payload.update(details)
    return Event(EventType.SCAN_FAILED, payload, source="scanner")


def tab_changed_event(old_tab: str, new_tab: str) -> Event:
    """Create a tab changed event."""
    return Event(
        EventType.TAB_CHANGED,
        {"old_tab": old_tab, "new_tab": new_tab},
        source="ui"
    )


def results_updated_event(results) -> Event:
    """Create a results updated event."""
    return Event(
        EventType.RESULTS_UPDATED,
        {"results": results},
        source="data"
    )


def error_occurred_event(error: Exception, context: str = None) -> Event:
    """Create an error occurred event."""
    payload = {"error": str(error), "error_type": type(error).__name__}
    if context:
        payload["context"] = context
    return Event(EventType.ERROR_OCCURRED, payload, source="system")