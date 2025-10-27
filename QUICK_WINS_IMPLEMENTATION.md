# Ashley AI - Quick Wins Implementation Guide

This guide provides step-by-step instructions for implementing the most impactful upgrades that can be done immediately.

## 🚀 **Quick Win #1: Wake Word Detection**

### **Implementation**
Create a new file `wake_word_detector.py`:

```python
import speech_recognition as sr
import threading
import time
from collections import deque

class WakeWordDetector:
    def __init__(self, wake_words=["hey ashley", "ashley", "wake up ashley"]):
        self.wake_words = [word.lower() for word in wake_words]
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.audio_buffer = deque(maxlen=10)
        
    def start_listening(self, callback):
        """Start continuous listening for wake words"""
        self.is_listening = True
        threading.Thread(target=self._listen_loop, args=(callback,), daemon=True).start()
    
    def _listen_loop(self, callback):
        """Main listening loop"""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        while self.is_listening:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    self.audio_buffer.append(audio)
                    
                    # Try to recognize speech
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        if any(wake_word in text for wake_word in self.wake_words):
                            callback(text)
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"Wake word recognition error: {e}")
                        
            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                print(f"Wake word detection error: {e}")
                time.sleep(1)
    
    def stop_listening(self):
        """Stop wake word detection"""
        self.is_listening = False
```

### **Integration with main.py**
```python
# Add to main.py
from wake_word_detector import WakeWordDetector

def on_wake_word_detected(text):
    print(f"Wake word detected: {text}")
    speak("Yes, I'm listening...")
    # Continue with normal command processing

# In assistant_loop(), replace the while True loop:
wake_detector = WakeWordDetector()
wake_detector.start_listening(on_wake_word_detected)

# Modified main loop
while True:
    try:
        # Wait for wake word, then process command
        query = take_command(source)
        # ... rest of the processing
    except KeyboardInterrupt:
        wake_detector.stop_listening()
        break
```

## 🚀 **Quick Win #2: Conversation Persistence**

### **Implementation**
Create `conversation_db.py`:

```python
import sqlite3
import json
import datetime
from typing import List, Dict, Optional

class ConversationDB:
    def __init__(self, db_path="conversations.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the conversation database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT NOT NULL,
                intent TEXT,
                confidence REAL,
                entities TEXT,
                response TEXT,
                success BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_input: str, intent: str, confidence: float, 
                         entities: Dict, response: str, success: bool):
        """Save a conversation turn"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations 
            (user_input, intent, confidence, entities, response, success)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_input, intent, confidence, json.dumps(entities), response, success))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_input, intent, confidence, entities, response, success, timestamp
            FROM conversations 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'user_input': row[0],
                'intent': row[1],
                'confidence': row[2],
                'entities': json.loads(row[3]) if row[3] else {},
                'response': row[4],
                'success': bool(row[5]),
                'timestamp': row[6]
            })
        
        conn.close()
        return conversations
    
    def get_user_preference(self, key: str) -> Optional[str]:
        """Get user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    
    def set_user_preference(self, key: str, value: str):
        """Set user preference"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, value))
        
        conn.commit()
        conn.close()
```

### **Integration with main.py**
```python
# Add to main.py
from conversation_db import ConversationDB

# Initialize database
conversation_db = ConversationDB()

# In assistant_loop(), after processing each command:
conversation_db.save_conversation(
    user_input=query,
    intent=intent,
    confidence=confidence,
    entities=entities,
    response=response_text,  # Store the response text
    success=True  # or False if error occurred
)
```

## 🚀 **Quick Win #3: Basic Web Interface**

### **Implementation**
Create `web_interface.py`:

```python
from flask import Flask, render_template, request, jsonify, Response
import json
import threading
import queue
from conversation_db import ConversationDB

app = Flask(__name__)
conversation_db = ConversationDB()

# Global queues for communication
command_queue = queue.Queue()
response_queue = queue.Queue()

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'running',
        'conversations_count': len(conversation_db.get_recent_conversations()),
        'last_activity': conversation_db.get_recent_conversations(1)[0]['timestamp'] if conversation_db.get_recent_conversations(1) else None
    })

@app.route('/api/conversations')
def get_conversations():
    """Get recent conversations"""
    limit = request.args.get('limit', 10, type=int)
    conversations = conversation_db.get_recent_conversations(limit)
    return jsonify(conversations)

@app.route('/api/send_command', methods=['POST'])
def send_command():
    """Send voice command"""
    data = request.get_json()
    command = data.get('command', '')
    
    if command:
        command_queue.put(command)
        return jsonify({'status': 'command_queued'})
    
    return jsonify({'error': 'No command provided'}), 400

@app.route('/api/stream')
def stream_responses():
    """Stream responses in real-time"""
    def generate():
        while True:
            if not response_queue.empty():
                response = response_queue.get()
                yield f"data: {json.dumps(response)}\n\n"
    
    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### **HTML Template** (`templates/dashboard.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <title>Ashley AI Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; background: #f0f0f0; border-radius: 5px; margin: 10px 0; }
        .conversation { border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px; }
        .command-input { width: 100%; padding: 10px; margin: 10px 0; }
        .send-btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Ashley AI Dashboard</h1>
        
        <div class="status" id="status">
            <h3>System Status</h3>
            <p>Status: <span id="status-text">Loading...</span></p>
            <p>Conversations: <span id="conversations-count">0</span></p>
        </div>
        
        <div>
            <h3>Send Command</h3>
            <input type="text" class="command-input" id="command-input" placeholder="Type your command here...">
            <button class="send-btn" onclick="sendCommand()">Send</button>
        </div>
        
        <div>
            <h3>Recent Conversations</h3>
            <div id="conversations"></div>
        </div>
    </div>

    <script>
        // Load status
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('status-text').textContent = data.status;
                document.getElementById('conversations-count').textContent = data.conversations_count;
            });

        // Load conversations
        fetch('/api/conversations')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('conversations');
                data.forEach(conv => {
                    const div = document.createElement('div');
                    div.className = 'conversation';
                    div.innerHTML = `
                        <strong>User:</strong> ${conv.user_input}<br>
                        <strong>Intent:</strong> ${conv.intent} (${conv.confidence.toFixed(2)})<br>
                        <strong>Response:</strong> ${conv.response}<br>
                        <small>${conv.timestamp}</small>
                    `;
                    container.appendChild(div);
                });
            });

        // Send command
        function sendCommand() {
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            
            if (command) {
                fetch('/api/send_command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command})
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Command sent:', data);
                    input.value = '';
                });
            }
        }

        // Enter key to send
        document.getElementById('command-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendCommand();
            }
        });
    </script>
</body>
</html>
```

## 🚀 **Quick Win #4: Multiple Voice Personalities**

### **Implementation**
Update `tts.py`:

```python
# Add to tts.py
VOICE_PERSONALITIES = {
    'ashley': {
        'voice': 'en-GB-LibbyNeural',
        'rate': 'slow',
        'pitch': 'low',
        'style': 'friendly'
    },
    'alex': {
        'voice': 'en-US-MichelleNeural',
        'rate': 'medium',
        'pitch': 'medium',
        'style': 'professional'
    },
    'sarah': {
        'voice': 'en-AU-NatashaNeural',
        'rate': 'fast',
        'pitch': 'high',
        'style': 'energetic'
    },
    'david': {
        'voice': 'en-GB-RyanNeural',
        'rate': 'slow',
        'pitch': 'low',
        'style': 'calm'
    }
}

def speak_with_personality(text, personality='ashley', use_ssml=True):
    """Speak with a specific personality"""
    if personality not in VOICE_PERSONALITIES:
        personality = 'ashley'
    
    config = VOICE_PERSONALITIES[personality]
    
    if use_ssml:
        ssml_text = f'''
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="{config['voice']}">
                <prosody rate="{config['rate']}" pitch="{config['pitch']}">
                    {text}
                </prosody>
            </voice>
        </speak>
        '''
        speak(ssml_text, use_ssml=True)
    else:
        speak(text, voice=config['voice'])

def change_personality(personality):
    """Change the current personality"""
    if personality in VOICE_PERSONALITIES:
        return f"Switching to {personality} personality"
    else:
        return f"Unknown personality. Available: {', '.join(VOICE_PERSONALITIES.keys())}"
```

### **Integration with main.py**
```python
# Add personality management
current_personality = 'ashley'

# In the intent handling section, add:
elif intent == "change_personality":
    personality = entities.get("personality", [query])[0] if entities.get("personality") else query
    response = change_personality(personality)
    speak_with_personality(response, current_personality)
    if "Switching to" in response:
        current_personality = personality

# Update all speak() calls to use:
speak_with_personality(response, current_personality)
```

## 🚀 **Quick Win #5: Command Shortcuts**

### **Implementation**
Create `command_shortcuts.py`:

```python
# Command shortcuts mapping
COMMAND_SHORTCUTS = {
    # App shortcuts
    'chrome': 'open chrome',
    'firefox': 'open firefox',
    'code': 'open vscode',
    'notepad': 'open notepad',
    'calc': 'open calculator',
    'explorer': 'open file explorer',
    'settings': 'open settings',
    
    # Search shortcuts
    'google': 'search google for',
    'youtube': 'search youtube for',
    'wiki': 'search wikipedia for',
    
    # Time shortcuts
    'time': 'what time is it',
    'date': 'what is the date',
    'datetime': 'what is the date and time',
    
    # Weather shortcuts
    'weather': 'what is the weather',
    'temp': 'what is the temperature',
    
    # System shortcuts
    'help': 'help me',
    'exit': 'goodbye',
    'bye': 'goodbye',
    'thanks': 'thank you',
    
    # Alarm shortcuts
    'alarm': 'set an alarm',
    'alarms': 'list alarms',
}

def expand_shortcut(command):
    """Expand command shortcuts"""
    command_lower = command.lower().strip()
    
    # Direct shortcut match
    if command_lower in COMMAND_SHORTCUTS:
        return COMMAND_SHORTCUTS[command_lower]
    
    # Check if command starts with a shortcut
    for shortcut, expansion in COMMAND_SHORTCUTS.items():
        if command_lower.startswith(shortcut + ' '):
            # Replace the shortcut with expansion
            remaining = command_lower[len(shortcut):].strip()
            return f"{expansion} {remaining}"
    
    return command  # Return original if no shortcut found

def add_shortcut(shortcut, expansion):
    """Add a new shortcut"""
    COMMAND_SHORTCUTS[shortcut.lower()] = expansion

def remove_shortcut(shortcut):
    """Remove a shortcut"""
    if shortcut.lower() in COMMAND_SHORTCUTS:
        del COMMAND_SHORTCUTS[shortcut.lower()]
        return True
    return False

def list_shortcuts():
    """List all available shortcuts"""
    return COMMAND_SHORTCUTS
```

### **Integration with main.py**
```python
# Add to main.py
from command_shortcuts import expand_shortcut

# In assistant_loop(), before processing the command:
query = take_command(source)
if not query:
    continue

# Expand shortcuts
original_query = query
query = expand_shortcut(query)

if query != original_query:
    logger.info(f"Shortcut expanded: '{original_query}' -> '{query}'")

query = query.lower().strip()
# ... rest of processing
```

## 🚀 **Quick Win #6: System Status Monitoring**

### **Implementation**
Create `system_monitor.py`:

```python
import psutil
import time
import threading
from datetime import datetime
from typing import Dict, Any

class SystemMonitor:
    def __init__(self):
        self.metrics = {}
        self.is_monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start system monitoring"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self.metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                    'network_io': psutil.net_io_counters()._asdict(),
                    'process_count': len(psutil.pids()),
                    'uptime': time.time() - psutil.boot_time()
                }
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return self.metrics
    
    def get_health_status(self) -> str:
        """Get overall system health status"""
        if not self.metrics:
            return "unknown"
        
        cpu = self.metrics.get('cpu_percent', 0)
        memory = self.metrics.get('memory_percent', 0)
        disk = self.metrics.get('disk_percent', 0)
        
        if cpu > 90 or memory > 90 or disk > 95:
            return "critical"
        elif cpu > 70 or memory > 70 or disk > 85:
            return "warning"
        else:
            return "healthy"
    
    def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        if not self.metrics:
            return "System status unavailable"
        
        health = self.get_health_status()
        cpu = self.metrics.get('cpu_percent', 0)
        memory = self.metrics.get('memory_percent', 0)
        disk = self.metrics.get('disk_percent', 0)
        
        return f"System status: {health}. CPU: {cpu:.1f}%, Memory: {memory:.1f}%, Disk: {disk:.1f}%"
```

### **Integration with main.py**
```python
# Add to main.py
from system_monitor import SystemMonitor

# Initialize monitoring
monitor = SystemMonitor()
monitor.start_monitoring()

# Add status command
elif intent == "system_status":
    status = monitor.get_status_summary()
    speak(status)
    logger.info(f"System status: {status}")

# In cleanup function
def cleanup():
    """Cleanup resources before exit."""
    logger.info("Cleaning up resources")
    try:
        monitor.stop_monitoring()
        tts_cleanup()
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
```

## 🚀 **Quick Win #7: Plugin System**

### **Implementation**
Create `plugin_system.py`:

```python
import os
import importlib
import inspect
from typing import Dict, List, Any, Callable
from abc import ABC, abstractmethod

class Plugin(ABC):
    """Base class for all plugins"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Get plugin name"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get plugin version"""
        pass
    
    @abstractmethod
    def get_commands(self) -> List[str]:
        """Get list of commands this plugin handles"""
        pass
    
    @abstractmethod
    def execute(self, command: str, **kwargs) -> Any:
        """Execute a command"""
        pass

class PluginManager:
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Plugin] = {}
        self.command_map: Dict[str, str] = {}
        
        # Create plugins directory if it doesn't exist
        os.makedirs(plugins_dir, exist_ok=True)
    
    def load_plugins(self):
        """Load all plugins from the plugins directory"""
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                plugin_name = filename[:-3]
                try:
                    self._load_plugin(plugin_name)
                except Exception as e:
                    print(f"Error loading plugin {plugin_name}: {e}")
    
    def _load_plugin(self, plugin_name: str):
        """Load a specific plugin"""
        module_path = f"{self.plugins_dir}.{plugin_name}"
        module = importlib.import_module(module_path)
        
        # Find Plugin classes in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, Plugin) and 
                obj != Plugin):
                
                plugin_instance = obj()
                plugin_name = plugin_instance.get_name()
                
                self.plugins[plugin_name] = plugin_instance
                
                # Map commands to plugin
                for command in plugin_instance.get_commands():
                    self.command_map[command] = plugin_name
                
                print(f"Loaded plugin: {plugin_name} v{plugin_instance.get_version()}")
    
    def execute_command(self, command: str, **kwargs) -> Any:
        """Execute a command using the appropriate plugin"""
        if command in self.command_map:
            plugin_name = self.command_map[command]
            plugin = self.plugins[plugin_name]
            return plugin.execute(command, **kwargs)
        else:
            return None
    
    def get_available_commands(self) -> List[str]:
        """Get list of all available commands"""
        return list(self.command_map.keys())
    
    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        """Get information about a specific plugin"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            return {
                'name': plugin.get_name(),
                'version': plugin.get_version(),
                'commands': plugin.get_commands()
            }
        return None

# Example plugin
class WeatherPlugin(Plugin):
    def get_name(self) -> str:
        return "weather"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_commands(self) -> List[str]:
        return ["weather", "temperature", "forecast"]
    
    def execute(self, command: str, **kwargs) -> Any:
        if command == "weather":
            return "The weather is sunny and 72°F"
        elif command == "temperature":
            return "The current temperature is 72°F"
        elif command == "forecast":
            return "Tomorrow will be partly cloudy with a high of 75°F"
        return None
```

### **Integration with main.py**
```python
# Add to main.py
from plugin_system import PluginManager

# Initialize plugin manager
plugin_manager = PluginManager()
plugin_manager.load_plugins()

# In assistant_loop(), before the main intent handling:
# Check if command can be handled by a plugin
plugin_result = plugin_manager.execute_command(intent, query=query, entities=entities)
if plugin_result:
    speak(plugin_result)
    continue

# Add plugin management commands
elif intent == "list_plugins":
    commands = plugin_manager.get_available_commands()
    speak(f"Available commands: {', '.join(commands)}")

elif intent == "plugin_info":
    plugin_name = entities.get("plugin_name", [query])[0] if entities.get("plugin_name") else query
    info = plugin_manager.get_plugin_info(plugin_name)
    if info:
        speak(f"Plugin {info['name']} version {info['version']} handles: {', '.join(info['commands'])}")
    else:
        speak(f"Plugin {plugin_name} not found")
```

## 📋 **Implementation Checklist**

- [ ] **Wake Word Detection**: Implement continuous listening
- [ ] **Conversation Persistence**: Add SQLite database
- [ ] **Web Interface**: Create Flask dashboard
- [ ] **Voice Personalities**: Add multiple TTS voices
- [ ] **Command Shortcuts**: Implement shortcut expansion
- [ ] **System Monitoring**: Add health monitoring
- [ ] **Plugin System**: Create extensible plugin architecture

## 🎯 **Expected Results**

After implementing these quick wins, Ashley AI will have:
- **Wake word activation** for hands-free operation
- **Persistent conversation history** for better context
- **Web dashboard** for monitoring and control
- **Multiple voice personalities** for variety
- **Command shortcuts** for faster interaction
- **System health monitoring** for reliability
- **Plugin architecture** for extensibility

These improvements will significantly enhance the user experience while maintaining the system's simplicity and effectiveness.

