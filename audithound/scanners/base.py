"""Base scanner interface for all security scanners."""

import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..core.config import ScannerConfig
from ..utils.docker import DockerRunner


class BaseScanner(ABC):
    """Abstract base class for all security scanners."""
    
    def __init__(self, config: ScannerConfig, docker_runner: Optional[DockerRunner] = None):
        self.config = config
        self.docker_runner = docker_runner
        self.name = self.__class__.__name__.replace('Scanner', '').lower()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def scan(self, target: Path) -> List[Dict[str, Any]]:
        """
        Run the scanner on the target path.
        
        Args:
            target: Path to scan
            
        Returns:
            List of findings as dictionaries
        """
        pass
    
    @abstractmethod
    def get_command(self, target: Path) -> List[str]:
        """
        Get the command to run the scanner.
        
        Args:
            target: Path to scan
            
        Returns:
            Command as list of strings
        """
        pass
    
    @abstractmethod
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse scanner output into standardized findings format.
        
        Args:
            output: Raw scanner output
            
        Returns:
            List of findings as dictionaries
        """
        pass
    
    def is_available(self) -> bool:
        """Check if the scanner is available (installed)."""
        self.logger.debug(f"Checking availability for {self.name} scanner")
        
        if self.docker_runner:
            # If using Docker, assume scanner is available in container
            self.logger.debug(f"{self.name} using Docker, assuming available")
            return True
        
        # Check if scanner binary is in PATH directly
        binary_name = self.get_binary_name()
        if shutil.which(binary_name) is not None:
            self.logger.debug(f"{self.name} binary found in PATH: {binary_name}")
            return True
            
        # Check if uv is available and can run the scanner
        if shutil.which('uv') is not None:
            try:
                self.logger.debug(f"Trying to run {self.name} via uv")
                result = subprocess.run(
                    ['uv', 'run', binary_name, '--help'],
                    capture_output=True,
                    timeout=10
                )
                available = result.returncode == 0
                if available:
                    self.logger.debug(f"{self.name} available via uv")
                else:
                    self.logger.debug(f"{self.name} not available via uv (exit code: {result.returncode})")
                return available
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                self.logger.debug(f"{self.name} check via uv failed: {e}")
        
        self.logger.warning(f"{self.name} scanner not available")
        return False
    
    def get_binary_name(self) -> str:
        """Get the name of the scanner binary."""
        return self.name
    
    def _get_command_prefix(self) -> List[str]:
        """Get command prefix (empty list or 'uv run')."""
        # If scanner is directly available, no prefix needed
        if shutil.which(self.get_binary_name()) is not None:
            return []
        
        # If uv is available, use it
        if shutil.which('uv') is not None:
            return ['uv', 'run']
        
        return []
    
    def get_version(self) -> str:
        """Get scanner version."""
        try:
            cmd = self._get_command_prefix() + [self.get_binary_name(), '--version']
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.stdout.strip() or result.stderr.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return "unknown"
    
    def run_command(self, cmd: List[str], target: Path) -> str:
        """
        Execute the scanner command.
        
        Args:
            cmd: Command to execute
            target: Target path being scanned
            
        Returns:
            Command output as string
            
        Raises:
            subprocess.CalledProcessError: If command fails
        """
        if self.docker_runner:
            return self.docker_runner.run_command(cmd, target, self.get_docker_image())
        else:
            return self._run_native_command(cmd, target)
    
    def _run_native_command(self, cmd: List[str], target: Path) -> str:
        """Run command natively (without Docker)."""
        # Add command prefix (uv run if needed)
        final_cmd = self._get_command_prefix() + cmd
        
        try:
            result = subprocess.run(
                final_cmd,
                cwd=target,
                capture_output=True,
                text=True,
                timeout=self.docker_runner.timeout if self.docker_runner else 300,
                check=False  # Don't raise exception on non-zero exit
            )
            
            # Many security scanners return non-zero exit codes when findings are found
            # So we don't check return code here, just return the output
            return result.stdout
            
        except subprocess.TimeoutExpired:
            raise subprocess.CalledProcessError(
                -1, final_cmd, f"Scanner timed out after {300}s"
            )
        except Exception as e:
            raise subprocess.CalledProcessError(-1, final_cmd, str(e))
    
    def get_docker_image(self) -> str:
        """Get Docker image name for this scanner."""
        # Override in subclasses if needed
        return f"securityscanner/{self.name}:latest"
    
    def should_exclude_path(self, path: Path, base_path: Path) -> bool:
        """Check if a path should be excluded from scanning."""
        relative_path = str(path.relative_to(base_path))
        
        for pattern in self.config.exclude_patterns:
            if self._matches_pattern(relative_path, pattern):
                return True
        
        return False
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches exclusion pattern."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
    
    def filter_by_severity(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter findings by severity threshold."""
        severity_levels = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1,
            'info': 0
        }
        
        threshold = severity_levels.get(self.config.severity_threshold.lower(), 2)
        
        filtered = []
        for finding in findings:
            finding_severity = finding.get('severity', 'medium').lower()
            finding_level = severity_levels.get(finding_severity, 2)
            
            if finding_level >= threshold:
                filtered.append(finding)
        
        return filtered