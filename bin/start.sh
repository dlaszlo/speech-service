#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
VENV_DIR="$PROJECT_ROOT/venv"

echo "=========================================="
echo "Speech Service Local Server Setup"
echo "=========================================="

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install -q -r "$PROJECT_ROOT/requirements/cpu.txt"
echo "Done!"

echo ""
echo "Starting server..."
echo ""

cd "$PROJECT_ROOT"

export STT_MODEL_NAME=Systran/faster-distil-whisper-small.en
export STT_COMPUTE_TYPE=int8
export TTS_MODEL_NAME=hexgrad/Kokoro-82M
export TTS_LANG_CODE=a

python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000
