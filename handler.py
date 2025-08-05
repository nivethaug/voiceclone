import runpod
import uuid
import requests
import tempfile
import os
import base64
from predict import VoiceCloner

voice_cloner = VoiceCloner()

async def handler(event):
    input_data = event.get("input", {})
    text = input_data.get('text', '')
    speaker_wav_url = input_data.get('speaker_wav', '')
    language = input_data.get('language', 'en')
    speed = input_data.get('speed', 1.0)

    if not text or not speaker_wav_url:
        return {"error": "Missing text or speaker_wav"}

    tmp_path = None
    output_path = None

    try:
        # Download speaker_wav
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            r = requests.get(speaker_wav_url)
            tmp_file.write(r.content)
            tmp_path = tmp_file.name

        # Generate voice output
        output_path = voice_cloner.synthesize(
            text=text,
            speaker_wav=tmp_path,
            language=language,
            speed=speed
        )

        # Handle errors from synthesize
        if isinstance(output_path, dict) and "error" in output_path:
            return output_path

        # Read audio bytes
        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        # Encode to base64 for JSON response
        audio_b64 = base64.b64encode(audio_bytes).decode()

        return {
            "audio_filename": f"cloned_voice_{uuid.uuid4().hex[:8]}.wav",
            "audio_base64": audio_b64
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        # Clean up temp files if they exist and are paths
        if tmp_path and isinstance(tmp_path, str) and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if output_path and isinstance(output_path, str) and os.path.exists(output_path):
            os.remove(output_path)

# Register the handler for Runpod serverless
runpod.serverless.start({"handler": handler})
