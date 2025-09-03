"""Base component class for TUI widgets."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from textual.widget import Widget
from textual.reactive import reactive

from ..state.store import AppStore
from ..state.events import Event, EventType
from ..state.actions import Action


class BaseComponent(Widget, ABC):
    """Base class for all TUI components with state management."""
    
    # Reactive attributes
    is_loading = reactive(False)
    has_error = reactive(False)
    error_message = reactive("")
    
    def __init__(
        self,
        store: AppStore,
        component_id: str = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.store = store
        self.component_id = component_id or self.__class__.__name__.lower()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # State subscriptions and event listeners
        self._subscriptions = []
        self._event_listeners = []
        
        # Initialize component
        self._setup_subscriptions()
        self._setup_event_listeners()
    
    def on_mount(self) -> None:
        """Called when component is mounted."""
        self.logger.debug(f"Component {self.component_id} mounted")
        self.on_component_mounted()
    
    def on_unmount(self) -> None:
        """Called when component is unmounted."""
        self.logger.debug(f"Component {self.component_id} unmounted")
        
        # Cleanup subscriptions
        for unsubscribe in self._subscriptions:
            unsubscribe()
        
        for unlisten in self._event_listeners:
            unlisten()
        
        self.on_component_unmounted()
    
    # Abstract methods for subclasses
    
    @abstractmethod
    def on_component_mounted(self) -> None:
        """Called when component is fully mounted."""
        pass
    
    def on_component_unmounted(self) -> None:
        """Called when component is being unmounted."""
        pass
    
    @abstractmethod
    def on_state_changed(self, new_state, old_state) -> None:
        """Called when subscribed state changes."""
        pass
    
    def on_event_received(self, event: Event) -> None:
        """Called when subscribed events are received."""
        pass
    
    # State and event management
    
    def subscribe_to_state(self, path: str, callback: Callable = None) -> None:
        """Subscribe to state changes at a specific path."""
        if callback is None:
            callback = self.on_state_changed
        
        unsubscribe = self.store.subscribe(path, callback)
        self._subscriptions.append(unsubscribe)
    
    def listen_to_event(self, event_type: EventType, callback: Callable = None) -> None:
        """Listen to specific event types."""
        if callback is None:
            callback = self.on_event_received
        
        unlisten = self.store.listen_to_event(event_type, callback)
        self._event_listeners.append(unlisten)
    
    def dispatch_action(self, action: Action) -> None:
        """Dispatch an action to the store."""
        self.store.dispatch_action(action)
    
    def emit_event(self, event: Event) -> None:
        """Emit an event through the store."""
        self.store.emit_event(event)
    
    def get_state_value(self, path: str, default: Any = None) -> Any:
        """Get a value from the current state."""
        return self.store.get_state_value(path, default)
    
    # Setup methods for subclasses to override
    
    def _setup_subscriptions(self) -> None:
        """Setup state subscriptions. Override in subclasses."""
        pass
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners. Override in subclasses."""
        pass
    
    # Error handling
    
    def set_error(self, error: Exception, context: str = None) -> None:
        """Set error state for this component."""
        self.has_error = True
        self.error_message = str(error)
        self.logger.error(f"Component error in {context or self.component_id}: {error}")
    
    def clear_error(self) -> None:
        """Clear error state for this component."""
        self.has_error = False
        self.error_message = ""
    
    def set_loading(self, loading: bool = True) -> None:
        """Set loading state for this component."""
        self.is_loading = loading
    
    # Utility methods
    
    def refresh_from_state(self) -> None:
        """Force refresh component from current state."""
        current_state = self.store.get_state()
        self.on_state_changed(current_state, current_state)
    
    def get_component_state(self) -> Dict[str, Any]:
        """Get component-specific state data."""
        return {
            "component_id": self.component_id,
            "is_loading": self.is_loading,
            "has_error": self.has_error,
            "error_message": self.error_message
        }
    
    # Watch reactive attributes
    
    def watch_is_loading(self, loading: bool) -> None:
        """React to loading state changes."""
        self.on_loading_changed(loading)
    
    def watch_has_error(self, has_error: bool) -> None:
        """React to error state changes."""
        self.on_error_changed(has_error)
    
    # Override these in subclasses if needed
    
    def on_loading_changed(self, loading: bool) -> None:
        """Called when loading state changes."""
        pass
    
    def on_error_changed(self, has_error: bool) -> None:
        """Called when error state changes."""
        pass


class StatelessComponent(Widget):
    """Base class for components that don't need state management."""
    
    def __init__(self, component_id: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.component_id = component_id or self.__class__.__name__.lower()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def on_mount(self) -> None:
        """Called when component is mounted."""
        self.logger.debug(f"Stateless component {self.component_id} mounted")