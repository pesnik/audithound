"""Docker utility for running security scanners in containers."""

import subprocess
import docker
from pathlib import Path
from typing import List, Dict, Any, Optional


class DockerRunner:
    """Utility class for running security scanners in Docker containers."""
    
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.client = None
        self._check_docker_availability()
    
    def _check_docker_availability(self) -> None:
        """Check if Docker is available and accessible."""
        try:
            self.client = docker.from_env()
            self.client.ping()
        except Exception:
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None
    
    def run_command(self, cmd: List[str], target_path: Path, image: str, 
                   environment: Optional[Dict[str, str]] = None) -> str:
        """
        Run a command in a Docker container.
        
        Args:
            cmd: Command to run
            target_path: Path to mount in container
            image: Docker image to use
            environment: Environment variables
            
        Returns:
            Command output
            
        Raises:
            subprocess.CalledProcessError: If command fails
            RuntimeError: If Docker is not available
        """
        if not self.is_available():
            raise RuntimeError("Docker is not available")
        
        try:
            # Pull image if not present
            self._ensure_image_available(image)
            
            # Prepare volume mounts
            volumes = {
                str(target_path.absolute()): {
                    'bind': '/workspace',
                    'mode': 'ro'
                }
            }
            
            # Set working directory
            working_dir = '/workspace'
            
            # Prepare environment
            env = environment or {}
            
            # Update command to work within container
            container_cmd = self._adapt_command_for_container(cmd)
            
            # Run container
            container = self.client.containers.run(
                image=image,
                command=container_cmd,
                volumes=volumes,
                working_dir=working_dir,
                environment=env,
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
                network_disabled=True,  # Security: disable network access
                mem_limit='512m',       # Limit memory usage
                cpu_period=100000,      # Limit CPU usage
                cpu_quota=50000,        # 50% CPU limit
                security_opt=['no-new-privileges'],  # Security hardening
                user='1000:1000',       # Run as non-root user
                read_only=True,         # Make filesystem read-only
                tmpfs={'/tmp': 'noexec,nosuid,size=100m'},  # Secure tmp
                timeout=self.timeout
            )
            
            # Decode output
            if isinstance(container, bytes):
                return container.decode('utf-8', errors='replace')
            else:
                return str(container)
                
        except docker.errors.ContainerError as e:
            # Container ran but exited with non-zero code
            output = e.container.logs().decode('utf-8', errors='replace')
            raise subprocess.CalledProcessError(e.exit_status, cmd, output)
        
        except docker.errors.ImageNotFound:
            raise RuntimeError(f"Docker image not found: {image}")
        
        except Exception as e:
            raise RuntimeError(f"Docker execution failed: {str(e)}")
    
    def _ensure_image_available(self, image: str) -> None:
        """Ensure Docker image is available locally."""
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            # Try to pull the image
            try:
                print(f"📥 Pulling Docker image: {image}")
                self.client.images.pull(image)
            except Exception as e:
                raise RuntimeError(f"Failed to pull Docker image {image}: {str(e)}")
    
    def _adapt_command_for_container(self, cmd: List[str]) -> List[str]:
        """
        Adapt command for running inside container.
        
        This method adjusts file paths and arguments to work within the container
        environment where the target is mounted at /workspace.
        """
        adapted_cmd = []
        
        for arg in cmd:
            # Replace absolute paths with container paths
            if arg.startswith('/') and not arg.startswith('/workspace'):
                # This might be a path argument - replace with workspace path
                adapted_cmd.append(arg.replace(str(Path.cwd()), '/workspace'))
            else:
                adapted_cmd.append(arg)
        
        return adapted_cmd
    
    def get_image_info(self, image: str) -> Dict[str, Any]:
        """Get information about a Docker image."""
        if not self.is_available():
            return {}
        
        try:
            image_obj = self.client.images.get(image)
            return {
                'id': image_obj.short_id,
                'tags': image_obj.tags,
                'created': image_obj.attrs.get('Created', ''),
                'size': image_obj.attrs.get('Size', 0),
                'architecture': image_obj.attrs.get('Architecture', ''),
                'os': image_obj.attrs.get('Os', '')
            }
        except Exception:
            return {}
    
    def cleanup_images(self, keep_latest: bool = True) -> None:
        """Clean up unused Docker images."""
        if not self.is_available():
            return
        
        try:
            # Remove dangling images
            self.client.images.prune()
            
            if not keep_latest:
                # Remove all unused images
                self.client.images.prune(filters={'dangling': False})
        except Exception as e:
            print(f"Warning: Failed to cleanup Docker images: {e}")
    
    def get_scanner_images(self) -> Dict[str, str]:
        """Get mapping of scanners to their Docker images."""
        return {
            'bandit': 'pipelinecomponents/bandit:latest',
            'safety': 'pyupio/safety:latest',
            'semgrep': 'returntocorp/semgrep:latest',
            'trufflehog': 'trufflesecurity/trufflehog:latest',
            'checkov': 'bridgecrew/checkov:latest'
        }