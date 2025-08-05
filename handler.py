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
            base64.b64decode(sb, validate=True)
            return True
        return False
    except Exception:
        return False

def chat_with_gpt(prompt):
    return "test"

async def handler(event):
    input_data = event.get("input", {})
    action = input_data.get("action", "clone")  # default to voice clone if not specified

    if action == "chat":
        prompt = input_data.get("prompt", "")
        if not prompt:
            return {"error": "Missing prompt for chat"}
        reply = chat_with_gpt(prompt)
        return {"response": reply}

    elif action == "clone":
        text = input_data.get('text', '')
        speaker_wav_input = input_data.get('speaker_wav', '')
        language = input_data.get('language', 'ta')  # default to Tamil, change if needed
        speed = input_data.get('speed', 1.0)
        speaker_id = input_data.get('speaker_id', 17)  # default female Tamil speaker
        style_id = input_data.get('style_id', 0)      # default style

        if not text:
            return {"error": "Missing text for synthesis"}

        tmp_path = None
        output_path = None

        try:
            # Determine if speaker_wav_input is URL or base64 audio (optional in this model)
            if speaker_wav_input:
                if speaker_wav_input.startswith(('http://', 'https://')):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        r = requests.get(speaker_wav_input)
                        tmp_file.write(r.content)
                        tmp_path = tmp_file.name
                elif is_base64(speaker_wav_input):
                    audio_bytes = base64.b64decode(speaker_wav_input)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_bytes)
                        tmp_path = tmp_file.name
                else:
                    return {"error": "speaker_wav must be a valid URL or base64 audio string"}
            else:
                tmp_path = None  # No speaker wav needed by default

            # Generate voice output
            output_path = voice_cloner.synthesize(
                text=text,
                speaker_wav=tmp_path,
                language=language,
                speed=speed,
                speaker_id=speaker_id,
                style_id=style_id
            )

            if isinstance(output_path, dict) and "error" in output_path:
                return output_path

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
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)

    else:
        return {"error": f"Unknown action '{action}'. Supported: 'chat', 'clone'"}

runpod.serverless.start({"handler": handler})
