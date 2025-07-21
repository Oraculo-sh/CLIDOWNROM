import logging
import sys
from dotenv import load_dotenv

from .utils.directory_manager import create_project_structure
from .utils.config_loader import config
from .utils.logging_manager import setup_logging
from .utils.dependency_checker import check_system_dependencies
from .scripts.check_updates import check_for_tool_updates
from . import cli

def main():
    """Ponto de entrada principal da V2.0."""
    load_dotenv()
    if not config:
        print("ERRO: Falha ao carregar 'config.yml'."); return
    
    create_project_structure()
    check_system_dependencies()
    setup_logging()
    check_for_tool_updates()

    try:
        cli.start()
    except Exception:
        logging.critical("Ocorreu um erro crítico e não tratado.", exc_info=True)
        print("\n❌ Um erro crítico ocorreu. Verifique 'crash.log' para detalhes.")
        sys.exit(1)

if __name__ == "__main__":
    main()