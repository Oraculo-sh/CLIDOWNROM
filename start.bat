@echo off
setlocal

set VENV_DIR=venv
set REQUIREMENTS_FILE=requirements.txt
set MODULE_NAME=Cli-Download-Rom

echo Verificando ambiente Python...

if not exist "%VENV_DIR%\" (
    echo Criando ambiente virtual...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao criar o ambiente virtual. Verifique se o Python esta instalado e no PATH.
        pause
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"

echo Verificando e instalando dependencias...
pip install -r "%REQUIREMENTS_FILE%" --quiet
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar as dependencias.
    pause
    exit /b 1
)

echo Iniciando a aplicacao...
echo.

python -m %MODULE_NAME% %*

pause
endlocal