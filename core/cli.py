"""
CLI Argument Parser Module
Handles all command-line argument parsing for the application.
"""
import argparse
import sys
from .config import load_config_to_env  # We will create this next

def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        tuple: (model, lang, deepseek_flag, faster_flag, turbo_flag, 
               video_source, video_input, preset_mode, no_resume, config_mode)
    """
    parser = argparse.ArgumentParser(description="Auto Subtitle Generator with DeepSeek AI")
    
    # Core arguments
    parser.add_argument("--model", type=str, default="base", 
                        help="Whisper model size (tiny, base, small, medium, large, distil-small, distil-medium, distil-large)")
    parser.add_argument("--lang", type=str, default=None, 
                        help="Language code (e.g., 'id', 'en'). Default: auto-detect")
    
    # Feature flags
    parser.add_argument("--deepseek", action="store_true", help="Use DeepSeek AI for translation (Recommended)")
    parser.add_argument("--google", action="store_true", help="Use Google Translate")
    parser.add_argument("--faster", action="store_true", help="Use Faster-Whisper (Recommended)")
    parser.add_argument("--original", action="store_true", help="Use original OpenAI Whisper")
    parser.add_argument("--turbo", action="store_true", help="Enable Turbo Mode (Fast transcription)")
    parser.add_argument("--accurate", action="store_true", help="Enable Standard Mode (Accurate transcription)")
    
    # Video source
    parser.add_argument("--youtube", type=str, help="YouTube URL to download")
    parser.add_argument("--file", type=str, help="Local video file path")
    
    # Output configuration
    parser.add_argument("--output-dir", type=str, help="Custom output directory")
    
    # Presets
    parser.add_argument("--preset", type=str, choices=["budget", "standard", "quality", "instant"], 
                        default=None, help="Use preset configuration")
    
    # Process control
    parser.add_argument("--no-resume", action="store_true", help="Ignore checkpoint and start from scratch")
    
    # Configuration
    parser.add_argument("--configure", action="store_true", help="Run configuration wizard")
    
    args = parser.parse_args()
    
    return args
