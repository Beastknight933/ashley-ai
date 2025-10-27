# AI Assistant Setup Guide

Complete setup instructions for the AI Assistant project.

---

## 📋 Prerequisites

- **Python 3.8+** (tested on 3.9-3.11)
- **Microphone** for voice input
- **Speakers** for audio output
- **Google Account** for Calendar integration (optional)
- **Internet connection** for API services

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <your-project-folder>
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
# Copy the template
cp .env.template .env

# Edit .env and add your API keys
# Use your favorite text editor
notepad .env      # Windows
nano .env         # Linux/macOS
```

### 5. Configure Google Calendar (Optional)
If you want alarm functionality:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Google Calendar API**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download the credentials as `credentials.json`
6. Place `credentials.json` in the project root

### 6. Run the Assistant
```bash
# Using the updated main file
python AI_main.py

# Or test the alarm system
python alarm.py
```

---

## 🔑 API Keys Setup

### OpenWeather API (Weather Features)
1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key
4. Add to `.env`:
   ```
   OPENWEATHER_API_KEY=your_key_here
   ```

### OpenRouter API (GPT Integration - Future)
1. Visit [OpenRouter](https://openrouter.ai/)
2. Create an account
3. Generate an API key
4. Add to `.env`:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```

---

## 🏗️ Project Structure

```
project/
├── AI_main.py              # Main assistant loop (use this)
├── trial_main.py           # Testing new features
├── alarm.py                # Alarm system (fixed version)
├── config.py               # Configuration management
├── error_handler.py        # Error handling framework
├── services.py             # Service layer (decoupled)
├── tts.py                  # Text-to-Speech
├── stt.py                  # Speech-to-Text
├── weather_utils.py        # Weather functions
├── SearchNow.py            # Search functions
├── Dictapp.py              # App control
├── GreetMe.py              # Greeting module
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
├── .env.template           # Environment template
├── .gitignore              # Git ignore rules
├── credentials.json        # Google OAuth (you provide)
└── assistant.log           # Log file (auto-generated)
```

---

## 🎯 Features

### ✅ Currently Working
- ✓ Voice recognition (Speech-to-Text)
- ✓ Text-to-Speech responses
- ✓ Weather information
- ✓ Google/YouTube/Wikipedia search
- ✓ Open/close applications
- ✓ Time and date queries
- ✓ Basic conversations
- ✓ Google Calendar integration for alarms

### 🚧 In Development
- ⏳ GPT-5 integration (planned)
- ⏳ NLP intent recognition (optional)
- ⏳ Frontend interface
- ⏳ Task management

---

## 🎤 Voice Commands

### General
- "Wake up" - Start conversation
- "Hello" - Greeting
- "What's your name?" - Assistant identity
- "Stop/Exit/Quit" - Exit assistant

### Search
- "Google [query]" - Search Google
- "YouTube [query]" - Search YouTube
- "Wikipedia [query]" - Search Wikipedia

### Weather
- "What's the temperature?" - Current temperature
- "What's the weather?" - Current weather
- "Temperature in [city]" - Temperature for specific city

### Time & Date
- "What time is it?" - Current time
- "What's the date?" - Current date

### Apps
- "Open [app name]" - Open application
- "Close [app name]" - Close application

### Alarms
- "Set an alarm" - Set new alarm
- "List alarms" - Show all alarms
- "Cancel alarm" - Cancel specific alarm

---

## 🔧 Configuration

### Changing Assistant Name
Edit `.env` or `config.json`:
```
ASSISTANT_NAME=YourName
```

### Changing TTS Voice
Available voices:
- `en-US-MichelleNeural` (default, female)
- `en-US-GuyNeural` (male)
- `en-GB-LibbyNeural` (British female)
- `en-GB-RyanNeural` (British male)

Edit in `.env`:
```
TTS_VOICE=en-US-GuyNeural
```

### Adjusting Microphone Sensitivity
Edit `config.py` defaults:
```python
'STT_ENERGY_THRESHOLD': 300,  # Increase if too sensitive
'STT_PAUSE_THRESHOLD': 1.5,   # Seconds of silence to end phrase
```

---

## 🐛 Troubleshooting

### "Microphone not detected"
```bash
# Test microphone
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# If empty, check:
# - Microphone is plugged in
# - Microphone permissions in OS settings
# - Try different USB port
```

### "Google Calendar not working"
1. Check `credentials.json` is in project root
2. Delete `token.pickle` and re-authenticate
3. Ensure Google Calendar API is enabled in Cloud Console

### "No module named 'X'"
```bash
pip install -r requirements.txt --upgrade
```

### "API key error"
1. Check `.env` file exists
2. Verify API keys are correct (no extra spaces)
3. Test API key in browser/Postman first

### "TTS files not cleaning up"
The updated `tts.py` auto-cleans. If issues persist:
```bash
# Manual cleanup
python -c "from tts import cleanup; cleanup()"
```

---

## 📝 Logging

Logs are saved to `assistant.log`. Check this file for detailed error information.

View logs:
```bash
# Windows
type assistant.log

# Linux/macOS
tail -f assistant.log
```

Change log level in `.env`:
```
LOG_LEVEL=DEBUG  # For verbose logging
LOG_LEVEL=INFO   # Normal (default)
LOG_LEVEL=ERROR  # Errors only
```

---

## 🔒 Security Best Practices

1. **Never commit** `.env` or `credentials.json`
2. **Rotate API keys** periodically
3. **Use environment variables** for all secrets
4. **Review `.gitignore`** before pushing code
5. **Keep dependencies updated**: `pip list --outdated`

---

## 🤝 Contributing

When testing new features:
1. Use `trial_main.py` for experiments
2. Once stable, migrate to `AI_main.py`
3. Update this README with new features
4. Test error handling thoroughly

---

## 📚 Next Steps

### Immediate (Priority)
1. ✅ Set up environment variables
2. ✅ Test basic voice commands
3. ✅ Configure alarm system
4. ⏳ Move API keys to `.env`

### Short Term
1. Integrate GPT-5 API
2. Remove old NLP files (after GPT works)
3. Build basic frontend
4. Add unit tests

### Long Term
1. Advanced NLP understanding
2. Context-aware conversations
3. Multi-language support
4. Mobile app integration

---

## 📞 Support

If you encounter issues:
1. Check `assistant.log` for errors
2. Review this setup guide
3. Check the troubleshooting section
4. Verify all dependencies are installed

---

## 📄 License

[Add your license here]

---

**Happy Coding! 🎉**