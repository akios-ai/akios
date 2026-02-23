"""
AKIOS Container/Environment Detection - Robust detection for multiple platforms.

Detects:
- Docker containers (standard and rootless)
- Kubernetes pods and environments
- Podman containers
- Other container runtimes
- CI/CD environments

Provides accurate color/symbol mode defaults based on environment.

Usage:
    from akios.config.detection import (
        detect_container_type, is_kubernetes, is_podman, 
        detect_environment, get_preferred_color_mode
    )
    
    env = detect_environment()
    print(f"Running in: {env.container_type}")  # 'kubernetes', 'docker', 'podman', 'native'
    
    # Get recommended color mode for this environment
    mode = get_preferred_color_mode()
    print(f"Recommended: {mode}")  # 'unicode', 'dark', 'colorblind', etc.
"""

import os
import sys
from typing import Optional, Dict, NamedTuple
from enum import Enum


class ContainerType(Enum):
    """Detected container/environment type."""
    NATIVE = "native"              # Native OS (Linux, macOS, Windows)
    DOCKER = "docker"              # Docker standard
    DOCKER_ROOTLESS = "docker_rootless"  # Docker rootless mode
    KUBERNETES = "kubernetes"      # Kubernetes pod
    KUBERNETES_DOCKER = "kubernetes_docker"  # K8s with Docker runtime
    KUBERNETES_PODMAN = "kubernetes_podman"  # K8s with Podman runtime
    PODMAN = "podman"              # Podman (standalone)
    PODMAN_ROOTLESS = "podman_rootless"    # Podman rootless
    CI_GITHUB = "ci_github"        # GitHub Actions
    CI_GITLAB = "ci_gitlab"        # GitLab CI
    CI_JENKINS = "ci_jenkins"      # Jenkins
    CI_OTHER = "ci_other"          # Other CI/CD


class EnvironmentInfo(NamedTuple):
    """Information about current environment."""
    container_type: ContainerType
    is_tty: bool
    is_ci: bool
    color_capable: bool
    has_unicode_support: bool
    run_as_root: bool
    details: Dict[str, str]  # Additional details (namespace, pod name, etc.)


def is_docker() -> bool:
    """
    Check if running in Docker container.
    
    Detects:
    - Standard Docker: /.dockerenv file
    - Docker with cgroups v2: /sys/fs/cgroup/docker
    - Docker environment variables
    
    Returns:
        True if running in Docker
    """
    # Most reliable: /.dockerenv file (Docker creates this)
    if os.path.exists('/.dockerenv'):
        return True
    
    # Check cgroup detection (Docker)
    try:
        with open('/proc/self/cgroup', 'r') as f:
            cgroup = f.read()
            if 'docker' in cgroup or '/docker/' in cgroup:
                return True
    except (OSError, IOError):
        pass
    
    # Check environment variables
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTAINER'):
        return True
    
    return False


def is_docker_rootless() -> bool:
    """
    Check if running in rootless Docker.
    
    Detects:
    - User namespace mapping
    - Rootless Docker specific paths
    
    Returns:
        True if running in rootless Docker
    """
    # Rootless Docker typically runs with unprivileged user
    if is_docker() and os.geteuid() != 0:
        return True
    
    # Check for rootless-specific socket
    if os.path.exists(os.path.expanduser('~/.docker/run/docker.sock')):
        return True
    
    return False


def is_kubernetes() -> bool:
    """
    Check if running in Kubernetes pod.
    
    Detects:
    - K8s service account (/.../token)
    - K8s environment variables
    - K8s API server endpoint
    - Kubernetes.io hostname
    
    Returns:
        True if running in Kubernetes
    """
    # Most reliable: K8s service account token
    if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'):
        return True
    
    # K8s API server environment variable
    if os.environ.get('KUBERNETES_SERVICE_HOST'):
        return True
    
    # K8s namespace file
    if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/namespace'):
        return True
    
    # Hostname pattern for K8s
    hostname = os.environ.get('HOSTNAME', '')
    if 'kubernetes.io' in hostname or '-' in hostname and any(c.isdigit() for c in hostname):
        # Could be K8s pod name (typically contains dashes and digits)
        if os.environ.get('KUBERNETES_PORT'):
            return True
    
    return False


def get_kubernetes_info() -> Dict[str, str]:
    """
    Get information about Kubernetes environment.
    
    Returns:
        Dictionary with pod_name, namespace, service_host, etc.
    """
    info = {}
    
    try:
        # Get pod name from hostname
        info['pod_name'] = os.environ.get('HOSTNAME', 'unknown')
        
        # Get namespace
        try:
            with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
                info['namespace'] = f.read().strip()
        except (OSError, IOError):
            info['namespace'] = 'unknown'
        
        # Get API server host
        info['api_host'] = os.environ.get('KUBERNETES_SERVICE_HOST', 'unknown')
        
        # Get API port
        info['api_port'] = os.environ.get('KUBERNETES_SERVICE_PORT', 'unknown')
        
        # Container runtime detection within K8s
        if is_docker():
            info['container_runtime'] = 'docker'
        elif is_podman():
            info['container_runtime'] = 'podman'
        else:
            info['container_runtime'] = 'other'
    
    except Exception as e:
        info['error'] = str(e)
    
    return info


def is_podman() -> bool:
    """
    Check if running in Podman container.
    
    Detects:
    - Podman socket (/run/podman.sock)
    - Podman cgroup markers
    - Podman environment variables
    
    Returns:
        True if running in Podman
    """
    # Check Podman socket
    if os.path.exists('/run/podman.sock'):
        return True
    
    # Podman-specific cgroup markers
    try:
        with open('/proc/self/cgroup', 'r') as f:
            cgroup = f.read()
            if 'podman' in cgroup or '/libpod/' in cgroup:
                return True
    except (OSError, IOError):
        pass
    
    # Podman environment variables
    if os.environ.get('PODMAN_CONTAINER'):
        return True
    
    return False


def is_podman_rootless() -> bool:
    """
    Check if running in rootless Podman.
    
    Returns:
        True if running in rootless Podman
    """
    if is_podman() and os.geteuid() != 0:
        return True
    
    return False


def is_ci_environment() -> bool:
    """
    Check if running in CI/CD environment.
    
    Detects: GitHub Actions, GitLab CI, Jenkins, Travis, CircleCI, etc.
    
    Returns:
        True if running in CI
    """
    # GitHub Actions
    if os.environ.get('GITHUB_ACTIONS'):
        return True
    
    # GitLab CI
    if os.environ.get('GITLAB_CI'):
        return True
    
    # Jenkins
    if os.environ.get('JENKINS_HOME') or os.environ.get('BUILD_ID'):
        return True
    
    # Travis CI
    if os.environ.get('TRAVIS'):
        return True
    
    # CircleCI
    if os.environ.get('CIRCLECI'):
        return True
    
    # Generic CI detection
    if os.environ.get('CI') or os.environ.get('CONTINUOUS_INTEGRATION'):
        return True
    
    return False


def detect_ci_type() -> Optional[ContainerType]:
    """Detect specific CI/CD platform."""
    if os.environ.get('GITHUB_ACTIONS'):
        return ContainerType.CI_GITHUB
    if os.environ.get('GITLAB_CI'):
        return ContainerType.CI_GITLAB
    if os.environ.get('JENKINS_HOME'):
        return ContainerType.CI_JENKINS
    if is_ci_environment():
        return ContainerType.CI_OTHER
    return None


def detect_container_type() -> ContainerType:
    """
    Detect what type of container/environment we're running in.
    
    Priority (checked in order):
    1. Kubernetes pod
    2. Docker (standard or rootless)
    3. Podman (standard or rootless)
    4. CI/CD environment
    5. Native OS
    
    Returns:
        ContainerType enum value
    """
    # Check Kubernetes first (might be running as K8s pod)
    if is_kubernetes():
        # Could be K8s with Docker/Podman runtime
        if is_docker():
            return ContainerType.KUBERNETES_DOCKER
        elif is_podman():
            return ContainerType.KUBERNETES_PODMAN
        else:
            return ContainerType.KUBERNETES
    
    # Check Docker
    if is_docker():
        if is_docker_rootless():
            return ContainerType.DOCKER_ROOTLESS
        else:
            return ContainerType.DOCKER
    
    # Check Podman
    if is_podman():
        if is_podman_rootless():
            return ContainerType.PODMAN_ROOTLESS
        else:
            return ContainerType.PODMAN
    
    # Check CI/CD
    ci_type = detect_ci_type()
    if ci_type:
        return ci_type
    
    # Default: native
    return ContainerType.NATIVE


def detect_environment() -> EnvironmentInfo:
    """
    Detect full environment information.
    
    Returns:
        EnvironmentInfo with container type, TTY status, etc.
    """
    container_type = detect_container_type()
    is_tty = sys.stdout.isatty()
    is_ci = is_ci_environment()
    is_root = os.geteuid() == 0 if sys.platform != 'win32' else False
    
    # Determine color capability
    color_capable = has_color_support()
    
    # Determine unicode support
    has_unicode = has_unicode_support()
    
    # Gather additional details
    details = {}
    
    if container_type in (ContainerType.KUBERNETES, 
                         ContainerType.KUBERNETES_DOCKER,
                         ContainerType.KUBERNETES_PODMAN):
        details.update(get_kubernetes_info())
    
    details['container_type'] = container_type.value
    details['is_tty'] = str(is_tty)
    details['term'] = os.environ.get('TERM', 'none')
    
    return EnvironmentInfo(
        container_type=container_type,
        is_tty=is_tty,
        is_ci=is_ci,
        color_capable=color_capable,
        has_unicode_support=has_unicode,
        run_as_root=is_root,
        details=details
    )


def has_color_support() -> bool:
    """
    Check if terminal supports colors.
    
    Checks:
    - NO_COLOR environment variable
    - TERM environment variable
    - TTY status
    - CI environment colors
    
    Returns:
        True if colors should be used
    """
    # NO_COLOR standard
    if os.environ.get('NO_COLOR'):
        return False
    
    # TERM variable
    term = os.environ.get('TERM', '')
    if term == 'dumb' or term == '':
        return False
    
    # CI environments usually support colors
    if is_ci_environment():
        return not os.environ.get('NO_COLOR')
    
    # Default: check if TTY
    return sys.stdout.isatty()


def has_unicode_support() -> bool:
    """
    Check if terminal supports Unicode.
    
    Checks:
    - LANG/LC_ALL environment variables
    - TERM variable
    - Platform detection
    
    Returns:
        True if Unicode is supported
    """
    # Check explicit dumb terminal first
    term = os.environ.get('TERM', '')
    if term == 'dumb':
        return False
    
    # Check locale
    lang = os.environ.get('LANG', '')
    if 'utf' in lang.lower() or 'utf8' in lang.lower():
        return True
    
    lc_all = os.environ.get('LC_ALL', '')
    if 'utf' in lc_all.lower():
        return True
    
    # TERM usually indicates unicode support
    if term and term != 'dumb':
        return True
    
    # Windows usually has unicode in console
    if sys.platform == 'win32':
        return True
    
    # Default for modern systems
    return True


def get_preferred_color_mode() -> str:
    """
    Get recommended color/symbol mode based on environment.
    
    Returns:
        Theme name or symbol mode
    
    Examples:
        - 'dark' for containers (high contrast)
        - 'colorblind' if accessibility requested
        - 'default' for native TTY
        - 'no-color' for CI without colors
    """
    env = detect_environment()
    
    # Respect explicit settings
    if os.environ.get('NO_COLOR'):
        return 'none'
    
    if os.environ.get('AKIOS_THEME'):
        return os.environ.get('AKIOS_THEME')
    
    # CI environments prefer dark (high contrast)
    if env.is_ci:
        return 'dark'
    
    # Containers prefer dark (high contrast)
    if env.container_type != ContainerType.NATIVE:
        return 'dark'
    
    # Default for native
    return 'default'


def get_preferred_symbol_mode() -> Optional[str]:
    """
    Get recommended symbol mode based on environment.
    
    Returns:
        Symbol mode name or None for default
    
    Examples:
        - 'unicode' for containers (compatible everywhere)
        - 'ascii' for CI (maximum compatibility)
        - None for native (use platform default)
    """
    if os.environ.get('AKIOS_SYMBOL_MODE'):
        return os.environ.get('AKIOS_SYMBOL_MODE')
    
    if os.environ.get('NO_SYMBOLS'):
        return None
    
    env = detect_environment()
    
    # ASCII mode for CI (maximum compatibility)
    if env.is_ci:
        return 'ascii'
    
    # Unicode for containers (good compatibility, shape-based)
    if env.container_type != ContainerType.NATIVE:
        return 'unicode'
    
    # Default: no forced mode
    return None


def print_environment_info() -> None:
    """Print environment detection information (for debugging)."""
    env = detect_environment()
    
    print(f"\n{'='*60}")
    print(f"AKIOS Environment Detection")
    print(f"{'='*60}")
    print(f"Container Type:    {env.container_type.value}")
    print(f"Is TTY:            {env.is_tty}")
    print(f"Is CI:             {env.is_ci}")
    print(f"Color Support:     {env.color_capable}")
    print(f"Unicode Support:   {env.has_unicode_support}")
    print(f"Run as Root:       {env.run_as_root}")
    
    print(f"\nEnvironment Details:")
    for key, value in env.details.items():
        print(f"  {key}: {value}")
    
    print(f"\nRecommended Settings:")
    print(f"  Theme:        {get_preferred_color_mode()}")
    print(f"  Symbol Mode:  {get_preferred_symbol_mode() or 'default'}")
    print(f"{'='*60}\n")


# Export public API
__all__ = [
    "ContainerType",
    "EnvironmentInfo",
    "is_docker",
    "is_docker_rootless",
    "is_kubernetes",
    "get_kubernetes_info",
    "is_podman",
    "is_podman_rootless",
    "is_ci_environment",
    "detect_ci_type",
    "detect_container_type",
    "detect_environment",
    "has_color_support",
    "has_unicode_support",
    "get_preferred_color_mode",
    "get_preferred_symbol_mode",
    "print_environment_info",
]
