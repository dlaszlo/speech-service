import io
import logging
import asyncio
import base64
import json
import numpy as np

from ..core.tts_dependencies import get_tts_model_state
from ..core.exceptions import ModelNotLoadedError, SynthesisError, TimeoutError as ServiceTimeoutError
from ..core.config import TTS_SYNTHESIS_TIMEOUT_SECONDS, TTS_SAMPLE_RATE
from ..core.audio_encoder import get_encoder

logger = logging.getLogger(__name__)
tts_model_state = get_tts_model_state()


def _next_wrapper(gen):
    """Helper to wrap generator next() call for use with asyncio.to_thread."""
    try:
        return next(gen), None
    except StopIteration:
        return None, "STOP"

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

        encoder = get_encoder(response_format, TTS_SAMPLE_RATE)
        
        output_io = io.BytesIO()
        
        # Add header if any
        header = encoder.create_header()
        if header:
            output_io.write(header)
            
        # Add encoded audio
        chunk_bytes = encoder.encode_chunk(full_audio)
        if chunk_bytes:
            output_io.write(chunk_bytes)
            
        # Finalize
        final_bytes = encoder.finalize()
        if final_bytes:
            output_io.write(final_bytes)
            
        return output_io.getvalue()

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
    Supports both SSE (Server-Sent Events) and raw audio streaming.
    """
    if not tts_model_state.pipeline:
        logger.error("TTS requested but no model is loaded.")
        raise ModelNotLoadedError("TTS model is not loaded.")

    logger.info(f"Starting streaming TTS synthesis: text_length={len(text)}, voice='{voice}', response_format='{response_format}', stream_format='{stream_format}'")

    pipeline = tts_model_state.pipeline
    is_sse = stream_format == "sse"
    log_prefix = "[SSE]" if is_sse else "[AUDIO]"
    
    try:
        generator = pipeline(text, voice=voice)  # type: ignore

        async def streaming_generator():
            chunk_count = 0
            encoder = get_encoder(response_format, TTS_SAMPLE_RATE)
            
            try:
                # Handle header
                header = encoder.create_header()
                if header:
                    if is_sse:
                        # For SSE, we'll prepend header to first audio chunk
                        pending_header = header
                    else:
                        logger.info(f"{log_prefix} Sending {response_format} header ({len(header)} bytes)")
                        yield header
                        pending_header = None
                else:
                    pending_header = None
                
                # Process audio chunks
                while True:
                    result, status = await asyncio.to_thread(_next_wrapper, generator)
                    if status == "STOP":
                        break
                    
                    gs, ps, audio_array = result

                    if http_request and await http_request.is_disconnected():
                        logger.info(f"{log_prefix} Client disconnected, stopping generation")
                        break

                    if audio_array is None:
                        logger.warning("Received None audio array, skipping")
                        continue

                    # Encode chunk
                    audio_bytes = encoder.encode_chunk(audio_array)
                    
                    # Prepend header if pending (SSE mode)
                    if pending_header:
                        audio_bytes = pending_header + audio_bytes
                        pending_header = None

                    if not audio_bytes:
                        continue
                    
                    chunk_count += 1
                    
                    if is_sse:
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                        logger.info(f"{log_prefix} Sending chunk #{chunk_count}, size={len(audio_base64)} chars")
                        yield f"data: {json.dumps({'type': 'speech.audio.delta', 'audio': audio_base64})}\n\n"
                    else:
                        logger.info(f"{log_prefix} Sending chunk #{chunk_count}, size={len(audio_bytes)} bytes")
                        yield audio_bytes

                # Finalize encoder
                final_bytes = encoder.finalize()
                if final_bytes:
                    if is_sse:
                        audio_base64 = base64.b64encode(final_bytes).decode('utf-8')
                        yield f"data: {json.dumps({'type': 'speech.audio.delta', 'audio': audio_base64})}\n\n"
                    else:
                        yield final_bytes

                # SSE done event
                if is_sse:
                    logger.info(f"{log_prefix} Sending done event, total_chunks={chunk_count}")
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
                logger.info(f"{log_prefix} Generator cleanup, sent {chunk_count} chunks")

        return streaming_generator()

    except Exception as e:
        logger.error(f"Error during streaming synthesis setup: {e}", exc_info=True)
        raise SynthesisError(f"Failed to setup streaming synthesis: {str(e)}")
