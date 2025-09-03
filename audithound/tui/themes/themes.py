"""Theme definitions for the TUI."""

from typing import Dict, Any
from .colors import ColorPalette, SecurityColors, get_palette_by_name


class BaseTheme:
    """Base theme class."""
    
    def __init__(self, name: str, palette: ColorPalette):
        self.name = name
        self.palette = palette
        self.security_colors = SecurityColors()
        self._css_cache = None
    
    def get_css(self) -> str:
        """Get CSS styles for this theme."""
        if self._css_cache is None:
            self._css_cache = self._generate_css()
        return self._css_cache
    
    def _generate_css(self) -> str:
        """Generate CSS styles from color palette."""
        return f"""
/* {self.name} Theme */

/* App-wide styles */
App {{
    background: {self.palette.background};
    color: {self.palette.text_primary};
}}

/* Header and footer */
Header {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

Footer {{
    background: {self.palette.surface};
    color: {self.palette.text_secondary};
}}

/* Containers and layout */
Vertical, Horizontal {{
    background: transparent;
}}

Container {{
    background: {self.palette.surface};
    border: solid {self.palette.border};
    margin: 1;
    padding: 1;
}}

/* Tabs */
TabbedContent {{
    background: {self.palette.background};
}}

Tabs {{
    background: {self.palette.surface};
    color: {self.palette.text_primary};
}}

Tab {{
    background: {self.palette.surface};
    color: {self.palette.text_secondary};
    margin: 0 1;
    padding: 1 2;
    border: none;
}}

Tab.-active {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

Tab:hover {{
    background: {self.palette.hover};
    color: {self.palette.text_inverse};
}}

TabPane {{
    background: {self.palette.background};
    padding: 1;
}}

/* Buttons */
Button {{
    background: {self.palette.button_secondary};
    color: {self.palette.text_inverse};
    border: none;
    margin: 0 1;
    padding: 1 2;
}}

Button:hover {{
    background: {self.palette.hover};
    text-style: bold;
}}

Button:focus {{
    border: solid {self.palette.focus};
}}

Button.-primary {{
    background: {self.palette.button_primary};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

Button.-success {{
    background: {self.palette.button_success};
    color: {self.palette.text_inverse};
}}

Button.-error, Button.-danger {{
    background: {self.palette.button_danger};
    color: {self.palette.text_inverse};
}}

/* Inputs and form controls */
Input {{
    background: {self.palette.surface};
    color: {self.palette.text_primary};
    border: solid {self.palette.border};
}}

Input:focus {{
    border: solid {self.palette.focus};
    background: {self.palette.background};
}}

Select {{
    background: {self.palette.surface};
    color: {self.palette.text_primary};
    border: solid {self.palette.border};
}}

Select:focus {{
    border: solid {self.palette.focus};
}}

Checkbox {{
    background: {self.palette.surface};
    color: {self.palette.text_primary};
}}

Switch {{
    background: {self.palette.surface};
}}

RadioSet {{
    background: {self.palette.surface};
    color: {self.palette.text_primary};
}}

/* Data tables */
DataTable {{
    background: {self.palette.surface};
    color: {self.palette.text_primary};
    border: solid {self.palette.border};
}}

DataTable > .datatable--header {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

DataTable > .datatable--row:hover {{
    background: {self.palette.hover};
    color: {self.palette.text_inverse};
}}

DataTable > .datatable--row.-selected {{
    background: {self.palette.accent};
    color: {self.palette.text_inverse};
}}

/* Progress bars */
ProgressBar {{
    background: {self.palette.surface};
    color: {self.palette.primary};
    border: solid {self.palette.border};
}}

ProgressBar > .bar--bar {{
    color: {self.palette.primary};
}}

ProgressBar > .bar--percentage {{
    color: {self.palette.text_primary};
}}

/* Static text and labels */
Static {{
    color: {self.palette.text_primary};
}}

Label {{
    color: {self.palette.text_secondary};
}}

/* Panels and sections */
.panel {{
    background: {self.palette.panel};
    border: solid {self.palette.border};
    margin: 1;
    padding: 1;
}}

.section-title {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
    padding: 1;
    margin-bottom: 1;
}}

.summary-panel {{
    background: {self.palette.surface};
    border: solid {self.palette.border};
    margin: 1;
    padding: 1;
}}

/* Security-specific styles */
.severity-critical {{
    background: {self.security_colors.critical};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

.severity-high {{
    background: {self.security_colors.high};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

.severity-medium {{
    background: {self.security_colors.medium};
    color: {self.palette.text_primary};
    text-style: bold;
}}

.severity-low {{
    background: {self.security_colors.low};
    color: {self.palette.text_inverse};
}}

.severity-info {{
    background: {self.security_colors.info};
    color: {self.palette.text_inverse};
}}

/* Scanner type styles */
.scanner-sast {{
    color: {self.security_colors.sast};
    text-style: bold;
}}

.scanner-dast {{
    color: {self.security_colors.dast};
    text-style: bold;
}}

.scanner-sca {{
    color: {self.security_colors.sca};
    text-style: bold;
}}

.scanner-secrets {{
    color: {self.security_colors.secrets};
    text-style: bold;
}}

.scanner-iac {{
    color: {self.security_colors.iac};
    text-style: bold;
}}

/* Status indicators */
.status-vulnerable {{
    color: {self.security_colors.vulnerable};
    text-style: bold;
}}

.status-secure {{
    color: {self.security_colors.secure};
    text-style: bold;
}}

.status-scanning {{
    color: {self.security_colors.scanning};
    text-style: bold;
}}

.status-unknown {{
    color: {self.security_colors.unknown};
}}

/* Navigation and command palette */
.command-palette {{
    background: {self.palette.panel};
    border: solid {self.palette.primary};
    color: {self.palette.text_primary};
}}

.navigation-bar {{
    background: {self.palette.surface};
    border-bottom: solid {self.palette.border};
}}

/* Error and notification styles */
.error {{
    background: {self.palette.error};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

.warning {{
    background: {self.palette.warning};
    color: {self.palette.text_primary};
    text-style: bold;
}}

.success {{
    background: {self.palette.success};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

.info {{
    background: {self.palette.info};
    color: {self.palette.text_inverse};
}}

/* Loading and disabled states */
.loading {{
    color: {self.palette.text_muted};
    text-style: italic;
}}

.disabled {{
    color: {self.palette.disabled};
    text-style: dim;
}}

/* Borders and rules */
Rule {{
    color: {self.palette.border};
}}

/* Collapsible sections */
Collapsible {{
    border: solid {self.palette.border};
    background: {self.palette.surface};
}}

Collapsible > Title {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
}}

Collapsible > Contents {{
    background: {self.palette.background};
    padding: 1;
}}

/* Filter and search controls */
.filter-controls {{
    background: {self.palette.surface};
    border: solid {self.palette.border};
    padding: 1;
    margin-bottom: 1;
}}

.search-input {{
    width: 1fr;
    margin-right: 1;
}}

.clear-button {{
    background: {self.palette.button_danger};
    color: {self.palette.text_inverse};
}}

/* Table status and info */
.table-status {{
    background: {self.palette.surface};
    border-top: solid {self.palette.border};
    padding: 1;
    margin-top: 1;
}}

/* Component-specific styles */
.config-header {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
    padding: 1;
    margin-bottom: 1;
}}

.config-actions {{
    align: right middle;
}}

.scanner-header {{
    background: {self.palette.primary};
    color: {self.palette.text_inverse};
    text-style: bold;
    padding: 1;
}}

.scanner-row {{
    border-bottom: solid {self.palette.border};
    padding: 1;
}}

.scanner-row:hover {{
    background: {self.palette.hover};
    color: {self.palette.text_inverse};
}}
"""
    
    def get_theme_info(self) -> Dict[str, Any]:
        """Get theme metadata."""
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "primary_color": self.palette.primary,
            "background": self.palette.background,
            "is_dark": self._is_dark_theme()
        }
    
    def _is_dark_theme(self) -> bool:
        """Check if this is a dark theme."""
        # Simple heuristic based on background color
        return self.palette.background in ["#000000", "#121212", "#1e1e1e", "#0f1419"]


class DefaultTheme(BaseTheme):
    """Default AuditHound theme (dark)."""
    
    def __init__(self):
        super().__init__("Default", get_palette_by_name("default"))


class DarkTheme(BaseTheme):
    """Dark theme for low-light environments."""
    
    def __init__(self):
        super().__init__("Dark", get_palette_by_name("dark"))


class LightTheme(BaseTheme):
    """Light theme for high-light environments."""
    
    def __init__(self):
        super().__init__("Light", get_palette_by_name("light"))


class HighContrastTheme(BaseTheme):
    """High contrast theme for accessibility."""
    
    def __init__(self):
        super().__init__("High Contrast", get_palette_by_name("high_contrast"))


class SecurityTheme(BaseTheme):
    """Security-focused theme with enhanced threat visualization."""
    
    def __init__(self):
        super().__init__("Security", get_palette_by_name("security"))
    
    def _generate_css(self) -> str:
        """Generate CSS with enhanced security visualizations."""
        base_css = super()._generate_css()
        
        # Add security-specific enhancements
        security_css = f"""

/* Enhanced security visualizations */
.threat-level-critical {{
    background: {self.security_colors.critical};
    color: white;
    text-style: bold;
    border: thick white;
    animation: pulse 2s ease-in-out infinite alternate;
}}

.threat-level-high {{
    background: {self.security_colors.high};
    color: white;
    text-style: bold;
}}

.vulnerability-count {{
    background: {self.security_colors.critical};
    color: white;
    text-style: bold;
    border: round white;
}}

.scanner-progress {{
    border: solid {self.palette.primary};
}}

.scanner-progress.-active {{
    border: solid {self.security_colors.scanning};
    background: {self.security_colors.progress_bg};
}}

.finding-item {{
    margin: 1 0;
    padding: 1;
    border-left: thick {self.security_colors.critical};
}}

.finding-item.-high {{
    border-left: thick {self.security_colors.high};
}}

.finding-item.-medium {{
    border-left: thick {self.security_colors.medium};
}}

.finding-item.-low {{
    border-left: thick {self.security_colors.low};
}}

.risk-score {{
    background: {self.security_colors.critical};
    color: white;
    text-style: bold;
    border: round;
    padding: 0 1;
}}

.remediation-info {{
    background: {self.security_colors.success_bg};
    color: {self.security_colors.secure};
    padding: 1;
    margin: 1 0;
}}
"""
        
        return base_css + security_css


# Theme registry
AVAILABLE_THEMES = {
    "default": DefaultTheme,
    "dark": DarkTheme,
    "light": LightTheme,
    "high_contrast": HighContrastTheme,
    "security": SecurityTheme
}


def get_theme_by_name(name: str) -> BaseTheme:
    """Get a theme instance by name."""
    theme_class = AVAILABLE_THEMES.get(name.lower(), DefaultTheme)
    return theme_class()


def get_available_themes() -> Dict[str, str]:
    """Get list of available themes."""
    return {
        name: theme_class().name 
        for name, theme_class in AVAILABLE_THEMES.items()
    }