# Multi-stage build for smaller image size
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY server/requirements.txt .

# Install PyTorch CPU-only version first (much smaller than default)
RUN pip install --no-cache-dir --user \
    torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies with increased timeout
RUN pip install --no-cache-dir --user --default-timeout=1000 -r requirements.txt

# Final stage - minimal runtime image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only Python dependencies from builder (not source files yet)
COPY --from=builder /root/.local /root/.local

# Copy only necessary application code
COPY server/app ./server/app
COPY server/start_server.py ./server/
COPY server/.env.example ./server/

# Make sure scripts are in PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check (lightweight)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

# Run the application
CMD ["python", "server/start_server.py"]
