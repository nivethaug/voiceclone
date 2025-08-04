from flask import Flask, request, jsonify, Response
import uuid
from predict import VoiceCloner

app = Flask(__name__)
voice_cloner = VoiceCloner()


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})


@app.route('/clone', methods=['POST'])
def clone_voice():
    try:
        data = request.get_json()

        text = data.get('text', '')
        speaker_wav = data.get('speaker_wav', '')  # URL to reference audio
        language = data.get('language', 'en')
        speed = data.get('speed', 1.0)

        if not text or not speaker_wav:
            return jsonify({"error": "Missing text or speaker_wav"}), 400

        output_path = voice_cloner.synthesize(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            speed=speed
        )

        with open(output_path, 'rb') as f:
            audio_data = f.read()

        return Response(
            audio_data,
            mimetype="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=cloned_voice_{uuid.uuid4().hex[:8]}.wav"
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# No app.run() here to comply with serverless environment
