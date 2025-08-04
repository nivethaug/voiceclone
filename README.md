# Voice Cloning Project

This is a simple voice cloning implementation using XTTS v2.

## Setup

1. Build the Docker image:
   ```bash
   docker build -t voice-cloner .
   ```

2. Run the container:
   ```bash
   docker run -p 8080:8080 voice-cloner
   ```

3. Test with health check:
   ```bash
   curl http://localhost:8080/health
   ```

## Usage

### Python API Usage:
```python
import requests

response = requests.post('http://localhost:8080/clone', json={
    "text": "Hello, this is my cloned voice speaking!",
    "speaker_wav": "https://example.com/my_voice_sample.wav",
    "language": "en",
    "speed": 1.0
})

if response.status_code == 200:
    with open('cloned_output.wav', 'wb') as f:
        f.write(response.content)
```

### cURL Usage:
```bash
curl -X POST http://localhost:8080/clone \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world, this is voice cloning!",
    "speaker_wav": "https://example.com/reference.wav",
    "language": "en",
    "speed": 1.0
  }' \
  --output cloned_voice.wav
```

## Features
- No DeepSpeed dependency
- Simple Flask API
- Automatic audio preprocessing
- Support for URL-based reference audio
- Multi-language support
- Adjustable speech speed
- Docker containerized
- Error handling and validation
