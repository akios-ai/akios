# AKIOS Environment Detection System
**Document Version:** 1.1.1  
**Date:** 2026-02-24  

**Automatic detection of your runtime environment and intelligent defaults.**

AKIOS automatically detects what environment you're running in and configures colors, symbols, and Unicode support accordingly. This means better output formatting across your local machine, Docker containers, Kubernetes pods, and CI/CD pipelines—without manual configuration.

## How Detection Works

When you run any AKIOS command, the detection system checks your environment in this order:

### 1. Container Type Detection

AKIOS detects whether you're running:
- **Native OS** - Local machine (macOS, Linux, Windows)
- **Docker** - Standard Docker container or rootless Docker
- **Kubernetes** - Kubernetes pod (with Docker/Podman/other runtime)
- **Podman** - Container runtime supporting OCI standards
- **CI/CD** - GitHub Actions, GitLab CI, Jenkins, CircleCI, etc.

**Detection Methods:**
```
Kubernetes (priority)
├─ /var/run/secrets/kubernetes.io/serviceaccount/token
├─ KUBERNETES_SERVICE_HOST environment variable
├─ KUBERNETES_SERVICE_PORT environment variable
└─ /var/run/secrets/kubernetes.io/serviceaccount/namespace

Docker
├─ /.dockerenv file presence
├─ /run/docker.sock socket
├─ DOCKER_HOST environment variable
└─ /proc/self/cgroup contains "docker"

Podman
├─ /run/podman.sock socket
├─ PODMAN_HOST environment variable
└─ /proc/self/cgroup contains "podman"

CI/CD
├─ CI environment variable
├─ GITHUB_ACTIONS environment variable
├─ GITLAB_CI environment variable
├─ JENKINS_URL environment variable
└─ Other CI provider detection
```

### 2. TTY Detection

AKIOS detects if connected to an interactive terminal:
```python
if sys.stdout.isatty():
    # Interactive terminal - enable colors
    color_capable = True
else:
    # Pipe, file redirect, or background - disable colors
    color_capable = False
```

### 3. Unicode Support Detection

AKIOS detects terminal and locale capabilities:
```
Unicode Support
├─ LANG environment variable (check for UTF-8/utf8)
├─ LC_ALL environment variable (prioritized over LANG)
├─ TERM variable (reject 'dumb' terminal)
├─ Windows console (native Unicode support)
└─ Default to True on modern systems
```

### 4. Color Support Detection

AKIOS respects multiple standards for color preferences:
```
Color Support
├─ NO_COLOR environment variable (if set → disable colors)
├─ CLICOLOR_FORCE environment variable (if set → force colors)
├─ FORCE_COLOR environment variable (if set → enable colors)
├─ isatty() check (interactive terminal → colors ok)
└─ Container detection (Docker → colors ok, CI → caution)
```

## Configuration Output

You can inspect what AKIOS detected programmatically:

```python
from akios.config.detection import detect_environment

env = detect_environment()
print(f"Container Type: {env.container_type.value}")
print(f"Is TTY: {env.is_tty}")
print(f"Is CI: {env.is_ci}")
print(f"Color Capable: {env.color_capable}")
print(f"Unicode Support: {env.has_unicode_support}")
print(f"Run as Root: {env.run_as_root}")
print(f"Details: {env.details}")
```

## Detection Results

The detection system populates `EnvironmentInfo` with:

```python
class EnvironmentInfo(NamedTuple):
    container_type: ContainerType  # What environment we're in
    is_tty: bool                   # Is connected to terminal?
    is_ci: bool                    # Running in CI/CD?
    color_capable: bool            # Can display colors?
    has_unicode_support: bool      # Can display Unicode?
    run_as_root: bool              # Running as root user?
    details: Dict[str, str]        # Additional details (namespace, pod name, etc.)
```

## Container Type Values

```python
class ContainerType(Enum):
    NATIVE = "native"                # Local machine
    DOCKER = "docker"                # Standard Docker
    DOCKER_ROOTLESS = "docker_rootless"  # Rootless Docker
    KUBERNETES = "kubernetes"        # K8s native runtime
    KUBERNETES_DOCKER = "kubernetes_docker"  # K8s with Docker
    KUBERNETES_PODMAN = "kubernetes_podman"  # K8s with Podman
    PODMAN = "podman"                # Standard Podman
    PODMAN_ROOTLESS = "podman_rootless"     # Rootless Podman
    CI_GITHUB = "ci_github"          # GitHub Actions
    CI_GITLAB = "ci_gitlab"          # GitLab CI
    CI_JENKINS = "ci_jenkins"        # Jenkins
    CI_OTHER = "ci_other"            # Other CI/CD
```

## Environment-Specific Defaults

### Native OS (macOS, Linux, Windows)
```
Color: Enabled (if TTY and not NO_COLOR)
Symbols: Unicode by default
Unicode: Enabled (if LANG/LC_ALL contains UTF-8)
Result: Full rich output with colors and Unicode symbols
```

### Docker Container
```
Color: Enabled (modern Docker supports colors)
Symbols: ASCII for compatibility (can override)
Unicode: Enabled if locale supports it
Result: Colorized output with ASCII fallback
```

### Kubernetes Pod
```
Color: Enabled (inherited from Docker/Podman runtime)
Symbols: ASCII by default (safer for cluster environments)
Unicode: Disabled by default (pods may not have proper locale)
Result: Colors with ASCII symbols for cluster safety
```

### CI/CD Pipeline
```
Color: Enabled (most CI systems support ANSI colors)
Symbols: ASCII for log compatibility
Unicode: Disabled (CI logs may not support Unicode properly)
Result: Colors in CI logs with ASCII symbols
```

### Dumb Terminal (e.g., `TERM=dumb`)
```
Color: Disabled (terminal can't display colors)
Symbols: ASCII only, basic symbols
Unicode: Disabled
Result: Plain text fallback mode
```

## Programmatic Access

### Python API

```python
from akios.config.detection import (
    detect_environment,
    detect_container_type,
    has_unicode_support,
    get_preferred_color_mode,
    is_kubernetes,
    is_docker,
    is_ci_environment
)

# Get complete environment info
env = detect_environment()
print(f"Running in: {env.container_type.value}")
print(f"TTY mode: {env.is_tty}")
print(f"Is CI: {env.is_ci}")
print(f"Colors: {env.color_capable}")
print(f"Unicode: {env.has_unicode_support}")
print(f"Root: {env.run_as_root}")

# Check specific environment
if is_kubernetes():
    print("Running in Kubernetes")
    
if is_docker():
    print("Running in Docker")
    
if is_ci_environment():  
    print("Running in CI/CD")

# Get recommended settings
color_mode = get_preferred_color_mode()
unicode_ok = has_unicode_support()
```

### CLI Access

```bash
# Override detected defaults with environment variables
export NO_COLOR=1          # Force disable colors
export CLICOLOR_FORCE=1    # Force enable colors (overrides NO_COLOR)
export FORCE_COLOR=1       # Alternative: force enable colors
```

## Configuration Overrides

You can override detection results with environment variables:

```bash
# Force specific color mode
export AKIOS_COLOR_MODE=dark

# Force specific symbol mode
export AKIOS_SYMBOL_MODE=unicode

# Disable all colors
export NO_COLOR=1

# Force colors even in pipes
export CLICOLOR_FORCE=1

# Force specific theme
export AKIOS_THEME=nord
```

Or in `config.yaml`:

```yaml
# config.yaml
ui:
  color_mode: light           # Override detection
  symbol_mode: ascii          # Force ASCII symbols
  theme: solarized-dark       # Force theme
  unicode_enabled: false      # Disable Unicode
```

## Common Scenarios

### Docker Development

```bash
# AKIOS auto-detects Docker
docker run -it akios/akios:latest
# → Auto-enables colors
# → Uses ASCII symbols for compatibility
# → Enabled Unicode if supported
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: akios-job
spec:
  containers:
  - name: akios
    image: akios:latest
    env:
    - name: TERM
      value: "xterm-256color"  # Ensure color support
```

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Run AKIOS
  run: |
    pipx install akios
    akios run workflow.yml
  # AKIOS auto-detects GitHub Actions environment
  # Colors enabled, ASCII symbols used
```

### Local Development (No Changes Needed)

```bash
# Terminal with Unicode support
export LANG=en_US.UTF-8
akios run workflow.yml
# → Full colors and Unicode symbols

# Dumb terminal or minimal shell
akios run workflow.yml
# → Colors disabled, ASCII fallback used
```

## Troubleshooting

### Colors not working?

1. Check if TTY connected: `akios setup --show-environment`
2. Check NO_COLOR: `echo $NO_COLOR`
3. Override with CLICOLOR_FORCE: `CLICOLOR_FORCE=1 akios run workflow.yml`
4. Check TERM: `echo $TERM`

### Unicode characters showing wrong?

1. Check locale: `locale`
2. Set UTF-8: `export LANG=en_US.UTF-8`
3. Override: `export AKIOS_SYMBOL_MODE=ascii`

### Wrong container type detected?

1. See detection results: `akios setup --show-environment`
2. Manual override in config.yaml:
   ```yaml
   ui:
     container_type: docker  # Force specific type
   ```

## Performance Impact

The detection system runs once at startup:
- **Detection time**: < 5ms (negligible)
- **Memory overhead**: < 1MB
- **No recurring checks** - Detection runs once at initialization

## Security Considerations

Detection is **read-only**:
- No environment modification
- No file creation outside allowed paths
- Respects security sandbox restrictions
- All detection results are logged in audit trail

## Architecture

```
CLI Command
    ↓
detect_environment()
    ├─ is_kubernetes() → check K8s files/env vars
    ├─ is_docker() → check Docker files/env vars
    ├─ is_podman() → check Podman files/env vars
    ├─ detect_ci_type() → check CI env vars
    ├─ has_unicode_support() → check LANG/TERM
    ├─ can_display_colors() → check TTY + NO_COLOR
    └─ get_preferred_mode() → synthesize defaults
    ↓
EnvironmentInfo (immutable)
    ↓
Theme/Color/Symbol System
    ↓
Output Rendering
```

## Related Documentation

- [Accessibility Guide](accessibility-guide.md) - Symbol modes and colorblind support
- [Theme Customization](theme-customization.md) - Customize colors and themes
- [Configuration Reference](configuration.md) - All config options
- [Examples](examples.md) - Real-world usage examples
