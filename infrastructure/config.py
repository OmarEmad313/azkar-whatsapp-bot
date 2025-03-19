import os
import configparser
from pathlib import Path


_config = None


def get_config():
    """Get application configuration"""
    global _config
    
    if _config is None:
        _config = configparser.ConfigParser()
        
        # Default config path
        config_path = Path("config.ini")
        
        # Load config file if it exists
        if config_path.exists():
            _config.read(config_path)
        else:
            # Create default configuration
            _config["General"] = {
                "debug": "true",
                "headless": "false"
            }
            
            _config["WhatsApp"] = {
                "session_dir": "./whatsapp-session",
                "chat_id": ""  # Placeholder, user should replace
            }
            
            _config["Scheduler"] = {
                "timezone": "Africa/Cairo",
                "morning_time": "05:00",
                "evening_time": "17:00"
            }
            
            # Save default config
            with open(config_path, "w") as f:
                _config.write(f)
    
    return _config


def save_config():
    """Save current configuration to file"""
    if _config:
        with open("config.ini", "w") as f:
            _config.write(f)