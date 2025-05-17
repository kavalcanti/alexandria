import logging
from logging.handlers import RotatingFileHandler
import os

def get_module_logger(module_path):
    """
    Configure a logger for a specific module.
    
    Args:
        module_path: Full module path (e.g., 'src.llm.completion', 'src.llm.chat')
    Returns:
        Logger instance configured for the specific module
    """
    # Create logs directory at project root level
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Get the main component name (e.g., 'llm' from 'src.llm.completion')
    components = module_path.split('.')
    main_component = components[1] if len(components) > 1 else components[0]
    
    # Configure module-specific logging with full path as logger name
    logger = logging.getLogger(module_path)
    
    # Only add handlers if the logger doesn't already have them
    if not logger.handlers:
        # Module-specific log file based on the main component
        log_file = os.path.join(log_dir, f'{main_component}.log')
        
        # Calculate max bytes based on average line length (assuming ~100 chars per line)
        max_bytes = 400 * 100  # 400 lines * 100 chars per line
        
        # Create rotating file handler for module-specific logs
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=1
        )
        file_handler.setLevel(logging.INFO)
        
        # Create formatter that includes the full module path
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger

def configure_logger():
    """Configure the root logger with file handler."""
    # Create logs directory at project root level
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, 'global.log')
    
    # Calculate max bytes based on average line length (assuming ~100 chars per line)
    max_bytes = 400 * 100  # 400 lines * 100 chars per line
    
    # Create rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=1
    )
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers from root logger
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handler to root logger
    root_logger.addHandler(file_handler)

# Configure root logging when module is imported
configure_logger()