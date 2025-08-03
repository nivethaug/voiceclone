FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

# Basic environment variables
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=/bin/bash \
    HOME=/home/user \
    WORKER_DIR=/app \
    WORKER_MODEL_DIR=/app/model \
    WORKER_USE_CUDA=True \
    LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu \
    RUNPOD_DEBUG_LEVEL=INFO

SHELL ["/bin/bash", "-c"]

# Create app directory
RUN mkdir -p ${WORKER_DIR}
WORKDIR ${WORKER_DIR}

# Install base packages
RUN apt-get update && apt-get install -y \
    wget bzip2 ca-certificates curl git sudo gcc build-essential \
    openssh-client cmake g++ ninja-build libaio-dev \
    python3-dev python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash user && \
    echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-user && \
    chown -R user:user ${WORKER_DIR}
USER user
WORKDIR ${WORKER_DIR}

# Install Python requirements (main + audio enhancer)
COPY builder/requirements.txt .
COPY builder/requirements_audio_enhancer.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_audio_enhancer.txt && \
    rm requirements.txt requirements_audio_enhancer.txt

# Confirm deepspeed version
RUN python3 -c "import deepspeed; print('Deepspeed version:', deepspeed.__version__)"

# Setup git-lfs and download models
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash && \
    sudo apt-get install -y git-lfs && \
    git lfs install && \
    git clone https://huggingface.co/coqui/XTTS-v2 ${WORKER_MODEL_DIR}/xttsv2 && \
    git clone https://huggingface.co/ResembleAI/resemble-enhance ${WORKER_MODEL_DIR}/audio_enhancer

# Add worker source
COPY src ${WORKER_DIR}

CMD ["python3", "-u", "/app/rp_handler.py", "--model-dir=/app/model"]
