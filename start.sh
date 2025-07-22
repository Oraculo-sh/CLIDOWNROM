#!/bin/bash

VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
MODULE_NAME="Cli-Download-Rom"

echo "Checking Python environment..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual."
        exit 1
    fi
fi

source "$VENV_DIR/bin/activate"

echo "Checking and installing dependencies..."
pip install -r "$REQUIREMENTS_FILE" --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies."
    exit 1
fi

echo "Starting the application..."
echo ""

python3 -m "$MODULE_NAME" "$@"