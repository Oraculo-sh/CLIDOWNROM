#!/bin/bash
printf "\033]0;Cli-Download-Rom\007"

cd "$(dirname "$0")"

echo "Cli-Download-Rom"
echo ""

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv) for the first time..."
    if command -v python3 &> /dev/null; then
        python3 -m venv .venv
    elif command -v python &> /dev/null; then
        python -m venv .venv
    else
        echo "ERROR: 'python' or 'python3' was not found."
        echo "Could not create the virtual environment."
        exit 1
    fi
    echo "Environment created successfully."
fi

source ".venv/bin/activate"

echo ""
echo "Checking and installing dependencies in the virtual environment..."
pip install -r requirements.txt

echo ""
echo "Starting the application..."
echo ""

python -m Cli-Download-Rom "$@"

deactivate