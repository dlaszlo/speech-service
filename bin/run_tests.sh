#!/bin/bash

# run_tests.sh
# Runs all TTS and STT tests in sequence.
# Usage: ./run_tests.sh

echo "========================================================"
echo "STARTING SPEECH SERVICE TEST SUITE"
echo "========================================================"

# Function to run a test and check its exit code
run_test() {
    echo "--------------------------------------------------------"
    echo "Running: $1"
    python3 "$1"
    if [ $? -eq 0 ]; then
        echo "✅ PASS: $1"
    else
        echo "❌ FAIL: $1"
        exit 1
    fi
}

# 1. Basic TTS Tests (Non-streaming)
echo ""
echo ">>> CATEGORY 1: Basic TTS (Non-streaming)"
run_test "tests/test_tts_wav.py"
run_test "tests/test_tts_pcm.py"
run_test "tests/test_tts_mp3.py"
run_test "tests/test_tts_aac.py"
run_test "tests/test_tts_opus.py"
run_test "tests/test_tts_flac.py"

# 2. Audio Streaming Tests (OpenAI Async Client)
echo ""
echo ">>> CATEGORY 2: Audio Streaming (Real-time)"
run_test "tests/test_tts_audio_wav.py"
run_test "tests/test_tts_audio_pcm.py"
run_test "tests/test_tts_audio_mp3.py"
run_test "tests/test_tts_audio_aac.py"
run_test "tests/test_tts_audio_opus.py"
run_test "tests/test_tts_audio_flac.py"

# 3. SSE Streaming Tests
echo ""
echo ">>> CATEGORY 3: SSE Streaming"
run_test "tests/test_tts_sse_wav.py"
run_test "tests/test_tts_sse_pcm.py"
run_test "tests/test_tts_sse_mp3.py"
run_test "tests/test_tts_sse_aac.py"
run_test "tests/test_tts_sse_opus.py"
run_test "tests/test_tts_sse_flac.py"

# 4. STT Tests
echo ""
echo ">>> CATEGORY 4: STT Transcription Support"
run_test "tests/test_stt_wav.py"
run_test "tests/test_stt_mp3.py"

echo ""
echo "========================================================"
echo "🎉 ALL TESTS PASSED SUCCESSFULLY!"
echo "========================================================"
exit 0
