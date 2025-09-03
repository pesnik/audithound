# 🔍 AuditHound

> **A comprehensive security audit platform with an intuitive TUI for multi-scanner SAST, SCA, secrets detection, and IaC security scanning.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security Scanners](https://img.shields.io/badge/scanners-5-green.svg)](#supported-scanners)

AuditHound is a powerful security audit orchestrator that integrates multiple industry-standard security scanning tools into a single, easy-to-use terminal user interface (TUI). Whether you're performing code security reviews, dependency audits, secrets detection, or infrastructure security assessments, AuditHound provides a unified interface for comprehensive security analysis.

## ✨ Key Features

### 🎯 **Multi-Scanner Integration**
- **5 integrated security scanners** covering all major security domains
- **Unified interface** for managing different scanner types
- **Parallel execution** for faster scan completion
- **Configurable scanner selection** - run only what you need

### 🖥️ **Interactive TUI**
- **Beautiful terminal interface** built with Textual
- **Real-time scan progress** with streaming updates
- **Rich results visualization** with severity breakdowns
- **Tabbed navigation** between Dashboard, Results, and Configuration
- **Keyboard shortcuts** for power users

### 🔧 **Flexible Configuration**
- **YAML configuration files** for repeatable scans
- **Per-scanner customization** with severity thresholds
- **Include/exclude patterns** for targeted scanning
- **Docker support** for isolated execution
- **Export presets** for different output formats

### 📊 **Rich Output Formats**
- **JSON, YAML, CSV, XML, SARIF** export formats
- **Filterable results** by severity, scanner, or file type
- **Summary statistics** and trend analysis
- **Integration-ready** outputs for CI/CD pipelines

## 🛡️ Supported Scanners

| Scanner | Purpose | Language Support | Key Features |
|---------|---------|------------------|--------------|
| **[Bandit](https://bandit.readthedocs.io/)** | SAST - Python Security | Python | AST-based security linting, common vulnerability patterns |
| **[Semgrep](https://semgrep.dev/)** | SAST - Multi-language | Python, JS, Java, Go, etc. | Rule-based pattern matching, custom rules support |
| **[Safety](https://pyup.io/safety/)** | SCA - Dependency Scanning | Python packages | Known vulnerability database, license checking |
| **[TruffleHog](https://trufflesecurity.com/)** | Secrets Detection | All text files | API keys, tokens, credentials, high accuracy detection |
| **[Checkov](https://checkov.io/)** | IaC Security | Terraform, K8s, etc. | Infrastructure as Code security and compliance |

## 🚨 **AUDIT WEEK EMERGENCY TOOLKIT**

**⚡ Your team has an audit this week? Get compliance-ready in 5 minutes:**

```bash
# 1. Install AuditHound with all scanners
pip install audithound[scanners]

# 2. Run automated compliance audit (SOC 2, NIST, CIS, OWASP)
audithound audit . --framework soc2 --auditor "Your Name" --org "Your Company"

# 3. Use enterprise audit preparation script
curl -O https://raw.githubusercontent.com/pesnik/audithound/main/scripts/prepare-audit.sh
chmod +x prepare-audit.sh
./prepare-audit.sh

# 4. Generate executive summary for auditors
audithound audit . --framework soc2 --format markdown --output audit-summary
```

**📋 What you'll get:**
- ✅ **Professional compliance reports** for SOC 2, NIST, CIS, OWASP
- ✅ **Executive summaries** with compliance percentages  
- ✅ **Evidence packages** with detailed technical findings
- ✅ **Audit checklists** and preparation templates
- ✅ **Before/after remediation tracking**

---

## 🚀 Quick Start

### Installation

#### Option 1: Using pip (recommended)
```bash
pip install audithound
```

#### Option 2: Development installation
```bash
git clone https://github.com/pesnik/audithound.git
cd audithound
pip install -e .
```

#### Option 3: With scanner dependencies  
```bash
pip install audithound[scanners]
```

#### Option 4: Enterprise audit-ready setup
```bash
pip install audithound[scanners]
wget https://raw.githubusercontent.com/pesnik/audithound/main/scripts/prepare-audit.sh
chmod +x prepare-audit.sh
```

### Basic Usage

#### 1. **🔍 Compliance Audit** (Enterprise Ready)
```bash
# Generate SOC 2 compliance report
audithound audit /path/to/project --framework soc2 --auditor "Jane Doe" --org "Acme Corp"

# Multi-framework audit  
audithound audit . --framework nist --format markdown --output nist-compliance

# Quick compliance check
audithound audit . --framework owasp --format json | jq '.compliance_percentage'
```

#### 2. **🖥️ Interactive TUI Mode**
```bash
# Launch the interactive TUI
audithound tui /path/to/your/project

# TUI with custom configuration
audithound tui /path/to/project --config audithound.yaml
```

#### 3. **⚡ Command-line Scanning**
```bash
# Quick scan with default scanners
audithound scan /path/to/project

# Scan with specific tools
audithound scan /path/to/project --tools bandit,safety,trufflehog

# Scan with output file
audithound scan /path/to/project --output results.json --format json
```

#### 4. **📋 Scanner Management**
```bash
# List all available scanners
audithound scanners --list-all

# Check scanner availability
audithound scanners --check
```

## 📋 Usage Examples

### Basic Project Scan
```bash
# Scan current directory with all available scanners
audithound scan .

# Scan specific directory with TUI
audithound tui ./my-python-app
```

### Targeted Security Scanning
```bash
# Python security focus - code + dependencies + secrets
audithound scan ./python-app --tools bandit,safety,trufflehog

# Infrastructure security - IaC + secrets  
audithound scan ./terraform --tools checkov,trufflehog

# Comprehensive analysis - all scanners
audithound scan ./enterprise-app --tools bandit,semgrep,safety,trufflehog,checkov
```

### Configuration-driven Scanning
```bash
# Use custom configuration file
audithound scan . --config security-audit.yaml

# Export configuration template
audithound config --export-template > audithound.yaml
```

### Output Formats and Integration
```bash
# JSON output for CI/CD integration
audithound scan . --output audit-results.json --format json

# SARIF for GitHub Security tab
audithound scan . --output results.sarif --format sarif

# CSV for reporting
audithound scan . --output security-report.csv --format csv
```

## ⚙️ Configuration

### Sample Configuration File (`audithound.yaml`)

```yaml
# AuditHound Configuration
target: "."
output:
  format: "json"
  file: "audit-results.json"
  include_passed: false
  group_by_severity: true

# Scanner Configuration
scanners:
  bandit:
    enabled: true
    severity_threshold: "medium"
    args: ["--skip", "B101,B601"]
    
  safety:
    enabled: true
    severity_threshold: "high"
    
  semgrep:
    enabled: true
    severity_threshold: "medium"
    args: ["--config=auto"]
    
  trufflehog:
    enabled: true
    args: ["--only-verified"]
    
  checkov:
    enabled: true
    severity_threshold: "high"
    args: ["--framework", "terraform"]

# File Patterns
include_patterns:
  - "*.py"
  - "*.js"
  - "*.tf"
  - "*.yaml"
  - "*.json"

exclude_patterns:
  - "node_modules/*"
  - "*.test.*"
  - "venv/*"
  - ".git/*"

# Docker Configuration (optional)
docker:
  enabled: false
  timeout: 300
```

## 🎨 TUI Interface

The TUI provides three main sections:

### 🏠 **Dashboard Tab**
- **Target Information**: Current scan target and configuration status
- **Scan Status**: Real-time progress and current scanner status
- **Quick Actions**: Start scan, view results, configure scanners
- **Recent Activity**: History of previous scans

### 📊 **Results Tab**  
- **Summary Panels**: Total findings and severity breakdown
- **Findings Table**: Detailed results with filtering capabilities
- **Progress Indicator**: Real-time scan progress during execution
- **Export Options**: Save results in multiple formats

### ⚙️ **Configuration Tab**
- **Scanner Toggles**: Enable/disable individual scanners
- **Output Settings**: Configure result formats and file paths  
- **Theme Options**: Customize the TUI appearance
- **Advanced Settings**: Docker, performance, and other options

### 🔥 **Keyboard Shortcuts**
- `1` - Dashboard tab
- `2` - Results tab  
- `3` - Configuration tab
- `F5` - Start scan
- `t` - Toggle theme
- `e` - Export results
- `Ctrl+Shift+P` - Command palette
- `q` or `Ctrl+C` - Quit

## 🔌 CI/CD Integration

### GitHub Actions
```yaml
name: Security Audit
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install AuditHound
        run: pip install audithound[scanners]
        
      - name: Run Security Scan
        run: audithound scan . --output results.sarif --format sarif
        
      - name: Upload SARIF results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif
```

### GitLab CI
```yaml
security_audit:
  image: python:3.11
  script:
    - pip install audithound[scanners]
    - audithound scan . --output audit-results.json
  artifacts:
    reports:
      junit: audit-results.json
```

## 🛠️ Development

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- [just](https://github.com/casey/just) (optional, for development tasks)

### Development Setup
```bash
# Clone repository
git clone https://github.com/pesnik/audithound.git
cd audithound

# Setup development environment
just setup

# Install in development mode
just install

# Run linting
just lint

# Run tests
just test

# Launch TUI for testing
just dev-tui ./test-project
```

### Project Structure
```
audithound/
├── audithound/
│   ├── core/           # Core scanning logic
│   ├── scanners/       # Individual scanner implementations  
│   ├── tui/           # Terminal user interface
│   ├── utils/         # Utilities and helpers
│   └── main.py        # CLI entry point
├── tests/             # Test suite
├── examples/          # Example configurations
└── docs/             # Documentation
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution
- 🔍 **New Scanner Integrations** - Add support for additional security tools
- 🎨 **TUI Enhancements** - Improve the user interface and experience  
- 📊 **Output Formats** - Support for additional export formats
- 🧪 **Test Coverage** - Expand test suite coverage
- 📚 **Documentation** - Improve documentation and examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Textual](https://github.com/Textualize/textual) - Amazing TUI framework
- [Typer](https://github.com/tiangolo/typer) - Excellent CLI framework
- All the security scanner projects that make this tool possible

## 📞 Support

- 📚 [Documentation](https://github.com/pesnik/audithound/wiki)
- 🐛 [Issue Tracker](https://github.com/pesnik/audithound/issues)
- 💬 [Discussions](https://github.com/pesnik/audithound/discussions)

---

**Made with ❤️ for the security community**