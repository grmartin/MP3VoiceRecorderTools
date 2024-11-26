@echo off

set SCRIPT_NAME=main.py
set ICON_FILE=icon.ico
set VENV_DIR=.venv
set VERSION_FILE=version_info.txt
set OUT_NAME=TagDatesOnMP3

if not exist %VENV_DIR% (
    echo Virtual environment not found. Creating .venv...
    python -m venv %VENV_DIR%
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Please check your Python installation.
        exit /b 1
    )
    echo Virtual environment created successfully.
)

call %VENV_DIR%\Scripts\activate

if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies. Please check your requirements.txt.
        exit /b 1
    )
    echo Dependencies installed successfully.
) else (
    echo No requirements.txt found. Skipping dependency installation.
)

pause