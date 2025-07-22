@echo off
setlocal

set VENV_DIR=.venv
set REQUIREMENTS_FILE=requirements.txt
set MODULE_NAME=Cli-Download-Rom

echo Verificando ambiente Python...

if not exist "%VENV_DIR%\" (
    echo Criando ambiente virtual...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"

echo Checking and installing dependencies...
pip install -r "%REQUIREMENTS_FILE%" --quiet
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo Starting the application...
echo.

python -m %MODULE_NAME% %*

pause
endlocal