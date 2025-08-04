FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Set environment variables
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    WORKER_MODEL_DIR=/app/model \
    WORKER_USE_CUDA=True \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=/bin/bash \
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu \
    HOME=/home/worker \
    WORKER_DIR=/app \
    RUNPOD_DEBUG_LEVEL=INFO

# Use bash with pipefail to catch errors
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# System dependencies and user setup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget bzip2 ca-certificates curl git sudo \
        gcc g++ cmake ninja-build libaio-dev \
        python3-dev python3-pip git-lfs \
        build-essential && \
    git lfs install && \
    useradd -m -s /bin/bash -u 1000 worker && \
    echo "worker ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/worker && \
    chmod 0440 /etc/sudoers.d/worker && \
    mkdir -p /app/model && chown -R worker:worker /app && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and tools
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA 11.8
RUN pip install --no-cache-dir torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

# Install DeepSpeed and compatible numpy
RUN pip install --no-cache-dir deepspeed==0.12.6 "numpy<2.0.0"

# Switch to non-root user
USER worker
WORKDIR ${WORKER_DIR}

# Install Python dependencies
COPY --chown=worker:worker builder/requirements.txt builder/requirements_audio_enhancer.txt ${WORKER_DIR}/
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt && \
    pip install --no-cache-dir -r requirements_audio_enhancer.txt && rm requirements_audio_enhancer.txt

# Clone models
RUN git clone https://huggingface.co/coqui/XTTS-v2 ${WORKER_MODEL_DIR}/xttsv2 && \
    git clone https://huggingface.co/ResembleAI/resemble-enhance ${WORKER_MODEL_DIR}/audio_enhancer

# Copy source code
COPY --chown=worker:worker src ${WORKER_DIR}

# Run the app
CMD ["python3", "-u", "/app/rp_handler.py", "--model-dir=/app/model"]
