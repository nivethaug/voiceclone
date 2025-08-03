FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

ENV WORKER_DIR=/workspace \
    MODE_TO_RUN=pod \
    PYTHONUNBUFFERED=1

WORKDIR $WORKER_DIR

# Install dependencies + TTS
COPY builder/requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

RUN pip install deepspeed==0.13.1
RUN python3 -c "import deepspeed; print('DS Version:', deepspeed.__version__)"

# Copy workspace files
COPY src ./src
COPY start.sh .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["bash", "./start.sh"]
