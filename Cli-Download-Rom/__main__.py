from utils.directory_manager import create_project_structure
from utils.config_loader import config
from utils.logging_manager import setup_logging # <-- IMPORTAR
from dotenv import load_dotenv
import logging # <-- IMPORTAR
import cli

def main():
    """
    Ponto de entrada principal da aplicação.
    """
    load_dotenv()

    if not config:
        return 
        
    create_project_structure()

    # Configura o sistema de logging
    setup_logging() # <-- CHAMAR

    try:
        # Inicia a interface de linha de comando
        cli.start()
    except Exception as e:
        # Captura exceções principais para garantir o log
        logging.critical("A critical error occurred in the main execution flow.", exc_info=True)


if __name__ == "__main__":
    main()