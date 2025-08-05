import torch
import soundfile as sf
from transformers import AutoModel
import tempfile
import base64
import os
import numpy as np
import traceback

class VoiceCloner:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Pass HF_TOKEN environment variable as token parameter to access gated model
        hf_token = os.getenv("HF_TOKEN", None)
        self.model = AutoModel.from_pretrained(
            "ai4bharat/IndicF5",
            trust_remote_code=True,
            token=hf_token
        ).to(self.device)

    def save_base64_audio(self, base64_str):
        try:
            audio_bytes = base64.b64decode(base64_str)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(audio_bytes)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            error_msg = f"Base64 decoding failed: {str(e)}\n{traceback.format_exc()}"
            return {"error": error_msg}

    def is_base64(self, s):
        try:
            if isinstance(s, str):
                base64.b64decode(s, validate=True)
                return True
            return False
        except Exception:
            return False

    def synthesize(self, text, speaker_wav=None, ref_text=None, language="ta", speed=1.0):
        if not speaker_wav or not ref_text:
            return {"error": "speaker_wav and ref_text are required for IndicF5 synthesis"}

        try:
            output_audio = self.model(
                text,
                ref_audio_path=speaker_wav,
                ref_text=ref_text
            )

            if output_audio.dtype == np.int16:
                output_audio = output_audio.astype(np.float32) / 32768.0

            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            sf.write(output_path, np.array(output_audio, dtype=np.float32), samplerate=24000)

            return output_path

        except Exception as e:
            error_msg = f"Voice synthesis failed: {str(e)}\n{traceback.format_exc()}"
            return {"error": error_msg}
