"""
Configuration Management Module
Centralizes loading and saving settings to .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Define constants
SCRIPT_DIR = Path(__file__).parent.parent
ENV_PATH = SCRIPT_DIR / ".env"

def load_config():
    """
    Load configuration from .env file
    
    Returns:
        dict: Configuration dictionary
    """
    load_dotenv(ENV_PATH)
    
    config = {
        'DEEPSEEK_API_KEY': os.getenv('DEEPSEEK_API_KEY'),
        'WHISPER_MODE': os.getenv('WHISPER_MODE', 'base'),
        'TURBO_MODE': os.getenv('TURBO_MODE', 'ask'),
        'SUBTITLE_PRESET': os.getenv('SUBTITLE_PRESET', 'auto'),
        'TRANSLATION_METHOD': os.getenv('TRANSLATION_METHOD', 'ask'),
        'FIDELITY_MODE': os.getenv('FIDELITY_MODE', 'economy'),
        'EMBEDDING_METHOD': os.getenv('EMBEDDING_METHOD', 'ask'),
        'SUBTITLE_GAP': float(os.getenv('SUBTITLE_GAP', '0.1')),
        'SUBTITLE_MIN_DURATION': float(os.getenv('SUBTITLE_MIN_DURATION', '1.5')),
        'SUBTITLE_MAX_DURATION': float(os.getenv('SUBTITLE_MAX_DURATION', '8.0')),
        
        # Style Settings
        'STYLE_PRESET': os.getenv('STYLE_PRESET', 'custom'),
        'SUB_FONT_SIZE': int(os.getenv('SUB_FONT_SIZE', '20')),
        'SUB_FONT_COLOR': os.getenv('SUB_FONT_COLOR', '&HFFFFFF'),
        'SUB_OUTLINE_WIDTH': int(os.getenv('SUB_OUTLINE_WIDTH', '2')),
        'SUB_SHADOW_DEPTH': int(os.getenv('SUB_SHADOW_DEPTH', '1')),
        'SUB_POSITION': os.getenv('SUB_POSITION', 'bottom'),
    }
    
    return config

def load_config_to_env():
    """Load .env to os.environment"""
    load_dotenv(ENV_PATH)

def save_config(key, value):
    """
    Save configuration to .env file
    
    Args:
        key: Environment variable key
        value: Value to save
    """
    # Create .env if it doesn't exist
    if not ENV_PATH.exists():
        ENV_PATH.touch()
    
    # Update or add key
    set_key(str(ENV_PATH), key, str(value))
    
    # Reload environment
    load_dotenv(ENV_PATH, override=True)
