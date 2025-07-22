@echo off
setlocal
title Cli-Download-Rom
cd /d "%~dp0"

echo Cli-Download-Rom
echo.

if not exist ".venv" (
    echo Criando ambiente virtual (.venv) pela primeira vez...
    python -m venv .venv >nul 2>nul
    if %errorlevel% neq 0 (
        python3 -m venv .venv >nul 2>nul
        if %errorlevel% neq 0 (
            echo ERRO: Nao foi possivel criar o ambiente virtual.
            echo Verifique se o Python esta instalado e se o modulo 'venv' esta disponivel.
            pause
            exit /b 1
        )
    )
    echo Ambiente criado com sucesso.
)

call ".venv\Scripts\activate.bat"

echo.
echo Verificando e instalando dependencias no ambiente virtual...
pip install -r requirements.txt

echo.
echo Iniciando a aplicacao...
echo.

python -m Cli-Download-Rom %*

deactivate

echo.
echo Pressione qualquer tecla para sair...
pause >nul