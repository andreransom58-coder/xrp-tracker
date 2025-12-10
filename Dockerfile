# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Security: Create non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup start.sh .
RUN chmod +x start.sh

# Create data directory with correct permissions
RUN mkdir -p /app/data && chown -R appuser:appgroup /app/data

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    DB_PATH=/app/data/xrp_monitor.db \
    # Disable pip version check for faster startup
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Volume for persistent data
VOLUME ["/app/data"]

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Switch to non-root user
USER appuser

# Run the application
CMD ["bash", "start.sh"]

# Labels for container metadata
LABEL org.opencontainers.image.title="XRP Tracker" \
      org.opencontainers.image.description="Real-time XRP Ledger monitoring with alerts" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="XRP Tracker" \
      org.opencontainers.image.licenses="MIT"
