"""Logging configuration for AuditHound."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any


def setup_logging(
    log_level: str = "INFO",
    log_file: Path = None,
    console: bool = True,
    debug_mode: bool = False
) -> None:
    """Setup logging configuration for AuditHound.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, uses ~/.audithound/logs/audithound.log)
        console: Whether to log to console/stderr
        debug_mode: Enable debug logging with verbose formatting
    """
    
    # Default log directory
    if log_file is None:
        log_dir = Path.home() / '.audithound' / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'audithound.log'
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Log format
    if debug_mode:
        log_format = (
            "%(asctime)s | %(levelname)-8s | %(name)-30s | "
            "%(funcName)-20s:%(lineno)-3d | %(message)s"
        )
    else:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
    
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Logging configuration
    config: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format,
                'datefmt': date_format,
            },
            'console': {
                'format': "%(levelname)-8s | %(name)-20s | %(message)s",
            }
        },
        'handlers': {},
        'loggers': {
            'audithound': {
                'level': log_level,
                'handlers': [],
                'propagate': False,
            },
            # Third-party loggers
            'docker': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': False,
            },
            'urllib3': {
                'level': 'WARNING', 
                'handlers': [],
                'propagate': False,
            }
        },
        'root': {
            'level': 'WARNING',
            'handlers': [],
        }
    }
    
    handlers = []
    
    # File handler
    if log_file:
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(log_file),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'standard',
            'level': log_level,
        }
        handlers.append('file')
    
    # Console handler
    if console:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'console',
            'level': 'WARNING' if not debug_mode else log_level,
        }
        handlers.append('console')
    
    # Assign handlers
    config['loggers']['audithound']['handlers'] = handlers
    config['loggers']['docker']['handlers'] = handlers  
    config['loggers']['urllib3']['handlers'] = handlers
    config['root']['handlers'] = handlers
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log the configuration
    logger = logging.getLogger('audithound.logging')
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}, Console: {console}")
    
    if debug_mode:
        logger.debug("Debug logging enabled with verbose formatting")


def get_log_file_path() -> Path:
    """Get the default log file path."""
    return Path.home() / '.audithound' / 'logs' / 'audithound.log'


def get_log_level_from_env() -> str:
    """Get log level from environment variable."""
    import os
    return os.getenv('AUDITHOUND_LOG_LEVEL', 'INFO').upper()


def configure_for_tui(log_file: Path = None) -> None:
    """Configure logging optimized for TUI mode.
    
    - Minimal console output (errors only)
    - Detailed file logging
    - TUI-specific loggers
    """
    setup_logging(
        log_level="DEBUG",
        log_file=log_file,
        console=True,  # Only errors to console
        debug_mode=False
    )
    
    # Additional TUI-specific configuration
    logger = logging.getLogger('audithound.tui')
    logger.info("TUI logging configuration applied")


def configure_for_cli(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging for CLI mode.
    
    Args:
        verbose: Enable verbose output
        quiet: Minimize console output
    """
    if verbose:
        level = "DEBUG"
        console = True
        debug = True
    elif quiet:
        level = "ERROR" 
        console = False
        debug = False
    else:
        level = "INFO"
        console = True  
        debug = False
    
    setup_logging(
        log_level=level,
        console=console,
        debug_mode=debug
    )
    
    logger = logging.getLogger('audithound.cli')
    logger.info(f"CLI logging configured - Verbose: {verbose}, Quiet: {quiet}")