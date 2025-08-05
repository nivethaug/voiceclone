FROM python:3.11-slim

WORKDIR /app
ENV COQUI_TOS_AGREED=1

# Install system dependencies first (cached if unchanged)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory if needed
RUN mkdir -p models

# Force clean model cache (to avoid corrupted GPT2 model errors)
RUN rm -rf /root/.local/share/tts/tts_models/multilingual/multi-dataset/xtts_v2

# Expose port
EXPOSE 8080

# Start handler
CMD ["python", "handler.py"]
