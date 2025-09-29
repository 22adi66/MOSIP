"""Logging Setup for MOSIP OCR System"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "mosip_ocr",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """Setup and configure logger for the application
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional custom log format
    
    Returns:
        Configured logger instance
    """
    
    # Default log format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            name: {
                'level': level,
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    # Add file handler if log file is specified
    if log_file:
        logging_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': level,
            'formatter': 'detailed',
            'filename': log_file,
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5
        }
        logging_config['loggers'][name]['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Get logger instance
    logger = logging.getLogger(name)
    
    # Log initial message
    logger.info(f"Logger '{name}' initialized with level {level}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance by name
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Configure root logger for the application
def configure_app_logging():
    """Configure application-wide logging"""
    from .config import config
    
    return setup_logger(
        name="mosip_ocr",
        level=config.log_level,
        log_file=config.log_file_path,
        log_format=config.log_format
    )


# Initialize application logger
app_logger = configure_app_logging()