#!/usr/bin/env python3
"""Test simple tabs display."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Tabs, TabPane

class TestTabsApp(App):
    """Simple test app to check if tabs work."""
    
    def compose(self) -> ComposeResult:
        """Create simple layout with tabs."""
        yield Header()
        
        with Tabs("Tab 1", "Tab 2", "Tab 3"):
            with TabPane("Tab 1"):
                yield Static("Content of Tab 1")
            with TabPane("Tab 2"):
                yield Static("Content of Tab 2")
            with TabPane("Tab 3"):
                yield Static("Content of Tab 3")
        
        yield Footer()

if __name__ == "__main__":
    app = TestTabsApp()
    app.run()