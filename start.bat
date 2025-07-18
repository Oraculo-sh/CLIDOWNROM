@echo off
setlocal

:: Define o nome da pasta do ambiente virtual
set VENV_DIR=venv

:: Define os caminhos e o nome do módulo
set REQUIREMENTS_FILE=Cli-Download-Rom\requirements.txt
set MODULE_NAME=Cli-Download-Rom

echo Verificando ambiente Python...

:: (O resto do script de verificação e instalação continua o mesmo)
if not exist "%VENV_DIR%\" (
    echo Criando ambiente virtual... Isso pode levar um momento.
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao criar o ambiente virtual. Verifique se o Python esta instalado e no PATH.
        pause
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"

echo Verificando e instalando dependencias...
pip install -r "%REQUIREMENTS_FILE%"
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar as dependencias do requirements.txt.
    pause
    exit /b 1
)

echo Iniciando a aplicacao...
echo.

:: --- MUDANÇA PRINCIPAL AQUI ---
:: Executa o script como um MÓDULO, que é a forma correta.
python -m %MODULE_NAME% %*

pause
endlocal