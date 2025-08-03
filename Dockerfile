FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    TZ=Etc/UTC \
    WORKER_DIR=/app \
    PATH="$PATH:/root/.local/bin"

# System dependencies
RUN apt-get update && \
    apt-get install -y \
    git \
    git-lfs \
    curl \
    wget \
    ffmpeg \
    build-essential \
    python3.10 \
    python3-pip \
    python3.10-venv \
    libsndfile1-dev \
    libgl1 \
    && apt-get clean

# Make python3.10 default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Upgrade pip
RUN python3 -m pip install --upgrade pip setuptools wheel

# Create working directory
WORKDIR ${WORKER_DIR}

# Copy code
COPY . ${WORKER_DIR}

# Install Python requirements
RUN pip install --no-cache-dir -r ${WORKER_DIR}/requirements.txt

# Optional: install Deepspeed if needed
RUN pip install deepspeed==0.13.1 && \
    python3 -c "import deepspeed; print('Deepspeed version:', deepspeed.__version__)"

# Git LFS pull (if models are tracked this way)
RUN git lfs install && git lfs pull || true

# Expose port (if using web server)
EXPOSE 3000

# Run command (adjust for your app entrypoint)
CMD ["python3", "main.py"]
