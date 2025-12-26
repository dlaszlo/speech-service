import io
import logging
import asyncio
import soundfile as sf

from ..core.tts_dependencies import get_tts_model_state
from ..core.exceptions import ModelNotLoadedError, SynthesisError, TimeoutError as ServiceTimeoutError
from ..core.config import TTS_SYNTHESIS_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)
tts_model_state = get_tts_model_state()

async def synthesize(text: str, voice: str) -> bytes:
    if not tts_model_state.pipeline:
        logger.error("TTS requested but no model is loaded.")
        raise ModelNotLoadedError("TTS model is not loaded.")

    try:
        wav_bytes = await asyncio.wait_for(
            asyncio.to_thread(_synthesize_sync, text, voice),
            timeout=TTS_SYNTHESIS_TIMEOUT_SECONDS
        )
        return wav_bytes

    except ModelNotLoadedError:
            raise
    except asyncio.TimeoutError as e:
        logger.error(f"TTS synthesis timed out after {TTS_SYNTHESIS_TIMEOUT_SECONDS} seconds: {e}")
        raise ServiceTimeoutError(f"Speech synthesis timed out after {TTS_SYNTHESIS_TIMEOUT_SECONDS} seconds")
    except Exception as e:
        logger.error(f"Error during speech synthesis wrapper: {e}", exc_info=True)
        raise SynthesisError(f"Speech synthesis failed: {str(e)}")

def _synthesize_sync(text: str, voice: str) -> bytes:
    try:
        logger.info(f"Synthesizing speech for text with voice '{voice}'.")
        
        generator = None
        audio_array = None
        
        try:
            generator = tts_model_state.pipeline(text, voice=voice)
            # The generator yields tuples of (gs, ps, audio)
            _, _, audio_array = next(generator)
        except StopIteration:
            logger.error("Audio generator produced no output.")
            raise SynthesisError("Audio generation failed to produce any output.")
        except Exception as e:
            logger.error(f"Error during audio generation: {e}")
            raise
        finally:
            if generator is not None and hasattr(generator, 'close'):
                try:
                    generator.close()
                except Exception as close_error:
                    logger.warning(f"Error closing generator: {close_error}")
        
        if audio_array is None:
            raise ValueError("Audio generation failed, received None.")

        logger.info("Speech synthesized successfully. Encoding to WAV format.")

        sample_rate = 24000
        
        wav_io = io.BytesIO()
        sf.write(wav_io, audio_array, sample_rate, format='WAV')
        wav_io.seek(0)
        
        return wav_io.read()

    except Exception as e:
        if isinstance(e, SynthesisError):
            raise e
        logger.error(f"Error during blocking speech synthesis: {e}", exc_info=True)
        raise SynthesisError(f"Internal synthesis error: {str(e)}")
