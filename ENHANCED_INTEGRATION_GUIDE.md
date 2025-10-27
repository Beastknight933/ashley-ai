# Ashley AI - Enhanced Integration Guide

This guide explains how to integrate all the enhanced systems into the main Ashley AI application.

## 🚀 **Completed Upgrades**

### ✅ **Point 1: Modern Dependencies & Compatibility**
- Updated `requirements.txt` with modern, compatible versions
- Fixed Python 3.12 compatibility issues
- Added enhanced dependencies for better performance

### ✅ **Point 2: Enhanced Error Handling & Logging**
- Created `enhanced_logging.py` with structured logging
- Updated `error_handler.py` to use enhanced logging
- Added error recovery mechanisms and health monitoring

### ✅ **Point 3: Configuration Management**
- Created `enhanced_config.py` with Pydantic validation
- Environment-based configuration with `.env` support
- Hot-reloading and validation capabilities

### ✅ **Point 5: Voice Processing Upgrades**
- Created `wake_word_detector.py` for "Hey Ashley" activation
- Created `enhanced_tts.py` with multiple voice personalities
- Added emotional speech and performance monitoring

### ✅ **Point 6: Memory & Context Management**
- Created `conversation_memory.py` with persistent storage
- SQLite database for conversation history
- Context-aware conversation analysis

## 🔧 **Integration Steps**

### **Step 1: Update main.py**

Replace the existing `main.py` with the enhanced version:

```python
import datetime
import logging
from enhanced_config import get_config, get_config_value
from enhanced_logging import get_enhanced_logger
from error_handler import handle_errors, ModuleImportError, APIError
from wake_word_detector import wake_word_detector, voice_personality_manager
from enhanced_tts import enhanced_tts, speak_with_personality
from conversation_memory import conversation_memory, save_conversation, get_conversation_context
from alarm import create_event
from weather_utils import handle_temperature, handle_weather
from stt import take_command, calibrate_microphone, get_microphone_source
from nlp_processor import get_intent_hybrid, get_intent_with_context, fallback_openrouter_gpt5

# Initialize enhanced systems
config = get_config()
logger = get_enhanced_logger("main")
logger.set_context(assistant_name=config.assistant_name, version=config.assistant_version)

# OpenRouter API Key
OPENROUTER_API_KEY = get_config_value("openrouter_api_key", "")

# Wake word detection callbacks
def on_wake_word_detected(text: str, confidence: float):
    """Handle wake word detection"""
    logger.info("Wake word detected", text=text, confidence=confidence)
    speak_with_personality("Yes, I'm listening...")

def on_assistant_activation():
    """Handle assistant activation"""
    logger.info("Assistant activated")
    speak_with_personality("Hello! I'm ready to help you.")

def on_assistant_deactivation():
    """Handle assistant deactivation"""
    logger.info("Assistant deactivated")
    speak_with_personality("Goodbye! I'm here when you need me.")

# Set up wake word detection
wake_word_detector.set_wake_word_callback(on_wake_word_detected)
wake_word_detector.set_activation_callback(on_assistant_activation)
wake_word_detector.set_deactivation_callback(on_assistant_deactivation)

# ... rest of the enhanced main.py implementation
```

### **Step 2: Environment Configuration**

Create a `.env` file based on `env_template.txt`:

```bash
# Copy the template
cp env_template.txt .env

# Edit with your actual values
# ASSISTANT_NAME=Ashley
# OPENROUTER_API_KEY=your_actual_key_here
# OPENWEATHER_API_KEY=your_weather_key_here
# etc.
```

### **Step 3: Install Dependencies**

```bash
pip install -r requirements.txt
```

### **Step 4: Initialize Database**

The conversation memory system will automatically create the database on first run.

## 🎯 **Key Features Now Available**

### **1. Wake Word Detection**
- Say "Hey Ashley" to activate the assistant
- Continuous listening mode available
- Configurable sensitivity and wake words

### **2. Multiple Voice Personalities**
- Ashley (British, friendly)
- Alex (American, professional)
- Sarah (Australian, energetic)
- David (British, calm)
- Emma (American, cheerful)

### **3. Enhanced Logging**
- Structured JSON logging
- Performance monitoring
- Health status tracking
- Error recovery

### **4. Persistent Memory**
- Conversation history storage
- User preference learning
- Context-aware responses
- Topic and mood analysis

### **5. Advanced Configuration**
- Environment variable support
- Hot-reloading configuration
- Validation and error checking
- Multiple configuration sources

## 🚀 **Usage Examples**

### **Basic Usage with Wake Word**
```python
# Start the enhanced assistant
python main.py

# Say "Hey Ashley" to activate
# Then give your command
# Say "goodbye" to deactivate
```

### **Using Different Personalities**
```python
# Switch to Alex personality
voice_personality_manager.set_personality("alex")
speak_with_personality("Hello, I'm Alex, your professional assistant.")

# Switch to Sarah personality
voice_personality_manager.set_personality("sarah")
speak_with_personality("Hi there! I'm Sarah, ready to help!")
```

### **Emotional Speech**
```python
# Speak with different emotions
enhanced_tts.speak_with_emotion("I'm so excited to help you!", "excited")
enhanced_tts.speak_with_emotion("I'm sorry to hear that.", "sad")
enhanced_tts.speak_with_emotion("That's wonderful news!", "happy")
```

### **Memory and Context**
```python
# Save conversation
save_conversation(
    user_input="What's the weather like?",
    intent="weather",
    confidence=0.88,
    entities={"location": ["here"]},
    response="Let me check the weather for you.",
    session_id="user_123"
)

# Get conversation context
context = get_conversation_context("user_123")
print(f"Topic: {context['conversation_topic']}")
print(f"Mood: {context['user_mood']}")
```

## 📊 **Monitoring and Health**

### **Check System Health**
```python
from enhanced_logging import get_enhanced_logger

logger = get_enhanced_logger("health")
health_status = logger.get_health_status()
print(f"System status: {health_status['status']}")
```

### **View Performance Stats**
```python
# TTS performance
tts_stats = enhanced_tts.get_performance_stats()
print(f"Average synthesis time: {tts_stats['avg_synthesis_time']:.2f}s")

# Memory stats
memory_stats = conversation_memory.get_memory_stats()
print(f"Conversations stored: {memory_stats['conversation_count']}")
```

### **Configuration Health**
```python
from enhanced_config import get_config_health

health = get_config_health()
print(f"Configuration status: {health['status']}")
print(f"Issues: {health['issues']}")
```

## 🔧 **Configuration Options**

### **Voice Settings**
```python
# Set default voice
config.set("default_voice", "en-GB-LibbyNeural")

# Set wake words
config.set("wake_words", ["hey ashley", "ashley", "wake up"])

# Set sensitivity
config.set("wake_word_sensitivity", 0.7)
```

### **Memory Settings**
```python
# Set retention period
config.set("conversation_retention_days", 30)

# Set context history length
config.set("max_conversation_history", 15)
```

### **Logging Settings**
```python
# Set log level
config.set("log_level", "DEBUG")

# Enable structured logging
config.set("enable_structured_logging", True)
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Wake word not detected**
   - Check microphone permissions
   - Adjust sensitivity: `config.set("wake_word_sensitivity", 0.5)`
   - Try different wake words

2. **TTS not working**
   - Check internet connection (for edge-tts)
   - Verify voice names are correct
   - Check audio output device

3. **Database errors**
   - Check file permissions
   - Ensure SQLite is available
   - Check disk space

4. **Configuration issues**
   - Validate configuration: `python -c "from enhanced_config import validate_config; print(validate_config())"`
   - Check environment variables
   - Verify .env file format

### **Debug Mode**
```python
# Enable debug logging
config.set("debug_mode", True)
config.set("log_level", "DEBUG")
```

## 📈 **Performance Optimization**

### **TTS Caching**
- Audio is automatically cached for repeated phrases
- Clear cache: `enhanced_tts.clear_cache()`

### **Database Optimization**
- Old conversations are automatically cleaned up
- Manual cleanup: `conversation_memory.cleanup_old_data()`

### **Memory Management**
- Context history is limited to prevent memory bloat
- Adjust: `config.set("max_conversation_history", 10)`

## 🎉 **Next Steps**

With these enhancements, Ashley AI now has:

1. **Professional-grade logging and error handling**
2. **Advanced voice processing with wake words and personalities**
3. **Persistent memory and context awareness**
4. **Modern configuration management**
5. **Comprehensive monitoring and health checks**

The system is now ready for production use and can be easily extended with additional features!


