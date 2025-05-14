#!/bin/bash

eval "$(conda shell.bash hook)"
conda activate ./.conda
python main.py "$@"