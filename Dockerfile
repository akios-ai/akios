# AKIOS V1.0.0 - Secure Cross-Platform Docker Deployment
# Multi-stage build: separate build dependencies from runtime image

# Build stage - includes all build dependencies
FROM ubuntu:24.04 AS builder

# Cache-busting build arguments to ensure fresh builds
ARG CACHE_BUST
ARG GIT_HASH
ARG BUILD_TIMESTAMP

# Create cache-busting marker file (this will invalidate COPY cache when values change)
RUN echo "${CACHE_BUST}-${GIT_HASH}-${BUILD_TIMESTAMP}" > /tmp/build_marker

ENV CACHE_BUST=${CACHE_BUST}
ENV GIT_HASH=${GIT_HASH}
ENV BUILD_TIMESTAMP=${BUILD_TIMESTAMP}

# Install Python build dependencies (Ubuntu base)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for build
WORKDIR /build

# Copy requirements first for better caching
COPY pyproject.toml .

# Install build dependencies in a virtual environment
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir build wheel

# ABSOLUTE CACHE INVALIDATION - Create and copy timestamp file
RUN echo "$(date +%s)-${CACHE_BUST}-${GIT_HASH}-${BUILD_TIMESTAMP}" > /tmp/force_rebuild_$(date +%s)
RUN cp /tmp/force_rebuild_* /tmp/force_rebuild

# Copy entire src directory to force cache invalidation
COPY src/ ./src/

# Build the wheel package
RUN /opt/venv/bin/python -m build --wheel --outdir /build/dist

# Runtime stage - Ubuntu 24.04 for maximum security
FROM ubuntu:24.04

# Install Python and essential system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    ca-certificates \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/* /tmp/* /var/tmp/* && \
    rm -rf /usr/share/doc/* /usr/share/man/* /usr/share/locale/* 2>/dev/null || true

# Security: Create non-root user
RUN groupadd -r akios -g 1001 && useradd -r -g akios -u 1001 akios

# Security: Remove setuid/setgid privileges from all binaries
RUN echo "Removing setuid binaries..." && \
    chmod u-s /usr/bin/* 2>/dev/null || true && \
    chmod u-s /bin/* 2>/dev/null || true && \
    chmod u-s /sbin/* 2>/dev/null || true && \
    echo "Setuid removal complete"

# Set working directory
WORKDIR /app

# Copy the wrapper script into the image (single source of truth)
COPY akios /app/akios
RUN chmod +x /app/akios

# Copy the built wheel from builder stage
COPY --from=builder /build/dist/ .

# Install the wheel package (clean, minimal)
RUN python3 -m pip install --no-cache-dir --break-system-packages *.whl && \
    rm *.whl && \
    find /usr/local/lib/python3.12 -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr/local/lib/python3.12 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /root/.cache/pip/* 2>/dev/null || true

# Security hardening, cleanup, and directory setup in single layer
RUN mkdir -p /app/data/input /app/data/output /app/audit /app/workflows && \
    chown -R akios:akios /app && \
    rm -rf /tmp/* /var/tmp/* /root/.cache/* 2>/dev/null || true

# Switch to non-root user
USER akios

# Health check (optional but recommended)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import akios; print('AKIOS OK')" || exit 1

# Default entrypoint
ENTRYPOINT ["python3", "-m", "akios"]
