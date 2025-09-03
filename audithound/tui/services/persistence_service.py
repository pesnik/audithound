"""Data persistence service for session management."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..state.store import AppStore
from ..state.events import EventType


class PersistenceService:
    """Service for managing data persistence and session state."""
    
    def __init__(self, store: AppStore, data_dir: Path = None):
        self.store = store
        self.data_dir = data_dir or Path.home() / '.audithound' / 'data'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Data files
        self.session_file = self.data_dir / 'session.json'
        self.history_file = self.data_dir / 'scan_history.json'
        self.bookmarks_file = self.data_dir / 'bookmarks.json'
        self.preferences_file = self.data_dir / 'preferences.json'
        
        # Setup event listeners
        self._setup_event_listeners()
    
    def _setup_event_listeners(self) -> None:
        """Setup event listeners for persistence."""
        self.store.listen_to_event(EventType.SCAN_COMPLETED, self._on_scan_completed)
        self.store.listen_to_event(EventType.BOOKMARK_ADDED, self._on_bookmark_added)
        self.store.listen_to_event(EventType.BOOKMARK_REMOVED, self._on_bookmark_removed)
        self.store.listen_to_event(EventType.THEME_CHANGED, self._on_theme_changed)
    
    def _on_scan_completed(self, event) -> None:
        """Handle scan completion for persistence."""
        # Auto-save scan results to history
        self.save_scan_history()
    
    def _on_bookmark_added(self, event) -> None:
        """Handle bookmark addition."""
        self.save_bookmarks()
    
    def _on_bookmark_removed(self, event) -> None:
        """Handle bookmark removal."""
        self.save_bookmarks()
    
    def _on_theme_changed(self, event) -> None:
        """Handle theme changes."""
        self.save_preferences()
    
    def load_session_data(self) -> bool:
        """Load session data from disk."""
        try:
            loaded_any = False
            
            # Load preferences
            if self.preferences_file.exists():
                self.load_preferences()
                loaded_any = True
            
            # Load scan history
            if self.history_file.exists():
                self.load_scan_history()
                loaded_any = True
            
            # Load bookmarks
            if self.bookmarks_file.exists():
                self.load_bookmarks()
                loaded_any = True
            
            # Load last session state
            if self.session_file.exists():
                self.load_session_state()
                loaded_any = True
            
            if loaded_any:
                self.logger.info("Session data loaded successfully")
            else:
                self.logger.info("No previous session data found")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to load session data: {e}")
            return False
    
    def save_session_data(self) -> bool:
        """Save current session data to disk."""
        try:
            # Save current session state
            self.save_session_state()
            
            # Save preferences
            self.save_preferences()
            
            # Save scan history
            self.save_scan_history()
            
            # Save bookmarks
            self.save_bookmarks()
            
            self.logger.info("Session data saved successfully")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save session data: {e}")
            return False
    
    def save_session_state(self) -> bool:
        """Save current session state."""
        try:
            state = self.store.get_state()
            
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "current_tab": state.current_tab,
                "theme": state.theme,
                "scan_target": state.scan_target,
                "scan_tools": state.scan_tools,
                "filters": state.filters,
                "sidebar_visible": state.sidebar_visible,
                "window_state": {
                    "maximized": True,  # Would get from actual window state
                    "size": [80, 24]    # Terminal size
                }
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.debug("Session state saved")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save session state: {e}")
            return False
    
    def load_session_state(self) -> bool:
        """Load previous session state."""
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Apply session state to store
            from ..state.actions import (
                change_tab_action, change_theme_action, 
                start_scan_action, Action, ActionType
            )
            
            # Restore tab
            if "current_tab" in session_data:
                self.store.dispatch_action(change_tab_action(session_data["current_tab"]))
            
            # Restore theme
            if "theme" in session_data:
                self.store.dispatch_action(change_theme_action(session_data["theme"]))
            
            # Restore scan target and tools
            state = self.store.get_state()
            if "scan_target" in session_data:
                state.scan_target = session_data["scan_target"]
            if "scan_tools" in session_data:
                state.scan_tools = session_data["scan_tools"]
            
            # Restore filters
            if "filters" in session_data:
                state.filters = session_data["filters"]
            
            self.logger.debug("Session state loaded")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to load session state: {e}")
            return False
    
    def save_scan_history(self) -> bool:
        """Save scan history to disk."""
        try:
            state = self.store.get_state()
            history_data = {
                "last_updated": datetime.now().isoformat(),
                "scan_history": [
                    {
                        "scan_id": scan.get("scan_id"),
                        "target": scan.get("target"),
                        "timestamp": scan.get("timestamp").isoformat() if hasattr(scan.get("timestamp"), 'isoformat') else str(scan.get("timestamp")),
                        "findings_count": scan.get("findings_count"),
                        "duration": scan.get("duration"),
                        "tools_used": scan.get("tools_used", [])
                    }
                    for scan in state.scan_history
                ]
            }
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            self.logger.debug(f"Scan history saved ({len(state.scan_history)} scans)")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save scan history: {e}")
            return False
    
    def load_scan_history(self) -> bool:
        """Load scan history from disk."""
        try:
            with open(self.history_file, 'r') as f:
                history_data = json.load(f)
            
            # Convert timestamps back to datetime objects
            scan_history = []
            for scan in history_data.get("scan_history", []):
                scan_copy = scan.copy()
                if "timestamp" in scan_copy:
                    try:
                        scan_copy["timestamp"] = datetime.fromisoformat(scan_copy["timestamp"])
                    except ValueError:
                        # Fallback for older timestamp formats
                        scan_copy["timestamp"] = datetime.now()
                scan_history.append(scan_copy)
            
            # Update state
            state = self.store.get_state()
            state.scan_history = scan_history
            
            self.logger.debug(f"Scan history loaded ({len(scan_history)} scans)")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to load scan history: {e}")
            return False
    
    def save_bookmarks(self) -> bool:
        """Save bookmarks to disk."""
        try:
            state = self.store.get_state()
            bookmarks_data = {
                "last_updated": datetime.now().isoformat(),
                "bookmarks": state.bookmarks
            }
            
            with open(self.bookmarks_file, 'w') as f:
                json.dump(bookmarks_data, f, indent=2)
            
            self.logger.debug(f"Bookmarks saved ({len(state.bookmarks)} bookmarks)")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save bookmarks: {e}")
            return False
    
    def load_bookmarks(self) -> bool:
        """Load bookmarks from disk."""
        try:
            with open(self.bookmarks_file, 'r') as f:
                bookmarks_data = json.load(f)
            
            # Update state
            state = self.store.get_state()
            state.bookmarks = bookmarks_data.get("bookmarks", {})
            
            self.logger.debug(f"Bookmarks loaded ({len(state.bookmarks)} bookmarks)")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to load bookmarks: {e}")
            return False
    
    def save_preferences(self) -> bool:
        """Save user preferences to disk."""
        try:
            state = self.store.get_state()
            preferences_data = {
                "last_updated": datetime.now().isoformat(),
                "theme": state.theme,
                "sidebar_visible": state.sidebar_visible,
                "default_export_format": "json",  # Would get from config
                "auto_save_results": True,
                "max_history_items": 50,
                "show_notifications": True,
                "notification_timeout": 5
            }
            
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences_data, f, indent=2)
            
            self.logger.debug("User preferences saved")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")
            return False
    
    def load_preferences(self) -> bool:
        """Load user preferences from disk."""
        try:
            with open(self.preferences_file, 'r') as f:
                preferences_data = json.load(f)
            
            # Apply preferences to state
            state = self.store.get_state()
            if "theme" in preferences_data:
                state.theme = preferences_data["theme"]
            if "sidebar_visible" in preferences_data:
                state.sidebar_visible = preferences_data["sidebar_visible"]
            
            self.logger.debug("User preferences loaded")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to load preferences: {e}")
            return False
    
    def export_scan_results(
        self,
        scan_id: str,
        output_path: Path,
        format_type: str = "json"
    ) -> bool:
        """Export specific scan results."""
        try:
            state = self.store.get_state()
            
            # Find the scan in history
            target_scan = None
            for scan in state.scan_history:
                if scan.get("scan_id") == scan_id:
                    target_scan = scan
                    break
            
            if not target_scan:
                self.logger.error(f"Scan {scan_id} not found in history")
                return False
            
            # Export the scan data
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "scan_data": target_scan,
                "format_version": "1.0"
            }
            
            if format_type.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            else:
                # Add support for other formats as needed
                with open(output_path, 'w') as f:
                    f.write(str(export_data))
            
            self.logger.info(f"Scan {scan_id} exported to {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to export scan {scan_id}: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old scan data."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            state = self.store.get_state()
            
            original_count = len(state.scan_history)
            
            # Filter out old scans
            state.scan_history = [
                scan for scan in state.scan_history
                if hasattr(scan.get("timestamp"), 'timestamp') and 
                   scan["timestamp"].timestamp() > cutoff_date
            ]
            
            cleaned_count = original_count - len(state.scan_history)
            
            if cleaned_count > 0:
                self.save_scan_history()
                self.logger.info(f"Cleaned up {cleaned_count} old scan records")
            
            return cleaned_count
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            stats = {
                "data_directory": str(self.data_dir),
                "files": {},
                "total_size": 0
            }
            
            for file_path in [
                self.session_file,
                self.history_file,
                self.bookmarks_file,
                self.preferences_file
            ]:
                if file_path.exists():
                    size = file_path.stat().st_size
                    stats["files"][file_path.name] = {
                        "size": size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                    stats["total_size"] += size
            
            return stats
        
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {"error": str(e)}