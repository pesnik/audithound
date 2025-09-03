"""Checkov infrastructure as code scanner implementation."""

import json
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseScanner


class CheckovScanner(BaseScanner):
    """Checkov Infrastructure as Code scanner."""
    
    def get_binary_name(self) -> str:
        return "checkov"
    
    def get_docker_image(self) -> str:
        return "bridgecrew/checkov:latest"
    
    def scan(self, target: Path) -> List[Dict[str, Any]]:
        """Run Checkov scanner for IaC security issues."""
        cmd = self.get_command(target)
        
        try:
            output = self.run_command(cmd, target)
            findings = self.parse_output(output)
            return self.filter_by_severity(findings)
        except Exception as e:
            # Checkov returns non-zero exit code when issues are found
            if hasattr(e, 'output') and e.output:
                try:
                    findings = self.parse_output(e.output)
                    return self.filter_by_severity(findings)
                except:
                    pass
            raise
    
    def get_command(self, target: Path) -> List[str]:
        """Get Checkov command."""
        cmd = ['checkov', '-d', str(target), '--compact', '--output', 'json']
        
        # Add configured arguments
        cmd.extend(self.config.args)
        
        # Add exclusions
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(['--skip-path', pattern])
        
        return cmd
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Checkov JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            # Parse failed checks - data is a list of check type results
            failed_checks = []
            if isinstance(data, list):
                for check_type_result in data:
                    if isinstance(check_type_result, dict):
                        results = check_type_result.get('results', {})
                        failed_checks.extend(results.get('failed_checks', []))
            
            for result in failed_checks:
                finding = {
                    'scanner': 'checkov',
                    'rule_id': result.get('check_id', 'unknown'),
                    'rule_name': result.get('check_name', 'unknown'),
                    'severity': self._map_severity(result.get('severity', 'MEDIUM')),
                    'message': self._format_message(result),
                    'file': result.get('file_path', ''),
                    'line': self._extract_line_range(result),
                    'resource': result.get('resource', ''),
                    'check_class': result.get('check_class', ''),
                    'framework': result.get('check_type', ''),
                    'description': result.get('description', ''),
                    'guideline': result.get('guideline', ''),
                    'cwe': self._extract_cwe(result),
                    'references': self._get_references(result)
                }
                findings.append(finding)
            
            # Parse skipped checks if needed
            if self.config.args and '--include-skipped' in self.config.args:
                skipped_checks = []
                if isinstance(data, list):
                    for check_type_result in data:
                        if isinstance(check_type_result, dict):
                            results = check_type_result.get('results', {})
                            skipped_checks.extend(results.get('skipped_checks', []))
                
                for result in skipped_checks:
                    finding = {
                        'scanner': 'checkov',
                        'rule_id': result.get('check_id', 'unknown'),
                        'rule_name': result.get('check_name', 'unknown'),
                        'severity': 'info',
                        'message': f"Skipped check: {result.get('suppress_comment', 'No reason provided')}",
                        'file': result.get('file_path', ''),
                        'line': self._extract_line_range(result),
                        'resource': result.get('resource', ''),
                        'status': 'skipped'
                    }
                    findings.append(finding)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Checkov output: {e}")
        
        return findings
    
    def _map_severity(self, checkov_severity: str) -> str:
        """Map Checkov severity to standard severity levels."""
        if checkov_severity is None:
            return 'medium'
        
        severity_map = {
            'CRITICAL': 'critical',
            'HIGH': 'high',
            'MEDIUM': 'medium',
            'LOW': 'low',
            'INFO': 'info'
        }
        return severity_map.get(checkov_severity.upper(), 'medium')
    
    def _format_message(self, result: Dict[str, Any]) -> str:
        """Format a readable message for the finding."""
        check_name = result.get('check_name', 'unknown')
        description = result.get('description', '')
        resource = result.get('resource', '')
        
        if description:
            message = f"{check_name}: {description}"
        else:
            message = check_name
        
        if resource:
            message += f" (Resource: {resource})"
        
        return message
    
    def _extract_line_range(self, result: Dict[str, Any]) -> int:
        """Extract line number from result."""
        file_line_range = result.get('file_line_range', [])
        if file_line_range and len(file_line_range) >= 2:
            return file_line_range[0]  # Return start line
        return 0
    
    def _extract_cwe(self, result: Dict[str, Any]) -> List[str]:
        """Extract CWE identifiers from result."""
        cwe_list = []
        
        # Look for CWE in various fields
        description = result.get('description') or ''
        guideline = result.get('guideline') or ''
        check_name = result.get('check_name') or ''
        
        import re
        cwe_pattern = r'CWE[-\s]?(\d+)'
        
        for text in [description, guideline, check_name]:
            if text:  # Only process non-empty strings
                matches = re.findall(cwe_pattern, text, re.IGNORECASE)
                cwe_list.extend([f'CWE-{match}' for match in matches])
        
        return list(set(cwe_list))
    
    def _get_references(self, result: Dict[str, Any]) -> List[str]:
        """Get reference URLs for the finding."""
        references = []
        
        # Add guideline if available
        guideline = result.get('guideline', '')
        if guideline and guideline.startswith('http'):
            references.append(guideline)
        
        # Add Checkov documentation
        check_id = result.get('check_id', '')
        if check_id:
            references.append(f'https://docs.checkov.io/5.Policy%20Index/{check_id}.html')
        
        # Add framework-specific references
        framework = result.get('check_type', '').lower()
        if framework == 'terraform':
            references.append('https://registry.terraform.io/')
        elif framework == 'cloudformation':
            references.append('https://docs.aws.amazon.com/AWSCloudFormation/')
        elif framework == 'kubernetes':
            references.append('https://kubernetes.io/docs/concepts/security/')
        elif framework == 'dockerfile':
            references.append('https://docs.docker.com/develop/dev-best-practices/')
        
        return references