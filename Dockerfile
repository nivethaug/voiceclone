FROM python:3.11-slim

WORKDIR /app
ENV COQUI_TOS_AGREED=1

# Install system dependencies (cached if unchanged)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage caching
COPY requirements.txt .

# Upgrade pip, setuptools, wheel and install Python dependencies
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN pip uninstall tts -y && pip install "coqui-tts>=0.25.0,<0.26.0"
#tts version printing
RUN python3 -c "from TTS import __version__ as tts_version; print('TTS version:', tts_version)"


RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory if needed
RUN mkdir -p models

# Clean old model cache (to avoid corrupt model errors)
RUN rm -rf /root/.local/share/tts/tts_models/multilingual/multi-dataset/xtts_v2

EXPOSE 8080

CMD ["python", "handler.py"]
