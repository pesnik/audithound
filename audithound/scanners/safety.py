"""Safety dependency vulnerability scanner implementation."""

import json
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseScanner


class SafetyScanner(BaseScanner):
    """Safety Python dependency vulnerability scanner."""
    
    def get_binary_name(self) -> str:
        return "safety"
    
    def get_docker_image(self) -> str:
        return "pyupio/safety:latest"
    
    def scan(self, target: Path) -> List[Dict[str, Any]]:
        """Run Safety scanner on Python dependencies."""
        cmd = self.get_command(target)
        
        try:
            output = self.run_command(cmd, target)
            findings = self.parse_output(output)
            return self.filter_by_severity(findings)
        except Exception as e:
            # Safety returns non-zero exit code when vulnerabilities are found
            if hasattr(e, 'output') and e.output:
                try:
                    findings = self.parse_output(e.output)
                    return self.filter_by_severity(findings)
                except:
                    pass
            raise
    
    def get_command(self, target: Path) -> List[str]:
        """Get Safety command."""
        cmd = ['safety', 'check']
        
        # Look for requirements files
        req_files = [
            target / 'requirements.txt',
            target / 'requirements-dev.txt',
            target / 'pyproject.toml',
            target / 'Pipfile',
            target / 'poetry.lock'
        ]
        
        # Use first found requirements file
        for req_file in req_files:
            if req_file.exists():
                if req_file.name == 'pyproject.toml':
                    # For pyproject.toml, we need to scan the environment
                    break
                else:
                    cmd.extend(['-r', str(req_file)])
                    break
        
        # Add configured arguments
        cmd.extend(self.config.args)
        
        return cmd
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse Safety output."""
        findings = []
        
        try:
            # Try parsing as JSON first
            data = json.loads(output)
            
            for vuln in data:
                finding = {
                    'scanner': 'safety',
                    'rule_id': vuln.get('id', 'unknown'),
                    'rule_name': f"Vulnerable dependency: {vuln.get('package', 'unknown')}",
                    'severity': self._map_severity(vuln.get('vulnerability_id', '')),
                    'message': vuln.get('advisory', ''),
                    'package': vuln.get('package', ''),
                    'installed_version': vuln.get('installed_version', ''),
                    'affected_version': vuln.get('affected_version', ''),
                    'safe_version': vuln.get('safe_version', ''),
                    'cve': self._extract_cve(vuln),
                    'references': self._get_references(vuln)
                }
                findings.append(finding)
                
        except json.JSONDecodeError:
            # Parse text output
            findings = self._parse_text_output(output)
        
        return findings
    
    def _map_severity(self, vuln_id: str) -> str:
        """Map vulnerability to severity level."""
        # Safety doesn't provide severity directly
        # We could implement CVE severity lookup here
        # For now, default to medium
        return 'medium'
    
    def _extract_cve(self, vuln: Dict[str, Any]) -> List[str]:
        """Extract CVE identifiers from vulnerability."""
        cve_list = []
        
        # Look for CVE in advisory text
        advisory = vuln.get('advisory', '')
        vuln_id = vuln.get('vulnerability_id', '')
        
        import re
        cve_pattern = r'CVE[-\s]?(\d{4}[-\s]?\d+)'
        
        for text in [advisory, vuln_id]:
            matches = re.findall(cve_pattern, text, re.IGNORECASE)
            cve_list.extend([f'CVE-{match.replace(" ", "-")}' for match in matches])
        
        return list(set(cve_list))
    
    def _get_references(self, vuln: Dict[str, Any]) -> List[str]:
        """Get reference URLs for the vulnerability."""
        references = []
        
        vuln_id = vuln.get('vulnerability_id', '')
        if vuln_id:
            references.append(f'https://pyup.io/vulnerabilities/{vuln_id}/')
        
        cve_list = self._extract_cve(vuln)
        for cve in cve_list:
            references.append(f'https://nvd.nist.gov/vuln/detail/{cve}')
        
        return references
    
    def _parse_text_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse text output as fallback."""
        findings = []
        lines = output.split('\n')
        
        current_finding = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for vulnerability entries
            if line.startswith('vulnerability found in ') or 'installed:' in line.lower():
                if current_finding:
                    findings.append(current_finding)
                
                # Parse package info from line like:
                # "vulnerability found in django installed: 2.0 affected: <2.0.8 safe: >=2.0.8"
                import re
                pattern = r'vulnerability found in (\w+) installed: ([\d\.]+) affected: ([<>=\d\.\s,]+) safe: ([<>=\d\.\s,]+)'
                match = re.search(pattern, line, re.IGNORECASE)
                
                if match:
                    current_finding = {
                        'scanner': 'safety',
                        'rule_name': f"Vulnerable dependency: {match.group(1)}",
                        'severity': 'medium',
                        'package': match.group(1),
                        'installed_version': match.group(2),
                        'affected_version': match.group(3),
                        'safe_version': match.group(4),
                        'message': line
                    }
            
            elif current_finding and line and not line.startswith('-'):
                # Additional description lines
                current_finding['message'] = current_finding.get('message', '') + ' ' + line
        
        if current_finding:
            findings.append(current_finding)
        
        return findings