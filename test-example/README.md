# AuditHound Example

This directory contains example vulnerable code for testing AuditHound scanners.

## Files included:
- `audithound.yaml` - Example configuration
- `vulnerable_app.py` - Python code with security vulnerabilities
- `Dockerfile` - Docker configuration with security issues
- `requirements.txt` - Python dependencies with known vulnerabilities
- `k8s-pod.yaml` - Kubernetes manifest with security misconfigurations
- `secret_key.txt` - Hardcoded secret file

## How to scan:
```bash
# Interactive mode
audithound scan test-example

# Headless mode with JSON output
audithound scan test-example --no-interactive --output results.json

# Scan with specific tools only
audithound scan test-example --tools bandit,safety --no-interactive
```

## Expected findings:
- **Bandit**: Hardcoded credentials, SQL injection, command injection, pickle usage
- **Safety**: Vulnerable Python packages in requirements.txt
- **Semgrep**: Code quality and security patterns
- **TruffleHog**: Hardcoded secrets in files
- **Checkov**: Dockerfile and Kubernetes security misconfigurations

⚠️  **Warning**: This code is intentionally vulnerable and should not be used in production!
