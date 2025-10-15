"""
Logging configuration for AI Gym Assistant.

Sets up structured logging with file rotation and console output.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_to_console: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("gym_assistant")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        # Main application log
        log_file = log_path / f"gym_assistant_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Error log
        error_log_file = log_path / f"gym_assistant_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    logger.info(f"Logging configured - Level: {log_level}, Console: {log_to_console}, File: {log_to_file}")
    
    return logger


def get_logger(name: str = "gym_assistant") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
