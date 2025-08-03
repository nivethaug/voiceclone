#!/bin/bash
set -e

echo "Mode: $MODE_TO_RUN"

if [ "$MODE_TO_RUN" = "pod" ]; then
  python3 -u src/rp_handler.py
else
  runpod.serverless.start({"handler": handler})
fi
