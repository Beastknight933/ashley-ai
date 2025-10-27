import logging
import functools
import traceback
from typing import Callable, Any, Optional
from tts import speak
from enhanced_logging import get_enhanced_logger, log_errors, log_performance

# Setup enhanced logging
enhanced_logger = get_enhanced_logger("error_handler")
logger = enhanced_logger.logger  # Keep backward compatibility

# ---------- CUSTOM EXCEPTIONS ----------
class AssistantError(Exception):
    """Base exception for all assistant errors."""
    pass

class SpeechRecognitionError(AssistantError):
    """Raised when speech recognition fails."""
    pass

class TTSError(AssistantError):
    """Raised when text-to-speech fails."""
    pass

class APIError(AssistantError):
    """Raised when external API calls fail."""
    pass

class ModuleImportError(AssistantError):
    """Raised when required module import fails."""
    pass

# ---------- ERROR HANDLER DECORATOR ----------
def handle_errors(
    speak_error: bool = True,
    default_return: Any = None,
    error_message: Optional[str] = None
):
    """
    Enhanced error handling decorator with structured logging.
    
    Args:
        speak_error: Whether to speak the error message to user
        default_return: Value to return on error
        error_message: Custom error message (if None, uses exception message)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            enhanced_logger.set_context(function=func.__name__)
            
            try:
                return func(*args, **kwargs)
            
            except SpeechRecognitionError as e:
                enhanced_logger.warning("Speech recognition error", exception=e)
                if speak_error:
                    speak("I couldn't hear you clearly. Please try again.")
                return default_return
            
            except TTSError as e:
                enhanced_logger.error("TTS error", exception=e)
                print(f"TTS Error: {e}")  # Can't speak if TTS failed
                return default_return
            
            except APIError as e:
                enhanced_logger.error("API error", exception=e)
                if speak_error:
                    msg = error_message or "I'm having trouble connecting to that service right now."
                    speak(msg)
                return default_return
            
            except ModuleImportError as e:
                enhanced_logger.error("Import error", exception=e)
                if speak_error:
                    speak("A required module is not available.")
                return default_return
            
            except FileNotFoundError as e:
                enhanced_logger.error("File not found", exception=e)
                if speak_error:
                    msg = error_message or "I couldn't find a required file."
                    speak(msg)
                return default_return
            
            except PermissionError as e:
                enhanced_logger.error("Permission error", exception=e)
                if speak_error:
                    speak("I don't have permission to do that.")
                return default_return
            
            except ValueError as e:
                enhanced_logger.error("Value error", exception=e)
                if speak_error:
                    msg = error_message or "I received an invalid value."
                    speak(msg)
                return default_return
            
            except KeyboardInterrupt:
                enhanced_logger.info("User interrupted function")
                raise  # Re-raise to allow graceful shutdown
            
            except Exception as e:
                enhanced_logger.critical("Unexpected error", exception=e)
                if speak_error:
                    msg = error_message or "Something went wrong. Please try again."
                    speak(msg)
                return default_return
        
        return wrapper
    return decorator

# ---------- CONTEXT MANAGER FOR CLEANUP ----------
class ResourceManager:
    """Context manager for resources that need cleanup."""
    
    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.resources = []
        logger.info(f"ResourceManager initialized for {resource_name}")
    
    def add(self, resource, cleanup_func: Callable):
        """Add a resource with its cleanup function."""
        self.resources.append((resource, cleanup_func))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all resources."""
        for resource, cleanup_func in reversed(self.resources):
            try:
                cleanup_func(resource)
                logger.info(f"Cleaned up {self.resource_name}")
            except Exception as e:
                logger.error(f"Error cleaning up {self.resource_name}: {e}")
        
        # Don't suppress exceptions
        return False

# ---------- SAFE IMPORT WRAPPER ----------
def safe_import(module_name: str, error_msg: Optional[str] = None):
    """
    Safely import a module with error handling.
    
    Args:
        module_name: Name of module to import
        error_msg: Optional custom error message
    
    Returns:
        Imported module or None if import fails
    
    Raises:
        ModuleImportError: If import fails and error should be propagated
    """
    try:
        module = __import__(module_name)
        logger.info(f"Successfully imported {module_name}")
        return module
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {e}")
        if error_msg:
            raise ModuleImportError(error_msg)
        return None

# ---------- RETRY DECORATOR ----------
def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    Retry decorator for functions that may fail temporarily.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(delay)
            
        return wrapper
    return decorator

# ---------- USAGE EXAMPLES ----------
if __name__ == "__main__":
    # Example 1: Using error handler decorator
    @handle_errors(speak_error=True, default_return="")
    def risky_function():
        raise ValueError("Something went wrong!")
    
    result = risky_function()
    print(f"Result: {result}")
    
    # Example 2: Using resource manager
    def cleanup_file(file):
        file.close()
        print("File closed")
    
    with ResourceManager("test_file") as rm:
        test_file = open("test.txt", "w")
        rm.add(test_file, cleanup_file)
        # File will be automatically closed even if error occurs
    
    # Example 3: Using retry decorator
    @retry(max_attempts=3, delay=0.5)
    def flaky_api_call():
        import random
        if random.random() < 0.7:
            raise APIError("API temporarily unavailable")
        return "Success!"
    
    try:
        result = flaky_api_call()
        print(result)
    except APIError:
        print("API call failed after all retries")