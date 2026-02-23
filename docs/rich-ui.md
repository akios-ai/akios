# Rich Terminal UI Guide
**Document Version:** 1.0.15  
**Date:** 2026-02-23  

## Overview

AKIOS v1.0.15 includes a **Semantic Rich-powered terminal UI** for professional, structured output. The system enforces a strict semantic color scheme to ensure consistency, accessibility, and security-focused aesthetics across all environments.

## Features

### 🎨 Semantic Output

All output uses professional color schemes that automatically adapt to terminal capabilities. Colors are applied based on *meaning* (Success, Warning, Error, Security), not aesthetic preference.

```python
from akios.core.ui import print_success, print_warning, print_error, print_info

print_success("Operation completed successfully")
print_warning("This action requires attention")
print_error("An error occurred during processing")
print_info("FYI: Additional information")
```

### 📊 Professional Tables

Display structured data with automatic column formatting:

```python
from akios.core.ui import print_table

data = [
    {"name": "analysis.txt", "size": "2.3 KB", "status": "clean"},
    {"name": "report.pdf", "size": "1.5 MB", "status": "suspicious"},
]

print_table(
    data, 
    title="Scan Results",
    columns=["name", "size", "status"]
)
```

### 📦 Styled Panels

Create structured sections with titled panels. The styling is handled automatically by the system theme.

```python
from akios.core.ui import print_panel

print_panel(
    "Security Status",
    "All systems operational. No threats detected."
)
```

### 🔍 PII Detection Visualization

Professional display of PII scan results with severity indicators:

```python
from akios.core.ui import display_pii_report

# Display comprehensive report
display_pii_report(scan_results, detailed=True)
```

## CLI Integration

All major CLI commands use the semantic UI:

### Status Command

```bash
# Display overall status
akios status

# Show security dashboard
akios status --security

# Show budget dashboard
akios status --budget
```

### Files Command

```bash
# List input/output files in professional table format
akios files
```

## Terminal Compatibility

The system automatically detects terminal capabilities:

- **Full color (16.7M colors)**: Modern terminals (iTerm2, VS Code, Windows Terminal)
- **256 colors**: Older Unix terminals
- **Plain text**: Non-color terminals (automatic fallback)

### Environment Variables

You can control color output using standard environment variables:

- `FORCE_COLOR=1`: Force color output (useful for Docker/CI)
- `NO_COLOR=1`: Disable color output
- `TERM`: Used for capability detection

## Best Practices for Developers

When extending AKIOS or writing scripts:

### ✅ Do

- Use **Semantic Functions**: `print_success()`, `print_warning()`, etc.
- Use **Structured Data**: `print_table()` for lists of objects.
- Use **Panels**: `print_panel()` to group related information.
- Use **Theme Tokens**: If you must use `rich` directly, use `get_theme_color("header")` etc.

### ❌ Don't

- **Hardcode Colors**: Never use raw colors like `[green]` or `#00ff00`.
- **Mix Styles**: Do not mix plain `print()` with Rich functions.
- **Bypass Theme**: Always use the centralized theme system.

## Related Documentation

- [CLI_REFERENCE.md](./cli-reference.md) - Full CLI command reference
- [SECURITY.md](./security.md) - Security features and constraints
