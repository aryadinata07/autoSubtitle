"""
Centralized logging system for AutoSubtitle.
Logs detailed event information to a file while the UI handles console output.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Constants
LOG_FILENAME = "autosub.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

def setup_logger():
    """
    Configure and return the project logger.
    Writes to autosub.log with rotation.
    """
    # Create logger
    logger = logging.getLogger("AutoSubtitle")
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
        
    # Determine log path (project root)
    script_dir = Path(__file__).resolve().parent.parent
    log_path = script_dir / LOG_FILENAME
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler (Rotating)
    try:
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=MAX_LOG_SIZE, 
            backupCount=BACKUP_COUNT, 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except Exception as e:
        print(f"Warning: Failed to setup logging to file: {e}")
        
    return logger

# Singleton logger instance
log = setup_logger()
