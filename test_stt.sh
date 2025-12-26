#!/bin/bash

# Check if audio file exists (if not, we generate an empty one for testing, but better if it comes from TTS)
if [ ! -f "test_speech.wav" ]; then
    echo "Error: The 'test_speech.wav' file was not found. Run test_tts.sh first or create one."
    exit 1
fi

echo "Sending STT Request (Transcription)..."
curl http://localhost:8000/v1/audio/transcriptions \
  -F "file=@test_speech.wav" \
  -F "model=Systran/faster-distil-whisper-small.en"

if [ $? -eq 0 ]; then
    echo ""
    echo "Success! Response received."
else
    echo ""
    echo "Error occurred during the request."
fi