"""Output formatting utilities for AuditHound."""

import json
import csv
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from io import StringIO

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from ..core.config import OutputConfig
from ..core.types import AggregatedResults


class OutputFormatter:
    """Formats scan results for various output formats."""
    
    def __init__(self, config: OutputConfig):
        self.config = config
        self.console = Console()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def format(self, results: AggregatedResults) -> str:
        """Format results according to configuration."""
        format_type = self.config.format.lower()
        self.logger.debug(f"Formatting results as {format_type}")
        
        if format_type == 'json':
            return self._format_json(results)
        elif self.config.format.lower() == 'csv':
            return self._format_csv(results)
        elif self.config.format.lower() == 'xml':
            return self._format_xml(results)
        elif self.config.format.lower() == 'html':
            return self._format_html(results)
        elif self.config.format.lower() == 'sarif':
            return self._format_sarif(results)
        else:
            return self._format_json(results)  # Default to JSON
    
    def format_for_console(self, results: AggregatedResults) -> str:
        """Format results for console display."""
        console = Console(file=StringIO(), width=120)
        
        # Summary panel
        summary = self._create_summary_panel(results)
        console.print(summary)
        console.print()
        
        # Results by severity
        if self.config.group_by_severity:
            self._print_by_severity(console, results)
        else:
            self._print_by_scanner(console, results)
        
        return console.file.getvalue()
    
    def _format_json(self, results: AggregatedResults) -> str:
        """Format results as JSON."""
        data = {
            'scan_info': {
                'target': results.target,
                'scan_time': results.scan_time.isoformat(),
                'total_findings': results.total_findings,
                'summary': results.summary
            },
            'results': []
        }
        
        for scanner_name, result in results.results_by_scanner.items():
            scanner_data = {
                'scanner': scanner_name,
                'status': result.status,
                'duration': result.duration,
                'findings': result.findings if self.config.include_passed or result.status != 'success' or result.findings else []
            }
            
            if result.error_message:
                scanner_data['error'] = result.error_message
            
            if result.metadata:
                scanner_data['metadata'] = result.metadata
            
            data['results'].append(scanner_data)
        
        return json.dumps(data, indent=2, default=str)
    
    def _format_csv(self, results: AggregatedResults) -> str:
        """Format results as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Scanner', 'Status', 'Severity', 'Rule ID', 'Rule Name', 
            'File', 'Line', 'Column', 'Message', 'CWE', 'References'
        ])
        
        # Write findings
        for scanner_name, result in results.results_by_scanner.items():
            if result.status == 'success':
                for finding in result.findings:
                    writer.writerow([
                        scanner_name,
                        result.status,
                        finding.get('severity', ''),
                        finding.get('rule_id', ''),
                        finding.get('rule_name', ''),
                        finding.get('file', ''),
                        finding.get('line', ''),
                        finding.get('column', ''),
                        finding.get('message', ''),
                        ','.join(finding.get('cwe', [])),
                        ','.join(finding.get('references', []))
                    ])
            else:
                # Include failed scans
                writer.writerow([
                    scanner_name,
                    result.status,
                    'error',
                    '',
                    'Scanner Failed',
                    '',
                    '',
                    '',
                    result.error_message or 'Unknown error',
                    '',
                    ''
                ])
        
        return output.getvalue()
    
    def _format_xml(self, results: AggregatedResults) -> str:
        """Format results as XML."""
        root = ET.Element('audit_report')
        
        # Scan info
        scan_info = ET.SubElement(root, 'scan_info')
        ET.SubElement(scan_info, 'target').text = results.target
        ET.SubElement(scan_info, 'scan_time').text = results.scan_time.isoformat()
        ET.SubElement(scan_info, 'total_findings').text = str(results.total_findings)
        
        # Summary
        summary = ET.SubElement(scan_info, 'summary')
        for severity, count in results.summary.items():
            ET.SubElement(summary, severity).text = str(count)
        
        # Results
        results_elem = ET.SubElement(root, 'results')
        
        for scanner_name, result in results.results_by_scanner.items():
            scanner_elem = ET.SubElement(results_elem, 'scanner')
            scanner_elem.set('name', scanner_name)
            scanner_elem.set('status', result.status)
            scanner_elem.set('duration', str(result.duration))
            
            if result.error_message:
                ET.SubElement(scanner_elem, 'error').text = result.error_message
            
            findings_elem = ET.SubElement(scanner_elem, 'findings')
            for finding in result.findings:
                finding_elem = ET.SubElement(findings_elem, 'finding')
                
                for key, value in finding.items():
                    if isinstance(value, list):
                        list_elem = ET.SubElement(finding_elem, key)
                        for item in value:
                            ET.SubElement(list_elem, 'item').text = str(item)
                    else:
                        ET.SubElement(finding_elem, key).text = str(value)
        
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    def _format_html(self, results: AggregatedResults) -> str:
        """Format results as HTML report."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>AuditHound Security Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .severity-critical { color: #d73a49; font-weight: bold; }
        .severity-high { color: #f85149; }
        .severity-medium { color: #fb8500; }
        .severity-low { color: #1f883d; }
        .severity-info { color: #656d76; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .error { color: #d73a49; }
    </style>
</head>
<body>
    <div class="header">
        <h1>AuditHound Security Report</h1>
        <p><strong>Target:</strong> {target}</p>
        <p><strong>Scan Time:</strong> {scan_time}</p>
        <p><strong>Total Findings:</strong> {total_findings}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <ul>
            <li class="severity-critical">Critical: {critical}</li>
            <li class="severity-high">High: {high}</li>
            <li class="severity-medium">Medium: {medium}</li>
            <li class="severity-low">Low: {low}</li>
            <li class="severity-info">Info: {info}</li>
        </ul>
    </div>
    
    <h2>Findings</h2>
    <table>
        <tr>
            <th>Severity</th>
            <th>Scanner</th>
            <th>Rule</th>
            <th>File</th>
            <th>Line</th>
            <th>Message</th>
        </tr>
        {findings_rows}
    </table>
</body>
</html>
        """
        
        # Generate findings rows
        findings_rows = []
        for scanner_name, result in results.results_by_scanner.items():
            if result.status == 'success':
                for finding in result.findings:
                    severity = finding.get('severity', 'unknown')
                    findings_rows.append(f"""
                        <tr>
                            <td class="severity-{severity}">{severity.upper()}</td>
                            <td>{scanner_name}</td>
                            <td>{finding.get('rule_name', '')}</td>
                            <td>{finding.get('file', '')}</td>
                            <td>{finding.get('line', '')}</td>
                            <td>{finding.get('message', '')}</td>
                        </tr>
                    """)
            else:
                findings_rows.append(f"""
                    <tr>
                        <td class="error">ERROR</td>
                        <td>{scanner_name}</td>
                        <td>Scanner Failed</td>
                        <td>-</td>
                        <td>-</td>
                        <td class="error">{result.error_message or 'Unknown error'}</td>
                    </tr>
                """)
        
        return html_template.format(
            target=results.target,
            scan_time=results.scan_time.strftime('%Y-%m-%d %H:%M:%S'),
            total_findings=results.total_findings,
            critical=results.summary.get('critical', 0),
            high=results.summary.get('high', 0),
            medium=results.summary.get('medium', 0),
            low=results.summary.get('low', 0),
            info=results.summary.get('info', 0),
            findings_rows=''.join(findings_rows)
        )
    
    def _format_sarif(self, results: AggregatedResults) -> str:
        """Format results as SARIF (Static Analysis Results Interchange Format)."""
        sarif_report = {
            'version': '2.1.0',
            '$schema': 'https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json',
            'runs': []
        }
        
        for scanner_name, result in results.results_by_scanner.items():
            run = {
                'tool': {
                    'driver': {
                        'name': scanner_name,
                        'version': result.metadata.get('scanner_version', 'unknown')
                    }
                },
                'results': []
            }
            
            if result.status == 'success':
                for finding in result.findings:
                    sarif_result = {
                        'ruleId': finding.get('rule_id', 'unknown'),
                        'level': self._severity_to_sarif_level(finding.get('severity', 'warning')),
                        'message': {
                            'text': finding.get('message', '')
                        },
                        'locations': []
                    }
                    
                    if finding.get('file'):
                        location = {
                            'physicalLocation': {
                                'artifactLocation': {
                                    'uri': finding['file']
                                }
                            }
                        }
                        
                        if finding.get('line'):
                            location['physicalLocation']['region'] = {
                                'startLine': finding['line']
                            }
                            if finding.get('column'):
                                location['physicalLocation']['region']['startColumn'] = finding['column']
                        
                        sarif_result['locations'].append(location)
                    
                    run['results'].append(sarif_result)
            
            sarif_report['runs'].append(run)
        
        return json.dumps(sarif_report, indent=2)
    
    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            'critical': 'error',
            'high': 'error',
            'medium': 'warning',
            'low': 'note',
            'info': 'note'
        }
        return mapping.get(severity.lower(), 'warning')
    
    def _create_summary_panel(self, results: AggregatedResults) -> Panel:
        """Create a rich summary panel."""
        summary_lines = [
            f"🎯 Target: {results.target}",
            f"⏰ Scan Time: {results.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"🔍 Total Findings: {results.total_findings}",
            "",
            "📊 Severity Breakdown:"
        ]
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = results.summary.get(severity, 0)
            if count > 0:
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': '⚪'}
                summary_lines.append(f"  {emoji.get(severity, '⚪')} {severity.capitalize()}: {count}")
        
        return Panel('\n'.join(summary_lines), title="Scan Summary", border_style="blue")
    
    def _print_by_severity(self, console: Console, results: AggregatedResults) -> None:
        """Print results grouped by severity."""
        severities = ['critical', 'high', 'medium', 'low', 'info']
        
        for severity in severities:
            findings = []
            for scanner_name, result in results.results_by_scanner.items():
                if result.status == 'success':
                    for finding in result.findings:
                        if finding.get('severity', '').lower() == severity:
                            findings.append((scanner_name, finding))
            
            if findings:
                self._print_severity_section(console, severity, findings)
    
    def _print_by_scanner(self, console: Console, results: AggregatedResults) -> None:
        """Print results grouped by scanner."""
        for scanner_name, result in results.results_by_scanner.items():
            if result.status == 'success' and result.findings:
                self._print_scanner_section(console, scanner_name, result.findings)
            elif result.status == 'error':
                console.print(f"\n❌ {scanner_name}: {result.error_message}", style="red")
    
    def _print_severity_section(self, console: Console, severity: str, findings: List) -> None:
        """Print a section for a specific severity level."""
        if not findings:
            return
        
        emoji_map = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🔵', 'info': '⚪'}
        style_map = {'critical': 'bold red', 'high': 'red', 'medium': 'yellow', 'low': 'blue', 'info': 'dim'}
        
        console.print(f"\n{emoji_map.get(severity, '⚪')} {severity.upper()} SEVERITY ({len(findings)} findings)", 
                     style=style_map.get(severity, 'white'))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Scanner", style="cyan")
        table.add_column("Rule", style="green")
        table.add_column("File", style="blue")
        table.add_column("Line", justify="right")
        table.add_column("Message")
        
        for scanner_name, finding in findings:
            table.add_row(
                scanner_name,
                finding.get('rule_name', '')[:40] + "..." if len(finding.get('rule_name', '')) > 40 else finding.get('rule_name', ''),
                finding.get('file', '')[:30] + "..." if len(finding.get('file', '')) > 30 else finding.get('file', ''),
                str(finding.get('line', '')),
                finding.get('message', '')[:60] + "..." if len(finding.get('message', '')) > 60 else finding.get('message', '')
            )
        
        console.print(table)
    
    def _print_scanner_section(self, console: Console, scanner_name: str, findings: List) -> None:
        """Print a section for a specific scanner."""
        console.print(f"\n🔍 {scanner_name.upper()} ({len(findings)} findings)", style="bold cyan")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Severity")
        table.add_column("Rule", style="green")
        table.add_column("File", style="blue")
        table.add_column("Line", justify="right")
        table.add_column("Message")
        
        for finding in findings:
            severity = finding.get('severity', 'unknown')
            severity_text = Text(severity.upper())
            
            if severity == 'critical':
                severity_text.stylize("bold red")
            elif severity == 'high':
                severity_text.stylize("red")
            elif severity == 'medium':
                severity_text.stylize("yellow")
            elif severity == 'low':
                severity_text.stylize("blue")
            else:
                severity_text.stylize("dim")
            
            table.add_row(
                severity_text,
                finding.get('rule_name', '')[:40] + "..." if len(finding.get('rule_name', '')) > 40 else finding.get('rule_name', ''),
                finding.get('file', '')[:30] + "..." if len(finding.get('file', '')) > 30 else finding.get('file', ''),
                str(finding.get('line', '')),
                finding.get('message', '')[:60] + "..." if len(finding.get('message', '')) > 60 else finding.get('message', '')
            )
        
        console.print(table)