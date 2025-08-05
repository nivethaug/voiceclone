FROM python:3.11-slim

WORKDIR /app
ENV COQUI_TOS_AGREED=1

# Install system dependencies (combine into one RUN command)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for caching
COPY requirements.txt .

# Upgrade pip, setuptools, wheel and install Python dependencies
RUN python3 -m pip install --upgrade pip setuptools wheel

# Install IndicF5 repo directly to fix ckpt_path error
RUN pip uninstall IndicF5
RUN pip install git+https://github.com/ai4bharat/IndicF5.git


# (Optional) If you still need coqui-tts for other models, keep this, else you can remove:
# RUN pip uninstall tts -y && pip install "coqui-tts>=0.25.0,<0.26.0"
# RUN python3 -c "from TTS import __version__ as tts_version; print('TTS version:', tts_version)"

# Install other dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code after dependencies for better layer caching
COPY . .

# Create models directory if needed
RUN mkdir -p models

EXPOSE 8080

CMD ["python", "handler.py"]
