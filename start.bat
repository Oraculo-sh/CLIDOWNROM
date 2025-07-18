@echo off
setlocal

:: Define o nome da pasta do ambiente virtual
set VENV_DIR=venv

:: Define o caminho para o script principal
set MAIN_SCRIPT=Cli-Download-Rom\__main__.py
set REQUIREMENTS_FILE=Cli-Download-Rom\requirements.txt

echo Verificando ambiente Python...

:: Verifica se a pasta do ambiente virtual existe
if not exist "%VENV_DIR%\" (
    echo Criando ambiente virtual... Isso pode levar um momento.
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao criar o ambiente virtual. Verifique se o Python esta instalado e no PATH.
        pause
        exit /b 1
    )
)

:: Ativa o ambiente virtual
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

:: Executa o script Python principal, passando todos os argumentos do batch
python "%MAIN_SCRIPT%" %*

:: --- ADICIONADO ---
:: Mantém a janela aberta para que você possa ver a saída ou erros
pause

endlocal