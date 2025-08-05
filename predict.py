
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
        # Do NOT move IndicF5 model to device manually!
        hf_token = os.getenv("HF_TOKEN", None)

        # Load model safely
        self.model = AutoModel.from_pretrained(
            "ai4bharat/IndicF5",
            trust_remote_code=True,
            token=hf_token
        )

    def save_base64_audio(self, base64_str):
        try:
            audio_bytes = base64.b64decode(base64_str)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(audio_bytes)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            return {"error": f"Base64 decoding failed: {str(e)}\n{traceback.format_exc()}"}

    def is_base64(self, s):
        try:
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False

    def synthesize(self, text, speaker_wav=None, ref_text=None, language="ta", speed=1.0):
        if not speaker_wav or not ref_text:
            return {"error": "speaker_wav and ref_text are required for IndicF5 synthesis"}

        try:
            # Run inference (model handles device and processing internally)
            output_audio = self.model(
                text=text,
                ref_audio_path=speaker_wav,
                ref_text=ref_text
            )

            # Normalize if needed
            if output_audio.dtype == np.int16:
                output_audio = output_audio.astype(np.float32) / 32768.0

            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            sf.write(output_path, output_audio, samplerate=24000)

            return output_path

        except Exception as e:
            return {"error": f"Voice synthesis failed: {str(e)}\n{traceback.format_exc()}"}
