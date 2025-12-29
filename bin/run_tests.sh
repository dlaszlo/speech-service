#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."
VENV_DIR="$PROJECT_ROOT/venv"

echo "========================================================"
echo "SPEECH SERVICE TEST SUITE SETUP"
echo "========================================================"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
pip install -q -r "$PROJECT_ROOT/requirements/tests.txt"
echo "Done!"

echo ""
echo "========================================================"
echo "STARTING SPEECH SERVICE TEST SUITE"
echo "========================================================"

# Check if server is running and healthy
HEALTH_URL="http://localhost:8000/health"
if ! curl -s "$HEALTH_URL" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo "Error: Server is not running or unhealthy at $HEALTH_URL"
    echo "Please start the server with: ./bin/start.sh"
    exit 1
fi

echo "Server is running and healthy"
echo ""

# Clean output directory
OUTPUT_DIR="$PROJECT_ROOT/tests/output"
echo "Cleaning output directory..."
rm -rf "$OUTPUT_DIR"/*
echo "Output directory cleaned."
echo ""

# Run pytest
echo "Running pytest..."
pytest tests/ -v --tb=short

echo ""
echo "========================================================"
echo "ALL TESTS PASSED SUCCESSFULLY!"
echo "========================================================"
exit 0
