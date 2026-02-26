# AKIOS Accessibility Guide
**Document Version:** 1.2.1  
**Date:** 2026-02-23  

**Making AKIOS work for everyone – symbol modes, colorblind support, and Unicode.**

AKIOS is designed from the ground up to be accessible to all users, regardless of ability or terminal capabilities. This guide covers symbol modes, colorblind support, Unicode accessibility, and terminal compatibility.

## Quick Start

### Colorblind Support
```bash
# For red-green colorblindness
export AKIOS_COLORBLIND_MODE=deuteranopia

# For blue-yellow colorblindness
export AKIOS_COLORBLIND_MODE=tritanopia

# For complete colorblindness (monochrome)
export AKIOS_COLORBLIND_MODE=achromasia
```

### Symbol Modes
```bash
# Use Unicode symbols (✓, ✗, ⚡, etc.)
export AKIOS_SYMBOL_MODE=unicode

# Use ASCII-safe symbols (✓ → OK, ✗ → XX, etc.)
export AKIOS_SYMBOL_MODE=ascii

# Use minimal symbols
export AKIOS_SYMBOL_MODE=minimal
```

### Disable All Visual Enhancements
```bash
# Plain text, no colors, no special symbols
export NO_COLOR=1
export AKIOS_SYMBOL_MODE=minimal
```

---

## Symbol Modes

AKIOS provides three symbol modes to accommodate different terminals and preferences.

### Unicode Symbols (Default)
**Best for:** Modern terminals, full visual appeal

```
Status Legend:
  ✓  Complete/Success
  ✗  Failed/Error
  ⚠  Warning
  ℹ  Information
  ⏱  Timing/Performance
  ⚡ Power/Energy
  🔒 Security/Lock
  📦 Package
  ✎  Workflow/Task
  ↳  Nested/Indented
```

**Configuration:**
```bash
export AKIOS_SYMBOL_MODE=unicode
```

**In config.yaml:**
```yaml
ui:
  symbol_mode: unicode
```

### ASCII Symbols (Recommended for CI/Log Compatibility)
**Best for:** CI/CD logs, old terminals, compatibility

```
Status Legend:
  [OK]        Complete/Success
  [XX]        Failed/Error
  [!]         Warning
  [i]         Information
  [T]         Timing/Performance
  [*]         Power/Energy
  [L]         Security/Lock
  [@]         Package
  [~]         Workflow/Task
  [>]         Nested/Indented
```

**Configuration:**
```bash
export AKIOS_SYMBOL_MODE=ascii
```

**Automatic Detection:**
- Kubernetes environments default to ASCII
- CI/CD pipelines default to ASCII
- Dumb terminals (TERM=dumb) force ASCII
- macOS/Linux with UTF-8 locale default to Unicode
- Windows Console uses ASCII with fallbacks

### Minimal Symbols
**Best for:** Screen readers, text-only viewing, maximum compatibility

```
Status Legend:
  -  Complete/Success
  !  Failed/Error
  ?  Warning
  i  Information
  t  Timing/Performance
  *  Power/Energy
  #  Security/Lock
  +  Package
  =  Workflow/Task
  >  Nested/Indented
```

**Configuration:**
```bash
export AKIOS_SYMBOL_MODE=minimal
```

---

## Colorblind Support

AKIOS includes built-in color palettes optimized for different types of color vision deficiency.

### Color Vision Deficiency Types

#### Protanopia (Red-Blind)
**Affects:** ~1% of males  
**Confusion:** Red ↔ Darkish colors  
**Solution:** AKIOS palette distinguishes red from dark using brightness

```bash
export AKIOS_COLORBLIND_MODE=protanopia
```

#### Deuteranopia (Green-Blind)
**Affects:** ~1% of males  
**Confusion:** Green ↔ Red  
**Solution:** AKIOS uses cyan/blue for success, orange/red for warnings

```bash
export AKIOS_COLORBLIND_MODE=deuteranopia
```

#### Tritanopia (Blue-Yellow Blind)
**Affects:** ~0.001% of people  
**Confusion:** Blue ↔ Yellow  
**Solution:** AKIOS uses red/black for errors, bright cyan for success

```bash
export AKIOS_COLORBLIND_MODE=tritanopia
```

#### Achromatopsia (Complete Color Blindness)
**Affects:** ~0.00001% of people  
**Solution:** Disable colors with NO_COLOR

```bash
export NO_COLOR=1
export AKIOS_SYMBOL_MODE=ascii
```

### Color Palette Examples

#### Success Message
```
Normal Vision:     [Green]  ✓ Workflow completed
Deuteranopia:      [Cyan]   ✓ Workflow completed
Tritanopia:        [Cyan]   ✓ Workflow completed
Achromatopsia:     Plain    ✓ Workflow completed
```

#### Error Message
```
Normal Vision:     [Red]       ✗ Workflow failed
Deuteranopia:      [Orange]    ✗ Workflow failed
Tritanopia:        [Red]       ✗ Workflow failed
Achromatopsia:     Plain       ✗ Workflow failed
```

#### Warning Message
```
Normal Vision:     [Yellow]    ⚠ High memory usage
Deuteranopia:      [Red]       ⚠ High memory usage
Tritanopia:        [Yellow]    ⚠ High memory usage
Achromatopsia:     Plain       ⚠ High memory usage
```

### How to Test

```bash
# Simulate color vision deficiencies
# (These tools can help verify compatibility)

# 1. Test your actual eyesight
#    https://www.colourblindawareness.org/colour-blindness/test/

# 2. Test AKIOS output with simulation:
AKIOS_COLORBLIND_MODE=deuteranopia akios run workflow.yml

# 3. Compare different modes:
echo -e "\n=== Normal Mode ===" && akios setup --show-environment
echo -e "\n=== Deuteranopia ===" && \
  AKIOS_COLORBLIND_MODE=deuteranopia akios setup --show-environment
echo -e "\n=== Tritanopia ===" && \
  AKIOS_COLORBLIND_MODE=tritanopia akios setup --show-environment
```

---

## Unicode Accessibility

### Unicode Support Detection

AKIOS automatically detects Unicode support:

```bash
# Check detected Unicode support
akios setup --show-environment | grep "Unicode Support"

# Override Unicode detection
export AKIOS_UNICODE_ENABLED=false   # Force disable Unicode
export AKIOS_UNICODE_ENABLED=true    # Force enable Unicode
```

### Setting Locale for Unicode

If Unicode symbols aren't displaying properly:

```bash
# Check current locale
locale

# Set UTF-8 locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Find available UTF-8 locales
locale -a | grep UTF

# Use specific locale
export LANG=en_GB.UTF-8  # British English
export LANG=de_DE.UTF-8  # German
export LANG=ja_JP.UTF-8  # Japanese
```

### Terminal Encoding

Ensure your terminal uses UTF-8 encoding:

**macOS:**
- Terminal.app: Preferences → Profiles → Advanced → Character Set → UTF-8
- iTerm2: Preferences → Profiles → General → Character Encoding → UTF-8

**Linux:**
- Most modern terminals: Settings → Character Encoding → UTF-8
- apt/pacman: Installed by default on modern systems

**Windows:**
- Windows Terminal: Settings → Startup → Default profile → Appearance → Font: Use "Cascadia Code" or "Consolas"
- PowerShell: `chcp 65001` before running AKIOS

**Docker:**
```dockerfile
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y locales
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
```

**Kubernetes:**
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
    - name: LANG
      value: "en_US.UTF-8"
    - name: LC_ALL
      value: "en_US.UTF-8"
```

---

## Screen Reader Support

AKIOS provides plain-text output suitable for screen readers:

```bash
# Disable all visual enhancements for screen reader optimization
export NO_COLOR=1
export AKIOS_SYMBOL_MODE=minimal

akios run workflow.yml
```

### Output Example

**With visual enhancements:** (Not ideal for screen readers)
```
✓ Setup complete [bold green]SUCCESS[/bold green]
```

**With screen reader optimization:** (Easy to read aloud)
```
[OK] Setup complete SUCCESS
```

### Terminal Emulator Accessibility

For best screen reader experience:

**Windows:**
- Windows Terminal with Narrator
- NVDA with JAWS support

**macOS:**
- Terminal.app with VoiceOver
- iTerm2 with VoiceOver

**Linux:**
- Gnome Terminal with ORCA
- Konsole with ORCA
- xterm with Festival

---

## Keyboard Navigation

AKIOS CLI commands support full keyboard navigation:

```bash
# Run in interactive mode
akios run workflow.yml --interactive

# Navigate options with keyboard
# ↑/↓  - Move between options
# Space - Select option
# Enter - Confirm selection
# Esc   - Cancel
```

### Configuration for Keyboard-Only Usage

```yaml
# config.yaml - Optimize for keyboard-only usage
ui:
  symbol_mode: ascii       # Simpler navigation
  color_mode: light         # High contrast
  no_mouse_hover: true      # Disable mouse-dependent features
```

---

## High Contrast Themes

For users with low vision, AKIOS provides high-contrast themes:

```bash
# Use high contrast theme
export AKIOS_THEME=high-contrast

# Current high-contrast themes:
# - nord (good dark/light contrast)
# - solarized-dark (excellent contrast)
# - solarized-light (excellent contrast)
```

### Theme Configuration

```yaml
# config.yaml
ui:
  theme: solarized-dark
  color_mode: dark
  min_contrast_ratio: 7.0  # WCAG AAA standard
```

---

## Text Size and Font

### Terminal Font Size

**macOS - Terminal.app:**
- Terminal → Preferences → Profiles → Text
- Increase "Display Font" size: 14, 16, 18, 20, 22+

**macOS - iTerm2:**
- iTerm2 → Preferences → Profiles → Text
- Increase font size as needed
- Or use Cmd+Up/Down to adjust live

**Linux (GNOME Terminal):**
- Preferences → Text → Font
- Increase "Monospace" size

**Windows Terminal:**
- Settings → Profiles → Appearance
- Increase "Font size"

### Recommended Fonts for Dyslexia

Research shows these fonts are easier to read for dyslexic users:
- **Dyslexie** (commercial)
- **OpenDyslexic** (free)
- **Atkinson Hyperlegible** (free, Google Fonts)
- **Courier New** (monospace, good for code)

---

## Complete Accessibility Configuration

### Example: Full Accessibility Setup

```bash
cat > ~/.akios-accessible << 'EOF'
# Accessibility profile
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# For colorblind users
export AKIOS_COLORBLIND_MODE=deuteranopia

# For ASCII compatibility
export AKIOS_SYMBOL_MODE=ascii

# For high contrast
export AKIOS_THEME=solarized-dark

# Enable screen reader mode
export AKIOS_SCREEN_READER_MODE=true
EOF

# Use the profile
source ~/.akios-accessible
akios run workflow.yml
```

### Example: config.yaml for Screen Readers

```yaml
# config.yaml - Optimized for accessibility
ui:
  symbol_mode: minimal          # Minimal special symbols
  color_mode: dark              # High contrast in dark theme
  theme: solarized-dark         # Good contrast
  colorblind_mode: deuteranopia # For common colorblindness
  unicode_enabled: true         # If terminal supports it
  screen_reader_mode: true      # Optimize text output
  
output:
  quiet_mode: false             # Stay verbose for clarity
  verbose: true                 # More details
  json_output: false            # Human-readable text
```

---

## Testing Accessibility

### Test Checklist

- [ ] Tested with `NO_COLOR=1` (should work)
- [ ] Tested with `AKIOS_SYMBOL_MODE=ascii` (should work)
- [ ] Tested with `AKIOS_SYMBOL_MODE=minimal` (should work)
- [ ] Tested with each `COLORBLIND_MODE` option
- [ ] Tested with screen reader (NVDA, ORCA, VoiceOver)
- [ ] Tested with high contrast display (120%+ zoom)
- [ ] Tested with increased terminal font size (18pt+)

### Accessibility Validation

```bash
#!/bin/bash
# Test accessibility compliance

echo "Testing accessibility modes..."

# Test 1: Colorblind support
for mode in protanopia deuteranopia tritanopia achromasia; do
  echo "Testing $mode..."
  AKIOS_COLORBLIND_MODE=$mode akios setup --show-environment > /dev/null
done

# Test 2: Symbol modes
for mode in unicode ascii minimal; do
  echo "Testing symbols: $mode..."
  AKIOS_SYMBOL_MODE=$mode akios setup --show-environment > /dev/null
done

# Test 3: No colors
echo "Testing NO_COLOR mode..."
NO_COLOR=1 akios setup --show-environment > /dev/null

echo "✓ All accessibility modes working"
```

---

## Related Documentation

- [Detection System](detection-system.md) - Automatic environment detection
- [Theme Customization](theme-customization.md) - Customize colors and themes
- [Configuration Reference](configuration.md) - All config options
- [Examples](examples.md) - Real-world usage examples

---

## Feedback and Accessibility Issues

Found an accessibility issue? Please report it:

1. **GitHub Issues:** github.com/akios-ai/akios/issues
2. **Accessibility Label:** Use the `accessibility` label
3. **Include Details:**
   - Your color vision type (if applicable)
   - Terminal/system information
   - Screenshot of the issue
   - Suggested fix if possible

We're committed to making AKIOS accessible for everyone.
