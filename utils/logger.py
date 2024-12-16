import logging
from config.settings import settings

def get_logger(name: str) -> logging.Logger:
    """Create a logger instance with specified configuration."""
    logger = logging.getLogger(name)
    
    # Set log level from settings
    logger.setLevel(settings.LOG_LEVEL)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger