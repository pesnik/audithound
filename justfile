# AuditHound Development Justfile
# https://github.com/casey/just

# Default recipe to display available commands
default:
    @just --list

# Install dependencies and setup development environment
setup:
    @echo "🔧 Setting up development environment..."
    uv sync --dev
    @echo "✅ Development environment ready!"

# Install the package in development mode
install:
    @echo "📦 Installing AuditHound in development mode..."
    uv pip install -e .
    @echo "✅ AuditHound installed!"

# Run linting with ruff
lint:
    @echo "🔍 Running linting checks..."
    uv run ruff check audithound/
    @echo "✅ Linting complete!"

# Auto-fix linting issues
lint-fix:
    @echo "🔧 Auto-fixing linting issues..."
    uv run ruff check --fix audithound/
    uv run ruff format audithound/
    @echo "✅ Linting fixes applied!"

# Run type checking with mypy
typecheck:
    @echo "🔍 Running type checks..."
    uv run mypy audithound/
    @echo "✅ Type checking complete!"

# Run all code quality checks
check: lint typecheck
    @echo "✅ All code quality checks passed!"

# Format code with ruff
format:
    @echo "🎨 Formatting code..."
    uv run ruff format audithound/
    @echo "✅ Code formatted!"

# Run unit tests
test:
    @echo "🧪 Running unit tests..."
    uv run pytest tests/unit/ -v
    @echo "✅ Unit tests complete!"

# Run integration tests
test-integration:
    @echo "🧪 Running integration tests..."
    uv run pytest tests/integration/ -v
    @echo "✅ Integration tests complete!"

# Run all tests with coverage
test-all:
    @echo "🧪 Running all tests with coverage..."
    uv run pytest tests/ -v --cov=audithound --cov-report=html --cov-report=term
    @echo "📊 Coverage report generated in htmlcov/"
    @echo "✅ All tests complete!"

# Clean up build artifacts and cache files
clean:
    @echo "🧹 Cleaning up build artifacts..."
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    @echo "✅ Cleanup complete!"

# Build the package
build:
    @echo "📦 Building package..."
    uv build
    @echo "✅ Package built in dist/"

# Install pre-commit hooks
install-hooks:
    @echo "🪝 Installing pre-commit hooks..."
    uv run pre-commit install
    @echo "✅ Pre-commit hooks installed!"

# Run pre-commit on all files
pre-commit:
    @echo "🪝 Running pre-commit checks..."
    uv run pre-commit run --all-files
    @echo "✅ Pre-commit checks complete!"

# Generate example vulnerable code for testing
example OUTPUT="./test-example":
    @echo "🎯 Creating example vulnerable code..."
    uv run audithound example --output {{OUTPUT}}
    @echo "✅ Example created in {{OUTPUT}}"

# Run AuditHound scan on example code
scan-example EXAMPLE_DIR="./test-example":
    @echo "🔍 Scanning example code..."
    uv run audithound scan {{EXAMPLE_DIR}} --no-interactive --format json --output example-results.json
    @echo "📄 Results saved to example-results.json"

# Start interactive TUI for development testing
dev-tui TARGET=".":
    @echo "🚀 Starting AuditHound TUI..."
    uv run audithound scan {{TARGET}}

# Launch TUI with specific theme
tui TARGET="." THEME="default":
    @echo "🎨 Starting AuditHound TUI with {{THEME}} theme..."
    uv run audithound tui {{TARGET}} --theme {{THEME}}

# Test all available themes
test-themes TARGET=".":
    @echo "🎨 Testing all TUI themes..."
    @echo "Available themes: default, dark, light, high_contrast, security"
    @echo "Run: just tui {{TARGET}} <theme_name>"

# Show AuditHound version
version:
    @echo "📋 AuditHound version:"
    uv run audithound version

# Show available security scanners
tools:
    @echo "🔧 Available security scanners:"
    uv run audithound tools --list

# Check scanner availability on system
check-scanners:
    @echo "🔍 Checking scanner availability..."
    uv run audithound tools --check

# Show Docker images for scanners
docker-images:
    @echo "🐳 Docker images for scanners:"
    uv run audithound tools --docker-images

# Initialize default configuration
config:
    @echo "⚙️  Creating default configuration..."
    uv run audithound config --init
    @echo "✅ Configuration created: audithound.yaml"

# Validate configuration file
validate-config CONFIG="audithound.yaml":
    @echo "✅ Validating configuration..."
    uv run audithound config --validate {{CONFIG}}

# Show current configuration
show-config:
    @echo "📋 Current configuration:"
    uv run audithound config --show

# Run a quick development scan (headless, JSON output)
dev-scan TARGET="." OUTPUT="dev-results.json":
    @echo "🔍 Running development scan..."
    uv run audithound scan {{TARGET}} --no-interactive --format json --output {{OUTPUT}}
    @echo "📄 Results saved to {{OUTPUT}}"

# Run security scan with specific tools only
scan-tools TARGET="." TOOLS="bandit,safety":
    @echo "🔍 Running scan with tools: {{TOOLS}}"
    uv run audithound scan {{TARGET}} --tools {{TOOLS}} --no-interactive

# Export results to different formats
export-results INPUT="results.json" FORMAT="html":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -f "{{INPUT}}" ]; then
        echo "❌ Input file {{INPUT}} not found"
        exit 1
    fi
    echo "📄 Converting results to {{FORMAT}} format..."
    # This would need implementation in the main app
    echo "⚠️  Export functionality needs to be implemented"

# Profile application performance
profile TARGET="." TOOLS="bandit":
    @echo "📊 Profiling AuditHound performance..."
    uv run python -m cProfile -s cumulative -m audithound.main scan {{TARGET}} --tools {{TOOLS}} --no-interactive

# Run benchmark tests
benchmark:
    @echo "⚡ Running performance benchmarks..."
    @echo "⚠️  Benchmark tests need to be implemented"

# Docker-related commands
docker-build:
    @echo "🐳 Building Docker image..."
    docker build -t audithound:latest .
    @echo "✅ Docker image built!"

# Pull all scanner Docker images
docker-pull:
    @echo "🐳 Pulling scanner Docker images..."
    docker pull pipelinecomponents/bandit:latest
    docker pull pyupio/safety:latest
    docker pull returntocorp/semgrep:latest
    docker pull trufflesecurity/trufflehog:latest
    docker pull bridgecrew/checkov:latest
    @echo "✅ All scanner images pulled!"

# Clean up Docker images
docker-clean:
    @echo "🐳 Cleaning up Docker images..."
    docker system prune -f
    @echo "✅ Docker cleanup complete!"

# Generate documentation
docs:
    @echo "📚 Generating documentation..."
    @echo "⚠️  Documentation generation needs to be implemented"

# Release preparation checklist
release-check: check test-all
    @echo "🚀 Release checklist:"
    @echo "✅ Code quality checks passed"
    @echo "✅ All tests passed"
    @echo "📋 Manual checklist:"
    @echo "  - Update version in __init__.py"
    @echo "  - Update CHANGELOG.md"
    @echo "  - Create git tag"
    @echo "  - Build and upload to PyPI"

# Show project structure
tree:
    @echo "📁 Project structure:"
    tree -I '.venv|__pycache__|*.pyc|.git|.pytest_cache|htmlcov|dist|build|*.egg-info' -a

# Quick development workflow: setup + check + test
dev: setup check test
    @echo "✅ Development workflow complete!"

# Full CI workflow: setup + check + test + build
ci: setup check test-all build
    @echo "✅ CI workflow complete!"

# Security check with multiple tools on current project
security-scan: 
    @echo "🔒 Running security scan on AuditHound itself..."
    just example audithound-self-test
    cp -r audithound/ audithound-self-test/
    uv run audithound scan audithound-self-test/ --no-interactive --format json --output audithound-security-report.json
    @echo "📄 Security report: audithound-security-report.json"
    rm -rf audithound-self-test/

# Run specific scanner on target
run-scanner SCANNER="bandit" TARGET=".":
    @echo "🔍 Running {{SCANNER}} on {{TARGET}}..."
    uv run audithound scan {{TARGET}} --tools {{SCANNER}} --no-interactive

# Watch for changes and run tests automatically (requires entr)
watch-test:
    @echo "👀 Watching for changes and running tests..."
    find audithound tests -name "*.py" | entr -c just test

# Interactive development console
console:
    @echo "🐍 Starting Python console with AuditHound loaded..."
    uv run python -c "import audithound; from audithound.core import *; from audithound.tui import *; print('AuditHound loaded! Available: Config, SecurityScanner, AuditHoundTUI'); exec(open('/dev/tty').read())" -i

# Show help for specific command
help COMMAND:
    @echo "📋 Help for {{COMMAND}}:"
    uv run audithound {{COMMAND}} --help

# TUI-specific development commands
# ================================

# Test TUI with dark theme
tui-dark TARGET=".":
    @echo "🌙 Starting AuditHound TUI with dark theme..."
    uv run audithound tui {{TARGET}} --theme dark

# Test TUI with light theme
tui-light TARGET=".":
    @echo "☀️  Starting AuditHound TUI with light theme..."
    uv run audithound tui {{TARGET}} --theme light

# Test TUI with high contrast theme (accessibility)
tui-accessible TARGET=".":
    @echo "♿ Starting AuditHound TUI with high contrast theme..."
    uv run audithound tui {{TARGET}} --theme high_contrast

# Test TUI with security-focused theme
tui-security TARGET=".":
    @echo "🛡️  Starting AuditHound TUI with security theme..."
    uv run audithound tui {{TARGET}} --theme security

# Quick TUI demo with example vulnerable code
demo:
    @echo "🎬 Running AuditHound TUI demo..."
    just example demo-code
    uv run audithound tui demo-code --theme security
    @echo "🧹 Cleaning up demo files..."
    rm -rf demo-code

# Test TUI state persistence (run multiple times to see session restore)
test-persistence TARGET=".":
    @echo "💾 Testing TUI session persistence..."
    @echo "Run this command multiple times to test session restore"
    uv run audithound tui {{TARGET}} --theme dark

# Clean TUI cache and session data
clean-tui:
    @echo "🧹 Cleaning TUI cache and session data..."
    rm -rf ~/.audithound/
    @echo "✅ TUI data cleaned!"

# Show TUI architecture overview
tui-info:
    @echo "🏗️  AuditHound TUI Architecture:"
    @echo ""
    @echo "📁 Core Components:"
    @echo "  • State Management  - centralized event-driven state"
    @echo "  • Component System  - reusable UI components"  
    @echo "  • Theme Engine      - 5 built-in themes + custom support"
    @echo "  • Service Layer     - scan execution & data persistence"
    @echo ""
    @echo "🎨 Available Themes:"
    @echo "  • default          - balanced dark theme"
    @echo "  • dark             - low-light optimized"
    @echo "  • light            - high-light environments"
    @echo "  • high_contrast    - accessibility focused"
    @echo "  • security         - threat-focused visualization"
    @echo ""
    @echo "⌨️  Key Features:"
    @echo "  • Command Palette   - Ctrl+Shift+P"
    @echo "  • Real-time Updates - live scan progress"
    @echo "  • Data Virtualization - handles large result sets" 
    @echo "  • Session Persistence - automatic save/restore"
    @echo ""
    @echo "🚀 Usage: just tui <target> <theme>"