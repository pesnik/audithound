"""Compliance framework definitions for security audits."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Set
from enum import Enum


class Severity(Enum):
    """Security finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ComplianceControl:
    """Individual compliance control definition."""
    control_id: str
    title: str
    description: str
    category: str
    severity_threshold: Severity
    required_scanners: List[str]
    evidence_types: List[str]


class ComplianceFramework(ABC):
    """Base class for compliance frameworks."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Framework name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Framework version."""
        pass
    
    @property
    @abstractmethod
    def controls(self) -> Dict[str, ComplianceControl]:
        """Framework controls mapping."""
        pass
    
    def get_applicable_controls(self, scan_results: Dict) -> List[str]:
        """Get controls applicable to scan results."""
        applicable = []
        for control_id, control in self.controls.items():
            # Check if any required scanners were used
            used_scanners = set(scan_results.get('scanners_used', []))
            required_scanners = set(control.required_scanners)
            
            if required_scanners.intersection(used_scanners):
                applicable.append(control_id)
        
        return applicable


class SOC2(ComplianceFramework):
    """SOC 2 Type II compliance framework."""
    
    @property
    def name(self) -> str:
        return "SOC 2 Type II"
    
    @property  
    def version(self) -> str:
        return "2017"
    
    @property
    def controls(self) -> Dict[str, ComplianceControl]:
        return {
            "CC6.1": ComplianceControl(
                control_id="CC6.1",
                title="Logical and Physical Access Controls",
                description="Restricts logical and physical access to system resources and data",
                category="Security",
                severity_threshold=Severity.HIGH,
                required_scanners=["bandit", "semgrep", "trufflehog"],
                evidence_types=["code_analysis", "secrets_scan", "access_controls"]
            ),
            "CC6.2": ComplianceControl(
                control_id="CC6.2", 
                title="System Access Monitoring",
                description="Monitors system access and unauthorized changes",
                category="Security",
                severity_threshold=Severity.MEDIUM,
                required_scanners=["bandit", "semgrep"],
                evidence_types=["code_analysis", "monitoring_controls"]
            ),
            "CC6.3": ComplianceControl(
                control_id="CC6.3",
                title="Data Classification and Handling", 
                description="Classifies data and implements appropriate handling procedures",
                category="Security",
                severity_threshold=Severity.HIGH,
                required_scanners=["trufflehog", "bandit"],
                evidence_types=["data_classification", "secrets_scan"]
            ),
            "CC7.1": ComplianceControl(
                control_id="CC7.1",
                title="System Boundaries and Data Flow",
                description="Identifies system boundaries and data flows",
                category="Security", 
                severity_threshold=Severity.MEDIUM,
                required_scanners=["semgrep", "checkov"],
                evidence_types=["architecture_analysis", "infrastructure_scan"]
            ),
            "CC7.2": ComplianceControl(
                control_id="CC7.2",
                title="Risk Assessment Process",
                description="Performs ongoing risk assessments", 
                category="Security",
                severity_threshold=Severity.MEDIUM,
                required_scanners=["bandit", "safety", "semgrep"],
                evidence_types=["vulnerability_scan", "risk_assessment"]
            )
        }


class NIST(ComplianceFramework):
    """NIST Cybersecurity Framework."""
    
    @property
    def name(self) -> str:
        return "NIST Cybersecurity Framework"
    
    @property
    def version(self) -> str:
        return "1.1"
    
    @property
    def controls(self) -> Dict[str, ComplianceControl]:
        return {
            "ID.AM-2": ComplianceControl(
                control_id="ID.AM-2",
                title="Software platforms and applications",
                description="Software platforms and applications within the organization are inventoried",
                category="Identify",
                severity_threshold=Severity.MEDIUM,
                required_scanners=["safety", "semgrep"],
                evidence_types=["software_inventory", "dependency_analysis"]
            ),
            "PR.DS-1": ComplianceControl(
                control_id="PR.DS-1", 
                title="Data-at-rest protection",
                description="Data-at-rest is protected",
                category="Protect",
                severity_threshold=Severity.HIGH,
                required_scanners=["bandit", "trufflehog"],
                evidence_types=["encryption_analysis", "secrets_scan"]
            ),
            "PR.DS-2": ComplianceControl(
                control_id="PR.DS-2",
                title="Data-in-transit protection", 
                description="Data-in-transit is protected",
                category="Protect",
                severity_threshold=Severity.HIGH,
                required_scanners=["bandit", "semgrep"],
                evidence_types=["tls_analysis", "crypto_analysis"]
            ),
            "DE.CM-4": ComplianceControl(
                control_id="DE.CM-4",
                title="Malicious code detection",
                description="Malicious code is detected",
                category="Detect", 
                severity_threshold=Severity.HIGH,
                required_scanners=["bandit", "semgrep", "safety"],
                evidence_types=["malware_scan", "code_analysis"]
            ),
            "RS.AN-1": ComplianceControl(
                control_id="RS.AN-1",
                title="Investigation process",
                description="Investigations incorporate lessons learned",
                category="Respond",
                severity_threshold=Severity.MEDIUM,
                required_scanners=["bandit", "semgrep", "trufflehog"],
                evidence_types=["incident_analysis", "forensic_analysis"]
            )
        }


class CIS(ComplianceFramework):
    """CIS Critical Security Controls."""
    
    @property
    def name(self) -> str:
        return "CIS Critical Security Controls"
    
    @property
    def version(self) -> str:
        return "8.0"
    
    @property
    def controls(self) -> Dict[str, ComplianceControl]:
        return {
            "CIS-2": ComplianceControl(
                control_id="CIS-2",
                title="Inventory and Control of Software Assets",
                description="Actively manage software inventory",
                category="Basic",
                severity_threshold=Severity.HIGH,
                required_scanners=["safety", "semgrep"],
                evidence_types=["software_inventory", "license_compliance"]
            ),
            "CIS-16": ComplianceControl(
                control_id="CIS-16", 
                title="Account Monitoring and Control",
                description="Actively manage account lifecycle",
                category="Foundational",
                severity_threshold=Severity.HIGH,
                required_scanners=["trufflehog", "bandit"],
                evidence_types=["credential_analysis", "access_review"]
            ),
            "CIS-18": ComplianceControl(
                control_id="CIS-18",
                title="Penetration Testing",
                description="Test the effectiveness of defenses",
                category="Organizational",
                severity_threshold=Severity.MEDIUM,
                required_scanners=["bandit", "semgrep", "safety"],
                evidence_types=["penetration_test", "vulnerability_scan"]
            )
        }


class OWASP(ComplianceFramework):
    """OWASP Application Security Verification Standard."""
    
    @property
    def name(self) -> str:
        return "OWASP ASVS"
    
    @property
    def version(self) -> str:
        return "4.0"
    
    @property
    def controls(self) -> Dict[str, ComplianceControl]:
        return {
            "V1.2.1": ComplianceControl(
                control_id="V1.2.1",
                title="Security Architecture",
                description="All application components are identified and have a known security impact",
                category="Architecture",
                severity_threshold=Severity.MEDIUM,
                required_scanners=["semgrep", "bandit"],
                evidence_types=["architecture_review", "component_analysis"]
            ),
            "V2.1.1": ComplianceControl(
                control_id="V2.1.1",
                title="Password Security",
                description="User set passwords are at least 12 characters in length",
                category="Authentication",
                severity_threshold=Severity.HIGH,
                required_scanners=["bandit", "semgrep"],
                evidence_types=["password_policy", "authentication_analysis"]
            ),
            "V6.2.1": ComplianceControl(
                control_id="V6.2.1",
                title="Data Classification",
                description="All data is classified according to protection requirements", 
                category="Data Protection",
                severity_threshold=Severity.HIGH,
                required_scanners=["trufflehog", "bandit"],
                evidence_types=["data_classification", "sensitive_data_scan"]
            ),
            "V7.1.1": ComplianceControl(
                control_id="V7.1.1",
                title="Log Content Requirements",
                description="Application does not log credentials or payment details",
                category="Error Handling and Logging",
                severity_threshold=Severity.CRITICAL,
                required_scanners=["bandit", "trufflehog", "semgrep"],
                evidence_types=["logging_analysis", "credential_leak_scan"]
            ),
            "V14.2.1": ComplianceControl(
                control_id="V14.2.1", 
                title="Dependency Management",
                description="All components are up to date with proper security patches",
                category="Configuration",
                severity_threshold=Severity.HIGH,
                required_scanners=["safety", "checkov"],
                evidence_types=["dependency_scan", "patch_management"]
            )
        }