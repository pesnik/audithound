"""Advanced data display components with virtualization and filtering."""

import logging
from typing import Any, Dict, List, Optional, Callable, Union
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Input, Select, Button, Static, Checkbox
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text

from .base import BaseComponent, StatelessComponent


class FilterableTable(BaseComponent):
    """Data table with built-in filtering and search capabilities."""
    
    filter_text = reactive("")
    sort_column = reactive("")
    sort_reverse = reactive(False)
    
    class FilterChanged(Message):
        """Message sent when filter changes."""
        def __init__(self, filter_text: str, filter_column: str = None) -> None:
            self.filter_text = filter_text
            self.filter_column = filter_column
            super().__init__()
    
    class SortChanged(Message):
        """Message sent when sort changes."""
        def __init__(self, column: str, reverse: bool = False) -> None:
            self.column = column
            self.reverse = reverse
            super().__init__()
    
    def __init__(
        self,
        store,
        columns: List[str] = None,
        data: List[Dict[str, Any]] = None,
        searchable_columns: List[str] = None,
        sortable_columns: List[str] = None,
        **kwargs
    ):
        super().__init__(store, **kwargs)
        self.columns = columns or []
        self.raw_data = data or []
        self.filtered_data = []
        self.searchable_columns = searchable_columns or self.columns
        self.sortable_columns = sortable_columns or self.columns
        
        # Filter state
        self.active_filters: Dict[str, Any] = {}
        self.column_filters: Dict[str, str] = {}
    
    def compose(self) -> ComposeResult:
        with Vertical():
            # Filter controls
            with Horizontal(classes="filter-controls"):
                yield Input(
                    placeholder="Search...",
                    id="search-input",
                    classes="search-input"
                )
                yield Select(
                    [("All Columns", "all")] + [(col, col) for col in self.searchable_columns],
                    value="all",
                    id="search-column-select"
                )
                yield Button("Clear", id="clear-filters", classes="clear-button")
            
            # Advanced filters (collapsible)
            with Horizontal(classes="advanced-filters", id="advanced-filters"):
                yield Static("Filters: None active", id="filter-status")
                yield Button("Advanced ⏷", id="toggle-advanced", classes="toggle-button")
            
            # Data table
            yield DataTable(
                cursor_type="row",
                zebra_stripes=True,
                id="data-table"
            )
            
            # Status bar
            with Horizontal(classes="table-status"):
                yield Static("", id="table-info")
                yield Static("", id="selection-info")
    
    def on_mount(self) -> None:
        """Initialize the filterable table."""
        super().on_mount()
        self._setup_table()
        self._update_data()
    
    def on_component_mounted(self) -> None:
        """Setup table when component is mounted."""
        pass
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes."""
        # Update data if needed based on state
        pass
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search-input":
            self.filter_text = event.value
            self._apply_filters()
            self.post_message(self.FilterChanged(event.value))
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle filter column selection."""
        if event.select.id == "search-column-select":
            self._apply_filters()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "clear-filters":
            self._clear_filters()
        elif event.button.id == "toggle-advanced":
            self._toggle_advanced_filters()
    
    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header clicks for sorting."""
        column_key = event.column_key
        
        if column_key in self.sortable_columns:
            # Toggle sort direction if same column
            if self.sort_column == column_key:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = column_key
                self.sort_reverse = False
            
            self._apply_sort()
            self.post_message(self.SortChanged(column_key, self.sort_reverse))
    
    def set_data(self, data: List[Dict[str, Any]], columns: List[str] = None) -> None:
        """Set new data for the table."""
        if columns:
            self.columns = columns
        self.raw_data = data
        self._update_data()
    
    def add_filter(self, column: str, value: Any, operator: str = "contains") -> None:
        """Add a filter to the table."""
        self.active_filters[column] = {"value": value, "operator": operator}
        self._apply_filters()
    
    def remove_filter(self, column: str) -> None:
        """Remove a filter from the table."""
        if column in self.active_filters:
            del self.active_filters[column]
            self._apply_filters()
    
    def clear_filters(self) -> None:
        """Clear all filters."""
        self._clear_filters()
    
    def get_selected_rows(self) -> List[Dict[str, Any]]:
        """Get currently selected rows."""
        table = self.query_one("#data-table", DataTable)
        selected_rows = []
        
        for row_key in table.selection:
            try:
                row_index = int(row_key)
                if 0 <= row_index < len(self.filtered_data):
                    selected_rows.append(self.filtered_data[row_index])
            except (ValueError, IndexError):
                continue
        
        return selected_rows
    
    def _setup_table(self) -> None:
        """Setup the data table columns."""
        if not self.columns:
            return
        
        table = self.query_one("#data-table", DataTable)
        table.clear()
        
        # Add columns
        for column in self.columns:
            sortable = column in self.sortable_columns
            table.add_column(column, key=column)
    
    def _update_data(self) -> None:
        """Update the table with current data."""
        self._apply_filters()
    
    def _apply_filters(self) -> None:
        """Apply current filters to the data."""
        self.filtered_data = self.raw_data.copy()
        
        # Apply text search
        search_text = self.filter_text.lower()
        if search_text:
            search_column = self._get_search_column()
            
            if search_column == "all":
                # Search all searchable columns
                self.filtered_data = [
                    row for row in self.filtered_data
                    if any(
                        search_text in str(row.get(col, "")).lower()
                        for col in self.searchable_columns
                    )
                ]
            else:
                # Search specific column
                self.filtered_data = [
                    row for row in self.filtered_data
                    if search_text in str(row.get(search_column, "")).lower()
                ]
        
        # Apply column filters
        for column, filter_config in self.active_filters.items():
            value = filter_config["value"]
            operator = filter_config.get("operator", "contains")
            
            if operator == "contains":
                self.filtered_data = [
                    row for row in self.filtered_data
                    if str(value).lower() in str(row.get(column, "")).lower()
                ]
            elif operator == "equals":
                self.filtered_data = [
                    row for row in self.filtered_data
                    if row.get(column) == value
                ]
            elif operator == "greater_than":
                self.filtered_data = [
                    row for row in self.filtered_data
                    if self._safe_compare(row.get(column), value) > 0
                ]
            elif operator == "less_than":
                self.filtered_data = [
                    row for row in self.filtered_data
                    if self._safe_compare(row.get(column), value) < 0
                ]
        
        # Apply sorting
        if self.sort_column:
            self._apply_sort()
        
        # Update table display
        self._refresh_table()
        self._update_status()
    
    def _apply_sort(self) -> None:
        """Apply current sort to filtered data."""
        if not self.sort_column or self.sort_column not in self.columns:
            return
        
        def sort_key(row):
            value = row.get(self.sort_column, "")
            # Try to convert to number for proper numeric sorting
            try:
                return float(value) if value else 0
            except (ValueError, TypeError):
                return str(value).lower()
        
        self.filtered_data.sort(key=sort_key, reverse=self.sort_reverse)
        self._refresh_table()
    
    def _refresh_table(self) -> None:
        """Refresh the table display with filtered data."""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        
        # Re-add columns (in case they changed)
        for column in self.columns:
            table.add_column(column, key=column)
        
        # Add filtered data rows
        for i, row in enumerate(self.filtered_data):
            row_data = []
            for column in self.columns:
                value = row.get(column, "")
                # Format value for display
                if isinstance(value, (int, float)):
                    if column.lower() in ["severity", "priority", "score"]:
                        # Color-code severity values
                        text = Text(str(value))
                        if isinstance(value, str):
                            if value.lower() in ["critical", "high"]:
                                text.stylize("bold red")
                            elif value.lower() == "medium":
                                text.stylize("yellow")
                            elif value.lower() == "low":
                                text.stylize("blue")
                        row_data.append(text)
                    else:
                        row_data.append(str(value))
                else:
                    row_data.append(str(value))
            
            table.add_row(*row_data, key=str(i))
    
    def _update_status(self) -> None:
        """Update status information."""
        try:
            table_info = self.query_one("#table-info", Static)
            total_rows = len(self.raw_data)
            filtered_rows = len(self.filtered_data)
            
            if self.active_filters or self.filter_text:
                info_text = f"Showing {filtered_rows} of {total_rows} rows"
            else:
                info_text = f"Total: {total_rows} rows"
            
            table_info.update(info_text)
            
            # Update filter status
            filter_status = self.query_one("#filter-status", Static)
            active_count = len(self.active_filters) + (1 if self.filter_text else 0)
            if active_count > 0:
                filter_status.update(f"Filters: {active_count} active")
            else:
                filter_status.update("Filters: None active")
        
        except Exception as e:
            self.logger.debug(f"Error updating status: {e}")
    
    def _get_search_column(self) -> str:
        """Get the currently selected search column."""
        try:
            select = self.query_one("#search-column-select", Select)
            return select.value
        except:
            return "all"
    
    def _clear_filters(self) -> None:
        """Clear all filters and search."""
        self.filter_text = ""
        self.active_filters.clear()
        
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.value = ""
            
            search_select = self.query_one("#search-column-select", Select)
            search_select.value = "all"
        except Exception as e:
            self.logger.debug(f"Error clearing filters: {e}")
        
        self._apply_filters()
    
    def _toggle_advanced_filters(self) -> None:
        """Toggle advanced filter panel visibility."""
        # This would show/hide additional filter controls
        # Implementation depends on specific UI design
        pass
    
    def _safe_compare(self, a: Any, b: Any) -> int:
        """Safely compare two values."""
        try:
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return a - b
            else:
                return (str(a) > str(b)) - (str(a) < str(b))
        except (TypeError, ValueError):
            return 0


class VirtualTable(BaseComponent):
    """High-performance table with virtualization for large datasets."""
    
    def __init__(
        self,
        store,
        data_provider: Callable[[int, int], List[Dict[str, Any]]],
        total_rows: int,
        columns: List[str],
        row_height: int = 1,
        **kwargs
    ):
        super().__init__(store, **kwargs)
        self.data_provider = data_provider
        self.total_rows = total_rows
        self.columns = columns
        self.row_height = row_height
        self.visible_rows = 20  # Will be calculated based on container size
        self.scroll_offset = 0
        self.cached_data: Dict[int, Dict[str, Any]] = {}
        self.cache_size = 100
    
    def compose(self) -> ComposeResult:
        with Vertical():
            # Virtual table container
            with Vertical(id="virtual-table-container"):
                yield DataTable(
                    cursor_type="row",
                    zebra_stripes=True,
                    id="virtual-table"
                )
            
            # Virtual scrollbar info
            yield Static("", id="virtual-scroll-info")
    
    def on_component_mounted(self) -> None:
        """Initialize virtual table."""
        self._setup_virtual_table()
        self._load_visible_data()
    
    def on_state_changed(self, new_state, old_state) -> None:
        """Handle state changes for virtual table."""
        pass
    
    def _setup_virtual_table(self) -> None:
        """Setup the virtual table structure."""
        table = self.query_one("#virtual-table", DataTable)
        table.clear()
        
        # Add columns
        for column in self.columns:
            table.add_column(column, key=column)
    
    def _load_visible_data(self, offset: int = 0) -> None:
        """Load data for currently visible rows."""
        end_offset = min(offset + self.visible_rows, self.total_rows)
        
        # Check cache first
        rows_to_load = []
        for i in range(offset, end_offset):
            if i not in self.cached_data:
                rows_to_load.append(i)
        
        # Load missing rows
        if rows_to_load:
            start_idx = min(rows_to_load)
            count = len(rows_to_load)
            new_data = self.data_provider(start_idx, count)
            
            # Cache the new data
            for i, row_data in enumerate(new_data):
                self.cached_data[start_idx + i] = row_data
            
            # Manage cache size
            self._manage_cache()
        
        # Update table display
        self._refresh_virtual_display(offset, end_offset)
    
    def _refresh_virtual_display(self, start: int, end: int) -> None:
        """Refresh the virtual table display."""
        table = self.query_one("#virtual-table", DataTable)
        table.clear()
        
        # Re-add columns
        for column in self.columns:
            table.add_column(column, key=column)
        
        # Add visible rows
        for i in range(start, end):
            if i in self.cached_data:
                row_data = self.cached_data[i]
                display_row = [str(row_data.get(col, "")) for col in self.columns]
                table.add_row(*display_row, key=str(i))
        
        # Update scroll info
        self._update_scroll_info(start, end)
    
    def _update_scroll_info(self, start: int, end: int) -> None:
        """Update virtual scroll information."""
        try:
            info_widget = self.query_one("#virtual-scroll-info", Static)
            info_text = f"Rows {start + 1}-{end} of {self.total_rows}"
            info_widget.update(info_text)
        except Exception as e:
            self.logger.debug(f"Error updating scroll info: {e}")
    
    def _manage_cache(self) -> None:
        """Manage cache size to prevent memory issues."""
        if len(self.cached_data) > self.cache_size:
            # Remove oldest entries (simple LRU)
            keys_to_remove = list(self.cached_data.keys())[:-self.cache_size]
            for key in keys_to_remove:
                del self.cached_data[key]
    
    def scroll_to(self, row: int) -> None:
        """Scroll to a specific row."""
        if 0 <= row < self.total_rows:
            self.scroll_offset = row
            self._load_visible_data(self.scroll_offset)
    
    def refresh_data(self, new_total_rows: int = None) -> None:
        """Refresh the virtual table data."""
        if new_total_rows:
            self.total_rows = new_total_rows
        
        self.cached_data.clear()
        self._load_visible_data(self.scroll_offset)