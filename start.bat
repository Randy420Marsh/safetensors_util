@echo off

setlocal enabledelayedexpansion

set "PYTHON=python"

echo "Launching..."

cd %CD%

set "USER=%USERNAME%"

echo Current User = %USER%

echo SD models root path = %SD_ROOT_PATH%

set SAFETENSORS_FAST_GPU=1

set PYTORCH_CUDA_ALLOC_CONF=garbage_collection_threshold:0.9,max_split_size_mb:512

call .\venv\scripts\activate.bat

echo "venv activated"
python --version

python -s gui.py

pause
