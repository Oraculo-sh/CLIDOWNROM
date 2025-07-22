import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import App

def main():
    """Ponto de entrada principal da aplicação."""
    try:
        cli_app = App()
        cli_app.run()
    except Exception as e:
        print(f"Ocorreu um erro fatal ao iniciar a aplicação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()