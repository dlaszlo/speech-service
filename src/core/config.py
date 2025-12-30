# --- Configuration Constants ---
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# --- Timeout Constants ---
TRANSCRIPTION_TIMEOUT_SECONDS = 300  # 5 minutes
TRANSCRIPTION_PROCESSING_TIMEOUT_SECONDS = 180  # 3 minutes for segment processing
TTS_SYNTHESIS_TIMEOUT_SECONDS = 120  # 2 minutes
MODEL_LOAD_TIMEOUT_SECONDS = 600     # 10 minutes
TTS_SAMPLE_RATE = 24000

# Audio encoding bitrates (kbps)
AUDIO_BITRATE_MP3 = 128
AUDIO_BITRATE_AAC = 128
AUDIO_BITRATE_OPUS = 96

# --- Default Model Configuration ---
DEFAULT_STT_MODEL = "Systran/faster-distil-whisper-small.en"
DEFAULT_STT_COMPUTE_TYPE = "auto"
DEFAULT_TTS_MODEL = "hexgrad/Kokoro-82M"
DEFAULT_TTS_LANG_CODE = "a"
DEFAULT_DEVICE = "cpu"  # Fallback if detection fails or for override check
