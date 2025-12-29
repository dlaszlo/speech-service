from fastapi import HTTPException


class TTSAPIError(HTTPException):
    """Base class for TTS API errors with structured response."""
    def __init__(self, detail: str, error_type: str = None, param: str = None, code: str = None):
        error_response = {
            "error": {
                "message": detail,
                "type": error_type or "api_error",
                "param": param,
                "code": code
            }
        }
        super().__init__(status_code=400, detail=error_response)


class InvalidVoiceError(TTSAPIError):
    def __init__(self, voice: str):
        super().__init__(
            detail=f"Invalid voice parameter: '{voice}'",
            error_type="invalid_request_error",
            param="voice",
            code="voice_not_found"
        )


class InvalidFormatError(TTSAPIError):
    def __init__(self, format: str):
        supported_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
        super().__init__(
            detail=f"Invalid response_format. Supported formats: {', '.join(supported_formats)}",
            error_type="invalid_request_error",
            param="response_format",
            code="invalid_format"
        )


class EmptyInputError(TTSAPIError):
    def __init__(self):
        super().__init__(
            detail="Input text cannot be empty",
            error_type="invalid_request_error",
            param="input",
            code="empty_input"
        )


class MaxLengthExceededError(TTSAPIError):
    def __init__(self, max_length: int = 4096):
        super().__init__(
            detail=f"Input text exceeds maximum length of {max_length} characters",
            error_type="invalid_request_error",
            param="input",
            code="context_length_exceeded"
        )


class InvalidModelError(TTSAPIError):
    def __init__(self, model: str):
        super().__init__(
            detail=f"Invalid model parameter: '{model}'",
            error_type="invalid_request_error",
            param="model",
            code="model_not_found"
        )
