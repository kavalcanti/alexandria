import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Dict

# Keep track of configured loggers to prevent duplicate handlers
_configured_loggers: Dict[str, logging.Logger] = {}

def _get_log_level(env_var='LOG_LEVEL', default='INFO'):
    """
    Get log level from environment variable.
    
    Args:
        env_var: Environment variable name to check for log level
        default: Default log level if environment variable is not set
    Returns:
        logging level constant
    """
    log_level = os.getenv(env_var, default).upper()
    return getattr(logging, log_level, logging.INFO)

def get_module_logger(module_path):
    """
    Configure a logger for a specific module.
    
    Args:
        module_path: Full module path (e.g., 'src.llm.completion', 'src.llm.chat')
    Returns:
        Logger instance configured for the specific module
    """
    # Return existing logger if already configured
    if module_path in _configured_loggers:
        return _configured_loggers[module_path]
    
    # Create logs directory at project root level
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Get the main component name (e.g., 'core' from 'src.core.generation.llm_generator')
    components = module_path.split('.')
    if len(components) >= 2 and components[0] == 'src':
        main_component = components[1]  # e.g., 'core', 'infrastructure', 'ui', 'utils'
    elif len(components) >= 1:
        main_component = components[0]  # fallback to first component
    else:
        main_component = 'unknown'
    
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
        
        # Get module-specific log level
        level = _get_log_level(env_var='MODULE_LOG_LEVEL', default='INFO')
        file_handler.setLevel(level)
        
        # Create formatter that includes the full module path
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        logger.setLevel(level)
        logger.propagate = False
    
    # Cache the configured logger
    _configured_loggers[module_path] = logger
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
    
    # Get root logger level
    level = _get_log_level(env_var='LOG_LEVEL', default='INFO')
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers from root logger to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handler to root logger
    root_logger.addHandler(file_handler)

def reset_loggers():
    """Reset all configured loggers. Useful for testing or reconfiguration."""
    global _configured_loggers
    _configured_loggers.clear()
    
    # Clear all existing loggers
    logging.getLogger().handlers.clear()
    
    # Reconfigure root logger
    configure_logger()

# Configure root logging when module is imported
configure_logger()