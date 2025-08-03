FROM nvidia/cuda:11.8.0-devel-ubuntu22.04

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV WORKER_MODEL_DIR=/app/model
ENV WORKER_USE_CUDA=True

SHELL ["/bin/bash","-o","pipefail","-c"]
ENV DEBIAN_FRONTEND=noninteractive SHELL=/bin/bash LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu

RUN apt-get update --fix-missing && \
    apt-get install -y wget bzip2 ca-certificates curl git sudo gcc build-essential openssh-client cmake g++ ninja-build libaio-dev python3-dev python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip ecosystem
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install PyTorch (CUDA 11.8)
RUN pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118

# Install DeepSpeed and pin NumPy <2.0
RUN pip install --no-cache-dir deepspeed==0.9.5 && \
    pip install --no-cache-dir "numpy<2.0.0"

# Verify installs
RUN python3 -c "import torch; print(f'PyTorch {torch.__version__}, CUDA {torch.cuda.is_available()}')"
RUN python3 -c "import numpy; print(f'NumPy {numpy.__version__}')"
RUN python3 -c "import deepspeed; print(f'DeepSpeed {deepspeed.__version__}')"

# Create non-root user
RUN adduser --disabled-password --gecos '' --shell /bin/bash user && \
    chown -R user:user /app && \
    echo "user ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/90-user

USER user
ENV HOME=/home/user SHELL=/bin/bash WORKER_DIR=/app

# Install remaining Python dependencies
COPY builder/requirements.txt ${WORKER_DIR}/requirements.txt
RUN pip install --no-cache-dir -r ${WORKER_DIR}/requirements.txt && rm ${WORKER_DIR}/requirements.txt

COPY builder/requirements_audio_enhancer.txt ${WORKER_DIR}/requirements_audio_enhancer.txt
RUN pip install --no-cache-dir -r ${WORKER_DIR}/requirements_audio_enhancer.txt && rm ${WORKER_DIR}/requirements_audio_enhancer.txt

USER root
# Install git-lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash && \
    apt-get install -y git-lfs && \
    git lfs install

USER user
# Clone models
RUN git clone https://huggingface.co/coqui/XTTS-v2 ${WORKER_MODEL_DIR}/xttsv2
RUN git clone https://huggingface.co/ResembleAI/resemble-enhance ${WORKER_MODEL_DIR}/audio_enhancer

# Add source and set permissions
ADD src /app
USER root
RUN chown -R user:user /app /app/model
USER user

ENV RUNPOD_DEBUG_LEVEL=INFO

CMD ["python3","-u","/app/rp_handler.py","--model-dir=/app/model"]
