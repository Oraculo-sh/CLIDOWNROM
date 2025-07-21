#!/bin/bash

VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
MODULE_NAME="Cli-Download-Rom"

echo "Verificando ambiente Python..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual."
        exit 1
    fi
fi

source "$VENV_DIR/bin/activate"

echo "Verificando e instalando dependências..."
pip install -r "$REQUIREMENTS_FILE" --quiet
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar as dependências."
    exit 1
fi

echo "Iniciando a aplicação..."
echo ""

python3 -m "$MODULE_NAME" "$@"