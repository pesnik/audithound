"""Bandit security scanner implementation."""

import json
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseScanner


class BanditScanner(BaseScanner):
    """Bandit Python security scanner."""
    
    def get_binary_name(self) -> str:
        return "bandit"
    
    def get_docker_image(self) -> str:
        return "pipelinecomponents/bandit:latest"
    
    def scan(self, target: Path) -> List[Dict[str, Any]]:
        """Run Bandit scanner on Python files."""
        cmd = self.get_command(target)
        
        try:
            output = self.run_command(cmd, target)
            findings = self.parse_output(output)
            return self.filter_by_severity(findings)
        except Exception as e:
            # Bandit returns non-zero exit code when issues are found
            # Try to parse output anyway
            if hasattr(e, 'output') and e.output:
                try:
                    findings = self.parse_output(e.output)
                    return self.filter_by_severity(findings)
                except:
                    pass
            raise
    
    def get_command(self, target: Path) -> List[str]:
        """Get Bandit command."""
        cmd = ['bandit', '-r', str(target)]
        
        # Add configured arguments
        cmd.extend(self.config.args)
        
        # Add exclusions
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(['--exclude', pattern])
        
        return cmd
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Bandit JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            for result in data.get('results', []):
                finding = {
                    'scanner': 'bandit',
                    'rule_id': result.get('test_id', 'unknown'),
                    'rule_name': result.get('test_name', 'unknown'),
                    'severity': self._map_severity(result.get('issue_severity', 'MEDIUM')),
                    'confidence': result.get('issue_confidence', 'MEDIUM').lower(),
                    'message': result.get('issue_text', ''),
                    'file': result.get('filename', ''),
                    'line': result.get('line_number', 0),
                    'column': result.get('col_offset', 0),
                    'code': result.get('code', ''),
                    'cwe': self._extract_cwe(result),
                    'references': self._get_references(result)
                }
                findings.append(finding)
                
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract info from text output
            findings = self._parse_text_output(output)
        
        return findings
    
    def _map_severity(self, bandit_severity: str) -> str:
        """Map Bandit severity to standard severity levels."""
        severity_map = {
            'LOW': 'low',
            'MEDIUM': 'medium',
            'HIGH': 'high'
        }
        return severity_map.get(bandit_severity.upper(), 'medium')
    
    def _extract_cwe(self, result: Dict[str, Any]) -> List[str]:
        """Extract CWE identifiers from result."""
        cwe_list = []
        
        # Look for CWE in various fields
        test_name = result.get('test_name', '')
        issue_text = result.get('issue_text', '')
        
        import re
        cwe_pattern = r'CWE[-\s]?(\d+)'
        
        for text in [test_name, issue_text]:
            matches = re.findall(cwe_pattern, text, re.IGNORECASE)
            cwe_list.extend([f'CWE-{match}' for match in matches])
        
        return list(set(cwe_list))
    
    def _get_references(self, result: Dict[str, Any]) -> List[str]:
        """Get reference URLs for the finding."""
        references = []
        
        test_id = result.get('test_id', '')
        if test_id:
            # Bandit documentation URL
            references.append(f'https://bandit.readthedocs.io/en/latest/plugins/{test_id.lower()}.html')
        
        return references
    
    def _parse_text_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse text output as fallback."""
        findings = []
        lines = output.split('\n')
        
        current_finding = {}
        in_issue = False
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('>> Issue: '):
                if current_finding and in_issue:
                    findings.append(current_finding)
                
                current_finding = {
                    'scanner': 'bandit',
                    'rule_name': line.replace('>> Issue: ', ''),
                    'severity': 'medium',
                    'message': '',
                    'file': '',
                    'line': 0
                }
                in_issue = True
            
            elif line.startswith('   Severity: '):
                if in_issue:
                    severity = line.replace('   Severity: ', '')
                    current_finding['severity'] = self._map_severity(severity)
            
            elif line.startswith('   Location: '):
                if in_issue:
                    location = line.replace('   Location: ', '')
                    # Parse location (filename:line_number)
                    if ':' in location:
                        file_part, line_part = location.rsplit(':', 1)
                        current_finding['file'] = file_part
                        try:
                            current_finding['line'] = int(line_part)
                        except ValueError:
                            current_finding['line'] = 0
        
        if current_finding and in_issue:
            findings.append(current_finding)
        
        return findings