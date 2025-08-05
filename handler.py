import runpod
import uuid
import requests
import tempfile
import os
import base64
from predict import VoiceCloner

voice_cloner = VoiceCloner()

def is_base64(sb):
    try:
        if isinstance(sb, str):
            # Try to decode base64, ignoring whitespace/newlines
            base64.b64decode(sb, validate=True)
            return True
        return False
    except Exception:
        return False

async def handler(event):
    input_data = event.get("input", {})
    text = input_data.get('text', '')
    speaker_wav_input = input_data.get('speaker_wav', '')
    language = input_data.get('language', 'en')
    speed = input_data.get('speed', 1.0)

    if not text or not speaker_wav_input:
        return {"error": "Missing text or speaker_wav"}

    tmp_path = None
    output_path = None

    try:
        # Determine if speaker_wav_input is URL or base64 audio
        if speaker_wav_input.startswith(('http://', 'https://')):
            # It is a URL - download audio and save to tmp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                r = requests.get(speaker_wav_input)
                tmp_file.write(r.content)
                tmp_path = tmp_file.name

        elif is_base64(speaker_wav_input):
            # It is base64-encoded audio data - decode and save to tmp file
            audio_bytes = base64.b64decode(speaker_wav_input)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_path = tmp_file.name

        else:
            return {"error": "speaker_wav must be a valid URL or base64 audio string"}

        # Generate voice output
        output_path = voice_cloner.synthesize(
            text=text,
            speaker_wav=tmp_path,
            language=language,
            speed=speed
        )

        if isinstance(output_path, dict) and "error" in output_path:
            return output_path

        # Read the generated audio bytes
        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        audio_b64 = base64.b64encode(audio_bytes).decode()

        return {
            "audio_filename": f"cloned_voice_{uuid.uuid4().hex[:8]}.wav",
            "audio_base64": audio_b64
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if tmp_path and isinstance(tmp_path, str) and os.path.exists(tmp_path):
            os.remove(tmp_path)
        if output_path and isinstance(output_path, str) and os.path.exists(output_path):
            os.remove(output_path)

runpod.serverless.start({"handler": handler})
