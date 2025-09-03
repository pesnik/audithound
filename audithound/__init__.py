"""AuditHound - Security audit compliance scanning tool."""

__version__ = "0.1.0"
__author__ = "AuditHound Team"
__description__ = "A robust TUI application for security audit compliance scanning"

from .core.config import Config
from .core.scanner import SecurityScanner

__all__ = ["Config", "SecurityScanner", "__version__"]