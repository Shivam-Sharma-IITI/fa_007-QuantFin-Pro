# config/logging_config.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import config # Import the shared config instance

def setup_logging():
    """
    Configures logging for the application.
    """
    log_level_str = config.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    log_file_path_str = config.get('LOG_FILE_PATH', 'logs/etl_pipeline.log')
    log_file_path = Path(log_file_path_str)
    
    # Create the directory for log files if it doesn't exist
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Create rotating file handler
    max_size = int(config.get('LOG_MAX_FILE_SIZE', 10485760))
    backup_count = int(config.get('LOG_BACKUP_COUNT', 5))
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_size,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    
    # Add handlers to the root logger
    # Check if handlers are already added to prevent duplicates in some environments
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")# config/logging_config.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import config # Import the shared config instance

def setup_logging():
    """
    Configures logging for the application.
    """
    log_level_str = config.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    log_file_path_str = config.get('LOG_FILE_PATH', 'logs/etl_pipeline.log')
    log_file_path = Path(log_file_path_str)
    
    # Create the directory for log files if it doesn't exist
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Create rotating file handler
    max_size = int(config.get('LOG_MAX_FILE_SIZE', 10485760))
    backup_count = int(config.get('LOG_BACKUP_COUNT', 5))
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_size,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    
    # Add handlers to the root logger
    # Check if handlers are already added to prevent duplicates in some environments
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")