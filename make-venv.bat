@echo off

setlocal enabledelayedexpansion

set "venv_dir=venv"

if not exist "%venv_dir%" (
    echo Creating virtual environment...
    python -m venv "%venv_dir%"
)

echo Activating virtual environment...
call "%venv_dir%\Scripts\activate.bat"

echo Virtual environment activated. You are now using Python from %venv_dir%.
python -V
where ffmpeg
where ffplay

echo Installing requirements...
pip install -r .\requirements.txt

echo Upgrading pip...
python.exe -m pip install --upgrade pip

echo All tasks completed.
pause
