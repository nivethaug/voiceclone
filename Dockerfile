FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    WORKER_MODEL_DIR=/app/model \
    WORKER_USE_CUDA=True \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=/bin/bash \
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu

SHELL ["/bin/bash","-o","pipefail","-c"]

# System dependencies
RUN apt-get update --fix-missing && \
    apt-get install -y \
      wget bzip2 ca-certificates curl git sudo \
      gcc build-essential cmake g++ ninja-build libaio-dev \
      python3-dev python3-pip git-lfs && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    git lfs install

# Upgrade pip and build tools
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install PyTorch (CUDA11.8)
RUN pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

# Install DeepSpeed (compat) and pin numpy
RUN pip install --no-cache-dir deepspeed==0.12.6 && \
    pip install --no-cache-dir "numpy<2.0.0"

# Create non-root user
RUN useradd -m -s /bin/bash -u 1000 worker && \
    echo "worker ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/worker && \
    chmod 0440 /etc/sudoers.d/worker

# Prepare model directory
RUN mkdir -p /app/model && chown -R worker:worker /app /app/model

USER worker
RUN git lfs install --skip-repo

ENV HOME=/home/worker \
    WORKER_DIR=/app

WORKDIR ${WORKER_DIR}

# Install Python dependencies
COPY builder/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

COPY builder/requirements_audio_enhancer.txt requirements_audio_enhancer.txt
RUN pip install --no-cache-dir -r requirements_audio_enhancer.txt && rm requirements_audio_enhancer.txt

# Clone model repos
RUN git clone https://huggingface.co/coqui/XTTS-v2 ${WORKER_MODEL_DIR}/xttsv2
RUN git clone https://huggingface.co/ResembleAI/resemble-enhance ${WORKER_MODEL_DIR}/audio_enhancer

# Copy source code into /app
COPY src/ ./

ENV RUNPOD_DEBUG_LEVEL=INFO

# Correct CMD path to rp_handler.py at /app/
CMD ["python3", "-u", "./rp_handler.py", "--model-dir=/app/model"]
