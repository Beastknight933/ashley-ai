"""
Enhanced Text-to-Speech system with multiple personalities and advanced features
"""

import asyncio
import edge_tts
import pygame
import tempfile
import os
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from enhanced_logging import get_enhanced_logger, log_performance
from enhanced_config import get_config
from wake_word_detector import voice_personality_manager

class EnhancedTTS:
    """Enhanced Text-to-Speech with multiple personalities and advanced features"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_enhanced_logger("enhanced_tts")
        self.personality_manager = voice_personality_manager
        
        # Audio settings
        self.audio_cache_dir = Path("audio_cache")
        self.audio_cache_dir.mkdir(exist_ok=True)
        
        # Performance tracking
        self.synthesis_times = []
        self.playback_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Audio queue for continuous playback
        self.audio_queue = asyncio.Queue()
        self.is_playing = False
        self.playback_task = None
        
        # Initialize pygame mixer
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        self.logger.info("Enhanced TTS initialized")
    
    @log_performance("tts_synthesis")
    async def synthesize_speech(self, text: str, voice: str = None, 
                              rate: str = "medium", pitch: str = "medium", 
                              use_ssml: bool = True) -> bytes:
        """Synthesize speech and return audio data"""
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(text, voice, rate, pitch, use_ssml)
            cache_file = self.audio_cache_dir / f"{cache_key}.mp3"
            
            # Check cache first
            if cache_file.exists():
                self.cache_hits += 1
                self.logger.debug("Audio cache hit", cache_key=cache_key)
                return cache_file.read_bytes()
            
            self.cache_misses += 1
            
            # Prepare text for synthesis
            if use_ssml:
                ssml_text = self._create_ssml(text, voice, rate, pitch)
                synthesis_text = ssml_text
            else:
                synthesis_text = text
            
            # Synthesize speech
            start_time = time.time()
            
            communicate = edge_tts.Communicate(synthesis_text, voice or self.config.default_voice)
            audio_data = b""
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            synthesis_time = time.time() - start_time
            self.synthesis_times.append(synthesis_time)
            
            # Cache the result
            cache_file.write_bytes(audio_data)
            
            self.logger.debug("Speech synthesized", 
                            text_length=len(text),
                            voice=voice,
                            synthesis_time=synthesis_time,
                            cache_key=cache_key)
            
            return audio_data
            
        except Exception as e:
            self.logger.error("Speech synthesis failed", 
                            text=text[:50] + "...", 
                            voice=voice, 
                            exception=e)
            raise
    
    def _create_ssml(self, text: str, voice: str, rate: str, pitch: str) -> str:
        """Create SSML markup for enhanced speech synthesis"""
        # Map rate and pitch to SSML values
        rate_map = {
            "slow": "0.8",
            "medium": "1.0",
            "fast": "1.2",
            "very_slow": "0.6",
            "very_fast": "1.4"
        }
        
        pitch_map = {
            "low": "-20%",
            "medium": "0%",
            "high": "+20%",
            "very_low": "-40%",
            "very_high": "+40%"
        }
        
        ssml_rate = rate_map.get(rate, "1.0")
        ssml_pitch = pitch_map.get(pitch, "0%")
        
        return f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{voice}">
                <prosody rate="{ssml_rate}" pitch="{ssml_pitch}">
                    {text}
                </prosody>
            </voice>
        </speak>
        '''
    
    def _generate_cache_key(self, text: str, voice: str, rate: str, 
                          pitch: str, use_ssml: bool) -> str:
        """Generate cache key for audio data"""
        import hashlib
        
        key_data = f"{text}|{voice}|{rate}|{pitch}|{use_ssml}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @log_performance("tts_playback")
    def play_audio(self, audio_data: bytes) -> bool:
        """Play audio data synchronously"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Play audio
            start_time = time.time()
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            playback_time = time.time() - start_time
            self.playback_times.append(playback_time)
            
            # Clean up
            os.unlink(temp_file_path)
            
            self.logger.debug("Audio played", playback_time=playback_time)
            return True
            
        except Exception as e:
            self.logger.error("Audio playback failed", exception=e)
            return False
    
    async def speak_async(self, text: str, personality: str = None, 
                         use_ssml: bool = True) -> bool:
        """Speak text asynchronously with specified personality"""
        try:
            # Get personality configuration
            if personality:
                personality_config = self.personality_manager.get_personality(personality)
                if not personality_config:
                    self.logger.warning("Personality not found, using current", 
                                      personality=personality)
                    personality_config = self.personality_manager.get_current_personality()
            else:
                personality_config = self.personality_manager.get_current_personality()
            
            # Synthesize speech
            audio_data = await self.synthesize_speech(
                text=text,
                voice=personality_config["voice"],
                rate=personality_config["rate"],
                pitch=personality_config["pitch"],
                use_ssml=use_ssml
            )
            
            # Play audio
            return self.play_audio(audio_data)
            
        except Exception as e:
            self.logger.error("Async speech failed", 
                            text=text[:50] + "...", 
                            personality=personality, 
                            exception=e)
            return False
    
    def speak(self, text: str, personality: str = None, use_ssml: bool = True) -> bool:
        """Speak text synchronously with specified personality"""
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.speak_async(text, personality, use_ssml))
            loop.close()
            return result
        except Exception as e:
            self.logger.error("Sync speech failed", 
                            text=text[:50] + "...", 
                            personality=personality, 
                            exception=e)
            return False
    
    def speak_with_emotion(self, text: str, emotion: str = "neutral", 
                          personality: str = None) -> bool:
        """Speak text with emotional tone"""
        try:
            # Map emotions to SSML parameters
            emotion_map = {
                "happy": {"rate": "1.1", "pitch": "+10%"},
                "sad": {"rate": "0.9", "pitch": "-10%"},
                "excited": {"rate": "1.2", "pitch": "+15%"},
                "calm": {"rate": "0.8", "pitch": "-5%"},
                "angry": {"rate": "1.0", "pitch": "-5%"},
                "surprised": {"rate": "1.1", "pitch": "+20%"},
                "neutral": {"rate": "1.0", "pitch": "0%"}
            }
            
            emotion_config = emotion_map.get(emotion, emotion_map["neutral"])
            
            # Get personality configuration
            if personality:
                personality_config = self.personality_manager.get_personality(personality)
            else:
                personality_config = self.personality_manager.get_current_personality()
            
            # Create emotional SSML
            ssml_text = f'''
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="{personality_config['voice']}">
                    <prosody rate="{emotion_config['rate']}" pitch="{emotion_config['pitch']}">
                        {text}
                    </prosody>
                </voice>
            </speak>
            '''
            
            # Synthesize and play
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_data = loop.run_until_complete(
                self.synthesize_speech(ssml_text, personality_config["voice"], use_ssml=True)
            )
            result = self.play_audio(audio_data)
            loop.close()
            
            self.logger.debug("Emotional speech", 
                            emotion=emotion, 
                            personality=personality)
            return result
            
        except Exception as e:
            self.logger.error("Emotional speech failed", 
                            emotion=emotion, 
                            personality=personality, 
                            exception=e)
            return False
    
    def speak_multiple(self, texts: List[str], personality: str = None, 
                      delay: float = 0.5) -> bool:
        """Speak multiple texts in sequence"""
        try:
            for i, text in enumerate(texts):
                if i > 0:
                    time.sleep(delay)
                
                success = self.speak(text, personality)
                if not success:
                    self.logger.warning("Failed to speak text in sequence", 
                                      index=i, text=text[:50] + "...")
                    return False
            
            self.logger.debug("Multiple texts spoken", count=len(texts))
            return True
            
        except Exception as e:
            self.logger.error("Multiple speech failed", 
                            count=len(texts), 
                            exception=e)
            return False
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available voices"""
        try:
            # This would typically query the TTS service for available voices
            # For now, return a predefined list
            return [
                {"name": "en-US-MichelleNeural", "gender": "female", "locale": "en-US"},
                {"name": "en-GB-LibbyNeural", "gender": "female", "locale": "en-GB"},
                {"name": "en-AU-NatashaNeural", "gender": "female", "locale": "en-AU"},
                {"name": "en-GB-RyanNeural", "gender": "male", "locale": "en-GB"},
                {"name": "en-US-AriaNeural", "gender": "female", "locale": "en-US"},
            ]
        except Exception as e:
            self.logger.error("Failed to get available voices", exception=e)
            return []
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get TTS performance statistics"""
        avg_synthesis = (
            sum(self.synthesis_times) / len(self.synthesis_times) 
            if self.synthesis_times else 0.0
        )
        avg_playback = (
            sum(self.playback_times) / len(self.playback_times) 
            if self.playback_times else 0.0
        )
        
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses) 
            if (self.cache_hits + self.cache_misses) > 0 else 0.0
        )
        
        return {
            "avg_synthesis_time": avg_synthesis,
            "avg_playback_time": avg_playback,
            "total_synthesis_count": len(self.synthesis_times),
            "total_playback_count": len(self.playback_times),
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_size": len(list(self.audio_cache_dir.glob("*.mp3")))
        }
    
    def clear_cache(self):
        """Clear audio cache"""
        try:
            for cache_file in self.audio_cache_dir.glob("*.mp3"):
                cache_file.unlink()
            
            self.cache_hits = 0
            self.cache_misses = 0
            
            self.logger.info("Audio cache cleared")
        except Exception as e:
            self.logger.error("Failed to clear cache", exception=e)
    
    def cleanup(self):
        """Cleanup TTS resources"""
        try:
            pygame.mixer.quit()
            self.logger.info("TTS cleanup completed")
        except Exception as e:
            self.logger.error("TTS cleanup failed", exception=e)

# Global TTS instance
enhanced_tts = EnhancedTTS()

# Convenience functions for backward compatibility
def speak(text: str, voice: str = None, use_ssml: bool = True) -> bool:
    """Speak text with enhanced TTS"""
    return enhanced_tts.speak(text, voice, use_ssml)

def speak_with_personality(text: str, personality: str = None) -> bool:
    """Speak text with specified personality"""
    return enhanced_tts.speak(text, personality)

def speak_with_emotion(text: str, emotion: str = "neutral", personality: str = None) -> bool:
    """Speak text with emotional tone"""
    return enhanced_tts.speak_with_emotion(text, emotion, personality)

def cleanup():
    """Cleanup TTS resources"""
    enhanced_tts.cleanup()

# Example usage and testing
if __name__ == "__main__":
    print("Testing Enhanced TTS System")
    print("=" * 40)
    
    # Test basic speech
    print("Testing basic speech...")
    success = speak("Hello, I'm Ashley, your AI assistant.")
    print(f"Basic speech: {'Success' if success else 'Failed'}")
    
    # Test personality switching
    print("\nTesting personality switching...")
    personalities = voice_personality_manager.list_personalities()
    
    for name, config in personalities.items():
        print(f"Testing {name} personality...")
        success = speak_with_personality(f"Hello, I'm {name}. {config['description']}", name)
        print(f"{name}: {'Success' if success else 'Failed'}")
        time.sleep(1)
    
    # Test emotional speech
    print("\nTesting emotional speech...")
    emotions = ["happy", "sad", "excited", "calm", "surprised"]
    
    for emotion in emotions:
        print(f"Testing {emotion} emotion...")
        success = speak_with_emotion(f"I'm feeling {emotion} today!", emotion)
        print(f"{emotion}: {'Success' if success else 'Failed'}")
        time.sleep(1)
    
    # Test performance stats
    print("\nPerformance Statistics:")
    stats = enhanced_tts.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nEnhanced TTS testing completed!")


