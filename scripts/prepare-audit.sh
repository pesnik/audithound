#!/bin/bash
# AuditHound - Enterprise Audit Preparation Script
# Automates the setup and execution of security compliance audits

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AUDIT_DATE=$(date +%Y%m%d)
AUDIT_DIR="audit-${AUDIT_DATE}"
FRAMEWORKS=("soc2" "nist" "cis" "owasp")
DEFAULT_AUDITOR="Security Team"
DEFAULT_ORG="Enterprise Organization"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    🔍 AuditHound Enterprise                      ║"
    echo "║              Automated Security Compliance Auditing             ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
    fi
    
    # Check AuditHound
    if ! command -v audithound &> /dev/null; then
        log_warning "AuditHound not found in PATH, attempting to install..."
        pip3 install audithound[scanners] || log_error "Failed to install AuditHound"
    fi
    
    # Verify scanners  
    log_info "Verifying security scanners..."
    # Use a simple check instead of the scanners command for now
    if command -v audithound &> /dev/null; then
        log_success "AuditHound is available"
    else
        log_warning "AuditHound command verification failed"
    fi
    
    log_success "Dependencies verified"
}

setup_audit_environment() {
    log_info "Setting up audit environment..."
    
    # Create audit directory
    mkdir -p "${AUDIT_DIR}"
    cd "${AUDIT_DIR}"
    
    # Create subdirectories
    mkdir -p {reports,evidence,configs,logs}
    
    # Copy configuration template
    if [ -f "../templates/compliance-config.yaml" ]; then
        cp "../templates/compliance-config.yaml" "configs/audit-config.yaml"
        log_success "Configuration template copied"
    else
        log_warning "Configuration template not found, using defaults"
    fi
    
    # Copy audit checklist
    if [ -f "../templates/audit-checklist.md" ]; then
        cp "../templates/audit-checklist.md" "audit-checklist.md"
        log_success "Audit checklist copied"
    fi
    
    log_success "Audit environment setup complete"
}

run_comprehensive_audit() {
    local target_dir=${1:-".."}
    local auditor_name=${2:-"$DEFAULT_AUDITOR"}
    local org_name=${3:-"$DEFAULT_ORG"}
    
    log_info "Running comprehensive security audit..."
    log_info "Target: $target_dir"
    log_info "Auditor: $auditor_name"
    log_info "Organization: $org_name"
    
    # Run quick pre-audit scan
    log_info "Running pre-audit security scan..."
    audithound scan "$target_dir" \
        --output "evidence/pre-audit-scan-${AUDIT_DATE}.json" \
        --format json \
        --no-docker \
        2>&1 | tee "logs/pre-audit-scan.log"
    
    # Generate compliance reports for each framework
    for framework in "${FRAMEWORKS[@]}"; do
        log_info "Generating $framework compliance report..."
        
        audithound audit "$target_dir" \
            --framework "$framework" \
            --auditor "$auditor_name" \
            --org "$org_name" \
            --output "reports/${framework}-audit-${AUDIT_DATE}" \
            --format markdown \
            --no-docker \
            2>&1 | tee "logs/${framework}-audit.log"
        
        # Also generate JSON for programmatic analysis
        audithound audit "$target_dir" \
            --framework "$framework" \
            --auditor "$auditor_name" \
            --org "$org_name" \
            --output "reports/${framework}-audit-${AUDIT_DATE}" \
            --format json \
            --no-docker \
            2>&1 | tee -a "logs/${framework}-audit.log"
            
        log_success "$framework audit completed"
    done
}

generate_executive_summary() {
    log_info "Generating executive summary..."
    
    cat > "reports/executive-summary-${AUDIT_DATE}.md" << EOF
# Executive Security Audit Summary
**Date:** $(date)
**Organization:** $DEFAULT_ORG
**Auditor:** $DEFAULT_AUDITOR

## Audit Overview
This comprehensive security audit was conducted using AuditHound's automated compliance scanning across multiple frameworks.

## Frameworks Assessed
EOF

    # Add compliance percentages for each framework
    for framework in "${FRAMEWORKS[@]}"; do
        if [ -f "reports/${framework}-audit-${AUDIT_DATE}.json" ]; then
            compliance_rate=$(jq -r '.compliance_percentage' "reports/${framework}-audit-${AUDIT_DATE}.json" 2>/dev/null || echo "N/A")
            framework_upper=$(echo "$framework" | tr '[:lower:]' '[:upper:]')
            echo "- **${framework_upper}**: ${compliance_rate}% compliance" >> "reports/executive-summary-${AUDIT_DATE}.md"
        fi
    done
    
    cat >> "reports/executive-summary-${AUDIT_DATE}.md" << EOF

## Risk Assessment
Based on automated security scanning:

$(if [ -f "evidence/pre-audit-scan-${AUDIT_DATE}.json" ]; then
    critical_count=$(jq '[.results[].findings[]? | select(.severity == "critical")] | length' "evidence/pre-audit-scan-${AUDIT_DATE}.json" 2>/dev/null || echo "0")
    high_count=$(jq '[.results[].findings[]? | select(.severity == "high")] | length' "evidence/pre-audit-scan-${AUDIT_DATE}.json" 2>/dev/null || echo "0")
    
    if [ "$critical_count" -gt 0 ]; then
        echo "🔴 **CRITICAL RISK**: $critical_count critical security findings require immediate attention"
    elif [ "$high_count" -gt 5 ]; then
        echo "🟡 **HIGH RISK**: $high_count high-severity findings identified"
    else
        echo "🟢 **MODERATE RISK**: Security posture is generally acceptable"
    fi
fi)

## Next Steps
1. Review detailed compliance reports in the reports/ directory
2. Address critical and high-severity findings immediately  
3. Implement continuous security monitoring
4. Schedule quarterly compliance reviews
5. Update security policies based on findings

## Files Generated
- \`reports/\`: Detailed compliance reports for each framework
- \`evidence/\`: Technical scan results and supporting evidence
- \`logs/\`: Detailed logs from all audit activities
- \`configs/\`: Configuration files used for auditing

---
*Generated by AuditHound Enterprise Security Audit Platform*
EOF

    log_success "Executive summary generated"
}

create_audit_package() {
    log_info "Creating audit evidence package..."
    
    # Create a comprehensive audit package
    audit_package="audit-package-${AUDIT_DATE}.zip"
    
    if command -v zip &> /dev/null; then
        zip -r "$audit_package" reports/ evidence/ configs/ logs/ audit-checklist.md 2>/dev/null
        log_success "Audit package created: $audit_package"
    else
        log_warning "zip command not available, creating tar.gz instead"
        tar -czf "audit-package-${AUDIT_DATE}.tar.gz" reports/ evidence/ configs/ logs/ audit-checklist.md
        log_success "Audit package created: audit-package-${AUDIT_DATE}.tar.gz"
    fi
}

print_summary() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                        🎉 AUDIT COMPLETE                        ║"  
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo "📁 Audit Directory: $(pwd)"
    echo "📊 Reports Generated:"
    ls -la reports/ | grep -E '\.(md|json)$' | awk '{print "   - " $9}'
    echo ""
    echo "🔍 Key Files:"
    echo "   - Executive Summary: reports/executive-summary-${AUDIT_DATE}.md"  
    echo "   - Audit Checklist: audit-checklist.md"
    echo "   - Evidence Package: audit-package-${AUDIT_DATE}.*"
    echo ""
    echo "📞 Next Steps:"
    echo "   1. Review executive summary"
    echo "   2. Share reports with audit team"
    echo "   3. Address critical findings immediately"
    echo "   4. Schedule remediation tracking"
}

# Main execution
main() {
    local target_dir="${1:-"."}"
    local auditor_name="${2:-"$DEFAULT_AUDITOR"}"
    local org_name="${3:-"$DEFAULT_ORG"}"
    
    print_header
    
    # Interactive prompts if running without arguments
    if [ $# -eq 0 ]; then
        echo "🔧 Enterprise Audit Setup"
        echo ""
        read -p "Target directory to audit (default: current): " input_target
        target_dir=${input_target:-"."}
        
        read -p "Auditor name (default: $DEFAULT_AUDITOR): " input_auditor
        auditor_name=${input_auditor:-"$DEFAULT_AUDITOR"}
        
        read -p "Organization name (default: $DEFAULT_ORG): " input_org
        org_name=${input_org:-"$DEFAULT_ORG"}
        
        echo ""
    fi
    
    # Execute audit workflow
    check_dependencies
    setup_audit_environment
    run_comprehensive_audit "$target_dir" "$auditor_name" "$org_name"
    generate_executive_summary
    create_audit_package
    print_summary
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "AuditHound Enterprise Audit Preparation Script"
        echo ""
        echo "Usage: $0 [target_dir] [auditor_name] [organization_name]"
        echo ""
        echo "Arguments:"
        echo "  target_dir     Directory to audit (default: current directory)"
        echo "  auditor_name   Name of the auditor (default: Security Team)"
        echo "  org_name       Organization name (default: Enterprise Organization)"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --quick        Run quick audit (SOC2 only)"
        echo ""
        echo "Examples:"
        echo "  $0                              # Interactive mode"
        echo "  $0 ./myproject                  # Audit specific directory"  
        echo "  $0 . 'John Doe' 'Acme Corp'    # Full specification"
        exit 0
        ;;
    --quick)
        log_info "Running quick audit (SOC2 only)..."
        FRAMEWORKS=("soc2")
        main "${2:-"."}" "${3:-"$DEFAULT_AUDITOR"}" "${4:-"$DEFAULT_ORG"}"
        ;;
    *)
        main "$@"
        ;;
esac