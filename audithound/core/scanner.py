"""Security scanner core functionality."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import Config
from .types import ScanResult, AggregatedResults
from ..scanners.base import BaseScanner
from ..scanners.bandit import BanditScanner
from ..scanners.safety import SafetyScanner
from ..scanners.semgrep import SemgrepScanner
from ..scanners.trufflehog import TrufflehogScanner
from ..scanners.checkov import CheckovScanner
from ..utils.output import OutputFormatter
from ..utils.docker import DockerRunner


class SecurityScanner:
    """Main security scanner orchestrator."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if config.use_docker:
            self.logger.info("Initializing Docker runner for scanners")
            self.docker_runner = DockerRunner()
        else:
            self.logger.info("Using local scanner binaries")
            self.docker_runner = None
        
        # Initialize available scanners
        self.available_scanners = {
            'bandit': BanditScanner,
            'safety': SafetyScanner,
            'semgrep': SemgrepScanner,
            'trufflehog': TrufflehogScanner,
            'checkov': CheckovScanner
        }
        
        # Initialize output formatter
        self.formatter = OutputFormatter(config.output)
    
    def scan(self, target: str, tools: Optional[List[str]] = None) -> AggregatedResults:
        """Run security scan on target directory or repository."""
        target_path = Path(target).resolve()
        
        if not target_path.exists():
            self.logger.error(f"Target path does not exist: {target}")
            raise FileNotFoundError(f"Target path does not exist: {target}")
        
        # Determine which scanners to run
        scanners_to_run = self._get_enabled_scanners(tools)
        
        if not scanners_to_run:
            self.logger.error("No scanners enabled or available")
            raise ValueError("No scanners enabled or available")
        
        self.logger.info(f"Starting scan of {target} with {len(scanners_to_run)} scanners: {list(scanners_to_run.keys())}")
        print(f"🔍 Scanning {target} with {len(scanners_to_run)} scanners...")
        
        # Run scanners
        results_by_scanner = {}
        
        if len(scanners_to_run) == 1:
            # Run single scanner synchronously
            scanner_name = list(scanners_to_run.keys())[0]
            scanner = scanners_to_run[scanner_name]
            results_by_scanner[scanner_name] = self._run_single_scanner(
                scanner_name, scanner, target_path
            )
        else:
            # Run multiple scanners in parallel
            with ThreadPoolExecutor(max_workers=min(len(scanners_to_run), 4)) as executor:
                future_to_scanner = {
                    executor.submit(self._run_single_scanner, name, scanner, target_path): name
                    for name, scanner in scanners_to_run.items()
                }
                
                for future in as_completed(future_to_scanner):
                    scanner_name = future_to_scanner[future]
                    try:
                        results_by_scanner[scanner_name] = future.result()
                    except Exception as e:
                        results_by_scanner[scanner_name] = ScanResult(
                            scanner=scanner_name,
                            target=str(target_path),
                            status="error",
                            error_message=str(e)
                        )
        
        # Aggregate results
        total_findings = sum(len(result.findings) for result in results_by_scanner.values())
        
        aggregated = AggregatedResults(
            target=str(target_path),
            scan_time=datetime.now(),
            total_findings=total_findings,
            results_by_scanner=results_by_scanner
        )
        
        print(f"✅ Scan completed! Found {total_findings} findings across {len(scanners_to_run)} scanners.")
        return aggregated
    
    def _get_enabled_scanners(self, tools: Optional[List[str]] = None) -> Dict[str, BaseScanner]:
        """Get enabled scanners based on configuration and tool selection."""
        scanners = {}
        
        # If specific tools requested, only use those
        if tools:
            requested_scanners = set(tools)
        else:
            # Use all enabled scanners from config
            requested_scanners = {
                name for name, config in self.config.scanners.items() 
                if config.enabled
            }
        
        # Initialize requested scanners that are available
        for scanner_name in requested_scanners:
            if scanner_name in self.available_scanners:
                scanner_class = self.available_scanners[scanner_name]
                scanner_config = self.config.scanners.get(scanner_name)
                
                if scanner_config:
                    scanner = scanner_class(
                        config=scanner_config,
                        docker_runner=self.docker_runner
                    )
                    
                    # Check if scanner is available
                    if scanner.is_available():
                        scanners[scanner_name] = scanner
                    else:
                        print(f"⚠️  Scanner '{scanner_name}' is not available (not installed)")
                else:
                    print(f"⚠️  No configuration found for scanner '{scanner_name}'")
            else:
                print(f"⚠️  Unknown scanner: '{scanner_name}'")
        
        return scanners
    
    def _run_single_scanner(self, name: str, scanner: BaseScanner, target: Path) -> ScanResult:
        """Run a single scanner and return its results."""
        print(f"🔍 Running {name} scanner...")
        
        start_time = datetime.now()
        
        try:
            # Run the scanner
            findings = scanner.scan(target)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result = ScanResult(
                scanner=name,
                target=str(target),
                status="success",
                findings=findings,
                duration=duration,
                metadata={
                    'scanner_version': scanner.get_version(),
                    'scan_time': start_time.isoformat()
                }
            )
            
            print(f"✅ {name}: Found {len(findings)} findings in {duration:.1f}s")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"❌ {name}: Failed after {duration:.1f}s - {str(e)}")
            
            return ScanResult(
                scanner=name,
                target=str(target),
                status="error",
                error_message=str(e),
                duration=duration
            )
    
    def export_results(self, results: AggregatedResults, output_path: Union[str, Path]) -> None:
        """Export scan results to file."""
        output_file = Path(output_path)
        formatted_output = self.formatter.format(results)
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write formatted results
        with open(output_file, 'w') as f:
            f.write(formatted_output)
        
        print(f"📄 Results exported to: {output_file}")
    
    def print_results(self, results: AggregatedResults) -> None:
        """Print scan results to console."""
        formatted_output = self.formatter.format_for_console(results)
        print(formatted_output)