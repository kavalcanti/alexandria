from src.userland import application
import logging
import os
from contextlib import redirect_stderr, redirect_stdout

# --- Configure Logging ---

# Option 1: Set the overall logging level for the root logger
# This is a simple way to broadly control logging output.
# Messages below the set level will be ignored.
# Possible levels: logging.DEBUG, logging.INFO, logging.WARNING,
# logging.ERROR, logging.CRITICAL
logging.basicConfig(level=logging.CRITICAL)


if __name__ == "__main__":
    
    application.run()
