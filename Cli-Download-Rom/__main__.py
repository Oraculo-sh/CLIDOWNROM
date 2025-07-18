import logging
import sys
from dotenv import load_dotenv

from .utils.directory_manager import create_project_structure
from .utils.config_loader import config
from .utils.logging_manager import setup_logging
from .utils.dependency_checker import check_system_dependencies, check_and_clone_dependencies
from .scripts.check_updates import check_for_tool_updates, check_for_crocdb_updates
from . import cli

def main():
    """Ponto de entrada principal da aplicação."""
    load_dotenv()

    if not config:
        print("ERRO: Falha ao carregar 'config.yml'. A aplicação não pode continuar.")
        return 
        
    create_project_structure()
    
    check_system_dependencies()
    check_and_clone_dependencies()

    check_for_tool_updates()
    check_for_crocdb_updates()

    setup_logging()

    try:
        cli.start()
    except Exception:
        logging.critical("Ocorreu um erro crítico e não tratado.", exc_info=True)
        print("\n❌ Um erro crítico ocorreu. Verifique 'crash.log' para detalhes.")
        sys.exit(1)

if __name__ == "__main__":
    main()