import io
import logging
import asyncio
import base64
import json
import soundfile as sf
import numpy as np
import struct

from ..core.tts_dependencies import get_tts_model_state
from ..core.exceptions import ModelNotLoadedError, SynthesisError, TimeoutError as ServiceTimeoutError
from ..core.config import TTS_SYNTHESIS_TIMEOUT_SECONDS, TTS_SAMPLE_RATE

logger = logging.getLogger(__name__)
tts_model_state = get_tts_model_state()

async def synthesize(text: str, voice: str, response_format: str = "wav") -> bytes:
    if not tts_model_state.pipeline:
        logger.error("TTS requested but no model is loaded.")
        raise ModelNotLoadedError("TTS model is not loaded.")

    try:
        audio_bytes = await asyncio.wait_for(
            asyncio.to_thread(_synthesize_sync, text, voice, response_format),
            timeout=TTS_SYNTHESIS_TIMEOUT_SECONDS
        )
        return audio_bytes

    except ModelNotLoadedError:
            raise
    except asyncio.TimeoutError as e:
        logger.error(f"TTS synthesis timed out after {TTS_SYNTHESIS_TIMEOUT_SECONDS} seconds: {e}")
        raise ServiceTimeoutError(f"Speech synthesis timed out after {TTS_SYNTHESIS_TIMEOUT_SECONDS} seconds")
    except Exception as e:
        logger.error(f"Error during speech synthesis wrapper: {e}", exc_info=True)
        raise SynthesisError(f"Speech synthesis failed: {str(e)}")

def _synthesize_sync(text: str, voice: str, response_format: str) -> bytes:
    try:
        logger.info(f"[TTS] Synthesizing speech: text_length={len(text)}, voice='{voice}', format='{response_format}'")

        generator = None
        all_audio_arrays = []

        try:
            logger.info("[TTS] Calling pipeline generator")
            generator = tts_model_state.pipeline(text, voice=voice)
            logger.info("[TTS] Consuming generator")
            
            for _, _, audio_array in generator:
                if audio_array is not None:
                    all_audio_arrays.append(audio_array)
                    
        except Exception as e:
            logger.error(f"Error during audio generation: {e}")
            raise
        finally:
            if generator is not None and hasattr(generator, 'close'):
                try:
                    generator.close()
                except Exception as close_error:
                    logger.warning(f"Error closing generator: {close_error}")

        if not all_audio_arrays:
            raise ValueError("Audio generation failed, received no audio output.")

        # Concatenate all audio chunks
        full_audio = np.concatenate(all_audio_arrays)
        logger.info(f"[TTS] Speech synthesized successfully: total_samples={len(full_audio)}. Encoding to {response_format}.")

        if response_format == "pcm":
            return _encode_audio(full_audio)
        else:
            # For non-streaming WAV, use soundfile to write a proper WAV file with correct length
            wav_io = io.BytesIO()
            sf.write(wav_io, full_audio, TTS_SAMPLE_RATE, format='WAV')
            wav_io.seek(0)
            return wav_io.read()

    except Exception as e:
        if isinstance(e, SynthesisError):
            raise e
        logger.error(f"Error during blocking speech synthesis: {e}", exc_info=True)
        raise SynthesisError(f"Internal synthesis error: {str(e)}")

async def synthesize_streaming(
    text: str,
    voice: str,
    response_format: str = "wav",
    stream_format: str = "audio",
    http_request=None
):
    """
    OpenAI compatible streaming TTS synthesis.
    """
    if not tts_model_state.pipeline:
        logger.error("TTS requested but no model is loaded.")
        raise ModelNotLoadedError("TTS model is not loaded.")

    logger.info(f"Starting streaming TTS synthesis: text_length={len(text)}, voice='{voice}', response_format='{response_format}', stream_format='{stream_format}'")

    pipeline = tts_model_state.pipeline
    try:
        generator = pipeline(text, voice=voice)  # type: ignore

        if stream_format == "sse":
            async def sse_generator():
                chunk_count = 0
                header_sent = False
                
                try:
                    def next_wrapper(gen):
                        try:
                            return next(gen), None
                        except StopIteration:
                            return None, "STOP"
                    
                    while True:
                        result, status = await asyncio.to_thread(next_wrapper, generator)
                        if status == "STOP":
                            break
                        
                        gs, ps, audio_array = result

                        if http_request and await http_request.is_disconnected():
                            logger.info("[SSE] Client disconnected, stopping generation")
                            break

                        if audio_array is None:
                            logger.warning("Received None audio array, skipping")
                            continue

                        audio_bytes = _encode_audio(audio_array)
                        
                        # For WAV format, prepend header to first chunk
                        if response_format == "wav" and not header_sent:
                            wav_header = _create_wav_header(TTS_SAMPLE_RATE)
                            audio_bytes_with_header = wav_header + audio_bytes
                            logger.info(f"[SSE] First chunk with WAV header ({len(wav_header)} bytes) + audio ({len(audio_bytes)} bytes)")
                            header_sent = True
                        else:
                            audio_bytes_with_header = audio_bytes
                        
                        audio_base64 = base64.b64encode(audio_bytes_with_header).decode('utf-8')

                        chunk_count += 1
                        samples = len(audio_array) if audio_array is not None else 0
                        logger.info(f"[SSE] Sending chunk #{chunk_count}, size={len(audio_base64)} chars, samples={samples}")

                        delta_event = {
                            "type": "speech.audio.delta",
                            "audio": audio_base64
                        }
                        yield f"data: {json.dumps(delta_event)}\n\n"

                    logger.info(f"[SSE] Sending done event, total_chunks={chunk_count}")
                    done_event = {
                        "type": "speech.audio.done",
                        "usage": {
                            "input_tokens": len(text),
                            "output_tokens": len(text),
                            "total_tokens": len(text) * 2
                        }
                    }
                    yield f"data: {json.dumps(done_event)}\n\n"

                finally:
                    logger.info(f"[SSE] Generator cleanup, sent {chunk_count} chunks")

            return sse_generator()
        else:
            async def audio_generator():
                chunk_count = 0
                header_sent = False
                try:
                    # If WAV is requested, send the header first
                    if response_format == "wav" and not header_sent:
                        wav_header = _create_wav_header(TTS_SAMPLE_RATE)
                        logger.info(f"[AUDIO] Sending WAV header ({len(wav_header)} bytes)")
                        yield wav_header
                        header_sent = True

                    def next_wrapper(gen):
                        try:
                            return next(gen), None
                        except StopIteration:
                            return None, "STOP"
                    
                    while True:
                        result, status = await asyncio.to_thread(next_wrapper, generator)
                        if status == "STOP":
                            break
                        
                        gs, ps, audio_array = result

                        if http_request and await http_request.is_disconnected():
                            logger.info("[AUDIO] Client disconnected, stopping generation")
                            break

                        if audio_array is None:
                            logger.warning("Received None audio array, skipping")
                            continue

                        audio_bytes = _encode_audio(audio_array)
                        chunk_count += 1
                        samples = len(audio_array) if audio_array is not None else 0
                        logger.info(f"[AUDIO] Sending chunk #{chunk_count}, size={len(audio_bytes)} bytes, samples={samples}")
                        yield audio_bytes
                finally:
                    logger.info(f"[AUDIO] Generator cleanup, sent {chunk_count} chunks")

            return audio_generator()

    except Exception as e:
        logger.error(f"Error during streaming synthesis setup: {e}", exc_info=True)
        raise SynthesisError(f"Failed to setup streaming synthesis: {str(e)}")

def _encode_audio(audio_array) -> bytes:
    """
    Encode float32 audio array to 16-bit PCM bytes.
    Handles both numpy arrays and PyTorch tensors.
    """
    if hasattr(audio_array, 'numpy'):
        audio_array = audio_array.numpy()
    
    audio = (audio_array * 32767).clip(-32768, 32767).astype(np.int16)
    return audio.tobytes()

def _create_wav_header(sample_rate: int) -> bytes:
    """
    Create a 44-byte WAV header for CD-quality audio (16-bit PCM, Mono).
    Sets length fields to 0 for unknown length/streaming.
    """
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    
    # RIFF chunk
    header = b'RIFF'
    header += struct.pack('<I', 0)  # ChunkSize
    header += b'WAVE'
    
    # fmt sub-chunk
    header += b'fmt '
    header += struct.pack('<I', 16)  # Subchunk1Size (16 for PCM)
    header += struct.pack('<H', 1)   # AudioFormat (1 for PCM)
    header += struct.pack('<H', num_channels)
    header += struct.pack('<I', sample_rate)
    header += struct.pack('<I', byte_rate)
    header += struct.pack('<H', block_align)
    header += struct.pack('<H', bits_per_sample)
    
    # data sub-chunk
    header += b'data'
    header += struct.pack('<I', 0)  # Subchunk2Size
    
    return header
