#!/bin/bash
printf "\033]0;Cli-Download-Rom\007"

cd "$(dirname "$0")"

echo "Cli-Download-Rom"
echo ""

if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual (.venv) pela primeira vez..."
    if command -v python3 &> /dev/null; then
        python3 -m venv .venv
    elif command -v python &> /dev/null; then
        python -m venv .venv
    else
        echo "ERRO: O 'python' ou 'python3' nao foi encontrado."
        echo "Nao foi possivel criar o ambiente virtual."
        exit 1
    fi
    echo "Ambiente criado com sucesso."
fi

source ".venv/bin/activate"

echo ""
echo "Verificando e instalando dependencias no ambiente virtual..."
pip install -r requirements.txt

echo ""
echo "Iniciando a aplicacao..."
echo ""

python -m Cli-Download-Rom "$@"

deactivate