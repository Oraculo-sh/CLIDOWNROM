# Cli-Download-Rom/utils/directory_manager.py (VERSÃO CORRIGIDA)

from pathlib import Path
from .config_loader import config
from .localization import t

def create_project_structure():
    """Verifica e cria a estrutura de diretórios necessária para o projeto."""
    if not config:
        print("Error: Config file could not be loaded. Aborting directory creation.")
        return

    base_path = Path(__file__).parent.parent

    # Lista completa de diretórios a serem criados
    all_dirs = [
        config['general']['roms_directory'],
        config['general']['lists_directory'],
        config['general']['temp_directory'],
        config['general']['logs_directory'],
        Path(config['general']['temp_directory']) / 'downloads',
        Path(config['general']['temp_directory']) / 'test-mirrors',
        'database',
        'interface/assets',
        'locales',
        'crocdb'
    ]

    print(t.get_string("DIR_STRUCTURE_CHECK"))
    for dir_name in all_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            print(t.get_string("DIR_CREATED", dir_path))
            dir_path.mkdir(parents=True, exist_ok=True)
    print(t.get_string("DIR_STRUCTURE_SUCCESS"))