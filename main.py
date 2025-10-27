import datetime
import logging
from config import get_config
from error_handler import handle_errors, ModuleImportError, APIError
from alarm import create_event
from weather_utils import handle_temperature, handle_weather
from tts import speak, cleanup as tts_cleanup
from stt import take_command, calibrate_microphone, get_microphone_source
from nlp_processor import get_intent_spacy, get_intent_transformer, fallback_openrouter_gpt5

# Initialize configuration
config = get_config()

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.get('LOG_FILE', 'assistant.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# OpenRouter API Key from ashley-ai(llm).py
OPENROUTER_API_KEY = "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"

# ---------- ALARM HANDLER ----------
@handle_errors(speak_error=True, default_return=False)
def alarm(query):
    """Set alarm using the improved alarm system."""
    from alarm import set_alarm_voice
    try:
        dt = datetime.datetime.strptime(query.strip(), "%Y-%m-%d %I:%M %p")
        create_event("Manual Alarm", dt)
        speak(f"Alarm set for {query}")
        logger.info(f"Alarm set for {query}")
        return True
    except ValueError:
        speak("Time format error. Use YYYY-MM-DD HH:MM AM/PM")
        logger.warning(f"Invalid time format: {query}")
        return False

# ---------- GREETING HANDLER ----------
@handle_errors(speak_error=True, error_message="I couldn't greet you properly.")
def greet_user():
    """Handle greeting with proper error handling."""
    try:
        from GreetMe import greetMe
        greetMe()
    except ImportError as e:
        logger.error(f"GreetMe module not found: {e}")
        raise ModuleImportError("GreetMe module not available")

# ---------- SEARCH HANDLERS ----------
@handle_errors(speak_error=True, error_message="I couldn't search for that.")
def handle_google_search(query):
    """Handle Google search with error handling."""
    from SearchNow import search_google
    search_google(query)
    logger.info(f"Google search: {query}")

@handle_errors(speak_error=True, error_message="I couldn't search YouTube.")
def handle_youtube_search(query):
    """Handle YouTube search with error handling."""
    from SearchNow import search_youtube
    search_youtube(query)
    logger.info(f"YouTube search: {query}")

@handle_errors(speak_error=True, error_message="I couldn't search Wikipedia.")
def handle_wikipedia_search(query):
    """Handle Wikipedia search with error handling."""
    from SearchNow import search_wikipedia
    search_wikipedia(query)
    logger.info(f"Wikipedia search: {query}")

# ---------- APP CONTROL HANDLERS ----------
@handle_errors(speak_error=True, error_message="I couldn't open that.")
def handle_open_app(query):
    """Handle app opening with error handling."""
    from Dictapp import openappweb
    openappweb(query)
    logger.info(f"Opening: {query}")

@handle_errors(speak_error=True, error_message="I couldn't close that.")
def handle_close_app(query):
    """Handle app closing with error handling."""
    from Dictapp import closeappweb
    closeappweb(query)
    logger.info(f"Closing: {query}")

# ---------- ALARM LIST HANDLER ----------
@handle_errors(speak_error=True, error_message="I couldn't list your alarms.")
def handle_list_alarms():
    """Handle alarm listing with error handling."""
    from alarm import list_alarms
    list_alarms()
    logger.info("Listed alarms")

# ---------- ALARM CANCEL HANDLER ----------
@handle_errors(speak_error=True, error_message="I couldn't cancel that alarm.")
def handle_cancel_alarm(voice_input):
    """Handle alarm cancellation with error handling."""
    from alarm import cancel_alarm
    cancel_alarm(voice_input)
    logger.info(f"Cancelled alarm: {voice_input}")

# ---------- MAIN AI ASSISTANT LOOP ----------
def assistant_loop():
    """Main assistant loop with NLP intent classification and OpenRouter fallback."""
    logger.info("Starting assistant loop")
    speak(f"Hello! I'm {config.get('ASSISTANT_NAME')}, your AI assistant.")
    
    with get_microphone_source() as source:
        try:
            calibrate_microphone(source)
        except Exception as e:
            logger.error(f"Microphone calibration failed: {e}")
            speak("I'm having trouble with the microphone, but I'll try to continue.")
        
        while True:
            try:
                query = take_command(source)
                
                if not query:
                    continue
                
                query = query.lower().strip()
                logger.info(f"User query: {query}")
                
                # Primary intent detection using transformer model
                intent = get_intent_transformer(query)
                if intent == "unknown":
                    # Fallback to spaCy if transformer doesn't recognize intent
                    intent = get_intent_spacy(query)
                
                logger.info(f"Detected intent: {intent}")
                
                # Handle intents using NLP classification
                if intent == "exit":
                    speak("Alright, have a great day! I'm just a call away.")
                    logger.info("User requested exit")
                    break
                
                elif intent == "greet":
                    greet_user()
                
                elif intent == "search_google":
                    handle_google_search(query)
                
                elif intent == "search_youtube":
                    handle_youtube_search(query)
                
                elif intent == "search_wikipedia":
                    handle_wikipedia_search(query)
                
                elif intent == "temperature":
                    try:
                        handle_temperature(query)
                    except APIError:
                        speak("I couldn't get the temperature right now. Please try again later.")
                
                elif intent == "weather":
                    try:
                        handle_weather(query)
                    except APIError:
                        speak("I couldn't get the weather information. Please try again later.")
                
                elif intent == "get_time":
                    now = datetime.datetime.now()
                    strTime = now.strftime("%I:%M %p")
                    speak(f"Sir, the time is {strTime}")
                
                elif intent == "get_date":
                    now = datetime.datetime.now()
                    strDate = now.strftime("%A, %B %d, %Y")
                    speak(f"Today is {strDate}")
                
                elif intent == "open_app":
                    handle_open_app(query)
                
                elif intent == "close_app":
                    handle_close_app(query)
                
                # Alarm commands (keeping these as they need special handling)
                elif "set an alarm" in query or "set alarm" in query:
                    speak("Would you like to type the time or say it aloud?")
                    print("You can either speak a date like 'tomorrow at 10 AM' or type it.")
                    user_input = input("If typing, enter time (YYYY-MM-DD HH:MM AM/PM): ").strip()
                    
                    if user_input:
                        alarm(user_input)
                    else:
                        speak("Speak now to set alarm.")
                        try:
                            from alarm import set_alarm_voice
                            voice_input = take_command(source)
                            if voice_input:
                                set_alarm_voice(voice_input, "Voice Alarm")
                            else:
                                speak("Couldn't detect any speech. Please try again.")
                        except Exception as e:
                            logger.error(f"Alarm setting error: {e}")
                            speak("I couldn't set the alarm. Please try again.")
                
                elif "list alarms" in query or "show alarms" in query:
                    handle_list_alarms()
                
                elif "cancel alarm" in query or "delete alarm" in query:
                    speak("Which alarm would you like to cancel?")
                    voice_input = take_command(source)
                    if voice_input:
                        handle_cancel_alarm(voice_input)
                    else:
                        speak("Couldn't detect any speech. Please try again.")
                
                # Default fallback - Use OpenRouter GPT 5 Pro for unknown intents
                else:
                    logger.info(f"Unknown intent '{intent}', using OpenRouter GPT 5 Pro fallback")
                    response = fallback_openrouter_gpt5(query, OPENROUTER_API_KEY)
                    if response:
                        print(f"GPT 5 Pro response: {response}")
                        speak(response)
                    else:
                        print("GPT 5 Pro did not return a valid response.")
                        speak("I couldn't find an answer to that.")
            
            except KeyboardInterrupt:
                logger.info("User interrupted with Ctrl+C")
                speak("Goodbye!")
                break
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                speak("I encountered an error. Let me try to continue.")

# ---------- CLEANUP ----------
def cleanup():
    """Cleanup resources before exit."""
    logger.info("Cleaning up resources")
    try:
        tts_cleanup()
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# ---------- RUN ----------
if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("AI Assistant Starting")
    logger.info("=" * 50)
    
    # Validate configuration
    if not config.validate():
        logger.warning("Configuration has warnings - some features may not work")
    
    try:
        assistant_loop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
    finally:
        cleanup()
        logger.info("AI Assistant Stopped")