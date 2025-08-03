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
RUN pip install \
      torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
      --index-url https://download.pytorch.org/whl/cu118

# Install DeepSpeed and pin numpy <2.0
RUN pip install --no-cache-dir deepspeed==0.9.5 && \
    pip install --no-cache-dir "numpy<2.0.0"

# Verify installations
RUN python3 - <<'EOF'
import torch, numpy, deepspeed
print("PyTorch:", torch.__version__, "CUDA:", torch.cuda.is_available())
print("NumPy:", numpy.__version__)
print("DeepSpeed:", deepspeed.__version__)
EOF

# Create non-root user via useradd (non-interactive)
RUN useradd -m -s /bin/bash -u 1000 worker && \
    echo "worker ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/worker && \
    chmod 0440 /etc/sudoers.d/worker

USER worker
ENV HOME=/home/worker \
    WORKER_DIR=/app

WORKDIR ${WORKER_DIR}

# Install Python dependencies
COPY builder/requirements.txt ${WORKER_DIR}/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

COPY builder/requirements_audio_enhancer.txt ${WORKER_DIR}/requirements_audio_enhancer.txt
RUN pip install --no-cache-dir -r requirements_audio_enhancer.txt && rm requirements_audio_enhancer.txt

# Clone models as non-root
RUN git clone https://huggingface.co/coqui/XTTS-v2 ${WORKER_MODEL_DIR}/xttsv2
RUN git clone https://huggingface.co/ResembleAI/resemble-enhance ${WORKER_MODEL_DIR}/audio_enhancer

# Add source code
ADD src ${WORKER_DIR}

ENV RUNPOD_DEBUG_LEVEL=INFO

CMD ["python3","-u","/app/rp_handler.py","--model-dir=/app/model"]
