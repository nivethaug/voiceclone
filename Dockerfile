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

# Copy only requirements first to leverage caching when dependencies don't change
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code last to avoid reinstalling dependencies on code changes
COPY . .

# Create models directory if needed
RUN mkdir -p models

# Expose the port your app listens on
EXPOSE 8080

# Directly run your serverless handler
CMD ["python", "handler.py"]
