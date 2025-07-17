#!/bin/bash

# Define o nome da pasta do ambiente virtual
VENV_DIR="venv"
MAIN_SCRIPT="Cli-Download-Rom/__main__.py"
REQUIREMENTS_FILE="Cli-Download-Rom/requirements.txt"

echo "Verificando ambiente Python..."

# Verifica se a pasta do ambiente virtual existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Criando ambiente virtual... Isso pode levar um momento."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual. Verifique se o Python 3 está instalado."
        exit 1
    fi
fi

# Ativa o ambiente virtual
source "$VENV_DIR/bin/activate"

echo "Verificando e instalando dependências..."
pip install -r "$REQUIREMENTS_FILE"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar as dependências do requirements.txt."
    exit 1
fi

echo "Iniciando a aplicação..."
echo ""

# Executa o script Python principal, passando todos os argumentos do shell
python3 "$MAIN_SCRIPT" "$@"