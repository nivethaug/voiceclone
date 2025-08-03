import sys
import traceback
print("=== Starting rp_handler.py ===", file=sys.stderr)
try:
    import io
    import os
    import argparse
    import runpod
    from runpod.serverless.utils.rp_validator import validate
    from runpod.serverless.utils.rp_upload import upload_in_memory_object
    from runpod.serverless.utils import rp_download, rp_cleanup
    import predict
    from rp_schema import INPUT_SCHEMA
    from scipy.io.wavfile import write
    print("=== Imports successful ===", file=sys.stderr)
except Exception:
    print("=== Import error ===", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)


# Model params
MODEL_DIR = os.getenv("WORKER_MODEL_DIR", "/model")


def upload_audio(wav, sample_rate, key):
    """Uploads audio to S3 bucket if configured, otherwise returns base64."""
    wav_io = io.BytesIO()
    write(wav_io, sample_rate, wav)

    # Upload to S3 if endpoint set
    if os.environ.get('BUCKET_ENDPOINT_URL'):
        print(f"=== Uploading {key} to S3 ===", file=sys.stderr)
        return upload_in_memory_object(
            key,
            wav_io.getvalue(),
            bucket_creds={
                "endpointUrl": os.environ.get('BUCKET_ENDPOINT_URL'),
                "accessId": os.environ.get('BUCKET_ACCESS_KEY_ID'),
                "accessSecret": os.environ.get('BUCKET_SECRET_ACCESS_KEY'),
            }
        )
    print("=== Returning base64 audio ===", file=sys.stderr)
    return wav_io.getvalue().decode('UTF-8')


def run(job):
    print(f"=== run() invoked for job {job.get('id')} ===", file=sys.stderr)
    try:
        job_input = job.get('input', {})
        validated = validate(job_input, INPUT_SCHEMA)
        if 'errors' in validated:
            print(f"=== Validation errors: {validated['errors']} ===", file=sys.stderr)
            return {"error": validated['errors']}
        data = validated['validated_input']

        # Download reference voice files
        for k, v in data.get("voice", {}).items():
            print(f"=== Downloading voice[{k}] from {v} ===", file=sys.stderr)
            files = rp_download.download_files_from_urls(job['id'], [v])
            data["voice"][k] = files[0]

        print("=== Running model inference ===", file=sys.stderr)
        wave, sr = MODEL.predict(
            language=data["language"],
            speaker_wav=data["voice"],
            text=data["text"],
            gpt_cond_len=data.get("gpt_cond_len", 7),
            max_ref_len=data.get("max_ref_len", 10),
            speed=data.get("speed", 1.0),
            enhance_audio=data.get("enhance_audio", True)
        )
        print("=== Inference complete ===", file=sys.stderr)

        print("=== Uploading audio ===", file=sys.stderr)
        audio_url = upload_audio(wave, sr, f"{job['id']}.wav")
        rp_cleanup.clean(['input_objects'])
        print("=== run() completed successfully ===", file=sys.stderr)
        return {"audio": audio_url}

    except Exception:
        print("=== run() error ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {"error": "Internal server error"}


if __name__ == "__main__":
    try:
        print("=== Initializing Predictor ===", file=sys.stderr)
        MODEL = predict.Predictor(model_dir=MODEL_DIR)
        MODEL.setup()
        print("=== Predictor setup complete ===", file=sys.stderr)
    except Exception:
        print("=== Predictor initialization error ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    try:
        print("=== Starting runpod serverless ===", file=sys.stderr)
        runpod.serverless.start({"handler": run})
    except Exception:
        print("=== runpod.serverless.start error ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
