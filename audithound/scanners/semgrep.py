"""Semgrep static analysis scanner implementation."""

import json
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseScanner


class SemgrepScanner(BaseScanner):
    """Semgrep static analysis scanner."""
    
    def get_binary_name(self) -> str:
        return "semgrep"
    
    def get_docker_image(self) -> str:
        return "returntocorp/semgrep:latest"
    
    def scan(self, target: Path) -> List[Dict[str, Any]]:
        """Run Semgrep scanner."""
        cmd = self.get_command(target)
        
        try:
            output = self.run_command(cmd, target)
            findings = self.parse_output(output)
            return self.filter_by_severity(findings)
        except Exception as e:
            # Semgrep may return non-zero exit code when findings are found
            if hasattr(e, 'output') and e.output:
                try:
                    findings = self.parse_output(e.output)
                    return self.filter_by_severity(findings)
                except:
                    pass
            raise
    
    def get_command(self, target: Path) -> List[str]:
        """Get Semgrep command."""
        cmd = ['semgrep']
        
        # Add configured arguments (should include --config and --json)
        cmd.extend(self.config.args)
        
        # Add exclusions
        if self.config.exclude_patterns:
            for pattern in self.config.exclude_patterns:
                cmd.extend(['--exclude', pattern])
        
        # Add target
        cmd.append(str(target))
        
        return cmd
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Semgrep JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            for result in data.get('results', []):
                finding = {
                    'scanner': 'semgrep',
                    'rule_id': result.get('check_id', 'unknown'),
                    'rule_name': self._get_rule_name(result),
                    'severity': self._map_severity(result.get('extra', {}).get('severity', 'INFO')),
                    'message': result.get('extra', {}).get('message', result.get('check_id', '')),
                    'file': result.get('path', ''),
                    'line': result.get('start', {}).get('line', 0),
                    'column': result.get('start', {}).get('col', 0),
                    'end_line': result.get('end', {}).get('line', 0),
                    'end_column': result.get('end', {}).get('col', 0),
                    'code': result.get('extra', {}).get('lines', ''),
                    'cwe': self._extract_cwe(result),
                    'owasp': self._extract_owasp(result),
                    'references': self._get_references(result)
                }
                findings.append(finding)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Semgrep output: {e}")
        
        return findings
    
    def _get_rule_name(self, result: Dict[str, Any]) -> str:
        """Get a readable rule name."""
        extra = result.get('extra', {})
        
        # Try to get a meaningful name
        if 'message' in extra:
            return extra['message']
        elif 'metadata' in extra and 'shortDescription' in extra['metadata']:
            return extra['metadata']['shortDescription']
        else:
            return result.get('check_id', 'unknown')
    
    def _map_severity(self, semgrep_severity: str) -> str:
        """Map Semgrep severity to standard severity levels."""
        severity_map = {
            'ERROR': 'high',
            'WARNING': 'medium',
            'INFO': 'low'
        }
        return severity_map.get(semgrep_severity.upper(), 'medium')
    
    def _extract_cwe(self, result: Dict[str, Any]) -> List[str]:
        """Extract CWE identifiers from result."""
        cwe_list = []
        
        extra = result.get('extra', {})
        metadata = extra.get('metadata', {})
        
        # Look for CWE in metadata
        if 'cwe' in metadata:
            cwe_data = metadata['cwe']
            if isinstance(cwe_data, list):
                cwe_list.extend([f'CWE-{cwe}' for cwe in cwe_data])
            elif isinstance(cwe_data, str):
                cwe_list.append(f'CWE-{cwe_data}')
        
        # Look for CWE in check_id or message
        check_id = result.get('check_id', '')
        message = extra.get('message', '')
        
        import re
        cwe_pattern = r'CWE[-\s]?(\d+)'
        
        for text in [check_id, message]:
            matches = re.findall(cwe_pattern, text, re.IGNORECASE)
            cwe_list.extend([f'CWE-{match}' for match in matches])
        
        return list(set(cwe_list))
    
    def _extract_owasp(self, result: Dict[str, Any]) -> List[str]:
        """Extract OWASP categories from result."""
        owasp_list = []
        
        extra = result.get('extra', {})
        metadata = extra.get('metadata', {})
        
        # Look for OWASP in metadata
        if 'owasp' in metadata:
            owasp_data = metadata['owasp']
            if isinstance(owasp_data, list):
                owasp_list.extend(owasp_data)
            elif isinstance(owasp_data, str):
                owasp_list.append(owasp_data)
        
        return owasp_list
    
    def _get_references(self, result: Dict[str, Any]) -> List[str]:
        """Get reference URLs for the finding."""
        references = []
        
        extra = result.get('extra', {})
        metadata = extra.get('metadata', {})
        
        # Add references from metadata
        if 'references' in metadata:
            refs = metadata['references']
            if isinstance(refs, list):
                references.extend(refs)
            elif isinstance(refs, str):
                references.append(refs)
        
        # Add Semgrep registry URL
        check_id = result.get('check_id', '')
        if check_id:
            # Convert check_id to registry URL format
            registry_url = f'https://semgrep.dev/r/{check_id}'
            references.append(registry_url)
        
        return references