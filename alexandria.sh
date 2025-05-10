#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate /home/kaoue/code/alexandria/.conda
export VLLM_CONFIGURE_LOGGING=1
export VLLM_LOGGING_LEVEL=ERROR # Optional, try if needed
export VLLM_LOGGING_CONFIG_PATH=conf/logging_config.json
python main.py