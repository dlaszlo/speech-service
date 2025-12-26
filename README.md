# Speech Service (STT & TTS)

This project provides a local, Dockerized API for both **Speech-to-Text (STT)** and **Text-to-Speech (TTS)**.
*   **STT**: Uses **Faster-Whisper** (via CTranslate2) and Hugging Face Transformers to deliver an OpenAI REST API-compatible endpoint for transcription.
*   **TTS**: Uses the **Kokoro TTS** model to provide an efficient, OpenAI-compatible endpoint for speech synthesis.

## Features

*   **STT**: Powered by `Faster-Whisper` for transcription.
*   **TTS**: Powered by `Kokoro-82M` for speech synthesis.
*   **Multi-Platform Support**: Optimized Docker images for **NVIDIA GPU**, **x86 CPU**, and **ARM64 CPU** (Raspberry Pi 4, Apple Silicon).
*   **OpenAI API Compatibility**: Provides `/v1/audio/transcriptions` (STT) and `/v1/audio/speech` (TTS) endpoints.
*   **Easy Deployment**: Simplified setup using `docker-compose`.
*   **Dynamic Model Management**: Load models on-the-fly via REST endpoints.
*   **Persistent Model Cache**: Models are cached in a volume to prevent re-downloading.

## Recommended Models

### Speech-to-Text (STT)
This service is designed for `ctranslate2` compatible models.
*   `Systran/faster-whisper-large-v3` (Default): Best quality, multilingual.
*   `Systran/faster-whisper-medium.en`: Great quality, English-only, faster.

### Text-to-Speech (TTS)
*   `Kokoro-82M-v1.0-ONNX` is used by default via the `kokoro` library. The language is configured via an environment variable.

## Prerequisites

*   **Docker**: Ensure Docker is installed and running.
*   **Docker Compose**: Part of modern Docker Desktop installations.
*   **NVIDIA Container Toolkit** (for GPU support): If you wish to use a GPU, you must install the toolkit. [Official Installation Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

## How to Build

We provide a build script to generate Docker images for all supported platforms (GPU, CPU, ARM).

1.  **Check Version**: The current version is defined in the `VERSION` file.
2.  **Run Build Script**:
    ```bash
    ./build.sh
    ```
    This script will:
    *   Build images for **GPU**, **CPU**, and **ARM**.
    *   Tag them with the version number (e.g., `speech-service:gpu-0.1.0`) and `latest` (e.g., `speech-service:gpu-latest`).

## How to Run

Using `docker-compose` is the recommended way to run this service.

### 1. Configure the Service in `docker-compose.yml`

Open `docker-compose.yml` and select the appropriate service configuration for your hardware.

*   **Option 1: NVIDIA GPU (x86_64)**
    *   Uncomment the "OPTION 1" section.
    *   Ensure the image is set to `speech-service:gpu-latest`.
    *   Ensure the `deploy` section with `nvidia` driver is active.
    *   Recommended `STT_COMPUTE_TYPE`: `float16` or `int8_float16`.

*   **Option 2: CPU (x86_64)**
    *   Uncomment the "OPTION 2" section (Default).
    *   Ensure the image is set to `speech-service:cpu-latest`.
    *   Recommended `STT_COMPUTE_TYPE`: `int8`.

*   **Option 3: ARM CPU (Raspberry Pi / Apple Silicon)**
    *   Uncomment the "OPTION 3" section.
    *   Ensure the image is set to `speech-service:arm-latest`.
    *   Recommended `STT_COMPUTE_TYPE`: `int8`.

### 2. Start the Container

Once you have configured `docker-compose.yml`, run:

```bash
docker-compose up -d
```
The first time you run this, it will start the container. The model download will happen automatically when the container starts (or when you first use the API), caching files in the `./data` directory (mapped volume).

### 3. Stop the Service

To stop the container run:
```bash
docker-compose down
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
     -F "file=@/path/to/your/audio.mp3" \
     -F "model=whisper-1"
```
*   `file=@/path/to/your/audio.mp3`: **Important:** Replace with the actual path to your audio file.

**Response:**
```json
{"text":"This is the transcribed text from the audio file."}
```

#### Dynamically Load a Different STT Model
You can switch the STT model at runtime without restarting the container.

```bash
curl -X POST "http://localhost:8000/v1/models/download" \
     -H "Content-Type: application/json" \
     -d '{"model_name": "ctranslate2-expert/faster-whisper-medium.en"}'
```

### Text-to-Speech (TTS)

#### Generate Speech from Text
This endpoint is compatible with the OpenAI TTS API. It generates a WAV audio file.

```bash
curl -X POST "http://localhost:8000/v1/audio/speech" \
     -H "Content-Type: application/json" \
     -d 
     {
           "model": "kokoro-82M-v1.0-ONNX",
           "input": "Hello, this is a test of the local text to speech service.",
           "voice": "af_heart"
         }
     --output speech.wav
```
*   `input`: The text to be synthesized.
*   `voice`: The voice to use (e.g., `af_heart`).
*   `--output speech.wav`: Saves the resulting audio to a file named `speech.wav`.

#### Dynamically Load a Different TTS Model/Language
You can switch the TTS language or model version at runtime.

```bash
curl -X POST "http://localhost:8000/v1/models/tts/download" \
     -H "Content-Type: application/json" \
     -d 
     {
           "lang_code": "b",
           "model_id": "hexgrad/Kokoro-82M-v1.0-ONNX"
         }
```
*   `lang_code`: The language code (e.g., `b` for British English).
*   `model_id`: (Optional) The Hugging Face model repository ID.

## Viewing Logs

You can monitor the service's output, including model loading progress and API requests, using:
```bash
docker-compose logs -f
```