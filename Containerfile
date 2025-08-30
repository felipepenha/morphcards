# Use Python 3.11 slim image
# Optimized for Podman (compatible with Docker)
FROM python:3.11-slim

# Create a non-root user and switch to it
RUN adduser --system --group appuser

# Set working directory
WORKDIR /app
ENV TMPDIR=/tmp
ENV PIP_TMPDIR=/tmp

# Install system dependencies
# Use root temporarily for apt-get, then switch back
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./ 
COPY src/ ./src/
COPY README.md ./ 
COPY LICENSE ./ 

# Install Python dependencies as root
RUN pip install --no-cache-dir --upgrade pip --cache-dir /tmp/pip_cache &&     pip install --no-cache-dir .[demo] --cache-dir /tmp/pip_cache

USER appuser

# Expose port for Gradio demo
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app/src
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Default command to run the demo
CMD ["python", "-m", "morphcards.demo"]
