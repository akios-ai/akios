# AKIOS Theme Customization Guide
**Document Version:** 1.0.11  
**Date:** 2026-02-22  

**Creating and customizing color themes for AKIOS output.**

AKIOS comes with built-in professional themes optimized for different preferences and accessibility needs. You can also create custom themes for your organization or personal use.

## Built-In Themes

### Default Theme

The default theme balances readability and visual appeal. Uses a moderate color palette suitable for most environments.

```bash
export AKIOS_THEME=default
akios run workflow.yml
```

**Color Scheme:**
- Success: Green (#00C41D)
- Error: Red (#FF3B30)
- Warning: Orange (#FF9500)
- Info: Blue (#007AFF)

### Dark Theme

High-contrast dark theme optimized for dark terminal backgrounds.

```bash
export AKIOS_THEME=dark
akios run workflow.yml
```

**Features:**
- Light text on dark background
- High contrast for readability
- Suitable for night work

### Light Theme

High-contrast light theme optimized for light terminal backgrounds.

```bash
export AKIOS_THEME=light
akios run workflow.yml
```

**Features:**
- Dark text on light background
- High contrast for readability
- Suitable for light-mode terminals

### Nord Theme

Popular Arctic theme with cool colors. 

```bash
export AKIOS_THEME=nord
akios run workflow.yml
```

**Color Scheme:**
- Polar Night (background): #2E3440
- Snow Storm (foreground): #ECEFF4
- Frost (accent): #88C0D0, #81A1C1
- Aurora (highlights): #BF616A, #D08770, #EBCB8B, #A3BE8C, #B48EAD

**Best for:** Developers familiar with Nord theme across many tools

### Solarized Dark Theme

Color-accurate dark theme from Ethan Schoonover.

```bash
export AKIOS_THEME=solarized-dark
akios run workflow.yml
```

**Color Scheme:**
- Base: #002B36
- Base Accent: #073642
- Orange: #CB4B16
- Red: #DC322F
- Green: #859900
- Cyan: #2AA198
- Blue: #268BD2
- Violet: #6C71C4

**Best for:** Designers and color-sensitive users

### Solarized Light Theme

Color-accurate light theme from Ethan Schoonover.

```bash
export AKIOS_THEME=solarized-light
akios run workflow.yml
```

**Color Scheme:**
- Base: #FDF6E3
- Base Accent: #EEE8D5
- Same accent colors as dark variant but with inverted backgrounds

**Best for:** Light-mode users who want Solarized color palette

### High Contrast Theme

WCAG AAA compliant theme for accessibility.

```bash
export AKIOS_THEME=high-contrast
akios run workflow.yml
```

**Features:**
- 7:1 contrast ratio (WCAG AAA minimum is 7:1)
- Bold colors easy to distinguish
- Minimal color confusion for colorblind users

**Best for:** Low-vision users, accessibility compliance

## Theme Configuration

### Via Environment Variable

```bash
# Set theme for current session
export AKIOS_THEME=nord
akios run workflow.yml

# Set for single command
AKIOS_THEME=solarized-dark akios run workflow.yml
```

### Via config.yaml

```yaml
ui:
  theme: solarized-dark
```

### Via Command Line

```bash
# If CLI supports --theme flag
akios run workflow.yml --theme=nord
```

## Custom Theme Creation

### Basic Custom Theme

Create a custom theme file:

```yaml
# File: ~/.akios/themes/my-theme.yaml
name: "My Custom Theme"
description: "Personal custom theme"
version: "1.0"

colors:
  # Status colors
  success: "#00C41D"          # ✓ Success
  error: "#FF3B30"             # ✗ Error
  warning: "#FF9500"           # ⚠ Warning
  info: "#007AFF"              # ℹ Information
  
  # UI elements
  primary: "#007AFF"           # Main UI color
  secondary: "#5856D6"         # Secondary color
  accent: "#00C41D"            # Accent color
  
  # Semantic colors
  good: "#00C41D"              # Good/positive state
  bad: "#FF3B30"               # Bad/negative state
  neutral: "#8E8E93"           # Neutral state
  
  # Special colors
  performance: "#FF8C00"       # Performance metrics
  security: "#FF3B30"          # Security alerts
  timing: "#FF8C00"            # Timing information
  
  # Background colors
  background: "#FFFFFF"        # Main background
  panel_background: "#F2F2F7"  # Panel background
  
  # Text colors
  text_primary: "#000000"      # Main text
  text_secondary: "#666666"    # Secondary text
  text_muted: "#999999"        # Muted text
```

### Advanced Custom Theme with Variants

```yaml
# File: ~/.akios/themes/corporate.yaml
name: "Corporate Theme"
description: "Company-wide branded colors"
version: "1.0"

variants:
  light:
    colors:
      success: "#00A651"       # Company green
      error: "#E63E36"         # Company red
      warning: "#F79300"       # Company orange
      info: "#0066CC"          # Company blue
      background: "#FFFFFF"
      text_primary: "#000000"
      
  dark:
    colors:
      success: "#00E68A"       # Lighter green for dark mode
      error: "#FF6B6B"         # Lighter red for dark mode
      warning: "#FFB800"       # Lighter orange for dark mode
      info: "#4DA6FF"          # Lighter blue for dark mode
      background: "#1A1A1A"
      text_primary: "#FFFFFF"
```

### Theme with Colorblind Optimization

```yaml
# File: ~/.akios/themes/colorblind-safe.yaml
name: "Colorblind-Safe Theme"
description: "Safe for all color vision types"
version: "1.0"

# Base theme
colors:
  success: "#0072B2"   # Safe blue (never confused)
  error: "#E69F00"     # Safe orange
  warning: "#CC79A7"   # Safe purple/pink
  info: "#009E73"      # Safe green (uses different hue)

# Colorblind variants
colorblind_variants:
  protanopia:         # Red-blind
    success: "#0072B2" # Blue
    error: "#E69F00"   # Orange
    warning: "#CC79A7" # Purple
    
  deuteranopia:        # Green-blind
    success: "#0072B2" # Blue
    error: "#E69F00"   # Orange
    warning: "#CC79A7" # Purple
    
  tritanopia:          # Blue-yellow blind
    success: "#0072B2" # Blue (works)
    error: "#E69F00"   # Orange
    warning: "#E63E36" # Red
```

## Using Custom Themes

### Register Theme

```bash
# Copy theme to themes directory
mkdir -p ~/.akios/themes
cp my-theme.yaml ~/.akios/themes/

# Or systemwide (requires admin)
sudo cp my-theme.yaml /etc/akios/themes/
```

### Activate Custom Theme

```bash
# Activate for session
export AKIOS_THEME=my-theme
akios run workflow.yml

# Or in config.yaml
cat > config.yaml << 'EOF'
ui:
  theme: my-theme
EOF
```

### View Available Themes

```bash
# List all themes
akios config list-themes

# Output:
# Built-in themes:
#   - default
#   - dark
#   - light
#   - nord
#   - solarized-dark
#   - solarized-light
#   - high-contrast
#
# Custom themes:
#   - my-theme
#   - corporate
#   - colorblind-safe
```

## Colorblind-Optimized Themes

### Deuteranopia (Red-Green Blind) Theme

For ~1% of male population with red-green color blindness:

```yaml
# File: ~/.akios/themes/colorblind-deuteranopia.yaml
name: "Colorblind Deuteranopia"
colors:
  success: "#0173B2"      # Cyan/Blue (clear)
  error: "#DE8F05"        # Orange (distinct from green)
  warning: "#DE8F05"      # Orange (distinct from red)
  info: "#0173B2"         # Cyan/Blue (clear)
  performance: "#DE8F05"  # Orange
  security: "#CC78BA"     # Purple/Magenta
```

### Tritanopia (Blue-Yellow Blind) Theme

For ~0.001% of population with blue-yellow color blindness:

```yaml
# File: ~/.akios/themes/colorblind-tritanopia.yaml
name: "Colorblind Tritanopia"
colors:
  success: "#D000E6"      # Purple/Magenta (clear)
  error: "#E60000"        # Red (distinct from blue)
  warning: "#FFB500"      # Orange/Yellow modified
  info: "#0088FF"         # Blue (inverted value)
  performance: "#E60000"  # Red
  security: "#D000E6"     # Purple
```

### Achromasia (Complete Color Blindness) Theme

For users with complete color blindness, use grayscale:

```yaml
# File: ~/.akios/themes/grayscale.yaml
name: "Grayscale (Complete CVD)"
colors:
  success: "#333333"      # Dark gray
  error: "#000000"        # Black
  warning: "#666666"      # Medium gray
  info: "#999999"         # Light gray
  background: "#FFFFFF"   # White
  text_primary: "#000000" # Black
  text_secondary: "#666666" # Medium gray
```

## Theme Development Best Practices

### Color Contrast

Ensure sufficient contrast for accessibility:

```yaml
# WCAG AA Standard: 4.5:1 contrast ratio
# WCAG AAA Standard: 7:1 contrast ratio

# Use this equation to calculate contrast:
# L1 = (0.299 * R + 0.587 * G + 0.114 * B) / 255
# Contrast = (L1_light + 0.05) / (L1_dark + 0.05)

colors:
  text_primary: "#000000"    # L1 = 0 (black)
  background: "#FFFFFF"      # L1 = 1 (white)
  # Contrast = (1 + 0.05) / (0 + 0.05) = 21:1 ✓ Excellent
```

### Color Palette Tools

Recommended tools for palette selection:

1. **Color Contrast Checker** - webaim.org/resources/contrastchecker/
2. **Color Blindness Simulator** - color-blindness.com/coblis-color-blindness-simulator/
3. **Accessible Colors** - accessible-colors.com/
4. **Paletton** - paletton.com/ (formerly ColorJack)

### Testing Theme

```bash
#!/bin/bash
# test-theme.sh - Test custom theme

THEME="my-theme"

echo "Testing theme: $THEME"

# Test with each symbol mode
for symbols in unicode ascii minimal; do
  echo "- Symbol mode: $symbols"
  AKIOS_THEME=$THEME AKIOS_SYMBOL_MODE=$symbols \
    akios setup --show-environment >/dev/null || echo "FAILED"
done

# Test with colorblind modes
for colorblind in protanopia deuteranopia tritanopia; do
  echo "- Colorblind mode: $colorblind"
  AKIOS_THEME=$THEME AKIOS_COLORBLIND_MODE=$colorblind \
    akios setup --show-environment >/dev/null || echo "FAILED"
done

# Test with NO_COLOR
echo "- NO_COLOR=1"
NO_COLOR=1 AKIOS_THEME=$THEME \
  akios setup --show-environment >/dev/null || echo "FAILED"

echo "✓ Theme test complete"
```

## Theme Examples

### Minimalist Theme

```yaml
name: "Minimalist"
colors:
  success: "#000000"
  error: "#000000"
  warning: "#000000"
  info: "#000000"
  background: "#FFFFFF"
  text_primary: "#000000"
```

### Dracula Theme

```yaml
name: "Dracula"
colors:
  success: "#50FA7B"      # Green
  error: "#FF5555"        # Red
  warning: "#F1FA8C"      # Yellow
  info: "#8BE9FD"         # Cyan
  background: "#282A36"   # Dark background
  text_primary: "#F8F8F2" # Light text
```

### Gruvbox Theme

```yaml
name: "Gruvbox Dark"
colors:
  success: "#B8BB26"      # Green
  error: "#FB4934"        # Red
  warning: "#FABD2F"      # Yellow
  info: "#83A598"         # Blue
  background: "#282828"   # Dark background
  text_primary: "#EBDBB2" # Light text
```

## Organization-Wide Theme

### Distributing Themes

For Teams:

```bash
# 1. Create theme repository
git clone https://github.com/mycompany/akios-themes.git
cd akios-themes

# 2. Add team themes
cp mycompany-theme.yaml themes/

# 3. Users install themes
cp themes/*.yaml ~/.akios/themes/

# Or system-wide
sudo cp themes/*.yaml /etc/akios/themes/
```

### Docker with Custom Theme

```dockerfile
FROM python:3.11-slim
RUN pip install akios

# Copy custom theme
COPY corporate-theme.yaml /etc/akios/themes/
RUN chmod 644 /etc/akios/themes/corporate-theme.yaml

ENV AKIOS_THEME=corporate-theme
ENTRYPOINT ["akios"]
```

### Kubernetes with Custom Theme

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: akios-theme
data:
  corporate.yaml: |
    name: "Corporate Theme"
    colors:
      success: "#00A651"
      error: "#E63E36"
      warning: "#F79300"

---
apiVersion: v1
kind: Pod
metadata:
  name: akios-job
spec:
  containers:
  - name: akios
    image: akios:latest
    env:
    - name: AKIOS_THEME
      value: "corporate"
    volumeMounts:
    - name: theme-vol
      mountPath: /etc/akios/themes
  volumes:
  - name: theme-vol
    configMap:
      name: akios-theme
```

## Troubleshooting Themes

### Theme Not Loading

```bash
# Check theme file syntax
akios config validate-theme my-theme.yaml

# List available themes
akios config list-themes

# Check theme location
ls ~/.akios/themes/
ls /etc/akios/themes/
```

### Colors Look Wrong

```bash
# Check color values (RGB hex format)
# Colors should be in format: #RRGGBB
# Example: #FF5733 (red: 255, green: 87, blue: 51)

# Validate RGB values
python3 << 'EOF'
import re
colors = ["#FF5733", "#not-valid", "#12345G"]
pattern = r'^#[0-9A-Fa-f]{6}$'
for color in colors:
    if re.match(pattern, color):
        print(f"✓ {color} valid")
    else:
        print(f"✗ {color} invalid")
EOF
```

### Contrast Issues

```bash
# Calculate contrast ratio
python3 << 'EOF'
def hex_to_rgb(hex_color):
    return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))

def luminance(rgb):
    r, g, b = [x / 255 for x in rgb]
    return 0.299*r + 0.587*g + 0.114*b

def contrast_ratio(color1, color2):
    lum1 = luminance(hex_to_rgb(color1))
    lum2 = luminance(hex_to_rgb(color2))
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)

# Test colors
text = "#000000"
bg = "#FFFFFF"
ratio = contrast_ratio(text, bg)
print(f"Contrast ratio: {ratio:.1f}:1")
print(f"WCAG AA (4.5:1): {'✓' if ratio >= 4.5 else '✗'}")
print(f"WCAG AAA (7:1): {'✓' if ratio >= 7 else '✗'}")
EOF
```

## Related Documentation

- [Accessibility Guide](accessibility-guide.md) - Colorblind support
- [Detection System](detection-system.md) - Automatic environment detection
- [Configuration Reference](configuration.md) - All config options
- [Examples](examples.md) - Real-world usage examples
