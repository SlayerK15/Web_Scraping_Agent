"""
Logger Module
Sets up logging for the application.
"""

import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(level: int = logging.INFO, log_file: Optional[str] = None, 
                name: Optional[str] = None) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        level (int, optional): Logging level. Defaults to logging.INFO.
        log_file (str, optional): Path to log file. Defaults to None.
        name (str, optional): Logger name. Defaults to None.
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logger
    if name is None:
        logger = logging.getLogger()  # Root logger
    else:
        logger = logging.getLogger(name)
    
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Create rotating file handler (max 10MB, 5 backup files)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name (str): Logger name
        level (int, optional): Logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level if logger doesn't have handlers yet
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def setup_file_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger that logs to a file.
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file
        level (int, optional): Logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Create rotating file handler (max 10MB, 5 backup files)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_default_log_file() -> str:
    """
    Get the default log file path.
    
    Returns:
        str: Default log file path
    """
    # Base logs directory
    logs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'logs'
    )
    
    # Ensure logs directory exists
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(logs_dir, f'scraper_{timestamp}.log')
    
    return log_file