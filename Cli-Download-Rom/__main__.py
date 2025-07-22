# Cli-Download-Rom/__main__.py

import sys
from .app import App # Alteração aqui

def main():
    """Ponto de entrada principal da aplicação."""
    try:
        cli_app = App()
        cli_app.run()
    except Exception as e:
        print(f"An fatal error occurred while starting the application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()