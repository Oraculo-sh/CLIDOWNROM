@echo off
setlocal
title Cli-Download-Rom
cd /d "%~dp0"

echo Cli-Download-Rom
echo.

if not exist ".venv" (
    echo Creating virtual environment .venv for the first time...
    python -m venv .venv >nul 2>nul
    if %errorlevel% neq 0 (
        python3 -m venv .venv >nul 2>nul
        if %errorlevel% neq 0 (
            echo ERROR: Could not create the virtual environment.
            echo Please make sure Python is installed and the 'venv' module is available.
            pause
            exit /b 1
        )
    )
    echo Environment created successfully.
)

call ".venv\Scripts\activate.bat"

echo.
echo Checking and installing dependencies in the virtual environment...
pip install -r requirements.txt

echo.
echo Starting the application...
echo.

python -m Cli-Download-Rom %*

deactivate

echo.
echo Pressione qualquer tecla para sair...
pause >nul