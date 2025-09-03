"""Color definitions and palettes for TUI themes."""

from dataclasses import dataclass
from typing import Dict, Any
from rich.color import Color


@dataclass
class ColorPalette:
    """Base color palette for themes."""
    
    # Primary brand colors
    primary: str = "#0066cc"
    secondary: str = "#6c757d"
    accent: str = "#17a2b8"
    
    # Background colors
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    panel: str = "#e9ecef"
    
    # Text colors
    text_primary: str = "#212529"
    text_secondary: str = "#6c757d"
    text_muted: str = "#adb5bd"
    text_inverse: str = "#ffffff"
    
    # Status colors
    success: str = "#28a745"
    warning: str = "#ffc107"
    error: str = "#dc3545"
    info: str = "#17a2b8"
    
    # Interactive elements
    button_primary: str = "#0066cc"
    button_secondary: str = "#6c757d"
    button_success: str = "#28a745"
    button_danger: str = "#dc3545"
    
    # Borders and dividers
    border: str = "#dee2e6"
    border_dark: str = "#adb5bd"
    divider: str = "#e9ecef"
    
    # Special states
    hover: str = "#0056b3"
    active: str = "#004085"
    focus: str = "#80bdff"
    disabled: str = "#adb5bd"


@dataclass 
class SecurityColors:
    """Security-specific color mappings."""
    
    # Severity levels
    critical: str = "#dc3545"  # Red
    high: str = "#fd7e14"      # Orange
    medium: str = "#ffc107"    # Yellow
    low: str = "#17a2b8"       # Cyan
    info: str = "#6c757d"      # Gray
    
    # Security states
    vulnerable: str = "#dc3545"
    secure: str = "#28a745"
    unknown: str = "#6c757d"
    scanning: str = "#17a2b8"
    
    # Scanner types
    sast: str = "#6f42c1"      # Purple
    dast: str = "#e83e8c"      # Pink
    sca: str = "#fd7e14"       # Orange
    secrets: str = "#dc3545"   # Red
    iac: str = "#20c997"       # Teal
    
    # Progress and status
    progress_bg: str = "#e9ecef"
    progress_fill: str = "#0066cc"
    success_bg: str = "#d4edda"
    warning_bg: str = "#fff3cd"
    error_bg: str = "#f8d7da"
    info_bg: str = "#d1ecf1"


# Pre-defined color palettes

LIGHT_PALETTE = ColorPalette(
    primary="#0066cc",
    secondary="#6c757d", 
    accent="#17a2b8",
    background="#ffffff",
    surface="#f8f9fa",
    panel="#e9ecef",
    text_primary="#212529",
    text_secondary="#6c757d",
    text_muted="#adb5bd",
    border="#dee2e6"
)

DARK_PALETTE = ColorPalette(
    primary="#4da6ff",
    secondary="#868e96",
    accent="#20c997",
    background="#121212",
    surface="#1e1e1e",
    panel="#2d2d2d",
    text_primary="#ffffff",
    text_secondary="#adb5bd",
    text_muted="#6c757d",
    text_inverse="#000000",
    border="#495057",
    border_dark="#343a40"
)

HIGH_CONTRAST_PALETTE = ColorPalette(
    primary="#0000ff",
    secondary="#808080",
    accent="#00ffff",
    background="#000000",
    surface="#1a1a1a",
    panel="#333333",
    text_primary="#ffffff",
    text_secondary="#cccccc",
    text_muted="#999999",
    border="#ffffff",
    success="#00ff00",
    warning="#ffff00",
    error="#ff0000",
    info="#00ffff"
)

SECURITY_PALETTE = ColorPalette(
    primary="#2c5aa0",
    secondary="#6c757d",
    accent="#dc3545",
    background="#0f1419",
    surface="#1a1f26",
    panel="#242b35",
    text_primary="#e1e8ed",
    text_secondary="#8ba2b5",
    text_muted="#5c6b7a",
    border="#2c3e50"
)


def get_palette_by_name(name: str) -> ColorPalette:
    """Get a color palette by name."""
    palettes = {
        "light": LIGHT_PALETTE,
        "dark": DARK_PALETTE,
        "high_contrast": HIGH_CONTRAST_PALETTE,
        "security": SECURITY_PALETTE,
        "default": DARK_PALETTE  # Default to dark
    }
    return palettes.get(name.lower(), DARK_PALETTE)


def get_security_color(severity: str) -> str:
    """Get color for security severity level."""
    colors = SecurityColors()
    return getattr(colors, severity.lower(), colors.info)


def lighten_color(color: str, factor: float = 0.2) -> str:
    """Lighten a color by the given factor."""
    try:
        rich_color = Color.parse(color)
        # Simple approximation - in production would use proper color math
        return color  # For now, return original
    except:
        return color


def darken_color(color: str, factor: float = 0.2) -> str:
    """Darken a color by the given factor."""
    try:
        rich_color = Color.parse(color)
        # Simple approximation - in production would use proper color math
        return color  # For now, return original
    except:
        return color


def get_contrast_color(background: str) -> str:
    """Get appropriate text color for given background."""
    # Simple heuristic - in production would calculate actual contrast
    dark_backgrounds = ["#000000", "#121212", "#1e1e1e", "#0f1419"]
    if any(bg in background.lower() for bg in dark_backgrounds):
        return "#ffffff"
    return "#000000"