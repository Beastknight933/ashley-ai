"""
Enhanced configuration management system with environment variables, validation, and hot-reloading
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv
import logging
from enhanced_logging import get_enhanced_logger

# Load environment variables
load_dotenv()

class AssistantSettings(BaseSettings):
    """Enhanced settings with validation and environment variable support"""
    
    # Basic Assistant Settings
    assistant_name: str = Field(default="Ashley", env="ASSISTANT_NAME")
    assistant_version: str = Field(default="1.0.0", env="ASSISTANT_VERSION")
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    
    # API Keys and Secrets
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openweather_api_key: str = Field(default="", env="OPENWEATHER_API_KEY")
    google_calendar_credentials: str = Field(default="", env="GOOGLE_CALENDAR_CREDENTIALS")
    
    # Voice Settings
    default_voice: str = Field(default="en-US-MichelleNeural", env="DEFAULT_VOICE")
    voice_rate: str = Field(default="medium", env="VOICE_RATE")
    voice_pitch: str = Field(default="medium", env="VOICE_PITCH")
    use_ssml: bool = Field(default=True, env="USE_SSML")
    
    # Wake Word Settings
    wake_words: List[str] = Field(default=["hey ashley", "ashley", "wake up ashley"], env="WAKE_WORDS")
    wake_word_sensitivity: float = Field(default=0.5, env="WAKE_WORD_SENSITIVITY")
    continuous_listening: bool = Field(default=False, env="CONTINUOUS_LISTENING")
    
    # NLP Settings
    nlp_confidence_threshold: float = Field(default=0.6, env="NLP_CONFIDENCE_THRESHOLD")
    use_context_awareness: bool = Field(default=True, env="USE_CONTEXT_AWARENESS")
    max_conversation_history: int = Field(default=10, env="MAX_CONVERSATION_HISTORY")
    
    # Database Settings
    database_url: str = Field(default="sqlite:///ashley_ai.db", env="DATABASE_URL")
    conversation_retention_days: int = Field(default=30, env="CONVERSATION_RETENTION_DAYS")
    
    # Logging Settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/ashley_ai.log", env="LOG_FILE")
    enable_structured_logging: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")
    
    # Performance Settings
    max_response_time: float = Field(default=5.0, env="MAX_RESPONSE_TIME")
    enable_performance_monitoring: bool = Field(default=True, env="ENABLE_PERFORMANCE_MONITORING")
    
    # Security Settings
    enable_encryption: bool = Field(default=False, env="ENABLE_ENCRYPTION")
    encryption_key: str = Field(default="", env="ENCRYPTION_KEY")
    
    # Web Interface Settings
    web_interface_enabled: bool = Field(default=False, env="WEB_INTERFACE_ENABLED")
    web_port: int = Field(default=5000, env="WEB_PORT")
    web_host: str = Field(default="0.0.0.0", env="WEB_HOST")
    
    # Plugin Settings
    plugins_enabled: bool = Field(default=True, env="PLUGINS_ENABLED")
    plugins_directory: str = Field(default="plugins", env="PLUGINS_DIRECTORY")
    
    @validator('wake_words', pre=True)
    def parse_wake_words(cls, v):
        if isinstance(v, str):
            return [word.strip() for word in v.split(',')]
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()
    
    @validator('nlp_confidence_threshold')
    def validate_confidence_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v
    
    @validator('max_conversation_history')
    def validate_conversation_history(cls, v):
        if v < 1:
            raise ValueError('Max conversation history must be at least 1')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

class ConfigManager:
    """Enhanced configuration manager with hot-reloading and validation"""
    
    def __init__(self, config_file: str = "config.yaml", env_file: str = ".env"):
        self.config_file = Path(config_file)
        self.env_file = Path(env_file)
        self.settings = None
        self.logger = get_enhanced_logger("config_manager")
        self._watchers = []
        self._last_modified = None
        
        # Load initial configuration
        self.load_config()
    
    def load_config(self) -> AssistantSettings:
        """Load configuration from files and environment variables"""
        try:
            # Load from YAML file if it exists
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f) or {}
            else:
                yaml_config = {}
            
            # Load from environment variables
            env_config = {}
            for key, value in os.environ.items():
                if key.startswith('ASHLEY_'):
                    env_key = key[7:].lower()  # Remove 'ASHLEY_' prefix
                    env_config[env_key] = value
            
            # Merge configurations (environment variables take precedence)
            merged_config = {**yaml_config, **env_config}
            
            # Create settings instance
            self.settings = AssistantSettings(**merged_config)
            
            self.logger.info("Configuration loaded successfully", 
                           config_file=str(self.config_file),
                           env_file=str(self.env_file))
            
            return self.settings
            
        except Exception as e:
            self.logger.error("Failed to load configuration", exception=e)
            # Return default settings
            self.settings = AssistantSettings()
            return self.settings
    
    def save_config(self, config_dict: Dict[str, Any]) -> bool:
        """Save configuration to YAML file"""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to YAML file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            self.logger.info("Configuration saved successfully", 
                           config_file=str(self.config_file))
            return True
            
        except Exception as e:
            self.logger.error("Failed to save configuration", exception=e)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        if self.settings is None:
            self.load_config()
        
        return getattr(self.settings, key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        if self.settings is None:
            self.load_config()
        
        try:
            setattr(self.settings, key, value)
            self.logger.info("Configuration value updated", key=key, value=value)
            return True
        except Exception as e:
            self.logger.error("Failed to set configuration value", 
                            key=key, value=value, exception=e)
            return False
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values"""
        if self.settings is None:
            self.load_config()
        
        try:
            for key, value in updates.items():
                setattr(self.settings, key, value)
            
            self.logger.info("Configuration updated", updates=updates)
            return True
        except Exception as e:
            self.logger.error("Failed to update configuration", 
                            updates=updates, exception=e)
            return False
    
    def validate(self) -> List[str]:
        """Validate current configuration and return any issues"""
        issues = []
        
        if self.settings is None:
            issues.append("Configuration not loaded")
            return issues
        
        # Check required API keys
        if not self.settings.openrouter_api_key:
            issues.append("OpenRouter API key not set")
        
        if not self.settings.openweather_api_key:
            issues.append("OpenWeather API key not set")
        
        # Check file paths
        if not Path(self.settings.log_file).parent.exists():
            issues.append(f"Log directory does not exist: {self.settings.log_file}")
        
        if self.settings.plugins_enabled and not Path(self.settings.plugins_directory).exists():
            issues.append(f"Plugins directory does not exist: {self.settings.plugins_directory}")
        
        # Check numeric ranges
        if not 0.0 <= self.settings.nlp_confidence_threshold <= 1.0:
            issues.append("NLP confidence threshold must be between 0.0 and 1.0")
        
        if self.settings.max_conversation_history < 1:
            issues.append("Max conversation history must be at least 1")
        
        return issues
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get configuration health status"""
        issues = self.validate()
        
        return {
            "status": "healthy" if not issues else "warning" if len(issues) < 3 else "critical",
            "issues": issues,
            "settings_count": len(self.settings.__dict__) if self.settings else 0,
            "config_file_exists": self.config_file.exists(),
            "env_file_exists": self.env_file.exists()
        }
    
    def export_config(self, format: str = "yaml") -> str:
        """Export current configuration to string"""
        if self.settings is None:
            self.load_config()
        
        config_dict = self.settings.dict()
        
        if format.lower() == "yaml":
            return yaml.dump(config_dict, default_flow_style=False, indent=2)
        elif format.lower() == "json":
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError("Format must be 'yaml' or 'json'")
    
    def import_config(self, config_data: str, format: str = "yaml") -> bool:
        """Import configuration from string"""
        try:
            if format.lower() == "yaml":
                config_dict = yaml.safe_load(config_data)
            elif format.lower() == "json":
                config_dict = json.loads(config_data)
            else:
                raise ValueError("Format must be 'yaml' or 'json'")
            
            # Validate the imported configuration
            temp_settings = AssistantSettings(**config_dict)
            
            # If validation passes, update current settings
            self.settings = temp_settings
            
            self.logger.info("Configuration imported successfully", format=format)
            return True
            
        except Exception as e:
            self.logger.error("Failed to import configuration", 
                            format=format, exception=e)
            return False
    
    def add_watcher(self, callback):
        """Add a callback to be called when configuration changes"""
        self._watchers.append(callback)
    
    def remove_watcher(self, callback):
        """Remove a configuration change callback"""
        if callback in self._watchers:
            self._watchers.remove(callback)
    
    def _notify_watchers(self):
        """Notify all watchers of configuration changes"""
        for callback in self._watchers:
            try:
                callback(self.settings)
            except Exception as e:
                self.logger.error("Error in configuration watcher", exception=e)
    
    def check_for_changes(self) -> bool:
        """Check if configuration files have changed and reload if necessary"""
        if not self.config_file.exists():
            return False
        
        current_modified = self.config_file.stat().st_mtime
        
        if self._last_modified is None or current_modified > self._last_modified:
            self._last_modified = current_modified
            old_settings = self.settings
            self.load_config()
            
            if old_settings != self.settings:
                self.logger.info("Configuration reloaded due to file changes")
                self._notify_watchers()
                return True
        
        return False

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> AssistantSettings:
    """Get the current configuration settings"""
    return config_manager.settings or config_manager.load_config()

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value"""
    return config_manager.get(key, default)

def set_config_value(key: str, value: Any) -> bool:
    """Set a specific configuration value"""
    return config_manager.set(key, value)

def validate_config() -> List[str]:
    """Validate the current configuration"""
    return config_manager.validate()

def get_config_health() -> Dict[str, Any]:
    """Get configuration health status"""
    return config_manager.get_health_status()

# Backward compatibility
def get_config_dict() -> Dict[str, Any]:
    """Get configuration as dictionary for backward compatibility"""
    settings = get_config()
    return settings.dict()

# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced configuration system
    print("Testing Enhanced Configuration System")
    print("=" * 50)
    
    # Load configuration
    config = get_config()
    print(f"Assistant Name: {config.assistant_name}")
    print(f"Debug Mode: {config.debug_mode}")
    print(f"Voice: {config.default_voice}")
    print(f"Wake Words: {config.wake_words}")
    
    # Test validation
    issues = validate_config()
    if issues:
        print(f"\nConfiguration Issues: {issues}")
    else:
        print("\nConfiguration is valid")
    
    # Test health status
    health = get_config_health()
    print(f"\nHealth Status: {health['status']}")
    print(f"Issues: {health['issues']}")
    
    # Test setting values
    print(f"\nOriginal voice: {get_config_value('default_voice')}")
    set_config_value('default_voice', 'en-GB-LibbyNeural')
    print(f"Updated voice: {get_config_value('default_voice')}")
    
    # Export configuration
    yaml_config = config_manager.export_config("yaml")
    print(f"\nExported YAML config:\n{yaml_config[:200]}...")

