"""
Wake word detection system for Ashley AI
"""

import speech_recognition as sr
import threading
import time
import queue
from collections import deque
from typing import List, Callable, Optional, Dict, Any
from enhanced_logging import get_enhanced_logger
from enhanced_config import get_config

class WakeWordDetector:
    """Advanced wake word detection with multiple patterns and confidence scoring"""
    
    def __init__(self, wake_words: Optional[List[str]] = None, sensitivity: float = 0.5):
        self.config = get_config()
        self.logger = get_enhanced_logger("wake_word_detector")
        
        # Wake word configuration
        self.wake_words = wake_words or self.config.wake_words
        self.sensitivity = sensitivity or self.config.wake_word_sensitivity
        self.continuous_listening = self.config.continuous_listening
        
        # Speech recognition setup
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # State management
        self.is_listening = False
        self.is_activated = False
        self.audio_buffer = deque(maxlen=20)  # Keep last 20 audio chunks
        self.confidence_scores = deque(maxlen=10)  # Track confidence over time
        
        # Callbacks
        self.wake_word_callback: Optional[Callable] = None
        self.activation_callback: Optional[Callable] = None
        self.deactivation_callback: Optional[Callable] = None
        
        # Threading
        self.listening_thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue()
        
        # Performance metrics
        self.detection_count = 0
        self.false_positive_count = 0
        self.avg_response_time = 0.0
        
        self.logger.info("Wake word detector initialized", 
                        wake_words=self.wake_words, 
                        sensitivity=self.sensitivity)
    
    def add_wake_word(self, wake_word: str):
        """Add a new wake word pattern"""
        if wake_word not in self.wake_words:
            self.wake_words.append(wake_word.lower())
            self.logger.info("Wake word added", wake_word=wake_word)
    
    def remove_wake_word(self, wake_word: str):
        """Remove a wake word pattern"""
        if wake_word in self.wake_words:
            self.wake_words.remove(wake_word.lower())
            self.logger.info("Wake word removed", wake_word=wake_word)
    
    def set_sensitivity(self, sensitivity: float):
        """Set wake word detection sensitivity (0.0 to 1.0)"""
        if 0.0 <= sensitivity <= 1.0:
            self.sensitivity = sensitivity
            self.logger.info("Sensitivity updated", sensitivity=sensitivity)
        else:
            self.logger.warning("Invalid sensitivity value", sensitivity=sensitivity)
    
    def set_wake_word_callback(self, callback: Callable[[str, float], None]):
        """Set callback for wake word detection"""
        self.wake_word_callback = callback
        self.logger.info("Wake word callback set")
    
    def set_activation_callback(self, callback: Callable[[], None]):
        """Set callback for assistant activation"""
        self.activation_callback = callback
        self.logger.info("Activation callback set")
    
    def set_deactivation_callback(self, callback: Callable[[], None]):
        """Set callback for assistant deactivation"""
        self.deactivation_callback = callback
        self.logger.info("Deactivation callback set")
    
    def start_listening(self):
        """Start continuous wake word detection"""
        if self.is_listening:
            self.logger.warning("Already listening")
            return
        
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
        self.listening_thread.start()
        
        self.logger.info("Wake word detection started")
    
    def stop_listening(self):
        """Stop wake word detection"""
        self.is_listening = False
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2.0)
        
        self.logger.info("Wake word detection stopped")
    
    def _listening_loop(self):
        """Main listening loop for wake word detection"""
        try:
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.logger.info("Microphone calibrated for ambient noise")
            
            while self.is_listening:
                try:
                    # Listen for audio
                    with self.microphone as source:
                        audio = self.recognizer.listen(
                            source, 
                            timeout=1, 
                            phrase_time_limit=3
                        )
                    
                    # Add to buffer
                    self.audio_buffer.append(audio)
                    
                    # Process audio for wake words
                    self._process_audio(audio)
                    
                except sr.WaitTimeoutError:
                    # No speech detected, continue listening
                    continue
                except sr.UnknownValueError:
                    # Speech not recognized, continue listening
                    continue
                except sr.RequestError as e:
                    self.logger.error("Speech recognition service error", error=str(e))
                    time.sleep(1)
                except Exception as e:
                    self.logger.error("Unexpected error in listening loop", exception=e)
                    time.sleep(1)
        
        except Exception as e:
            self.logger.critical("Critical error in wake word detection", exception=e)
    
    def _process_audio(self, audio):
        """Process audio for wake word detection"""
        try:
            # Recognize speech
            text = self.recognizer.recognize_google(audio).lower()
            
            # Check for wake words
            wake_word_detected, confidence = self._detect_wake_word(text)
            
            if wake_word_detected:
                self._handle_wake_word_detection(text, confidence)
            
        except sr.UnknownValueError:
            # Speech not recognized, this is normal
            pass
        except Exception as e:
            self.logger.error("Error processing audio", exception=e)
    
    def _detect_wake_word(self, text: str) -> tuple[bool, float]:
        """Detect if text contains a wake word with confidence scoring"""
        if not text:
            return False, 0.0
        
        best_confidence = 0.0
        detected_word = None
        
        for wake_word in self.wake_words:
            # Check for exact match
            if wake_word in text:
                confidence = 1.0
            else:
                # Check for partial match with fuzzy matching
                confidence = self._calculate_similarity(text, wake_word)
            
            if confidence > best_confidence:
                best_confidence = confidence
                detected_word = wake_word
        
        # Apply sensitivity threshold
        if best_confidence >= self.sensitivity:
            self.logger.debug("Wake word detected", 
                            text=text, 
                            wake_word=detected_word, 
                            confidence=best_confidence)
            return True, best_confidence
        
        return False, best_confidence
    
    def _calculate_similarity(self, text: str, wake_word: str) -> float:
        """Calculate similarity between text and wake word"""
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, text, wake_word).ratio()
        except ImportError:
            # Fallback to simple substring matching
            return 1.0 if wake_word in text else 0.0
    
    def _handle_wake_word_detection(self, text: str, confidence: float):
        """Handle wake word detection"""
        start_time = time.time()
        
        # Update metrics
        self.detection_count += 1
        self.confidence_scores.append(confidence)
        
        # Calculate average response time
        response_time = time.time() - start_time
        self.avg_response_time = (
            (self.avg_response_time * (self.detection_count - 1) + response_time) 
            / self.detection_count
        )
        
        # Log detection
        self.logger.info("Wake word detected", 
                        text=text, 
                        confidence=confidence,
                        response_time=response_time,
                        total_detections=self.detection_count)
        
        # Call wake word callback
        if self.wake_word_callback:
            try:
                self.wake_word_callback(text, confidence)
            except Exception as e:
                self.logger.error("Error in wake word callback", exception=e)
        
        # Handle activation/deactivation
        if not self.is_activated:
            self._activate_assistant()
        else:
            self._deactivate_assistant()
    
    def _activate_assistant(self):
        """Activate the assistant"""
        self.is_activated = True
        self.logger.info("Assistant activated")
        
        if self.activation_callback:
            try:
                self.activation_callback()
            except Exception as e:
                self.logger.error("Error in activation callback", exception=e)
    
    def _deactivate_assistant(self):
        """Deactivate the assistant"""
        self.is_activated = False
        self.logger.info("Assistant deactivated")
        
        if self.deactivation_callback:
            try:
                self.deactivation_callback()
            except Exception as e:
                self.logger.error("Error in deactivation callback", exception=e)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get detection statistics"""
        avg_confidence = (
            sum(self.confidence_scores) / len(self.confidence_scores) 
            if self.confidence_scores else 0.0
        )
        
        return {
            "is_listening": self.is_listening,
            "is_activated": self.is_activated,
            "detection_count": self.detection_count,
            "false_positive_count": self.false_positive_count,
            "avg_confidence": avg_confidence,
            "avg_response_time": self.avg_response_time,
            "wake_words": self.wake_words,
            "sensitivity": self.sensitivity
        }
    
    def reset_stats(self):
        """Reset detection statistics"""
        self.detection_count = 0
        self.false_positive_count = 0
        self.avg_response_time = 0.0
        self.confidence_scores.clear()
        self.logger.info("Statistics reset")

class VoicePersonalityManager:
    """Manage multiple voice personalities for Ashley AI"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_enhanced_logger("voice_personality")
        self.current_personality = "ashley"
        
        # Define voice personalities
        self.personalities = {
            "ashley": {
                "voice": "en-GB-LibbyNeural",
                "rate": "slow",
                "pitch": "low",
                "style": "friendly",
                "description": "Friendly and approachable British assistant"
            },
            "alex": {
                "voice": "en-US-MichelleNeural",
                "rate": "medium",
                "pitch": "medium",
                "style": "professional",
                "description": "Professional and efficient American assistant"
            },
            "sarah": {
                "voice": "en-AU-NatashaNeural",
                "rate": "fast",
                "pitch": "high",
                "style": "energetic",
                "description": "Energetic and enthusiastic Australian assistant"
            },
            "david": {
                "voice": "en-GB-RyanNeural",
                "rate": "slow",
                "pitch": "low",
                "style": "calm",
                "description": "Calm and reassuring British assistant"
            },
            "emma": {
                "voice": "en-US-AriaNeural",
                "rate": "medium",
                "pitch": "high",
                "style": "cheerful",
                "description": "Cheerful and optimistic American assistant"
            }
        }
        
        self.logger.info("Voice personality manager initialized", 
                        personalities=list(self.personalities.keys()))
    
    def get_personality(self, name: str) -> Optional[Dict[str, str]]:
        """Get personality configuration by name"""
        return self.personalities.get(name.lower())
    
    def set_personality(self, name: str) -> bool:
        """Set the current voice personality"""
        if name.lower() in self.personalities:
            self.current_personality = name.lower()
            self.logger.info("Voice personality changed", 
                           old_personality=self.current_personality,
                           new_personality=name.lower())
            return True
        else:
            self.logger.warning("Unknown personality", personality=name)
            return False
    
    def get_current_personality(self) -> Dict[str, str]:
        """Get current personality configuration"""
        return self.personalities[self.current_personality]
    
    def list_personalities(self) -> Dict[str, Dict[str, str]]:
        """List all available personalities"""
        return self.personalities.copy()
    
    def add_personality(self, name: str, config: Dict[str, str]) -> bool:
        """Add a new voice personality"""
        required_keys = ["voice", "rate", "pitch", "style", "description"]
        
        if all(key in config for key in required_keys):
            self.personalities[name.lower()] = config
            self.logger.info("New personality added", personality=name, config=config)
            return True
        else:
            self.logger.error("Invalid personality configuration", 
                            personality=name, 
                            required_keys=required_keys)
            return False
    
    def remove_personality(self, name: str) -> bool:
        """Remove a voice personality (cannot remove default personalities)"""
        if name.lower() in ["ashley", "alex", "sarah", "david", "emma"]:
            self.logger.warning("Cannot remove default personality", personality=name)
            return False
        
        if name.lower() in self.personalities:
            del self.personalities[name.lower()]
            self.logger.info("Personality removed", personality=name)
            return True
        else:
            self.logger.warning("Personality not found", personality=name)
            return False
    
    def speak_with_personality(self, text: str, personality: Optional[str] = None, 
                              use_ssml: bool = True) -> bool:
        """Speak text with specified personality"""
        try:
            from tts import speak
            
            # Use specified personality or current one
            personality_name = personality or self.current_personality
            personality_config = self.get_personality(personality_name)
            
            if not personality_config:
                self.logger.error("Personality not found", personality=personality_name)
                return False
            
            if use_ssml:
                # Create SSML with personality settings
                ssml_text = f'''
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                    <voice name="{personality_config['voice']}">
                        <prosody rate="{personality_config['rate']}" pitch="{personality_config['pitch']}">
                            {text}
                        </prosody>
                    </voice>
                </speak>
                '''
                speak(ssml_text, use_ssml=True)
            else:
                speak(text, voice=personality_config['voice'])
            
            self.logger.debug("Text spoken with personality", 
                            text=text[:50] + "...", 
                            personality=personality_name)
            return True
            
        except Exception as e:
            self.logger.error("Error speaking with personality", 
                            personality=personality_name, 
                            exception=e)
            return False

# Global instances
wake_word_detector = WakeWordDetector()
voice_personality_manager = VoicePersonalityManager()

# Example usage and testing
if __name__ == "__main__":
    # Test wake word detection
    print("Testing Wake Word Detection")
    print("=" * 40)
    
    def on_wake_word(text, confidence):
        print(f"Wake word detected: '{text}' (confidence: {confidence:.2f})")
    
    def on_activation():
        print("Assistant activated!")
    
    def on_deactivation():
        print("Assistant deactivated!")
    
    # Set up callbacks
    wake_word_detector.set_wake_word_callback(on_wake_word)
    wake_word_detector.set_activation_callback(on_activation)
    wake_word_detector.set_deactivation_callback(on_deactivation)
    
    # Test voice personalities
    print("\nTesting Voice Personalities")
    print("=" * 40)
    
    personalities = voice_personality_manager.list_personalities()
    for name, config in personalities.items():
        print(f"{name}: {config['description']}")
    
    # Test personality switching
    print(f"\nCurrent personality: {voice_personality_manager.current_personality}")
    
    if voice_personality_manager.set_personality("alex"):
        print("Switched to Alex personality")
    
    print(f"Current personality: {voice_personality_manager.current_personality}")
    
    # Test stats
    stats = wake_word_detector.get_stats()
    print(f"\nWake word detector stats: {stats}")
    
    print("\nWake word detection ready. Say 'Hey Ashley' to test!")
    print("Press Ctrl+C to stop...")
    
    try:
        wake_word_detector.start_listening()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        wake_word_detector.stop_listening()
        print("\nWake word detection stopped.")


