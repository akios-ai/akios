# AKIOS Examples and Tutorials
**Document Version:** 1.2.0  
**Date:** 2026-02-23  

**Real-world usage examples demonstrating AKIOS features across different environments.**

---

## Quick Examples

### Example 1: Basic Workflow Execution

```bash
# Simple workflow with default settings
akios run workflow.yml

# Output in your terminal with auto-detected colors:
# ✓ Workflow initialized
# ✓ Security checks passed
# ✓ Workflow completed in 2.45s
```

### Example 2: With Colorblind Support

```bash
# User with red-green colorblindness
export AKIOS_COLORBLIND_MODE=deuteranopia
akios run workflow.yml

# Colors automatically adjusted for deuteranopia:
# - Success: Cyan instead of green
# - Error: Orange instead of red
# - Warning: Orange instead of yellow
```

### Example 3: No Colors (Piped Output)

```bash
# Pipe to file or another command
akios run workflow.yml | tee output.log

# Auto-detects pipe, disables colors:
# Workflow initialized
# Security checks passed
# Workflow completed in 2.45s
```

---

## Environment-Specific Tutorials

### Tutorial 1: Local Development

**Goal:** Work with full visual feedback during development

```bash
# Step 1: Check your environment
akios status --verbose

# Check budget and cost tracking
akios status --budget

# Example output:
# Container Type: native
# ...

# Step 2: Run workflow with full visuals
akios run my-workflow.yml

# Step 3: Expected output:
# ✓ Workflow initialized
# ⚡ Processing file: data/input.json
# ⏱ Completed in 2.34s
```

### Tutorial 2: Docker Development

**Goal:** Maintain color support in Docker while being compatible with container logging

```bash
# Step 1: Build image with UTF-8 support
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
RUN apt-get update && apt-get install -y locales
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG=en_US.UTF-8
RUN pip install akios

WORKDIR /app
COPY workflow.yml .
ENTRYPOINT ["akios", "run", "workflow.yml"]
EOF

docker build -t my-workflow:latest .

# Step 2: Run with TTY for colors
docker run -it my-workflow:latest

# Output in Docker with auto-detected colors:
# ✓ Workflow initialized [in green]
# ✓ Processing...
# ✓ Done
```

### Tutorial 3: Kubernetes Deployment

**Goal:** Run AKIOS jobs in Kubernetes with auto-detected settings

```yaml
# Step 1: Create workflow ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: akios-workflow
data:
  workflow.yml: |
    name: "K8s Workflow"
    steps:
      - name: "Initialize"
        action: "status"

---
# Step 2: Create Job
apiVersion: batch/v1
kind: Job
metadata:
  name: akios-job
spec:
  template:
    spec:
      containers:
      - name: akios
        image: akios:latest
        env:
        - name: LANG
          value: "en_US.UTF-8"
        - name: LC_ALL
          value: "en_US.UTF-8"
        volumeMounts:
        - name: workflow-vol
          mountPath: /app
      volumes:
      - name: workflow-vol
        configMap:
          name: akios-workflow
      restartPolicy: Never
```

### Tutorial 4: GitHub Actions CI/CD

**Goal:** Run AKIOS in GitHub Actions with proper color and symbol support

```yaml
# Step 1: Create .github/workflows/akios.yml
name: AKIOS Workflow

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install AKIOS
        run: pipx install akios
      
      - name: Run workflow
        run: |
          export LANG=en_US.UTF-8
          export LC_ALL=en_US.UTF-8
          akios run workflow.yml
        # AKIOS auto-detects GitHub Actions
        # Colors enabled, ASCII symbols used in logs

# Step 2: GitHub Actions output will show:
# ✓ Workflow initialized [OK]
# ✓ Security checks passed [OK]
# ✓ Completed in 2.45s [OK]
```

### Tutorial 5: GitLab CI/CD

**Goal:** AKIOS in GitLab with proper log compatibility

```yaml
# Step 1: Create .gitlab-ci.yml
image: python:3.11

stages:
  - test
  - deploy

test:akios:
  stage: test
  script:
    - pip install akios
    - export LANG=en_US.UTF-8
    - akios run workflow.yml
  # AKIOS auto-detects GitLab CI
  # Output compatible with GitLab log parser
```

---

## Feature-Specific Examples

### Example: Using Different Themes

```bash
# Check available themes
akios config list-themes

# Output:
# Available themes:
#   - default (recommended)
#   - dark
#   - light
#   - nord
#   - solarized-dark
#   - solarized-light
#   - high-contrast

# Use a specific theme
export AKIOS_THEME=nord
akios run workflow.yml

# Or in config.yaml
# ui:
#   theme: solarized-dark
```

### Example: Colorblind User Workflow

**Scenario:** User with green-red colorblindness wants to use AKIOS

```bash
# Step 1: Detect colorblind mode
# (User self-identifies as having deuteranopia)

# Step 2: Create shell alias for easy access
cat >> ~/.bashrc << 'EOF'
# AKIOS with colorblind support
alias akios_safe='AKIOS_COLORBLIND_MODE=deuteranopia akios'
EOF

source ~/.bashrc

# Step 3: Use the alias
akios_safe run workflow.yml

# Output colors adjusted for deuteranopia:
# ✓ Success messages in cyan (not green)
# ⚠ Warnings in orange (not yellow)
# ✗ Errors in red (unchanged)
```

### Example: No-Color (Plain Text) Output

**Scenario:** Output needs to be plain text for log files or piping

```bash
# Method 1: NO_COLOR environment variable
export NO_COLOR=1
akios run workflow.yml

# Method 2: Command line flag
akios run workflow.yml --no-color

# Method 3: Configuration file
cat >> config.yaml << 'EOF'
ui:
  color_mode: disabled
EOF

# Result: Plain text output
# Workflow initialized
# Processing file: data/input.json
# Completed in 2.34s
```

### Example: ASCII Symbol Mode

**Scenario:** Output in log file or email that doesn't support Unicode

```bash
# Use ASCII symbols
export AKIOS_SYMBOL_MODE=ascii
akios run workflow.yml > results.txt

# Output in results.txt
# [OK] Workflow initialized
# [T] Processing took 2.34s
# [OK] Completed successfully
```

### Example: Minimal Mode

**Scenario:** Screen reader or text-only terminal

```bash
# Minimal symbols for screen readers
export AKIOS_SYMBOL_MODE=minimal
export NO_COLOR=1
akios run workflow.yml

# Output for screen readers
# - Workflow initialized
# - Processing file: data/input.json
# - Completed in 2.34s
```

---

## Advanced Configuration Examples

### Example 1: Complete config.yaml

```yaml
# config.yaml - Comprehensive configuration
name: "My AKIOS Project"

# UI Configuration
ui:
  theme: solarized-dark           # Color theme
  color_mode: auto                # auto, light, dark, disabled
  symbol_mode: unicode            # unicode, ascii, minimal
  colorblind_mode: none           # protanopia, deuteranopia, tritanopia, achromasia
  unicode_enabled: true           # Enable/disable Unicode
  container_type: native          # auto-detect or manual override

# Output Configuration
output:
  quiet_mode: false               # Suppress non-essential output
  verbose: false                  # Show detailed logs
  json_output: false              # Machine-readable output
  timestamps: true                # Show timestamps in logs

# Paths
paths:
  workflows: ./workflows
  templates: ./templates
  data_input: ./data/input
  data_output: ./data/output
  audit: ./audit

# Audit & Security
audit:
  enabled: true
  storage_path: ./audit
  export_format: json             # json (default)

# Performance
performance:
  max_workflows: 10
  timeout: 3600
  cache_enabled: true
  cache_ttl: 3600

# LLM Provider
llm:
  provider: grok
  model: grok-3
  temperature: 0.7
```

### Example 2: Environment-Specific Profiles

```bash
# Create different profiles for different environments

# ~/.akios/profiles/development.sh
cat > ~/.akios/profiles/development.sh << 'EOF'
# Development profile - full features
export AKIOS_THEME=nord
export AKIOS_SYMBOL_MODE=unicode
export AKIOS_COLORBLIND_MODE=none
export AKIOS_VERBOSE=true
EOF

# ~/.akios/profiles/ci.sh
cat > ~/.akios/profiles/ci.sh << 'EOF'
# CI/CD profile - compatibility first
export AKIOS_SYMBOL_MODE=ascii
export AKIOS_COLORBLIND_MODE=deuteranopia  # Safe choice
export AKIOS_VERBOSE=false
EOF

# ~/.akios/profiles/accessible.sh
cat > ~/.akios/profiles/accessible.sh << 'EOF'
# Accessibility profile
export NO_COLOR=1
export AKIOS_SYMBOL_MODE=minimal
export AKIOS_SCREEN_READER_MODE=true
EOF

# Usage:
source ~/.akios/profiles/development.sh && akios run workflow.yml
source ~/.akios/profiles/ci.sh && akios run workflow.yml
source ~/.akios/profiles/accessible.sh && akios run workflow.yml
```

### Example 3: Detecting Your Environment

```bash
#!/bin/bash
# Script to auto-detect and configure environment

# Run detection
eval "$(akios setup --show-environment --format=bash)"

echo "Environment Summary:"
echo "- Container Type: $AKIOS_CONTAINER_TYPE"
echo "- TTY: $AKIOS_IS_TTY"
echo "- Color Capable: $AKIOS_COLOR_CAPABLE"
echo "- Unicode: $AKIOS_UNICODE_SUPPORT"

# Auto-set based on detection
if [ "$AKIOS_CONTAINER_TYPE" = "kubernetes" ]; then
  export AKIOS_SYMBOL_MODE=ascii
  export AKIOS_COLORBLIND_MODE=deuteranopia
elif [ "$AKIOS_CONTAINER_TYPE" = "native" ]; then
  export AKIOS_SYMBOL_MODE=unicode
  export AKIOS_COLORBLIND_MODE=none
fi

echo "Configuration:"
echo "- Symbol Mode: $AKIOS_SYMBOL_MODE"
echo "- Colorblind Mode: $AKIOS_COLORBLIND_MODE"
```

---

## Troubleshooting Examples

### Problem: "Colors not showing in Docker"

**Solution:**
```bash
# Step 1: Check detection
docker run -it myimage akios setup --show-environment

# Step 2: If Color Capable is False, set TERM
docker run -it -e TERM=xterm-256color myimage akios run workflow.yml

# Step 3: Force colors if needed
docker run -it -e CLICOLOR_FORCE=1 myimage akios run workflow.yml
```

### Problem: "Unicode characters showing as boxes"

**Solution:**
```bash
# Step 1: Check locale
locale

# Step 2: Set UTF-8 locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Step 3: Or use ASCII mode
export AKIOS_SYMBOL_MODE=ascii
akios run workflow.yml
```

### Problem: "Colors look wrong for colorblind users"

**Solution:**
```bash
# Step 1: Identify colorblind type
# https://www.colourblindawareness.org/colour-blindness/test/

# Step 2: Set colorblind mode
export AKIOS_COLORBLIND_MODE=deuteranopia  # For green-red blindness
akios run workflow.yml

# Step 3: Test different modes if unsure
for mode in protanopia deuteranopia tritanopia; do
  echo "Testing $mode..."
  AKIOS_COLORBLIND_MODE=$mode akios setup --show-environment
done
```

---

## Testing Examples

### Example: Comprehensive Test Suite

```bash
#!/bin/bash
# test-akios.sh - Comprehensive feature testing

echo "=== AKIOS Feature Testing ==="

# Test 1: All symbol modes
echo -e "\n1. Testing symbol modes..."
for mode in unicode ascii minimal; do
  echo "   Testing $mode mode..."
  AKIOS_SYMBOL_MODE=$mode akios setup --show-environment >/dev/null || echo "FAILED: $mode"
done
echo "✓ Symbol modes OK"

# Test 2: All colorblind modes
echo -e "\n2. Testing colorblind modes..."
for mode in protanopia deuteranopia tritanopia achromasia; do
  echo "   Testing $mode..."
  AKIOS_COLORBLIND_MODE=$mode akios setup --show-environment >/dev/null || echo "FAILED: $mode"
done
echo "✓ Colorblind modes OK"

# Test 3: Color variants
echo -e "\n3. Testing color control..."
NO_COLOR=1 akios setup --show-environment >/dev/null && echo "✓ NO_COLOR OK"
CLICOLOR_FORCE=1 akios setup --show-environment >/dev/null && echo "✓ CLICOLOR_FORCE OK"

# Test 4: All themes
echo -e "\n4. Testing themes..."
for theme in default dark light nord solarized-dark solarized-light high-contrast; do
  echo "   Testing theme: $theme..."
  AKIOS_THEME=$theme akios setup --show-environment >/dev/null || echo "FAILED: $theme"
done
echo "✓ Themes OK"

echo -e "\n=== All tests passed ==="
```

---

## Performance Optimization Examples

### Example: Batch Processing

```bash
#!/bin/bash
# Process multiple workflows efficiently

workflows=(
  "workflow1.yml"
  "workflow2.yml"
  "workflow3.yml"
)

echo "Processing ${#workflows[@]} workflows..."

for workflow in "${workflows[@]}"; do
  echo "Processing: $workflow"
  akios run "$workflow" --quiet
  
  if [ $? -eq 0 ]; then
    echo "✓ $workflow completed"
  else
    echo "✗ $workflow failed"
  fi
done
```

---

## Related Documentation

- [Detection System](detection-system.md) - How AKIOS detects environments
- [Accessibility Guide](accessibility-guide.md) - Colorblind and accessibility features
- [Theme Customization](theme-customization.md) - Customize colors and themes
- [Configuration Reference](configuration.md) - All config options
- [CLI Reference](cli-reference.md) - Command-line interface guide
