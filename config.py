import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class Config:
    """
    Centralized configuration management.
    Supports environment variables, config files, and defaults.
    """
    
    # ---------- DEFAULT CONFIGURATIONS ----------
    DEFAULTS = {
        # API Keys (will be overridden by environment variables)
        'OPENWEATHER_API_KEY': '',
        'GOOGLE_CREDENTIALS_PATH': 'credentials.json',
        'OPENROUTER_API_KEY': '',
        
        # TTS Settings
        'TTS_VOICE': 'en-US-MichelleNeural',
        'TTS_RATE': 'medium',
        'TTS_VOLUME': 1.0,
        
        # STT Settings
        'STT_TIMEOUT': 8,
        'STT_PHRASE_TIME_LIMIT': 3,
        'STT_LANGUAGE': 'en-US',
        'STT_ENERGY_THRESHOLD': 300,
        'STT_PAUSE_THRESHOLD': 1.5,
        
        # Alarm Settings
        'ALARM_CHECK_INTERVAL': 30,
        'ALARM_TIMEZONE': 'Asia/Kolkata',
        
        # Assistant Settings
        'ASSISTANT_NAME': 'Ashley',
        'CONVERSATION_MEMORY_SIZE': 5,
        'LOG_LEVEL': 'INFO',
        
        # File Paths
        'LOG_FILE': 'assistant.log',
        'TOKEN_FILE': 'token.pickle',
        'CONFIG_FILE': 'config.json',
        
        # Feature Flags
        'USE_NLP': False,  # Set to True when NLP is ready
        'USE_GPT': False,  # Set to True when GPT integration is ready
        'AUTO_CLEANUP_TTS': True,
        'ENABLE_ALARM_WATCHER': True,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Priority order:
        1. Environment variables
        2. Config file
        3. Defaults
        """
        self._config: Dict[str, Any] = self.DEFAULTS.copy()
        self._config_file = config_file or self.DEFAULTS['CONFIG_FILE']
        
        # Load from file if exists
        self._load_from_file()
        
        # Override with environment variables
        self._load_from_env()
        
        logger.info("Configuration loaded successfully")
    
    def _load_from_file(self):
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r') as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
                    logger.info(f"Loaded config from {self._config_file}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'OPENWEATHER_API_KEY': 'OPENWEATHER_API_KEY',
            'OPENROUTER_API_KEY': 'OPENROUTER_API_KEY',
            'GOOGLE_CREDENTIALS_PATH': 'GOOGLE_CREDENTIALS',
            'TTS_VOICE': 'TTS_VOICE',
            'STT_LANGUAGE': 'STT_LANGUAGE',
            'ASSISTANT_NAME': 'ASSISTANT_NAME',
            'LOG_LEVEL': 'LOG_LEVEL',
        }
        
        for config_key, env_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                self._config[config_key] = env_value
                logger.debug(f"Loaded {config_key} from environment")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value (runtime only, not saved)."""
        self._config[key] = value
    
    def save(self):
        """Save current configuration to file."""
        try:
            # Don't save sensitive data like API keys
            safe_config = {
                k: v for k, v in self._config.items()
                if not k.endswith('_KEY') and k != 'GOOGLE_CREDENTIALS_PATH'
            }
            
            with open(self._config_file, 'w') as f:
                json.dump(safe_config, f, indent=4)
                logger.info(f"Configuration saved to {self._config_file}")
        except Exception as e:
            logger.error(f"Could not save config file: {e}")
    
    def validate(self) -> bool:
        """
        Validate critical configuration values.
        Returns True if all required configs are present.
        """
        warnings = []
        
        # Check API keys
        if not self.get('OPENWEATHER_API_KEY'):
            warnings.append("OPENWEATHER_API_KEY not set - weather features will not work")
        
        if self.get('USE_GPT') and not self.get('OPENROUTER_API_KEY'):
            warnings.append("OPENROUTER_API_KEY not set but GPT is enabled")
        
        # Check file paths
        creds_path = self.get('GOOGLE_CREDENTIALS_PATH')
        if not os.path.exists(creds_path):
            warnings.append(f"Google credentials not found at {creds_path}")
        
        # Log warnings
        for warning in warnings:
            logger.warning(warning)
        
        return len(warnings) == 0
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any):
        """Allow dict-like assignment."""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return key in self._config
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()


# ---------- GLOBAL CONFIG INSTANCE ----------
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get or create global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config():
    """Reload configuration from file and environment."""
    global _config_instance
    _config_instance = Config()
    return _config_instance


# ---------- USAGE EXAMPLES ----------
if __name__ == "__main__":
    # Initialize config
    config = get_config()
    
    # Access values
    print(f"Assistant Name: {config.get('ASSISTANT_NAME')}")
    print(f"TTS Voice: {config.get('TTS_VOICE')}")
    print(f"Use NLP: {config.get('USE_NLP')}")
    
    # Validate configuration
    is_valid = config.validate()
    print(f"Configuration valid: {is_valid}")
    
    # Update runtime value
    config.set('ASSISTANT_NAME', 'Medusa')
    
    # Save to file (won't save API keys)
    config.save()
    
    # Access like dictionary
    print(f"Log Level: {config['LOG_LEVEL']}")
    
    # Check if key exists
    if 'OPENWEATHER_API_KEY' in config:
        print("Weather API key is configured")