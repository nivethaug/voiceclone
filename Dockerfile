FROM python:3.11-slim

WORKDIR /app
ENV COQUI_TOS_AGREED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libsndfile1 \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn for production server
RUN pip install gunicorn

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

EXPOSE 8080

# Use Gunicorn to serve the Flask app on port 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
