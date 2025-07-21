# Cli-Download-Rom/utils/db_checker.py

import logging
from pathlib import Path
import time
from .config_loader import config
from .localization import t

def check_database_status():
    """Verifica a existência e a idade do banco de dados SQLite."""
    if not config: return

    db_path = Path(__file__).parent.parent / 'crocdb' / 'crocdb-db' / 'database' / 'roms.db'
    
    if not db_path.exists():
        print(f"ℹ️ {t.get_string('DB_STATUS_NOT_FOUND')}")
        logging.warning("Banco de dados local (roms.db) não encontrado.")
        return

    try:
        warning_days = config['general'].get('db_update_warning_days', 30)
        file_mod_time = db_path.stat().st_mtime
        age_seconds = time.time() - file_mod_time
        age_days = age_seconds / (24 * 3600)

        if age_days > warning_days:
            print(f"⚠️ {t.get_string('DB_STATUS_OUTDATED', int(age_days))}")
            logging.warning(f"O banco de dados local tem {int(age_days)} dias.")
    except Exception as e:
        logging.error(f"Não foi possível verificar a idade do banco de dados: {e}")