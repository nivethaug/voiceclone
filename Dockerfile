# Base image (CPU-only)
FROM python:3.10-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    WORKER_DIR=/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential cmake ninja-build \
        git git-lfs curl wget \
        libaio-dev ffmpeg sox && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Git LFS
RUN git lfs install

# Create app directory
WORKDIR ${WORKER_DIR}

# Copy everything
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r builder/requirements.txt && \
    pip install --no-cache-dir -r builder/requirements_audio_enhancer.txt || true

# Make start script executable
RUN chmod +x start.sh

# Start the container
CMD ["./start.sh"]
