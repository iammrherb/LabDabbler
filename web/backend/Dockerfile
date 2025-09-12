# Multi-stage build for production backend
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies and security updates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY ../../pyproject.toml ../../uv.lock ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install --no-cache-dir -r uv.lock

# Production stage
FROM python:3.11-slim AS production

# Install runtime dependencies and security updates
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        docker.io \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install containerlab
RUN curl -sL https://containerlab.dev/setup | bash -s "all"

# Create non-root user for security
RUN groupadd -r labdabbler && \
    useradd -r -g labdabbler -u 1001 labdabbler && \
    mkdir -p /app /var/log/labdabbler && \
    chown -R labdabbler:labdabbler /app /var/log/labdabbler

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=labdabbler:labdabbler . .

# Create necessary directories
RUN mkdir -p data labs configs uploads && \
    chown -R labdabbler:labdabbler data labs configs uploads

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Expose port
EXPOSE 8000

# Switch to non-root user
USER labdabbler

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Start the application (ensure we're in the correct directory)
CMD ["sh", "-c", "cd /app && python -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4 --access-log --log-level info"]