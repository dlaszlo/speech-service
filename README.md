# Speech Service (STT & TTS)

This project provides a local, Dockerized REST API with OpenAI compatible endpoints for both **Speech-to-Text (STT)** and **Text-to-Speech (TTS)**.

## Features

*   **STT**: Powered by `Faster-Whisper` for transcription.
*   **TTS**: Powered by `Kokoro-82M` for speech synthesis.
*   **Multi-Platform Support**: Optimized Docker images for **NVIDIA GPU**, **x86 CPU**, and **ARM64 CPU** (Raspberry Pi 4, Apple Silicon).
*   **OpenAI API Compatibility**: Provides `/v1/audio/transcriptions` (STT) and `/v1/audio/speech` (TTS) endpoints.
*   **Easy Deployment**: Simplified setup using `docker-compose`.
*   **Dynamic Model Management**: Load models on-the-fly via REST endpoints.

## Recommended Models

### Speech-to-Text (STT)
*   `Systran/faster-whisper-large-v3`: Best quality, multilingual.
*   `Systran/faster-distil-whisper-small.en`: Good quality, English-only, faster.

### Text-to-Speech (TTS)
*   `Kokoro-82M` is used by default via the `kokoro` library. The language is configured via an environment variable.

## Prerequisites

*   **Docker**: Ensure Docker is installed and running.
*   **Docker Compose**: Part of modern Docker Desktop installations.
*   **NVIDIA Container Toolkit** (for GPU support): If you wish to use a GPU, you must install the toolkit. [Official Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

### System Dependencies (Local Run Only)

If you plan to run the application or tests locally (outside Docker), you must install the following system libraries:

*   **Linux (Debian/Ubuntu)**:
    ```bash
    sudo apt-get update && sudo apt-get install -y ffmpeg espeak-ng
    ```
*   **macOS**:
    ```bash
    brew install ffmpeg espeak
    ```
*   **Windows**:
    *   Install `ffmpeg` and ensure it's in your PATH.
    *   Install `espeak-ng` and ensure it's in your PATH (and `PHONEMIZER_ESPEAK_LIBRARY` env var might be needed).

## How to Run

Using `docker-compose` is the recommended way to run this service.

### Running Locally (Without Docker)

If you prefer to run the service directly on your host system:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/dlaszlo/speech-service.git
    cd speech-service
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements/cpu.txt
    ```

4.  **Set environment variables and start the server:**
    ```bash
    export STT_MODEL_NAME=Systran/faster-distil-whisper-small.en
    export STT_COMPUTE_TYPE=int8
    export TTS_MODEL_NAME=hexgrad/Kokoro-82M
    export TTS_LANG_CODE=a
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
    ```

Or use the provided helper script:
```bash
./bin/start.sh
```

### Running with Docker Compose

### 1. Configure the Service in `docker-compose.yml`

Create or edit your `docker-compose.yml` file and select the appropriate service configuration for your hardware.

#### Option 1: NVIDIA GPU (x86_64)

```yaml
services:
  speech-service:
    image: dlaszlo/speech-service:gpu-latest
    container_name: speech-service
    ports:
      - "8000:8000"
    volumes:
      - huggingface_cache:/data/huggingface
    environment:
      - STT_MODEL_NAME=Systran/faster-distil-whisper-small.en
      # Compute type: float16 or int8_float16 for GPU recommended
      - STT_COMPUTE_TYPE=int8_float16
      - TTS_MODEL_NAME=hexgrad/Kokoro-82M
      - TTS_LANG_CODE=a
      - HF_HOME=/data/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  huggingface_cache:
    driver: local
```

#### Option 2: CPU (x86_64 & ARM64)

The CPU image supports both x86_64 and ARM64 (Raspberry Pi / Apple Silicon) automatically.

```yaml
services:
  speech-service:
    image: dlaszlo/speech-service:cpu-latest
    container_name: speech-service
    ports:
      - "8000:8000"
    volumes:
      - huggingface_cache:/data/huggingface
    environment:
      - STT_MODEL_NAME=Systran/faster-distil-whisper-small.en
      # Compute type: int8 usually works well on ARM too
      - STT_COMPUTE_TYPE=int8
      - TTS_MODEL_NAME=hexgrad/Kokoro-82M
      - TTS_LANG_CODE=a
      - HF_HOME=/data/huggingface
    restart: unless-stopped

volumes:
  huggingface_cache:
    driver: local
```

## API Usage

The API is available at `http://localhost:8000`.

### Health Check

Check if the service is running and what STT model is loaded.

```bash
curl http://localhost:8000/health
```

### Speech-to-Text (STT)

#### Transcribe an Audio File
This endpoint is compatible with the OpenAI STT API.

 ```bash
  curl -X POST "http://localhost:8000/v1/audio/transcriptions" \
      -H "Content-Type: multipart/form-data" \
      -F "file=@test_speech.wav" \
      -F "model=Systran/faster-distil-whisper-small.en"
  ```

**Response:**
```json
{"text":"This is the transcribed text from the audio file."}
```

#### Dynamically Load a Different STT Model
You can switch the STT model at runtime without restarting the container.

```bash
curl -X POST "http://localhost:8000/v1/models/stt/download" \
     -H "Content-Type: application/json" \
     -d '{"model_id": "ctranslate2-expert/faster-whisper-medium.en"}'
```

 ### Text-to-Speech (TTS)

 #### Generate Speech from Text
 This endpoint is compatible with OpenAI TTS API. It generates audio in various formats.

```bash
    curl -X POST "http://localhost:8000/v1/audio/speech" \
        -H "Content-Type: application/json" \
        -d '{"model": "hexgrad/Kokoro-82M", "input": "The quick brown fox jumps over the lazy dog. This is a test of the English text to speech generation.", "voice": "af_sarah", "response_format": "mp3", "speed": 1.0}' \
        --output test_speech.mp3
```

**Request Parameters:**
* `model` (Required): The model to use (e.g., `hexgrad/Kokoro-82M`).
* `input` (Required): The text to be synthesized. Maximum length: 4096 characters.
* `voice` (Required): The voice to use (e.g., `af_sarah`, `af_heart`, `am_michael`, etc.).
* `response_format` (Optional): The audio format. Supported formats: `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm`. Default: `mp3`.
* `speed` (Optional): The speed of generated audio. Range: 0.25 to 4.0. Default: 1.0.
  -  Values below 1.0 produce slower speech (e.g., 0.5 = half speed, 0.25 = quarter speed).
  -  Values above 1.0 produce faster speech (e.g., 2.0 = double speed, 4.0 = quadruple speed).
* `stream_format` (Optional): The streaming format. Supported: `audio` (default), `sse` (Server-Sent Events).
* `instructions` (Optional): Additional voice control instructions.
  -  **Note**: This parameter is accepted for OpenAI compatibility but is **not supported**.

#### Dynamically Load a Different TTS Model/Language
You can switch the TTS language or model version at runtime.

```bash
 curl -X POST "http://localhost:8000/v1/models/tts/download" \
      -H "Content-Type: application/json" \
      -d '{"lang_code": "b", "model_id": "hexgrad/Kokoro-82M"}'
 ```
*   `lang_code`: The language code (e.g., `b` for British English).
*   `model_id`: (Optional) The Hugging Face model repository ID.

## Testing

## Testing

The project uses `pytest` for testing. The tests run **in-process** using `FastAPI TestClient`, so you **do not** need to start the server manually before running them.

 The tests cover:
 *   **STT**: Transcription validation and edge cases.
 *   **TTS**: Audio generation for all supported formats and streaming (Chunked & SSE).
 *   **Edge Cases**: Error handling, invalid inputs, and boundary conditions.

### Quick Run
The easiest way to run the full test suite (handling virtualenv and dependencies automatically) is:

```bash
./bin/run_tests.sh
```

### Manual Test Execution

1.  **Install Test Dependencies**:
    ```bash
    pip install -r requirements/tests.txt
    ```

2.  **Run All Tests**:
    ```bash
    pytest tests/
    ```

3.  **Run Specific Tests**:
    *   **STT Tests**:
        ```bash
        pytest tests/test_stt.py
        pytest tests/test_stt_edge_cases.py
        ```
    *   **TTS Basic Tests**:
        ```bash
        pytest tests/test_tts_basic.py
        ```
    *   **TTS Streaming Tests**:
        ```bash
        pytest tests/test_tts_audio_streaming.py
        pytest tests/test_tts_sse_streaming.py
        ```

## Links

*   **Docker Hub**: [dlaszlo/speech-service](https://hub.docker.com/r/dlaszlo/speech-service)
*   **GitHub Repository**: [dlaszlo/speech-service](https://github.com/dlaszlo/speech-service)
*   **OpenAI: Text to speech**: [OpenAI - Text to speech API](https://platform.openai.com/docs/guides/text-to-speech)
*   **OpenAI: Speech to text**: [OpenAI - Speech to text API](https://platform.openai.com/docs/guides/speech-to-text)

