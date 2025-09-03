"""Theme management and application system."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import json

from .themes import BaseTheme, get_theme_by_name, get_available_themes, DefaultTheme
from ..state.store import AppStore
from ..state.events import Event, EventType
from ..state.actions import Action, ActionType


class ThemeManager:
    """Manages theme selection, persistence, and application."""
    
    def __init__(self, store: AppStore, config_dir: Path = None):
        self.store = store
        self.config_dir = config_dir or Path.home() / '.audithound' / 'themes'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Current theme state
        self._current_theme: Optional[BaseTheme] = None
        self._theme_cache: Dict[str, BaseTheme] = {}
        self._custom_themes: Dict[str, Dict[str, Any]] = {}
        
        # Theme change callbacks
        self._theme_callbacks: list[Callable[[BaseTheme], None]] = []
        
        # Setup
        self._load_custom_themes()
        self._setup_event_listeners()
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners for theme management."""
        # Disabled to prevent infinite loops
        # self.store.listen_to_event(EventType.THEME_CHANGED, self._on_theme_changed)
        self.store.listen_to_event(EventType.CONFIG_CHANGED, self._on_config_changed)
    
    def _on_theme_changed(self, event: Event) -> None:
        """Handle theme change events."""
        theme_name = event.get_payload_value("theme")
        current_name = self.get_current_theme_name()
        # Avoid circular updates - only set if different
        if theme_name and theme_name.lower() != current_name.lower():
            self.set_theme(theme_name)
    
    def _on_config_changed(self, event: Event) -> None:
        """Handle config changes that might affect themes."""
        # Could reload themes if config affects theme settings
        pass
    
    def get_current_theme(self) -> BaseTheme:
        """Get the currently active theme."""
        if self._current_theme is None:
            # Load default theme
            default_theme_name = self.store.get_state_value("theme", "default")
            self._current_theme = self._load_theme(default_theme_name)
        
        return self._current_theme
    
    def get_current_theme_name(self) -> str:
        """Get the name of the currently active theme."""
        if self._current_theme:
            return self._current_theme.name.lower().replace(" ", "_")
        return "default"
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the active theme."""
        try:
            new_theme = self._load_theme(theme_name)
            old_theme = self._current_theme
            self._current_theme = new_theme
            
            # Notify callbacks
            for callback in self._theme_callbacks:
                try:
                    callback(new_theme)
                except Exception as e:
                    self.logger.error(f"Error in theme callback: {e}")
            
            # Save theme preference
            self._save_theme_preference(theme_name)
            
            self.logger.info(f"Theme changed from {old_theme.name if old_theme else 'None'} to {new_theme.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set theme '{theme_name}': {e}")
            return False
    
    def get_available_themes(self) -> Dict[str, str]:
        """Get all available themes including custom ones."""
        themes = get_available_themes()
        
        # Add custom themes
        for name, theme_data in self._custom_themes.items():
            themes[name] = theme_data.get("display_name", name.title())
        
        return themes
    
    def get_theme_info(self, theme_name: str) -> Dict[str, Any]:
        """Get detailed information about a theme."""
        try:
            theme = self._load_theme(theme_name)
            return theme.get_theme_info()
        except Exception as e:
            self.logger.error(f"Failed to get theme info for '{theme_name}': {e}")
            return {"name": theme_name, "error": str(e)}
    
    def register_theme_callback(self, callback: Callable[[BaseTheme], None]) -> Callable:
        """Register a callback for theme changes."""
        self._theme_callbacks.append(callback)
        return lambda: self._theme_callbacks.remove(callback)
    
    def create_custom_theme(
        self,
        name: str,
        base_theme: str = "default",
        color_overrides: Dict[str, str] = None,
        css_overrides: str = None
    ) -> bool:
        """Create a custom theme."""
        try:
            base = self._load_theme(base_theme)
            
            custom_theme_data = {
                "name": name,
                "display_name": name.title(),
                "base_theme": base_theme,
                "color_overrides": color_overrides or {},
                "css_overrides": css_overrides or "",
                "created_date": str(Path.cwd()),  # Simple timestamp placeholder
                "version": "1.0"
            }
            
            self._custom_themes[name] = custom_theme_data
            self._save_custom_themes()
            
            self.logger.info(f"Created custom theme: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create custom theme '{name}': {e}")
            return False
    
    def delete_custom_theme(self, name: str) -> bool:
        """Delete a custom theme."""
        if name in self._custom_themes:
            del self._custom_themes[name]
            
            # Remove from cache
            if name in self._theme_cache:
                del self._theme_cache[name]
            
            self._save_custom_themes()
            self.logger.info(f"Deleted custom theme: {name}")
            return True
        
        return False
    
    def export_theme(self, theme_name: str, export_path: Path) -> bool:
        """Export a theme to a file."""
        try:
            if theme_name in self._custom_themes:
                theme_data = self._custom_themes[theme_name]
            else:
                # Export built-in theme structure
                theme = self._load_theme(theme_name)
                theme_data = {
                    "name": theme_name,
                    "display_name": theme.name,
                    "base_theme": theme_name,
                    "color_overrides": {},
                    "css_overrides": "",
                    "version": "1.0",
                    "exported_css": theme.get_css()
                }
            
            with open(export_path, 'w') as f:
                json.dump(theme_data, f, indent=2)
            
            self.logger.info(f"Exported theme '{theme_name}' to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export theme '{theme_name}': {e}")
            return False
    
    def import_theme(self, import_path: Path) -> bool:
        """Import a theme from a file."""
        try:
            with open(import_path, 'r') as f:
                theme_data = json.load(f)
            
            name = theme_data.get("name", import_path.stem)
            self._custom_themes[name] = theme_data
            self._save_custom_themes()
            
            self.logger.info(f"Imported theme '{name}' from {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import theme from {import_path}: {e}")
            return False
    
    def get_theme_css(self, theme_name: str = None) -> str:
        """Get CSS for a specific theme or current theme."""
        if theme_name is None:
            theme = self.get_current_theme()
        else:
            theme = self._load_theme(theme_name)
        
        return theme.get_css()
    
    def reload_themes(self) -> None:
        """Reload all themes from disk."""
        self._theme_cache.clear()
        self._load_custom_themes()
        
        # Reload current theme
        if self._current_theme:
            current_name = self.get_current_theme_name()
            self._current_theme = None
            self.set_theme(current_name)
    
    def _load_theme(self, theme_name: str) -> BaseTheme:
        """Load a theme by name with caching."""
        if theme_name in self._theme_cache:
            return self._theme_cache[theme_name]
        
        try:
            # Check if it's a custom theme
            if theme_name in self._custom_themes:
                theme = self._create_custom_theme(theme_name)
            else:
                # Load built-in theme
                theme = get_theme_by_name(theme_name)
            
            self._theme_cache[theme_name] = theme
            return theme
            
        except Exception as e:
            self.logger.error(f"Failed to load theme '{theme_name}': {e}")
            # Fallback to default theme
            if theme_name != "default":
                return self._load_theme("default")
            else:
                return DefaultTheme()
    
    def _create_custom_theme(self, theme_name: str) -> BaseTheme:
        """Create a custom theme instance."""
        theme_data = self._custom_themes[theme_name]
        base_theme_name = theme_data.get("base_theme", "default")
        
        # Load base theme
        base_theme = get_theme_by_name(base_theme_name)
        
        # Apply customizations
        if theme_data.get("color_overrides"):
            # Would apply color overrides to base theme palette
            # For now, just return base theme
            pass
        
        if theme_data.get("css_overrides"):
            # Would append CSS overrides
            # For now, just return base theme
            pass
        
        return base_theme
    
    def _load_custom_themes(self) -> None:
        """Load custom themes from disk."""
        config_file = self.config_dir / "custom_themes.json"
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self._custom_themes = json.load(f)
                self.logger.debug(f"Loaded {len(self._custom_themes)} custom themes")
            else:
                self._custom_themes = {}
                
        except Exception as e:
            self.logger.error(f"Failed to load custom themes: {e}")
            self._custom_themes = {}
    
    def _save_custom_themes(self) -> None:
        """Save custom themes to disk."""
        config_file = self.config_dir / "custom_themes.json"
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self._custom_themes, f, indent=2)
            self.logger.debug("Saved custom themes to disk")
            
        except Exception as e:
            self.logger.error(f"Failed to save custom themes: {e}")
    
    def _save_theme_preference(self, theme_name: str) -> None:
        """Save theme preference to application state."""
        # Update the state to reflect the theme change
        try:
            from ..state.actions import change_theme_action
            action = change_theme_action(theme_name)
            # Dispatch the action to update application state
            self.store.dispatch_action(action)
            self.logger.debug(f"Theme preference saved: {theme_name}")
        except Exception as e:
            self.logger.error(f"Failed to save theme preference: {e}")
    
    def get_theme_preferences_path(self) -> Path:
        """Get path to theme preferences file."""
        return self.config_dir / "theme_preferences.json"
    
    def is_dark_theme(self, theme_name: str = None) -> bool:
        """Check if a theme is a dark theme."""
        theme = self._load_theme(theme_name) if theme_name else self.get_current_theme()
        return theme._is_dark_theme()
    
    def get_adaptive_theme(self) -> str:
        """Get adaptive theme based on system settings."""
        # This would detect system theme preference
        # For now, return default
        return "default"