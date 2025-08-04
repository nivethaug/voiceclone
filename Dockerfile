# Base image with CUDA, cuDNN (optimized for RunPod + Python)
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables early for efficiency
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    PYTHONUNBUFFERED=1 \
    PATH="/home/worker/.local/bin:$PATH" \
    WORKER_DIR=/app

# Install core dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev \
        wget curl git git-lfs sudo \
        build-essential cmake ninja-build \
        libaio-dev bzip2 ca-certificates gcc g++ \
    && git lfs install \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash -u 1000 worker && \
    echo "worker ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/worker && \
    chmod 0440 /etc/sudoers.d/worker

# Set work directory
WORKDIR ${WORKER_DIR}
COPY --chown=worker:worker . ${WORKER_DIR}

# Install Python dependencies early to cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Optional: for audio processing enhancements (can be skipped if unused)
COPY requirements_audio_enhancer.txt .
RUN pip install --no-cache-dir -r requirements_audio_enhancer.txt || true

# Use non-root user
USER worker

CMD ["bash", "start.sh"]

