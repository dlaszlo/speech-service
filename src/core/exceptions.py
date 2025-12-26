class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass

class ModelNotLoadedError(ServiceError):
    """Raised when an operation is attempted but the required model is not loaded."""
    pass

class TranscriptionError(ServiceError):
    """Raised when STT transcription fails."""
    pass

class SynthesisError(ServiceError):
    """Raised when TTS synthesis fails."""
    pass

class TimeoutError(ServiceError):
    """Raised when an operation times out."""
    pass
