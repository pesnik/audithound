"""TruffleHog secrets scanner implementation."""

import json
from pathlib import Path
from typing import List, Dict, Any

from .base import BaseScanner


class TrufflehogScanner(BaseScanner):
    """TruffleHog secrets detection scanner."""
    
    def get_binary_name(self) -> str:
        return "trufflehog"
    
    def get_docker_image(self) -> str:
        return "trufflesecurity/trufflehog:latest"
    
    def scan(self, target: Path) -> List[Dict[str, Any]]:
        """Run TruffleHog scanner for secrets detection."""
        cmd = self.get_command(target)
        
        try:
            output = self.run_command(cmd, target)
            findings = self.parse_output(output)
            return self.filter_by_severity(findings)
        except Exception as e:
            # TruffleHog may return non-zero exit code when secrets are found
            if hasattr(e, 'output') and e.output:
                try:
                    findings = self.parse_output(e.output)
                    return self.filter_by_severity(findings)
                except:
                    pass
            raise
    
    def get_command(self, target: Path) -> List[str]:
        """Get TruffleHog command."""
        cmd = ['trufflehog', 'filesystem']
        
        # Add configured arguments
        cmd.extend(self.config.args)
        
        # Add target
        cmd.append(str(target))
        
        return cmd
    
    def parse_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse TruffleHog JSON output."""
        findings = []
        
        # TruffleHog outputs one JSON object per line
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                result = json.loads(line)
                
                finding = {
                    'scanner': 'trufflehog',
                    'rule_id': result.get('DetectorName', 'unknown'),
                    'rule_name': f"Secret detected: {result.get('DetectorName', 'unknown')}",
                    'severity': self._map_severity(result.get('Verified', False)),
                    'message': self._format_message(result),
                    'file': self._extract_file_path(result),
                    'line': self._extract_line_number(result),
                    'secret_type': result.get('DetectorName', ''),
                    'verified': result.get('Verified', False),
                    'raw_secret': result.get('Raw', ''),
                    'redacted_secret': self._redact_secret(result.get('Raw', '')),
                    'source_metadata': result.get('SourceMetadata', {}),
                    'references': self._get_references(result)
                }
                findings.append(finding)
                
            except json.JSONDecodeError:
                # Skip invalid JSON lines
                continue
        
        return findings
    
    def _map_severity(self, verified: bool) -> str:
        """Map verification status to severity level."""
        # Verified secrets are high severity, unverified are medium
        return 'high' if verified else 'medium'
    
    def _format_message(self, result: Dict[str, Any]) -> str:
        """Format a readable message for the finding."""
        detector = result.get('DetectorName', 'unknown')
        verified = result.get('Verified', False)
        
        status = "verified" if verified else "potential"
        
        source_metadata = result.get('SourceMetadata', {})
        if 'Data' in source_metadata and 'Filesystem' in source_metadata['Data']:
            file_info = source_metadata['Data']['Filesystem']
            file_path = file_info.get('file', 'unknown file')
            return f"Detected {status} {detector} secret in {file_path}"
        
        return f"Detected {status} {detector} secret"
    
    def _extract_file_path(self, result: Dict[str, Any]) -> str:
        """Extract file path from result."""
        source_metadata = result.get('SourceMetadata', {})
        
        if 'Data' in source_metadata and 'Filesystem' in source_metadata['Data']:
            return source_metadata['Data']['Filesystem'].get('file', '')
        
        return ''
    
    def _extract_line_number(self, result: Dict[str, Any]) -> int:
        """Extract line number from result."""
        source_metadata = result.get('SourceMetadata', {})
        
        if 'Data' in source_metadata and 'Filesystem' in source_metadata['Data']:
            return source_metadata['Data']['Filesystem'].get('line', 0)
        
        return 0
    
    def _redact_secret(self, raw_secret: str) -> str:
        """Redact the secret for safe display."""
        if len(raw_secret) <= 8:
            return '*' * len(raw_secret)
        else:
            # Show first 4 and last 4 characters
            return raw_secret[:4] + '*' * (len(raw_secret) - 8) + raw_secret[-4:]
    
    def _get_references(self, result: Dict[str, Any]) -> List[str]:
        """Get reference URLs for the finding."""
        references = []
        
        detector = result.get('DetectorName', '')
        if detector:
            # Add TruffleHog documentation
            references.append('https://trufflesecurity.com/trufflehog')
            
            # Add detector-specific references if available
            detector_refs = {
                'AWS': 'https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html',
                'GitHub': 'https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens',
                'GitLab': 'https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html',
                'Slack': 'https://api.slack.com/authentication/token-types',
                'JWT': 'https://jwt.io/introduction',
                'Docker': 'https://docs.docker.com/engine/reference/commandline/login/#credentials-store',
                'NPM': 'https://docs.npmjs.com/about-access-tokens'
            }
            
            if detector in detector_refs:
                references.append(detector_refs[detector])
        
        return references