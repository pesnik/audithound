"""Dashboard components."""

from .base import BaseComponent


class DashboardComponent(BaseComponent):
    """Main dashboard component."""
    
    def __init__(self, store, **kwargs):
        super().__init__(store, **kwargs)
    
    def on_component_mounted(self) -> None:
        """Initialize dashboard component."""
        pass
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        pass