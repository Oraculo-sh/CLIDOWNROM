# Cli-Download-Rom/utils/logging_manager.py

import logging
import sys
from pathlib import Path
from .config_loader import config
from .localization import t

def setup_logging():
    """Configura o sistema de logging com base no arquivo config.yml."""
    if not config or not config['general'].get('enable_logging', False):
        return

    log_config = config['general']
    log_dir = Path(__file__).parent.parent / log_config['logs_directory']
    log_level_str = log_config.get('log_level', 'info').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # --- Configuração do Logger Principal (Root) ---
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Formato do Log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Remover handlers padrão para evitar duplicidade
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. Handler para o Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Handler para o `latest.log` (sobrescrito a cada execução)
    latest_log_file = log_dir / 'latest.log'
    latest_handler = logging.FileHandler(latest_log_file, mode='w', encoding='utf-8')
    latest_handler.setLevel(log_level)
    latest_handler.setFormatter(formatter)
    root_logger.addHandler(latest_handler)

    # 3. Handler para o `error.log` (apenas nível ERROR ou superior)
    error_log_file = log_dir / 'error.log'
    error_handler = logging.FileHandler(error_log_file, mode='a', encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # --- Configuração do Logger de Sucesso (Customizado) ---
    success_logger = logging.getLogger('success_logger')
    success_logger.setLevel(logging.INFO)
    success_logger.propagate = False # Impede que o log de sucesso vá para outros handlers
    
    success_log_file = log_dir / 'success.log'
    success_handler = logging.FileHandler(success_log_file, mode='a', encoding='utf-8')
    success_handler.setFormatter(formatter)
    success_logger.addHandler(success_handler)

    # --- Manipulador de Exceções (Crash) ---
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Captura exceções não tratadas e as registra no crash.log."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        crash_log_file = log_dir / 'crash.log'
        logging.critical("Unhandled exception caught!", exc_info=(exc_type, exc_value, exc_traceback))
        
        with open(crash_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n--- CRASH REPORT - {formatter.formatTime(logging.makeLogRecord({}))} ---\n")
        
        # Loga o traceback no arquivo de crash
        error_handler_crash = logging.FileHandler(crash_log_file, mode='a', encoding='utf-8')
        error_handler_crash.setFormatter(formatter)
        crash_logger = logging.getLogger('crash_logger')
        crash_logger.addHandler(error_handler_crash)
        crash_logger.critical("Unhandled exception caught!", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    logging.info(t.get_string("LOGGING_SYSTEM_SETUP"))