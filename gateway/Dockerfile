# Sona AI OS - API Gateway Dockerfile
# Multi-stage build with non-root user

# ---- Build Stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy shared kernel first (dependency)
COPY libs/shared-kernel /build/libs/shared-kernel
RUN pip install --no-cache-dir /build/libs/shared-kernel

# Copy gateway source
COPY gateway/pyproject.toml /build/gateway/
COPY gateway/app /build/gateway/app

RUN pip install --no-cache-dir /build/gateway

# ---- Runtime Stage ----
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -g 1000 sona && \
    useradd -u 1000 -g sona -m -s /bin/bash sona

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Copy application code
COPY gateway/app /app/app

# Set ownership
RUN chown -R sona:sona /app

USER sona

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
