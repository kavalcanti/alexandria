#!/bin/bash
source .venv/bin/activate
export VLLM_CONFIGURE_LOGGING=1
export VLLM_LOGGING_LEVEL=ERROR # Optional, try if needed
export VLLM_LOGGING_CONFIG_PATH=conf/logging_config.json
python main.py