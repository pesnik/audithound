#!/usr/bin/env python3
"""Test TUI result handling with actual results file."""

import json
from datetime import datetime
from pathlib import Path
from audithound.core.types import AggregatedResults, ScanResult

def load_results_from_json():
    """Load results from the JSON file and convert to AggregatedResults."""
    results_path = Path('audithound_results.json')
    if not results_path.exists():
        print("Results file not found")
        return None
    
    with open(results_path) as f:
        data = json.load(f)
    
    print(f"JSON data structure: {list(data.keys())}")
    print(f"Scan info: {data['scan_info']}")
    
    # Convert to AggregatedResults structure
    scan_info = data['scan_info']
    target = scan_info['target']
    scan_time = datetime.fromisoformat(scan_info['scan_time'])
    total_findings = scan_info['total_findings']
    
    results_by_scanner = {}
    for result_data in data['results']:
        scanner_name = result_data['scanner']
        scan_result = ScanResult(
            scanner=scanner_name,
            target=target,
            status=result_data['status'],
            findings=result_data.get('findings', []),
            metadata=result_data.get('metadata', {}),
            duration=result_data.get('duration', 0.0)
        )
        results_by_scanner[scanner_name] = scan_result
        print(f"Scanner {scanner_name}: {scan_result.status}, {len(scan_result.findings)} findings")
    
    # Create AggregatedResults
    results = AggregatedResults(
        target=target,
        scan_time=scan_time,
        total_findings=total_findings,
        results_by_scanner=results_by_scanner
    )
    
    print(f"AggregatedResults created: {results.total_findings} findings")
    print(f"Summary: {results.summary}")
    
    return results

def test_results_display():
    """Test the results display like TUI would."""
    results = load_results_from_json()
    if not results:
        return
    
    print("\n=== TUI Display Test ===")
    
    # Test summary display
    summary_text = f"""
📊 Scan Summary
Target: {results.target}
Total Findings: {results.total_findings}

Severity Breakdown:
  Critical: {results.summary.get('critical', 0)}
  High: {results.summary.get('high', 0)}
  Medium: {results.summary.get('medium', 0)}
  Low: {results.summary.get('low', 0)}

Scanners: {len(results.results_by_scanner)}
Scan Time: {results.scan_time.strftime('%Y-%m-%d %H:%M:%S')}
    """
    print(summary_text.strip())
    
    # Test table data
    print("\n=== Table Data ===")
    for scanner_name, result in results.results_by_scanner.items():
        if result.status == "success":
            for finding in result.findings:
                severity = finding.get('severity', 'unknown')
                rule_name = finding.get('rule_name', 'unknown')
                file_path = finding.get('file', '')
                line = finding.get('line', 0)
                message = finding.get('message', '')[:50] + "..." if len(finding.get('message', '')) > 50 else finding.get('message', '')
                
                print(f"{severity.upper():8} | {scanner_name:8} | {rule_name:30} | {file_path:30} | {line:4} | {message}")

if __name__ == "__main__":
    test_results_display()