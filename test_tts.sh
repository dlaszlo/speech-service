#!/bin/bash

# Check if the server is running (optional, just a warning)
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "WARNING: It does not appear that the server is running at http://localhost:8000."
    echo "Make sure you started it with the 'uvicorn src.main:app' command."
    echo "----------------------------------------------------------------"
fi

echo "Sending TTS Request..."
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "hexgrad/Kokoro-82M", "input": "The quick brown fox jumps over the lazy dog. This is a test of the English text to speech generation.", "voice": "af_sarah"}' \
  --output test_speech.wav

if [ $? -eq 0 ]; then
    echo ""
    echo "Success! Audio file saved: test_speech.wav"
else
    echo ""
    echo "Error occurred during the request."
fi
