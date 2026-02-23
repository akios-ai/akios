#!/bin/bash
# AKIOS Docker wrapper
set -euo pipefail

# ============================================================================
# DEVELOPER SETTING: Change this to use local development image
# ============================================================================
# Set to "1" for local development (uses akios:latest)
# Set to "0" for production (uses akiosai/akios:vX.X.X from Docker Hub)
# Default: 0 (production mode)
# Dev repository: Change to 1 when working on AKIOS itself
LOCAL_DEV_MODE=0
# ============================================================================

PROJECT_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_ENV_ARGS=()

# Detect AKIOS version dynamically (Option A + B: pyproject.toml → VERSION → fallback)
detect_version() {
    local version=""
    
    # Option A: Try to read from pyproject.toml (if in repo)
    if [[ -f "$SCRIPT_DIR/../pyproject.toml" ]]; then
        version=$(grep '^version = ' "$SCRIPT_DIR/../pyproject.toml" 2>/dev/null | cut -d'"' -f2 || echo "")
    elif [[ -f "$SCRIPT_DIR/pyproject.toml" ]]; then
        version=$(grep '^version = ' "$SCRIPT_DIR/pyproject.toml" 2>/dev/null | cut -d'"' -f2 || echo "")
    fi
    
    # Option B: Fallback to VERSION file (multiple locations)
    if [[ -z "$version" ]]; then
        # Try repo root
        if [[ -f "$SCRIPT_DIR/../VERSION" ]]; then
            version=$(cat "$SCRIPT_DIR/../VERSION" 2>/dev/null | tr -d '[:space:]' || echo "")
        # Try local directory
        elif [[ -f "$SCRIPT_DIR/VERSION" ]]; then
            version=$(cat "$SCRIPT_DIR/VERSION" 2>/dev/null | tr -d '[:space:]' || echo "")
        # Try Python package installation
        elif command -v python3 &>/dev/null; then
            version=$(python3 -c "import akios; import os; vf=os.path.join(os.path.dirname(akios.__file__), 'VERSION'); print(open(vf).read().strip() if os.path.exists(vf) else '')" 2>/dev/null || echo "")
        fi
    fi
    
    # Final fallback: hardcoded stable version
    if [[ -z "$version" ]]; then
        version="1.0.12"
    fi
    
    echo "$version"
}



# Load optional .env file if it exists (for API keys and settings)
# Note: .env does NOT control Docker image selection - use LOCAL_DEV_MODE above
AKIOS_ENV_FILE="$PROJECT_DIR/.env"
if [[ -f "$AKIOS_ENV_FILE" ]]; then
    if [[ "${AKIOS_DEBUG_ENABLED:-0}" == "1" ]]; then
        echo "📄 Loading API keys from .env" >&2
    fi
    set -a  # Automatically export all variables
    source "$AKIOS_ENV_FILE"
    set +a
fi

# Determine Docker image to use
# Priority: 1. Command-line AKIOS_LOCAL_MODE=1 (override)
#           2. LOCAL_DEV_MODE variable (edit at top of this script)
#           3. Default: 0 (production)
if [[ "${AKIOS_LOCAL_MODE:-$LOCAL_DEV_MODE}" == "1" ]]; then
    MODE="1"
else
    MODE="0"
fi

# Detect version dynamically
AKIOS_VERSION=$(detect_version)

# Set image based on mode
if [[ "$MODE" == "1" ]]; then
    # Development mode: use local development build
    DOCKER_IMAGE="akios:latest"
    DEBUG_MSG="LOCAL_DEV_MODE=1: Using development image (akios:latest)"
else
    # Production mode: use stable release with dynamic version
    DOCKER_IMAGE="akiosai/akios:v${AKIOS_VERSION}"
    DEBUG_MSG="Using production image (akiosai/akios:v${AKIOS_VERSION})"
fi

if [[ "${AKIOS_DEBUG_ENABLED:-0}" == "1" ]]; then
    echo "[DEBUG] LOCAL_DEV_MODE=$LOCAL_DEV_MODE (set in wrapper script)" >&2
    echo "[DEBUG] AKIOS_LOCAL_MODE=${AKIOS_LOCAL_MODE:-not set} (command-line override)" >&2
    echo "[DEBUG] Detected version: $AKIOS_VERSION" >&2
    echo "[DEBUG] $DEBUG_MSG" >&2
fi

# Pass wrapper path for auto-copy during init
AKIOS_WRAPPER_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"

# Always run in Docker (simplified - no auto-detection)
if [[ "${AKIOS_DEBUG_ENABLED:-0}" == "1" ]]; then
    echo "🐳 Using Docker for cross-platform security" >&2
fi

# Enable TTY for interactive commands only (setup, init --wizard)
DOCKER_TTY_FLAGS=""
if [[ "${1:-}" == "setup" ]]; then
    DOCKER_TTY_FLAGS="-it"
elif [[ "${1:-}" == "init" ]]; then
    for arg in "$@"; do
        if [[ "$arg" == "--wizard" ]]; then
            DOCKER_TTY_FLAGS="-it"
            break
        fi
    done
fi

# Only pass optional settings when explicitly set to avoid type parse errors
add_env_if_set() {
    local name="$1"
    local value="${!name-}"
    if [[ -n "$value" ]]; then
        DOCKER_ENV_ARGS+=(-e "${name}=${value}")
    fi
}

# Check if image exists locally (avoid unnecessary pulls)
check_image_cached() {
    docker image inspect "$DOCKER_IMAGE" &>/dev/null
}

# Show progress message if pulling
pull_if_needed() {
    # Allow developers to force fresh pulls during testing
    if [[ "${AKIOS_FORCE_PULL:-0}" == "1" ]]; then
        echo "🐳 Force-pulling AKIOS Docker image (dev mode)..." >&2
        docker pull "$DOCKER_IMAGE"
        echo "✅ Docker image updated!" >&2
    elif ! check_image_cached; then
        echo "🐳 Pulling AKIOS Docker image..." >&2
        docker pull "$DOCKER_IMAGE"
        echo "✅ Docker image ready!" >&2
    fi
}

# All commands run through Docker
pull_if_needed
DOCKER_ENV_ARGS=()
add_env_if_set AKIOS_BUDGET_LIMIT_PER_RUN
add_env_if_set AKIOS_MAX_TOKENS_PER_CALL
add_env_if_set AKIOS_NETWORK_ACCESS_ALLOWED
add_env_if_set AKIOS_ALLOWED_DOMAINS
add_env_if_set AKIOS_PII_REDACTION_ENABLED
add_env_if_set AKIOS_SANDBOX_ENABLED
add_env_if_set FORCE_COLOR
add_env_if_set CLICOLOR_FORCE

# Only allocate TTY when stdout is a terminal (preserves stderr separation for piping)
DOCKER_IT_FLAGS=""
if [[ -t 1 ]]; then
    DOCKER_IT_FLAGS="-it"
fi

exec docker run --rm \
    $DOCKER_IT_FLAGS \
    $DOCKER_TTY_FLAGS \
    -v "$PROJECT_DIR:/app" \
    -w /app \
    -e TERM="${TERM:-xterm-256color}" \
    -e AKIOS_WRAPPER_PATH="$AKIOS_WRAPPER_PATH" \
    -e AKIOS_MOCK_LLM="${AKIOS_MOCK_LLM:-0}" \
    ${DOCKER_ENV_ARGS[@]+"${DOCKER_ENV_ARGS[@]}"} \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
    -e GROK_API_KEY="${GROK_API_KEY:-}" \
    -e MISTRAL_API_KEY="${MISTRAL_API_KEY:-}" \
    -e GEMINI_API_KEY="${GEMINI_API_KEY:-}" \
    -e AKIOS_LLM_PROVIDER="${AKIOS_LLM_PROVIDER:-}" \
    -e AKIOS_LLM_MODEL="${AKIOS_LLM_MODEL:-}" \
    ${NO_COLOR:+-e NO_COLOR="$NO_COLOR"} \
    "$DOCKER_IMAGE" \
    "$@"
