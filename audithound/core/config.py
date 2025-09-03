"""Configuration management for AuditHound."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ScannerConfig:
    """Configuration for individual scanners."""
    enabled: bool = True
    args: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    severity_threshold: str = "medium"


@dataclass
class OutputConfig:
    """Output configuration."""
    format: str = "json"
    file: Optional[str] = None
    include_passed: bool = False
    group_by_severity: bool = True


@dataclass
class Config:
    """Main configuration class for AuditHound."""
    
    # Scanning configuration
    target_path: str = "."
    exclude_paths: List[str] = field(default_factory=lambda: [".git", "__pycache__", "node_modules"])
    include_hidden: bool = False
    
    # Scanner configurations
    scanners: Dict[str, ScannerConfig] = field(default_factory=dict)
    
    # Output configuration
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Docker configuration
    use_docker: bool = True
    docker_timeout: int = 300
    
    @classmethod
    def load(cls, config_file: Optional[Path] = None) -> "Config":
        """Load configuration from file or create default."""
        if config_file and config_file.exists():
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
                return cls.from_dict(data)
        else:
            return cls.default()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()
        
        # Update basic fields
        if 'target_path' in data:
            config.target_path = data['target_path']
        if 'exclude_paths' in data:
            config.exclude_paths = data['exclude_paths']
        if 'include_hidden' in data:
            config.include_hidden = data['include_hidden']
        if 'use_docker' in data:
            config.use_docker = data['use_docker']
        if 'docker_timeout' in data:
            config.docker_timeout = data['docker_timeout']
        
        # Load scanner configurations
        if 'scanners' in data:
            for name, scanner_data in data['scanners'].items():
                config.scanners[name] = ScannerConfig(**scanner_data)
        
        # Load output configuration
        if 'output' in data:
            config.output = OutputConfig(**data['output'])
        
        return config
    
    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        config = cls()
        
        # Default scanner configurations
        default_scanners = {
            'bandit': ScannerConfig(
                enabled=True,
                args=['-f', 'json'],
                exclude_patterns=['*/test*', '*/venv/*'],
                severity_threshold='medium'
            ),
            'safety': ScannerConfig(
                enabled=True,
                args=['--json'],
                severity_threshold='medium'
            ),
            'semgrep': ScannerConfig(
                enabled=True,
                args=['--config=auto', '--json'],
                exclude_patterns=['*/test*', '*/node_modules/*'],
                severity_threshold='medium'
            ),
            'trufflehog': ScannerConfig(
                enabled=True,
                args=['--json'],
                severity_threshold='medium'
            ),
            'checkov': ScannerConfig(
                enabled=True,
                args=['-o', 'json'],
                exclude_patterns=['*/test*'],
                severity_threshold='medium'
            )
        }
        
        config.scanners = default_scanners
        return config
    
    @classmethod
    def create_default(cls, path: str = "audithound.yaml") -> None:
        """Create default configuration file."""
        config = cls.default()
        config.save(Path(path))
    
    @classmethod
    def validate(cls, config_file: Path) -> bool:
        """Validate configuration file."""
        try:
            cls.load(config_file)
            return True
        except Exception:
            return False
    
    def save(self, path: Path) -> None:
        """Save configuration to file."""
        data = self.to_dict()
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'target_path': self.target_path,
            'exclude_paths': self.exclude_paths,
            'include_hidden': self.include_hidden,
            'use_docker': self.use_docker,
            'docker_timeout': self.docker_timeout,
            'scanners': {
                name: {
                    'enabled': scanner.enabled,
                    'args': scanner.args,
                    'exclude_patterns': scanner.exclude_patterns,
                    'severity_threshold': scanner.severity_threshold
                }
                for name, scanner in self.scanners.items()
            },
            'output': {
                'format': self.output.format,
                'file': self.output.file,
                'include_passed': self.output.include_passed,
                'group_by_severity': self.output.group_by_severity
            }
        }
    
    def to_yaml(self) -> str:
        """Convert configuration to YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, indent=2)