from flask import Flask, request, jsonify, send_file
import os
import tempfile
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
        
        # Extract parameters
        text = data.get('text', '')
        speaker_wav = data.get('speaker_wav', '')  # URL to reference audio
        language = data.get('language', 'en')
        speed = data.get('speed', 1.0)
        
        if not text or not speaker_wav:
            return jsonify({"error": "Missing text or speaker_wav"}), 400
        
        # Generate audio
        output_path = voice_cloner.synthesize(
            text=text,
            speaker_wav=speaker_wav,
            language=language,
            speed=speed
        )
        
        return send_file(output_path, as_attachment=True, 
                        download_name=f"cloned_voice_{uuid.uuid4().hex[:8]}.wav")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)