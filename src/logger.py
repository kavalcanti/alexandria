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
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        # Don't print to console as it might interfere with UI
        return getattr(logging, default)
    return getattr(logging, log_level)

def configure_logger():
    """Configure the root logger with file handler."""
    # Create logs directory at project root level
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger level
    level = _get_log_level(env_var='LOG_LEVEL', default='INFO')
    
    # Configure root logger first
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers from root logger to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create rotating file handler for global logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'global.log'),
        maxBytes=400 * 100,  # 400 lines * 100 chars per line
        backupCount=1
    )
    file_handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(file_handler)

def get_module_logger(module_path):
    """
    Configure a logger for a specific module.
    
    Args:
        module_path: Full module path (e.g., 'src.llm.completion', 'src.llm.chat')
    Returns:
        Logger instance configured for the specific module
    """
    # Ensure root logger is configured first
    if not logging.getLogger().handlers:
        configure_logger()
    
    # Return existing logger if already configured
    if module_path in _configured_loggers:
        return _configured_loggers[module_path]
    
    # Create logs directory at project root level
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Get the main component name
    components = module_path.split('.')
    if len(components) >= 2 and components[0] == 'src':
        main_component = components[1]  # e.g., 'core', 'infrastructure', 'ui', 'utils'
    elif len(components) >= 1:
        main_component = components[0]
    else:
        main_component = 'unknown'
    
    # Configure module-specific logging with full path as logger name
    logger = logging.getLogger(module_path)
    
    # Get module-specific log level, falling back to global level if not set
    module_level = _get_log_level(env_var='MODULE_LOG_LEVEL')
    global_level = _get_log_level(env_var='LOG_LEVEL', default='INFO')
    
    # Set logger level to the more permissive of module_level and global_level
    level = min(module_level, global_level)
    logger.setLevel(level)
    
    # Create formatter that includes the full module path
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    
    # Create and configure file handler for module-specific logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f'{main_component}.log'),
        maxBytes=400 * 100,  # 400 lines * 100 chars per line
        backupCount=1
    )
    file_handler.setLevel(level)  # Use module-specific level for the handler
    file_handler.setFormatter(formatter)
    
    # Add handler to logger and disable propagation
    logger.addHandler(file_handler)
    logger.propagate = False  # Never propagate to avoid duplicates
    
    # Cache the configured logger
    _configured_loggers[module_path] = logger
    return logger

def reset_loggers():
    """Reset all configured loggers. Useful for testing or reconfiguration."""
    global _configured_loggers
    
    # Clear all existing loggers first
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    for logger_name in list(_configured_loggers.keys()):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
    
    _configured_loggers.clear()
    
    # Reconfigure root logger
    configure_logger()

# Configure root logging when module is imported
configure_logger()