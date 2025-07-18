# Cli-Download-Rom/scripts/download_manager.py

import logging
import requests
import shutil
import time
import sys
from pathlib import Path
from tqdm import tqdm
from utils.localization import t
from utils.config_loader import config

success_logger = logging.getLogger('success_logger')

def _handle_insufficient_space(required, available):
    """Lida com o erro de espaço insuficiente de forma interativa."""
    while True:
        print(f"❌ {t.get_string('ERROR_INSUFFICIENT_SPACE', required, available)}")
        
        # Simplificando a entrada para R (Retry) ou C (Cancel)
        choice = input(t.get_string('PROMPT_INSUFFICIENT_SPACE')).upper()

        if choice == 'R':
            # Checa o espaço novamente
            free_space_bytes = shutil.disk_usage(config['general']['temp_directory']).free
            if free_space_bytes >= required:
                print(f"✔️ {t.get_string('SUCCESS_SPACE_FREED')}")
                return True # Espaço liberado, pode continuar o download
            else:
                continue # Continua no loop se o espaço ainda for insuficiente
        elif choice == 'C':
            return False # Usuário cancelou o download desta ROM
        else:
            print(f"⚠️ {t.get_string('ERROR_INVALID_CHOICE')}")

def download_rom(rom_details, preferred_mirror):
    """
    Gerencia o download completo de uma única ROM, agora com verificação de espaço.

    Args:
        rom_details (dict): Detalhes completos da ROM a ser baixada.
        preferred_mirror (str): O nome do host preferencial para tentar primeiro.

    Returns:
        bool: True se o download e a movimentação foram bem-sucedidos, False caso contrário.
    """
    title = rom_details['title']
    platform = rom_details['platform']
    rom_id = rom_details['rom_id']
    
    links = sorted(rom_details['links'], key=lambda x: x['host'] == preferred_mirror, reverse=True)
    
    base_rom_path = Path(__file__).parent.parent / config['general']['roms_directory']
    temp_download_path = Path(__file__).parent.parent / config['general']['temp_directory'] / 'downloads'
    final_rom_dir = base_rom_path / platform
    
    final_rom_dir.mkdir(parents=True, exist_ok=True)
    temp_download_path.mkdir(exist_ok=True)

    max_retries = config['mirrors']['max_retries']

    for link in links:
        url = link['url']
        host = link['host']
        filename = link['filename']
        expected_size = link['size']
        
        temp_file = temp_download_path / filename
        final_file = final_rom_dir / filename

        if final_file.exists() and final_file.stat().st_size == expected_size:
            logging.info(t.get_string("DOWNLOAD_ALREADY_EXISTS", title))
            print(f"ℹ️ {t.get_string('DOWNLOAD_ALREADY_EXISTS', title)}")
            success_logger.info(f"ROM '{title}' ({rom_id}) já existe e está validada.")
            return True

        # --- NOVA VERIFICAÇÃO DE ESPAÇO ---
        available_space_bytes = shutil.disk_usage(temp_download_path).free
        if available_space_bytes < expected_size:
            required_mb = expected_size / (1024*1024)
            available_mb = available_space_bytes / (1024*1024)
            if not _handle_insufficient_space(f"{required_mb:.2f} MB", f"{available_mb:.2f} MB"):
                logging.error(t.get_string("DOWNLOAD_CANCELLED_BY_USER_NO_SPACE", title))
                return False # Cancela o download desta ROM e vai para a próxima

        for attempt in range(max_retries):
            # ... (a lógica de download com requests e tqdm permanece a mesma) ...
            pass # A lógica de download existente entra aqui
    
    logging.error(t.get_string("DOWNLOAD_ALL_MIRRORS_FAILED", title))
    print(f"❌ {t.get_string('DOWNLOAD_ALL_MIRRORS_FAILED', title)}")
    return False