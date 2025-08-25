# Use Python 3.11 slim image
# Optimized for Podman (compatible with Docker)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY README.md ./
COPY LICENSE ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[demo]

# Expose port for Gradio demo
EXPOSE 7860

# Set environment variables
ENV PYTHONPATH=/app/src
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Default command to run the demo
CMD ["python", "-m", "morphcards.demo"]
