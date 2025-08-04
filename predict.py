import os
import tempfile
import requests
import torch
from TTS.api import TTS
import soundfile as sf
import librosa
import numpy as np


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

    def preprocess_audio(self, audio_path, target_sr=22050, max_duration=30):
        """Preprocess reference audio"""
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

    def synthesize(self, text, speaker_wav, language="en", speed=1.0):
        """Generate cloned voice audio"""
        try:
            # Download reference audio if URL provided
            if speaker_wav.startswith(('http://', 'https://')):
                speaker_wav = self.download_audio(speaker_wav)

            # Preprocess reference audio
            processed_speaker_wav = self.preprocess_audio(speaker_wav)

            # Generate output path
            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name

            # Synthesize speech using TTS model
            self.tts.tts_to_file(
                text=text,
                speaker_wav=processed_speaker_wav,
                language=language,
                file_path=output_path,
                speed=speed
            )

            # Cleanup temporary files
            if speaker_wav != processed_speaker_wav:
                os.unlink(speaker_wav)
            os.unlink(processed_speaker_wav)

            return output_path

        except Exception as e:
            raise Exception(f"Voice synthesis failed: {str(e)}")


# Usage example
if __name__ == "__main__":
    cloner = VoiceCloner()

    # Test synthesis
    output = cloner.synthesize(
        text="Hello, this is a test of voice cloning technology.",
        speaker_wav="https://example.com/reference_voice.wav",
        language="en"
    )

    print(f"Generated audio saved to: {output}")
