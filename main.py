from src.userland import application

import logging
import os
from contextlib import redirect_stderr, redirect_stdout
from prompt_toolkit.patch_stdout import patch_stdout
import logging
import re

from dotenv import load_dotenv

load_dotenv()

# def set_global_logging_level(level=logging.ERROR, prefices=[""]):
#     """
#     Override logging levels of different modules based on their name as a prefix.
#     It needs to be invoked after the modules have been loaded so that their loggers have been initialized.

#     Args:
#         - level: desired level. e.g. logging.INFO. Optional. Default is logging.ERROR
#         - prefices: list of one or more str prefices to match (e.g. ["transformers", "torch"]). Optional.
#           Default is `[""]` to match all active loggers.
#           The match is a case-sensitive `module_name.startswith(prefix)`
#     """
#     prefix_re = re.compile(fr'^(?:{ "|".join(prefices) })')
#     for name in logging.root.manager.loggerDict:
#         if re.match(prefix_re, name):
#             logging.getLogger(name).setLevel(level)

# set_global_logging_level(logging.ERROR)


if __name__ == "__main__":
    
    with patch_stdout():
        application.run()

