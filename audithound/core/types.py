"""Type definitions for AuditHound core functionality."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ScanResult:
    """Result from a security scan."""
    scanner: str
    target: str
    status: str  # success, error, skipped
    findings: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    duration: float = 0.0


@dataclass
class AggregatedResults:
    """Aggregated results from all scanners."""
    target: str
    scan_time: datetime
    total_findings: int
    results_by_scanner: Dict[str, ScanResult]
    summary: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate summary statistics."""
        self.summary = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0,
            'total': 0
        }
        
        for result in self.results_by_scanner.values():
            for finding in result.findings:
                severity = finding.get('severity', 'unknown').lower()
                if severity in self.summary:
                    self.summary[severity] += 1
                self.summary['total'] += 1