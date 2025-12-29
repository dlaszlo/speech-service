import io
import struct
import logging
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Union
import av

from .config import (
    AUDIO_BITRATE_MP3,
    AUDIO_BITRATE_AAC,
    AUDIO_BITRATE_OPUS
)

logger = logging.getLogger(__name__)

class AudioEncoder(ABC):
    """Base class for audio encoders."""
    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate

    @abstractmethod
    def get_mime_type(self) -> str:
        """Return the MIME type for this format."""
        pass

    @abstractmethod
    def create_header(self) -> Optional[bytes]:
        """Create format header if needed. Return None if not applicable."""
        pass

    @abstractmethod
    def encode_chunk(self, audio_array: Union[np.ndarray, object]) -> bytes:
        """Encode a single audio chunk."""
        pass

    @abstractmethod
    def finalize(self) -> Optional[bytes]:
        """Return any final bytes needed to close the stream."""
        pass

    def _to_pcm16(self, audio_array) -> np.ndarray:
        """Convert float32 audio array/tensor to 16-bit PCM numpy array."""
        if hasattr(audio_array, 'numpy'):
            audio_array = audio_array.numpy()
        
        return (audio_array * 32767).clip(-32768, 32767).astype(np.int16)


class PCMEncoder(AudioEncoder):
    """Raw 16-bit PCM encoder."""
    def get_mime_type(self) -> str:
        return "audio/pcm"

    def create_header(self) -> Optional[bytes]:
        return None

    def encode_chunk(self, audio_array) -> bytes:
        return self._to_pcm16(audio_array).tobytes()

    def finalize(self) -> Optional[bytes]:
        return None


class WAVEncoder(AudioEncoder):
    """WAV format encoder with streaming header support."""
    def get_mime_type(self) -> str:
        return "audio/wav"

    def create_header(self) -> bytes:
        """Create a 44-byte WAV header for CD-quality audio (16-bit PCM, Mono)."""
        num_channels = 1
        bits_per_sample = 16
        byte_rate = self.sample_rate * num_channels * (bits_per_sample // 8)
        block_align = num_channels * (bits_per_sample // 8)
        
        header = b'RIFF'
        header += struct.pack('<I', 0)  # ChunkSize (0 for streaming)
        header += b'WAVE'
        header += b'fmt '
        header += struct.pack('<I', 16)  # Subchunk1Size
        header += struct.pack('<H', 1)   # AudioFormat (PCM)
        header += struct.pack('<H', num_channels)
        header += struct.pack('<I', self.sample_rate)
        header += struct.pack('<I', byte_rate)
        header += struct.pack('<H', block_align)
        header += struct.pack('<H', bits_per_sample)
        header += b'data'
        header += struct.pack('<I', 0)  # Subchunk2Size
        
        return header

    def encode_chunk(self, audio_array) -> bytes:
        return self._to_pcm16(audio_array).tobytes()

    def finalize(self) -> Optional[bytes]:
        return None


class PyAVEncoder(AudioEncoder):
    """Base class for encoders using PyAV (FFmpeg bindings)."""
    def __init__(self, sample_rate: int, format_name: str, codec_name: str, bitrate: Optional[int] = None):
        super().__init__(sample_rate)
        self.output_io = io.BytesIO()
        self.container = av.open(self.output_io, mode='w', format=format_name)
        
        self.stream = self.container.add_stream(codec_name, rate=sample_rate)
        # Fix for modern PyAV: set properties on codec_context
        # Use layout instead of channels as channels is often read-only
        self.stream.codec_context.layout = 'mono'
        
        if bitrate:
            self.stream.codec_context.bit_rate = bitrate * 1000

    def encode_chunk(self, audio_array) -> bytes:
        pcm16 = self._to_pcm16(audio_array)
        
        # Create frame from numpy array
        frame = av.AudioFrame.from_ndarray(pcm16.reshape(1, -1), format='s16', layout='mono')
        frame.sample_rate = self.sample_rate
        
        output_bytes = b''
        for packet in self.stream.encode(frame):
            self.container.mux(packet)
            output_bytes += self.output_io.getvalue()
            self.output_io.seek(0)
            self.output_io.truncate()
            
        return output_bytes

    def finalize(self) -> bytes:
        output_bytes = b''
        # Flush encoder
        for packet in self.stream.encode(None):
            self.container.mux(packet)
            
        self.container.close()
        
        output_bytes += self.output_io.getvalue()
        self.output_io.seek(0)
        self.output_io.truncate()
        return output_bytes


class MP3Encoder(PyAVEncoder):
    def __init__(self, sample_rate: int):
        super().__init__(sample_rate, format_name='mp3', codec_name='libmp3lame', bitrate=AUDIO_BITRATE_MP3)

    def get_mime_type(self) -> str:
        return "audio/mpeg"

    def create_header(self) -> Optional[bytes]:
        return None


class AACEncoder(PyAVEncoder):
    def __init__(self, sample_rate: int):
        # ADTS is the streaming format for AAC
        super().__init__(sample_rate, format_name='adts', codec_name='aac', bitrate=AUDIO_BITRATE_AAC)

    def get_mime_type(self) -> str:
        return "audio/aac"

    def create_header(self) -> Optional[bytes]:
        return None


class OpusEncoder(PyAVEncoder):
    def __init__(self, sample_rate: int):
        # Opus in Ogg container for streaming
        super().__init__(sample_rate, format_name='ogg', codec_name='libopus', bitrate=AUDIO_BITRATE_OPUS)

    def get_mime_type(self) -> str:
        return "audio/ogg"

    def create_header(self) -> Optional[bytes]:
        return None


class FLACEncoder(PyAVEncoder):
    def __init__(self, sample_rate: int):
        super().__init__(sample_rate, format_name='flac', codec_name='flac')

    def get_mime_type(self) -> str:
        return "audio/flac"

    def create_header(self) -> Optional[bytes]:
        return None


def get_encoder(format_name: str, sample_rate: int) -> AudioEncoder:
    """Factory function to get the appropriate encoder."""
    encoders = {
        "pcm": PCMEncoder,
        "wav": WAVEncoder,
        "mp3": MP3Encoder,
        "aac": AACEncoder,
        "opus": OpusEncoder,
        "flac": FLACEncoder,
    }
    
    if format_name not in encoders:
        logger.error(f"Unsupported audio format: {format_name}")
        raise ValueError(f"Unsupported audio format: {format_name}")
        
    return encoders[format_name](sample_rate)
