"""Main entry point for AuditHound application."""

import typer
from rich.console import Console
from pathlib import Path
from typing import Optional, List

from .tui.app import AuditHoundTUI
from .core.scanner import SecurityScanner
from .core.config import Config

app = typer.Typer(
    name="audithound",
    help="Security Audit Compliance TUI Tool",
    rich_markup_mode="rich"
)

console = Console()


@app.command()
def scan(
    target: str = typer.Argument(..., help="Target directory or repository to scan"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output report file path"),
    tools: Optional[List[str]] = typer.Option(None, "--tools", "-t", help="Specific tools to run"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-ni", help="Run in interactive TUI mode"),
    format: Optional[str] = typer.Option("json", "--format", "-f", help="Output format (json, csv, xml, html, sarif)"),
    severity: Optional[str] = typer.Option(None, "--severity", "-s", help="Minimum severity threshold (critical, high, medium, low, info)"),
    docker: Optional[bool] = typer.Option(None, "--docker/--no-docker", help="Use Docker for scanners"),
):
    """Run security audit scan on target directory or repository."""
    
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]❌ Target path does not exist: {target}[/red]")
        raise typer.Exit(1)
    
    try:
        # Load configuration
        config = Config.load(config_file)
        
        # Override config with CLI arguments
        if format:
            config.output.format = format
        if output:
            config.output.file = str(output)
        if docker is not None:
            config.use_docker = docker
        if severity:
            # Apply severity threshold to all enabled scanners
            for scanner_config in config.scanners.values():
                if scanner_config.enabled:
                    scanner_config.severity_threshold = severity
        
        if interactive:
            # Launch TUI application
            console.print("🚀 Launching AuditHound TUI...")
            tui_app = AuditHoundTUI(
                target=target,
                config=config,
                config_file=config_file,
                output=output,
                tools=tools,
                theme="default"
            )
            tui_app.run()
        else:
            # Run headless scan
            console.print(f"🔍 Starting headless scan of [cyan]{target}[/cyan]")
            
            scanner = SecurityScanner(config)
            results = scanner.scan(target, tools)
            
            if output:
                scanner.export_results(results, output)
                console.print(f"[green]📄 Report saved to: {output}[/green]")
            else:
                scanner.print_results(results)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Scan interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    init: bool = typer.Option(False, "--init", help="Initialize default configuration"),
    validate: Optional[Path] = typer.Option(None, "--validate", help="Validate configuration file"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    path: str = typer.Option("audithound.yaml", "--path", "-p", help="Configuration file path")
):
    """Manage AuditHound configuration."""
    
    if init:
        config_path = Path(path)
        if config_path.exists():
            if not typer.confirm(f"Configuration file {path} already exists. Overwrite?"):
                console.print("[yellow]Configuration creation cancelled.[/yellow]")
                return
        
        Config.create_default(path)
        console.print(f"[green]✅ Default configuration created at: {path}[/green]")
    
    if validate:
        if Config.validate(validate):
            console.print(f"[green]✅ Configuration file {validate} is valid[/green]")
        else:
            console.print(f"[red]❌ Configuration file {validate} is invalid[/red]")
            raise typer.Exit(1)
    
    if show:
        try:
            config = Config.load(Path(path) if Path(path).exists() else None)
            console.print("[cyan]📋 Current Configuration:[/cyan]")
            console.print(config.to_yaml())
        except Exception as e:
            console.print(f"[red]❌ Error loading configuration: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def tools(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all available scanners"),
    check: bool = typer.Option(False, "--check", "-c", help="Check scanner availability"),
    docker_images: bool = typer.Option(False, "--docker-images", help="Show Docker images for scanners")
):
    """Show information about available security scanners."""
    
    if list_all:
        console.print("[cyan]📋 Available Security Scanners:[/cyan]")
        scanners = {
            'bandit': 'Python security linter - finds common security issues in Python code',
            'safety': 'Checks Python dependencies for known security vulnerabilities',
            'semgrep': 'Static analysis tool for finding bugs, security issues, and code patterns',
            'trufflehog': 'Searches for secrets in git repositories and filesystems',
            'checkov': 'Static code analysis tool for infrastructure as code (IaC) security scanning'
        }
        
        for name, description in scanners.items():
            console.print(f"  [green]✓[/green] [bold]{name}[/bold]: {description}")
    
    if check:
        console.print("[cyan]🔍 Checking Scanner Availability:[/cyan]")
        
        # Load default config to get scanners
        config = Config.default()
        scanner = SecurityScanner(config)
        
        for name, scanner_class in scanner.available_scanners.items():
            scanner_instance = scanner_class(config.scanners[name], scanner.docker_runner)
            
            if scanner_instance.is_available():
                version = scanner_instance.get_version()
                console.print(f"  [green]✅ {name}[/green] - Version: {version}")
            else:
                console.print(f"  [red]❌ {name}[/red] - Not available")
    
    if docker_images:
        console.print("[cyan]🐳 Docker Images for Scanners:[/cyan]")
        
        from .utils.docker import DockerRunner
        docker_runner = DockerRunner()
        images = docker_runner.get_scanner_images()
        
        for scanner, image in images.items():
            console.print(f"  [blue]{scanner}[/blue]: {image}")


@app.command()
def tui(
    target: str = typer.Argument(..., help="Target directory or repository to scan"),
    config_file: Optional[Path] = typer.Option(None, "--config", "-c", help="Configuration file path"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output report file path"),
    tools: Optional[List[str]] = typer.Option(None, "--tools", "-t", help="Specific tools to run"),
    theme: str = typer.Option("default", "--theme", help="UI theme (default, dark, light, high_contrast, security)"),
):
    """Launch the interactive TUI interface."""
    
    target_path = Path(target)
    if not target_path.exists():
        console.print(f"[red]❌ Target path does not exist: {target}[/red]")
        raise typer.Exit(1)
    
    try:
        # Load configuration
        config = Config.load(config_file)
        
        console.print(f"🚀 Launching AuditHound TUI with {theme} theme...")
        tui_app = AuditHoundTUI(
            target=target,
            config=config,
            config_file=config_file,
            output=output,
            tools=tools,
            theme=theme
        )
        tui_app.run()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  TUI interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]❌ Error launching TUI: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show AuditHound version."""
    from . import __version__
    console.print(f"[cyan]AuditHound[/cyan] v{__version__}")


@app.command()
def example(
    output_dir: str = typer.Option("./audithound-example", "--output", "-o", help="Output directory for example")
):
    """Create example configuration and sample vulnerable code for testing."""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create example config
    Config.create_default(str(output_path / "audithound.yaml"))
    
    # Create sample vulnerable Python code
    vulnerable_py = '''
import os
import pickle
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# Hardcoded credentials (bandit will catch this)
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

# SQL Injection vulnerability
def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Vulnerable to SQL injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()

# Command injection vulnerability
@app.route('/ping')
def ping():
    host = request.args.get('host', 'localhost')
    # Vulnerable to command injection
    result = os.system(f'ping -c 1 {host}')
    return f"Ping result: {result}"

# Pickle deserialization vulnerability
def load_config(config_data):
    # Dangerous use of pickle
    return pickle.loads(config_data)

# Weak random generation
def generate_token():
    import random
    return random.randint(1000, 9999)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')  # Debug mode in production
'''
    
    # Create sample Dockerfile with security issues
    dockerfile = '''
FROM ubuntu:latest

# Running as root (security issue)
USER root

# Installing packages without specific versions
RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    curl \\
    wget

# Copying secrets into image (bad practice)
COPY secret_key.txt /app/

# Setting weak permissions
RUN chmod 777 /app

# Exposing unnecessary ports
EXPOSE 22 80 443 8080 9000

# Running with elevated privileges
CMD ["python3", "app.py"]
'''
    
    # Create sample requirements.txt with vulnerable packages
    requirements = '''
Django==2.0.0
requests==2.20.0
Pillow==5.0.0
PyYAML==3.13
Jinja2==2.10
'''
    
    # Create sample Kubernetes manifest with security issues
    k8s_manifest = '''
apiVersion: v1
kind: Pod
metadata:
  name: vulnerable-pod
spec:
  containers:
  - name: app
    image: nginx:latest
    securityContext:
      privileged: true
      runAsUser: 0
    env:
    - name: API_KEY
      value: "hardcoded-secret-key"
    ports:
    - containerPort: 80
    volumeMounts:
    - name: host-root
      mountPath: /host
  volumes:
  - name: host-root
    hostPath:
      path: /
'''
    
    # Write example files
    (output_path / "vulnerable_app.py").write_text(vulnerable_py)
    (output_path / "Dockerfile").write_text(dockerfile)
    (output_path / "requirements.txt").write_text(requirements)
    (output_path / "k8s-pod.yaml").write_text(k8s_manifest)
    (output_path / "secret_key.txt").write_text("super-secret-api-key-12345")
    
    # Create README
    readme = f'''# AuditHound Example

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
audithound scan {output_dir}

# Headless mode with JSON output
audithound scan {output_dir} --no-interactive --output results.json

# Scan with specific tools only
audithound scan {output_dir} --tools bandit,safety --no-interactive
```

## Expected findings:
- **Bandit**: Hardcoded credentials, SQL injection, command injection, pickle usage
- **Safety**: Vulnerable Python packages in requirements.txt
- **Semgrep**: Code quality and security patterns
- **TruffleHog**: Hardcoded secrets in files
- **Checkov**: Dockerfile and Kubernetes security misconfigurations

⚠️  **Warning**: This code is intentionally vulnerable and should not be used in production!
'''
    
    (output_path / "README.md").write_text(readme)
    
    console.print(f"[green]✅ Example created in: {output_path}[/green]")
    console.print("[yellow]📝 See README.md for scanning instructions[/yellow]")


if __name__ == "__main__":
    app()