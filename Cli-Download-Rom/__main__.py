import logging
import sys
from dotenv import load_dotenv

from .utils.config_loader import config
from .utils.localization import t

from .utils.directory_manager import create_project_structure
from .utils.logging_manager import setup_logging
from .utils.dependency_checker import check_system_dependencies
from .scripts.check_updates import check_for_tool_updates
from . import cli

def main():
    """Ponto de entrada principal da V2.0."""
    load_dotenv()
    
    if not config:
        print("ERROR: Could not load 'config.yml'. The application cannot continue.")
        return 
    
    create_project_structure()
    check_system_dependencies()
    setup_logging()
    check_for_tool_updates()

    try:
        cli.start()
    except Exception:
        logging.critical(t.get_string('LOG_UNHANDLED_CRITICAL_ERROR'), exc_info=True)
        print(f"\n❌ {t.get_string('ERROR_CRITICAL_FAILURE')}")
        sys.exit(1)

if __name__ == "__main__":
    main()