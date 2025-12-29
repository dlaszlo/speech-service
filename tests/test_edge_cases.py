import pytest
import logging
import json
import os
import tempfile
from openai import OpenAI

logger = logging.getLogger(__name__)

def test_max_input_length(sync_client, common_constants):
    """Test that TTS rejects input longer than 4096 characters."""
    long_text = "A" * 4097
    
    logger.info(f"Testing with {len(long_text)} characters (should fail)")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    
    try:
        with sync_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=long_text,
            voice=common_constants["VOICE"],
            response_format="wav"
        ) as response:
            response.stream_to_file(temp_file.name)
        
        pytest.fail("Expected error for input exceeding 4096 characters, but request succeeded")
    except Exception as e:
        logger.info(f"Got expected error: {type(e).__name__}: {e}")
        
        # Check if it's a structured error response
        structured_error = _get_structured_error(e)
        if structured_error:
            logger.info(f"Structured error: {structured_error}")
            
            # Validate error code
            error_code = structured_error.get('code', '')
            error_type = structured_error.get('type', '')
            error_param = structured_error.get('param', '')
            error_message = structured_error.get('message', '')
            
            assert error_code == "context_length_exceeded", \
                f"Expected error code 'context_length_exceeded', got: {error_code}"
            assert error_type == "invalid_request_error", \
                f"Expected error type 'invalid_request_error', got: {error_type}"
            assert error_param == "input", \
                f"Expected error param 'input', got: {error_param}"
            assert "4096" in error_message.lower() or "exceeds" in error_message.lower() or "maximum" in error_message.lower(), \
                f"Error message should mention 4096/exceeds/maximum, got: {error_message}"
        else:
            # Fallback for non-structured errors
            error_msg = str(e).lower()
            assert ("4096" in error_msg or "too long" in error_msg or 
                    "exceeds" in error_msg or "maximum" in error_msg), \
                f"Error message should mention 4096 character limit, got: {e}"
    finally:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

def test_invalid_output_format(sync_client, common_constants):
    """Test that TTS rejects invalid output format."""
    invalid_format = "invalid_format"
    test_text = "This is a test text."
    
    logger.info(f"Testing with invalid output format: {invalid_format}")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    
    try:
        with sync_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=test_text,
            voice=common_constants["VOICE"],
            response_format=invalid_format
        ) as response:
            response.stream_to_file(temp_file.name)
        
        pytest.fail(f"Expected error for invalid format '{invalid_format}', but request succeeded")
        
    except Exception as e:
        logger.info(f"Got expected error: {type(e).__name__}: {e}")
        
        # Check if it's a structured error response
        structured_error = _get_structured_error(e)
        if structured_error:
            logger.info(f"Structured error: {structured_error}")
            
            # Validate error code
            error_code = structured_error.get('code', '')
            error_type = structured_error.get('type', '')
            error_param = structured_error.get('param', '')
            error_message = structured_error.get('message', '')
            
            assert error_code == "invalid_format", \
                f"Expected error code 'invalid_format', got: {error_code}"
            assert error_type == "invalid_request_error", \
                f"Expected error type 'invalid_request_error', got: {error_type}"
            assert error_param == "response_format", \
                f"Expected error param 'response_format', got: {error_param}"
            assert ("invalid" in error_message.lower() or "unsupported" in error_message.lower() or 
                    "format" in error_message.lower()), \
                f"Error message should mention invalid/unsupported/format, got: {error_message}"
        else:
            # Fallback for non-structured errors
            error_msg = str(e).lower()
            assert ("invalid" in error_msg or "format" in error_msg or 
                    "unsupported" in error_msg), \
                f"Error message should mention invalid/unsupported format, got: {e}"
    finally:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

def test_empty_input(sync_client, common_constants):
    """Test that TTS handles empty input."""
    empty_text = ""
    
    logger.info(f"Testing with empty input ({len(empty_text)} characters)")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    
    try:
        with sync_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=empty_text,
            voice=common_constants["VOICE"],
            response_format="wav"
        ) as response:
            response.stream_to_file(temp_file.name)
        
        pytest.fail("Expected error for empty input, but request succeeded")
        
    except Exception as e:
        logger.info(f"Got expected error: {type(e).__name__}: {e}")
        
        # Check if it's a structured error response
        structured_error = _get_structured_error(e)
        if structured_error:
            logger.info(f"Structured error: {structured_error}")
            
            # Validate error code
            error_code = structured_error.get('code', '')
            error_type = structured_error.get('type', '')
            error_param = structured_error.get('param', '')
            error_message = structured_error.get('message', '')
            
            assert error_code == "empty_input", \
                f"Expected error code 'empty_input', got: {error_code}"
            assert error_type == "invalid_request_error", \
                f"Expected error type 'invalid_request_error', got: {error_type}"
            assert error_param == "input", \
                f"Expected error param 'input', got: {error_param}"
            assert ("empty" in error_message.lower() or "required" in error_message.lower() or 
                    "cannot be empty" in error_message.lower()), \
                f"Error message should mention empty/required/cannot be empty, got: {error_message}"
        else:
            # Fallback for non-structured errors
            error_msg = str(e).lower()
            assert ("empty" in error_msg or "input" in error_msg or 
                    "required" in error_msg or "cannot be empty" in error_msg), \
                f"Error message should mention empty/required input, got: {e}"
    finally:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

def test_invalid_voice(sync_client, common_constants):
    """Test that TTS rejects invalid voice parameter."""
    invalid_voice = "invalid_voice_xyz"
    test_text = "This is a test text."
    
    logger.info(f"Testing with invalid voice: {invalid_voice}")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    
    try:
        with sync_client.audio.speech.with_streaming_response.create(
            model=common_constants["TTS_MODEL"],
            input=test_text,
            voice=invalid_voice,
            response_format="wav"
        ) as response:
            response.stream_to_file(temp_file.name)
        
        pytest.fail(f"Expected error for invalid voice '{invalid_voice}', but request succeeded")
        
    except Exception as e:
        logger.info(f"Got expected error: {type(e).__name__}: {e}")
        
        # Check if it's a structured error response
        structured_error = _get_structured_error(e)
        if structured_error:
            logger.info(f"Structured error: {structured_error}")
            
            # Validate error code
            error_code = structured_error.get('code', '')
            error_type = structured_error.get('type', '')
            error_param = structured_error.get('param', '')
            error_message = structured_error.get('message', '')
            
            assert error_code == "voice_not_found", \
                f"Expected error code 'voice_not_found', got: {error_code}"
            assert error_type == "invalid_request_error", \
                f"Expected error type 'invalid_request_error', got: {error_type}"
            assert error_param == "voice", \
                f"Expected error param 'voice', got: {error_param}"
            assert ("voice" in error_message.lower() or "invalid" in error_message.lower() or 
                    "not found" in error_message.lower()), \
                f"Error message should mention voice/invalid/not found, got: {error_message}"
        else:
            # Fallback: accept any error that indicates request failed
            error_msg = str(e).lower()
            assert ("voice" in error_msg or "invalid" in error_msg or 
                    "not found" in error_msg or "connection" in error_msg or 
                    "closed" in error_msg or "incomplete" in error_msg or 
                    "failed" in error_msg or "error" in error_msg), \
                f"Error should indicate request failure, got: {e}"
    finally:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

def test_invalid_model(sync_client, common_constants):
    """Test that TTS rejects invalid model parameter."""
    invalid_model = "invalid/model/name"
    test_text = "This is a test text."
    
    logger.info(f"Testing with invalid model: {invalid_model}")
    
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    
    try:
        with sync_client.audio.speech.with_streaming_response.create(
            model=invalid_model,
            input=test_text,
            voice=common_constants["VOICE"],
            response_format="wav"
        ) as response:
            response.stream_to_file(temp_file.name)
        
        pytest.fail(f"Expected error for invalid model '{invalid_model}', but request succeeded")
        
    except Exception as e:
        logger.info(f"Got expected error: {type(e).__name__}: {e}")
        
        # Check if it's a structured error response
        structured_error = _get_structured_error(e)
        if structured_error:
            logger.info(f"Structured error: {structured_error}")
            
            # Validate error code
            error_code = structured_error.get('code', '')
            error_type = structured_error.get('type', '')
            error_param = structured_error.get('param', '')
            error_message = structured_error.get('message', '')
            
            assert error_code == "model_not_found", \
                f"Expected error code 'model_not_found', got: {error_code}"
            assert error_type == "invalid_request_error", \
                f"Expected error type 'invalid_request_error', got: {error_type}"
            assert error_param == "model", \
                f"Expected error param 'model', got: {error_param}"
            assert ("model" in error_message.lower() or "invalid" in error_message.lower() or 
                    "not found" in error_message.lower()), \
                f"Error message should mention model/invalid/not found, got: {error_message}"
        else:
            # Fallback: accept any error that indicates request failed
            error_msg = str(e).lower()
            assert ("model" in error_msg or "invalid" in error_msg or 
                    "not found" in error_msg or "not loaded" in error_msg or 
                    "failed" in error_msg or "error" in error_msg), \
                f"Error should indicate model failure, got: {e}"
    finally:
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass

def _get_structured_error(exception: Exception):
    """Helper function to extract structured error from exception if available."""
    if hasattr(exception, 'response'):
        try:
            error_data = json.loads(exception.response.text)
            if 'error' in error_data:
                return error_data['error']
        except (json.JSONDecodeError, AttributeError):
            logger.warning(f"Could not parse error as structured JSON: {exception}")
    return None
