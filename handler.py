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

        # Read audio bytes
        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        # Clean up temp files
        os.remove(tmp_path)
        os.remove(output_path)

        # Encode to base64 for JSON response
        audio_b64 = base64.b64encode(audio_bytes).decode()

        return {
            "audio_filename": f"cloned_voice_{uuid.uuid4().hex[:8]}.wav",
            "audio_base64": audio_b64
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    runpod.serverless.start({
        "handler": handler,
        "concurrency_modifier": lambda c: 1,
    })
