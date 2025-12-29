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
This endpoint is compatible with the OpenAI TTS API. It generates a WAV audio file.

 ```bash
  curl -X POST "http://localhost:8000/v1/audio/speech" \
      -H "Content-Type: application/json" \
      -d '{"model": "hexgrad/Kokoro-82M", "input": "The quick brown fox jumps over the lazy dog. This is a test of the English text to speech generation.", "voice": "af_sarah"}' \
      --output test_speech.wav
  ```
 *   `input`: The text to be synthesized.
 *   `voice`: The voice to use (e.g., `af_sarah`).
 *   `--output test_speech.wav`: Saves the resulting audio to a file named `test_speech.wav`.

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

You can use the provided Python scripts to quickly test the service:

1.  **TTS Test**: Generates a sample audio file.
    ```bash
    python tests/test_tts_service.py
    ```
2.  **STT Test**: Transcribes the previously generated audio file (requires running the TTS test first).
    ```bash
    python tests/test_stt_service.py
    ```
3.  **TTS Streaming Test**: Tests streaming TTS with SSE events.
    ```bash
    python tests/test_tts_service_streaming.py
    ```

## Links

*   **Docker Hub**: [dlaszlo/speech-service](https://hub.docker.com/r/dlaszlo/speech-service)
*   **GitHub Repository**: [dlaszlo/speech-service](https://github.com/dlaszlo/speech-service)

