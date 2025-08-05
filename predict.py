import torch
import soundfile as sf
from transformers import AutoModel, AutoTokenizer
import tempfile
import base64
import os
import librosa
import numpy as np
import traceback

class VoiceCloner:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained("ai4bharat/vits_rasa_13", trust_remote_code=True)
        self.model = AutoModel.from_pretrained("ai4bharat/vits_rasa_13", trust_remote_code=True).to(self.device)

    def preprocess_audio(self, audio_path, target_sr=22050, max_duration=30):
        try:
            audio, sr = librosa.load(audio_path, sr=target_sr)
            audio, _ = librosa.effects.trim(audio, top_db=20)
            if len(audio) > max_duration * target_sr:
                audio = audio[:max_duration * target_sr]
            audio = audio / np.max(np.abs(audio))
            processed_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            sf.write(processed_path, audio, target_sr)
            return processed_path
        except Exception as e:
            error_msg = f"Preprocess synthesis failed: {str(e)}\n{traceback.format_exc()} Path: {audio_path}"
            return {"error": error_msg}

    def synthesize(self, text, speaker_wav=None, language="ta", speed=1.0, speaker_id=17, style_id=0):
        try:
            # Tokenize input text
            inputs = self.tokenizer(text=text, return_tensors="pt").to(self.device)

            # Generate audio with speaker and style parameters
            with torch.no_grad():
                outputs = self.model(
                    inputs["input_ids"],
                    speaker_id=torch.tensor([speaker_id]).to(self.device),
                    emotion_id=torch.tensor([style_id]).to(self.device)
                )

            audio_tensor = outputs.waveform.squeeze(0).cpu().float()
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            sf.write(output_path, audio_tensor.numpy(), self.model.config.sampling_rate)

            return output_path
        except Exception as e:
            error_msg = f"Voice synthesis failed: {str(e)}\n{traceback.format_exc()}"
            return {"error": error_msg}

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
