"""Compliance reporting and audit documentation generator."""

import json
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from .frameworks import ComplianceFramework, Severity


@dataclass 
class ComplianceEvidence:
    """Evidence for compliance control."""
    control_id: str
    scanner: str
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    status: str  # "compliant", "non_compliant", "needs_review"
    evidence_files: List[str]
    remediation_notes: str


@dataclass
class AuditReport:
    """Complete audit report structure."""
    framework: str
    framework_version: str
    scan_target: str
    scan_date: str
    auditor: str
    organization: str
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    needs_review_controls: int
    compliance_percentage: float
    executive_summary: str
    detailed_findings: List[ComplianceEvidence]
    recommendations: List[str]
    attestation: Dict[str, Any]


class ComplianceReporter:
    """Generate compliance reports for security audits."""
    
    def __init__(self, framework: ComplianceFramework):
        self.framework = framework
    
    def generate_report(
        self,
        scan_results: Dict[str, Any],
        auditor_info: Dict[str, str],
        organization_info: Dict[str, str]
    ) -> AuditReport:
        """Generate comprehensive compliance report."""
        
        # Extract scan metadata
        scan_date = datetime.now(timezone.utc).isoformat()
        scan_target = scan_results.get('target', 'Unknown')
        
        # Analyze compliance for each applicable control
        evidence_list = []
        compliant = 0
        non_compliant = 0
        needs_review = 0
        
        applicable_controls = self.framework.get_applicable_controls(scan_results)
        
        for control_id in applicable_controls:
            control = self.framework.controls[control_id]
            evidence = self._analyze_control_compliance(control, scan_results)
            evidence_list.append(evidence)
            
            # Count compliance status
            if evidence.status == "compliant":
                compliant += 1
            elif evidence.status == "non_compliant": 
                non_compliant += 1
            else:
                needs_review += 1
        
        total_controls = len(applicable_controls)
        compliance_percentage = (compliant / total_controls * 100) if total_controls > 0 else 0
        
        # Generate executive summary
        exec_summary = self._generate_executive_summary(
            compliance_percentage, compliant, non_compliant, needs_review
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(evidence_list)
        
        # Create attestation section
        attestation = {
            "auditor_statement": f"This security audit was conducted using AuditHound automated scanning tools in accordance with {self.framework.name} {self.framework.version} controls.",
            "methodology": "Automated static analysis using Bandit, Semgrep, Safety, TruffleHog, and Checkov scanners",
            "scope": f"Source code and infrastructure analysis of {scan_target}",
            "limitations": "This automated audit covers technical controls only. Manual review of business processes and physical controls is recommended.",
            "auditor": auditor_info.get('name', 'Unknown'),
            "auditor_title": auditor_info.get('title', 'Security Analyst'),
            "audit_firm": auditor_info.get('organization', organization_info.get('name', 'Unknown')),
            "date": scan_date
        }
        
        return AuditReport(
            framework=self.framework.name,
            framework_version=self.framework.version,
            scan_target=scan_target,
            scan_date=scan_date,
            auditor=auditor_info.get('name', 'Unknown'),
            organization=organization_info.get('name', 'Unknown'),
            total_controls=total_controls,
            compliant_controls=compliant,
            non_compliant_controls=non_compliant, 
            needs_review_controls=needs_review,
            compliance_percentage=compliance_percentage,
            executive_summary=exec_summary,
            detailed_findings=evidence_list,
            recommendations=recommendations,
            attestation=attestation
        )
    
    def _analyze_control_compliance(
        self, 
        control: 'ComplianceControl', 
        scan_results: Dict[str, Any]
    ) -> ComplianceEvidence:
        """Analyze compliance status for a specific control."""
        
        # Count findings by severity for relevant scanners
        total_findings = 0
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0
        evidence_files = []
        
        results_by_scanner = scan_results.get('results_by_scanner', {})
        
        for scanner_name in control.required_scanners:
            if scanner_name in results_by_scanner:
                scanner_result = results_by_scanner[scanner_name]
                if hasattr(scanner_result, 'findings'):
                    findings = scanner_result.findings
                    
                    for finding in findings:
                        severity = finding.get('severity', 'low').lower()
                        total_findings += 1
                        
                        if severity == 'critical':
                            critical_count += 1
                        elif severity == 'high':
                            high_count += 1
                        elif severity == 'medium':
                            medium_count += 1
                        else:
                            low_count += 1
                        
                        # Collect evidence files
                        file_path = finding.get('file')
                        if file_path and file_path not in evidence_files:
                            evidence_files.append(file_path)
        
        # Determine compliance status based on severity threshold
        status = self._determine_compliance_status(
            control.severity_threshold,
            critical_count,
            high_count, 
            medium_count,
            low_count
        )
        
        # Generate remediation notes
        remediation = self._generate_remediation_notes(control, total_findings, status)
        
        return ComplianceEvidence(
            control_id=control.control_id,
            scanner=", ".join(control.required_scanners),
            finding_count=total_findings,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            status=status,
            evidence_files=evidence_files[:10],  # Limit to first 10 files
            remediation_notes=remediation
        )
    
    def _determine_compliance_status(
        self,
        threshold: Severity,
        critical: int,
        high: int,
        medium: int, 
        low: int
    ) -> str:
        """Determine compliance status based on findings and threshold."""
        
        if critical > 0:
            return "non_compliant"
        
        if threshold == Severity.HIGH and high > 0:
            return "non_compliant" 
        
        if threshold == Severity.MEDIUM and (high > 0 or medium > 0):
            return "needs_review"
        
        if threshold == Severity.LOW and (high > 0 or medium > 0 or low > 0):
            return "needs_review"
        
        return "compliant"
    
    def _generate_executive_summary(
        self,
        compliance_percentage: float,
        compliant: int,
        non_compliant: int,
        needs_review: int
    ) -> str:
        """Generate executive summary for audit report."""
        
        total = compliant + non_compliant + needs_review
        
        summary = f"""
EXECUTIVE SUMMARY

This automated security audit evaluated {total} applicable {self.framework.name} controls using industry-standard SAST, SCA, and secrets detection tools.

COMPLIANCE OVERVIEW:
• Overall Compliance Rate: {compliance_percentage:.1f}%
• Fully Compliant Controls: {compliant} ({compliant/total*100:.1f}% of applicable controls)
• Non-Compliant Controls: {non_compliant} ({non_compliant/total*100:.1f}% of applicable controls)  
• Controls Requiring Review: {needs_review} ({needs_review/total*100:.1f}% of applicable controls)

RISK ASSESSMENT:
"""
        
        if compliance_percentage >= 90:
            summary += "• RISK LEVEL: LOW - Strong security posture with minimal compliance gaps"
        elif compliance_percentage >= 75:
            summary += "• RISK LEVEL: MEDIUM - Generally compliant with some areas requiring attention"  
        elif compliance_percentage >= 50:
            summary += "• RISK LEVEL: HIGH - Significant compliance gaps requiring immediate remediation"
        else:
            summary += "• RISK LEVEL: CRITICAL - Extensive non-compliance requiring urgent action"
        
        return summary.strip()
    
    def _generate_recommendations(self, evidence_list: List[ComplianceEvidence]) -> List[str]:
        """Generate actionable recommendations based on findings."""
        
        recommendations = []
        
        # Count issues by type
        critical_controls = len([e for e in evidence_list if e.critical_count > 0])
        high_controls = len([e for e in evidence_list if e.high_count > 0])
        non_compliant = len([e for e in evidence_list if e.status == "non_compliant"])
        
        if critical_controls > 0:
            recommendations.append(
                f"IMMEDIATE ACTION: Address {critical_controls} controls with critical security findings. "
                "These represent severe security vulnerabilities requiring urgent remediation."
            )
        
        if high_controls > 0:
            recommendations.append(
                f"HIGH PRIORITY: Remediate {high_controls} controls with high-severity findings within 30 days."
            )
        
        if non_compliant > 0:
            recommendations.append(
                f"COMPLIANCE REMEDIATION: {non_compliant} controls are currently non-compliant. "
                "Develop remediation plans with defined timelines and responsible parties."
            )
        
        # Generic recommendations
        recommendations.extend([
            "Implement automated security scanning in CI/CD pipelines to prevent regression.",
            "Establish regular security audit cycles (quarterly recommended).",
            "Provide security training to development teams on secure coding practices.",
            "Document all remediation efforts for audit trail purposes.",
            "Consider engaging security consultants for complex compliance requirements."
        ])
        
        return recommendations
    
    def _generate_remediation_notes(
        self, 
        control: 'ComplianceControl',
        finding_count: int,
        status: str
    ) -> str:
        """Generate specific remediation guidance for a control."""
        
        if status == "compliant":
            return "Control is compliant. Continue current security practices and monitor regularly."
        
        notes = f"Control {control.control_id} has {finding_count} findings. "
        
        if status == "non_compliant":
            notes += "IMMEDIATE REMEDIATION REQUIRED: "
        else:
            notes += "REVIEW RECOMMENDED: "
        
        # Add control-specific guidance
        category_guidance = {
            "Security": "Review access controls, encryption, and authentication mechanisms.",
            "Identify": "Update asset inventory and risk assessment procedures.",
            "Protect": "Strengthen protective controls and data handling procedures.", 
            "Detect": "Enhance monitoring and detection capabilities.",
            "Respond": "Review incident response procedures and forensic capabilities.",
            "Basic": "Address fundamental security controls as highest priority.",
            "Foundational": "Strengthen core security infrastructure.",
            "Organizational": "Review governance and policy frameworks."
        }
        
        notes += category_guidance.get(control.category, "Review security controls and implement necessary improvements.")
        
        return notes
    
    def export_report(
        self,
        report: AuditReport,
        output_path: Path,
        format: str = "json"
    ) -> None:
        """Export compliance report to file."""
        
        output_path = Path(output_path)
        
        if format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        
        elif format.lower() == "yaml":
            with open(output_path, 'w') as f:
                yaml.dump(asdict(report), f, default_flow_style=False, sort_keys=False)
        
        elif format.lower() == "markdown":
            self._export_markdown_report(report, output_path)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_markdown_report(self, report: AuditReport, output_path: Path) -> None:
        """Export audit report as professional markdown document."""
        
        markdown_content = f"""# Security Audit Report
## {report.framework} Compliance Assessment

**Organization:** {report.organization}  
**Audit Date:** {report.scan_date}  
**Auditor:** {report.auditor}  
**Target System:** {report.scan_target}

---

{report.executive_summary}

## Detailed Compliance Results

**Framework:** {report.framework} v{report.framework_version}  
**Total Applicable Controls:** {report.total_controls}  
**Compliance Rate:** {report.compliance_percentage:.1f}%

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Compliant | {report.compliant_controls} | {report.compliant_controls/report.total_controls*100:.1f}% |
| ❌ Non-Compliant | {report.non_compliant_controls} | {report.non_compliant_controls/report.total_controls*100:.1f}% |
| ⚠️ Needs Review | {report.needs_review_controls} | {report.needs_review_controls/report.total_controls*100:.1f}% |

## Control-by-Control Analysis

"""
        
        for evidence in report.detailed_findings:
            status_emoji = {
                "compliant": "✅",
                "non_compliant": "❌", 
                "needs_review": "⚠️"
            }
            
            markdown_content += f"""### {status_emoji.get(evidence.status, "❓")} Control {evidence.control_id}

**Scanner(s):** {evidence.scanner}  
**Total Findings:** {evidence.finding_count}  
**Status:** {evidence.status.replace('_', ' ').title()}

**Finding Breakdown:**
- Critical: {evidence.critical_count}
- High: {evidence.high_count}  
- Medium: {evidence.medium_count}
- Low: {evidence.low_count}

**Remediation Notes:**
{evidence.remediation_notes}

**Evidence Files:** {len(evidence.evidence_files)} file(s) analyzed

---

"""
        
        markdown_content += f"""## Recommendations

"""
        for i, rec in enumerate(report.recommendations, 1):
            markdown_content += f"{i}. {rec}\n"
        
        markdown_content += f"""

## Auditor Attestation

{report.attestation['auditor_statement']}

**Methodology:** {report.attestation['methodology']}  
**Scope:** {report.attestation['scope']}  
**Limitations:** {report.attestation['limitations']}

**Auditor:** {report.attestation['auditor']} ({report.attestation['auditor_title']})  
**Organization:** {report.attestation['audit_firm']}  
**Date:** {report.attestation['date']}

---

*This report was generated by AuditHound - Automated Security Audit Platform*
"""
        
        with open(output_path, 'w') as f:
            f.write(markdown_content)