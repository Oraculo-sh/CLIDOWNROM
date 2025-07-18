#!/bin/bash

VENV_DIR="venv"
REQUIREMENTS_FILE="Cli-Download-Rom/requirements.txt"
MODULE_NAME="Cli-Download-Rom"

echo "Verificando ambiente Python..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Criando ambiente virtual... Isso pode levar um momento."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual. Verifique se o Python 3 está instalado."
        exit 1
    fi
fi

source "$VENV_DIR/bin/activate"

echo "Verificando e instalando dependências..."
pip install -r "$REQUIREMENTS_FILE"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar as dependências do requirements.txt."
    exit 1
fi

echo "Iniciando a aplicação..."
echo ""

# --- MUDANÇA PRINCIPAL AQUI ---
# Executa o script como um MÓDULO.
python3 -m "$MODULE_NAME" "$@"