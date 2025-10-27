"""
Service layer to decouple modules and provide unified interfaces.
This prevents tight coupling and circular dependencies.
"""

import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# ---------- BASE SERVICE CLASS ----------
class Service(ABC):
    """Base class for all services."""
    
    def __init__(self, name: str):
        self.name = name
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the service. Return True if successful."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup service resources."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if service is initialized."""
        return self._initialized


# ---------- TTS SERVICE ----------
class TTSService(Service):
    """Text-to-Speech service wrapper."""
    
    def __init__(self):
        super().__init__("TTS")
        self._speak_func = None
    
    def initialize(self) -> bool:
        """Initialize TTS."""
        try:
            from tts import speak
            self._speak_func = speak
            self._initialized = True
            logger.info("TTS Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            return False
    
    def speak(self, text: str, voice: Optional[str] = None):
        """Speak text using TTS."""
        if not self._initialized:
            logger.warning("TTS not initialized")
            print(f"[TTS]: {text}")  # Fallback to print
            return
        
        try:
            if voice:
                self._speak_func(text, voice=voice)
            else:
                self._speak_func(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            print(f"[TTS ERROR]: {text}")
    
    def cleanup(self):
        """Cleanup TTS resources."""
        try:
            from tts import cleanup
            cleanup()
            logger.info("TTS Service cleaned up")
        except Exception as e:
            logger.error(f"TTS cleanup error: {e}")


# ---------- STT SERVICE ----------
class STTService(Service):
    """Speech-to-Text service wrapper."""
    
    def __init__(self):
        super().__init__("STT")
        self._microphone = None
    
    def initialize(self) -> bool:
        """Initialize STT."""
        try:
            from stt import get_microphone_source, calibrate_microphone
            self._microphone = get_microphone_source()
            self._microphone.__enter__()
            calibrate_microphone(self._microphone)
            self._initialized = True
            logger.info("STT Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize STT: {e}")
            return False
    
    def listen(self, timeout: int = 8) -> Optional[str]:
        """Listen for speech and return text."""
        if not self._initialized:
            logger.warning("STT not initialized")
            return None
        
        try:
            from stt import take_command
            return take_command(self._microphone, timeout=timeout)
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None
    
    def cleanup(self):
        """Cleanup STT resources."""
        try:
            if self._microphone:
                self._microphone.__exit__(None, None, None)
            logger.info("STT Service cleaned up")
        except Exception as e:
            logger.error(f"STT cleanup error: {e}")


# ---------- WEATHER SERVICE ----------
class WeatherService(Service):
    """Weather information service wrapper."""
    
    def __init__(self):
        super().__init__("Weather")
    
    def initialize(self) -> bool:
        """Initialize weather service."""
        try:
            from weather_utils import get_openweather_data
            self._get_data = get_openweather_data
            self._initialized = True
            logger.info("Weather Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Weather: {e}")
            return False
    
    def get_temperature(self, query: str) -> Optional[Dict[str, Any]]:
        """Get temperature for location."""
        if not self._initialized:
            return None
        
        try:
            from weather_utils import handle_temperature
            handle_temperature(query)
            return {"success": True}
        except Exception as e:
            logger.error(f"Temperature fetch error: {e}")
            return None
    
    def get_weather(self, query: str) -> Optional[Dict[str, Any]]:
        """Get weather for location."""
        if not self._initialized:
            return None
        
        try:
            from weather_utils import handle_weather
            handle_weather(query)
            return {"success": True}
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return None
    
    def cleanup(self):
        """Cleanup weather service."""
        logger.info("Weather Service cleaned up")


# ---------- SEARCH SERVICE ----------
class SearchService(Service):
    """Search service wrapper."""
    
    def __init__(self):
        super().__init__("Search")
    
    def initialize(self) -> bool:
        """Initialize search service."""
        try:
            from SearchNow import search_google, search_youtube, search_wikipedia
            self._google = search_google
            self._youtube = search_youtube
            self._wikipedia = search_wikipedia
            self._initialized = True
            logger.info("Search Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Search: {e}")
            return False
    
    def google(self, query: str) -> bool:
        """Search Google."""
        if not self._initialized:
            return False
        try:
            self._google(query)
            return True
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return False
    
    def youtube(self, query: str) -> bool:
        """Search YouTube."""
        if not self._initialized:
            return False
        try:
            self._youtube(query)
            return True
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return False
    
    def wikipedia(self, query: str) -> bool:
        """Search Wikipedia."""
        if not self._initialized:
            return False
        try:
            self._wikipedia(query)
            return True
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup search service."""
        logger.info("Search Service cleaned up")


# ---------- ALARM SERVICE ----------
class AlarmService(Service):
    """Alarm management service wrapper."""
    
    def __init__(self):
        super().__init__("Alarm")
    
    def initialize(self) -> bool:
        """Initialize alarm service."""
        try:
            from alarm import set_alarm_voice, list_alarms, cancel_alarm, create_event
            self._set_alarm = set_alarm_voice
            self._list_alarms = list_alarms
            self._cancel_alarm = cancel_alarm
            self._create_event = create_event
            self._initialized = True
            logger.info("Alarm Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Alarm: {e}")
            return False
    
    def set_alarm(self, time_input: str, label: str = "Alarm") -> bool:
        """Set an alarm."""
        if not self._initialized:
            return False
        try:
            return self._set_alarm(time_input, label)
        except Exception as e:
            logger.error(f"Set alarm error: {e}")
            return False
    
    def list_alarms(self) -> List[Dict[str, Any]]:
        """List all alarms."""
        if not self._initialized:
            return []
        try:
            self._list_alarms()
            return []
        except Exception as e:
            logger.error(f"List alarms error: {e}")
            return []
    
    def cancel_alarm(self, alarm_id: str) -> bool:
        """Cancel an alarm."""
        if not self._initialized:
            return False
        try:
            return self._cancel_alarm(alarm_id)
        except Exception as e:
            logger.error(f"Cancel alarm error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup alarm service."""
        logger.info("Alarm Service cleaned up")


# ---------- APP CONTROL SERVICE ----------
class AppControlService(Service):
    """Application control service wrapper."""
    
    def __init__(self):
        super().__init__("AppControl")
    
    def initialize(self) -> bool:
        """Initialize app control service."""
        try:
            from Dictapp import openappweb, closeappweb
            self._open = openappweb
            self._close = closeappweb
            self._initialized = True
            logger.info("AppControl Service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize AppControl: {e}")
            return False
    
    def open_app(self, query: str) -> bool:
        """Open an application."""
        if not self._initialized:
            return False
        try:
            self._open(query)
            return True
        except Exception as e:
            logger.error(f"Open app error: {e}")
            return False
    
    def close_app(self, query: str) -> bool:
        """Close an application."""
        if not self._initialized:
            return False
        try:
            self._close(query)
            return True
        except Exception as e:
            logger.error(f"Close app error: {e}")
            return False
    
    def cleanup(self):
        """Cleanup app control service."""
        logger.info("AppControl Service cleaned up")


# ---------- SERVICE MANAGER ----------
class ServiceManager:
    """Centralized service manager."""
    
    def __init__(self):
        self.services: Dict[str, Service] = {}
        logger.info("ServiceManager initialized")
    
    def register(self, service: Service) -> bool:
        """Register a service."""
        try:
            if service.initialize():
                self.services[service.name] = service
                logger.info(f"Registered service: {service.name}")
                return True
            else:
                logger.warning(f"Failed to register service: {service.name}")
                return False
        except Exception as e:
            logger.error(f"Error registering {service.name}: {e}")
            return False
    
    def get(self, service_name: str) -> Optional[Service]:
        """Get a service by name."""
        return self.services.get(service_name)
    
    def cleanup_all(self):
        """Cleanup all services."""
        logger.info("Cleaning up all services")
        for service in self.services.values():
            try:
                service.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {service.name}: {e}")


# ---------- USAGE EXAMPLE ----------
if __name__ == "__main__":
    # Create service manager
    manager = ServiceManager()
    
    # Register services
    manager.register(TTSService())
    manager.register(STTService())
    manager.register(WeatherService())
    manager.register(SearchService())
    manager.register(AlarmService())
    manager.register(AppControlService())
    
    # Use services
    tts = manager.get("TTS")
    if tts:
        tts.speak("Hello! Services are initialized.")
    
    # Cleanup
    manager.cleanup_all()