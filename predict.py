import os
import tempfile
import traceback
import requests
import torch
from TTS.api import TTS
import soundfile as sf
import librosa
import numpy as np
import base64

class VoiceCloner:

    def __init__(self):
        # Initialize XTTS v2 model with GPU support if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = TTS(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            gpu=(self.device == "cuda")
        )

    def download_audio(self, url):
        """Download audio file from URL"""
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to download audio from {url}")
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name

    def save_base64_audio(self, base64_str):
        """Decode base64 string and save as wav file"""
        try:
            audio_bytes = base64.b64decode(base64_str)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.write(audio_bytes)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            error_msg = f"Base64 decoding failed: {str(e)}\n{traceback.format_exc()}"
            return {"error": error_msg}

    def preprocess_audio(self, audio_path, target_sr=22050, max_duration=30):
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=target_sr)
            # Trim silence
            audio, _ = librosa.effects.trim(audio, top_db=20)
            # Limit duration
            if len(audio) > max_duration * target_sr:
                audio = audio[:max_duration * target_sr]
            # Normalize
            audio = audio / np.max(np.abs(audio))
            # Save processed audio
            processed_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
            sf.write(processed_path, audio, target_sr)
            return processed_path
        except Exception as e:
            error_msg = f"Preprocess synthesis failed: {str(e)}\n{traceback.format_exc()} Path: {audio_path}"
            return {"error": error_msg}

    def synthesize(self, text, speaker_wav, language="en", speed=1.0):
        """
        speaker_wav can be: 
        - a local file path (string)
        - a URL (string starting with http or https)
        - a base64 string (automatically detected)
        """
        processed_speaker_wav = None
        try:
            # Detect type and fetch input as local file
            if isinstance(speaker_wav, str):
                if speaker_wav.startswith(('http://', 'https://')):
                    speaker_wav = self.download_audio(speaker_wav)
                elif self.is_base64(speaker_wav):
                    tmp = self.save_base64_audio(speaker_wav)
                    if isinstance(tmp, dict) and "error" in tmp:
                        return tmp
                    speaker_wav = tmp
                # Otherwise, assume it's a local file path (as before)
            else:
                return {"error": "Unsupported speaker_wav input type."}

            processed_result = self.preprocess_audio(speaker_wav)
            if isinstance(processed_result, dict) and "error" in processed_result:
                return processed_result
            processed_speaker_wav = processed_result

            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name

            self.tts.tts_to_file(
                text=text,
                speaker_wav=processed_speaker_wav,
                language=language,
                file_path=output_path,
                speed=speed
            )

            return output_path
        except Exception as e:
            error_msg = f"Voice synthesis failed: {str(e)}\n{traceback.format_exc()}"
            return {"error": error_msg}
        finally:
            # Cleanup temporary files
            try:
                if processed_speaker_wav and speaker_wav != processed_speaker_wav and os.path.exists(processed_speaker_wav):
                    os.unlink(processed_speaker_wav)
                if speaker_wav and speaker_wav.startswith('/tmp') and os.path.exists(speaker_wav):
                    os.unlink(speaker_wav)
            except Exception:
                pass

    def is_base64(self, s):
        try:
            if isinstance(s, str):
                base64.b64decode(s, validate=True)
                return True
            return False
        except Exception:
            return False

