# Cli-Download-Rom/scripts/download_manager.py (VERSÃO CORRIGIDA E COMPLETA)

import logging
import requests
import shutil
import time
from pathlib import Path
from tqdm import tqdm
from ..utils.localization import t
from ..utils.config_loader import config

success_logger = logging.getLogger('success_logger')

def _handle_insufficient_space(required_bytes):
    """Lida com o erro de espaço insuficiente de forma interativa."""
    while True:
        available_bytes = shutil.disk_usage(config['general']['temp_directory']).free
        required_mb_str = f"{required_bytes / (1024*1024):.2f} MB"
        available_mb_str = f"{available_bytes / (1024*1024):.2f} MB"
        
        print(f"\n❌ {t.get_string('ERROR_INSUFFICIENT_SPACE', required_mb_str, available_mb_str)}")
        
        choice = input(f"   {t.get_string('PROMPT_INSUFFICENT_SPACE')} ").upper()

        if choice == 'R':
            print(f"   {t.get_string('RECHECKING_SPACE')}")
            # Re-verifica o espaço. Se o usuário liberou, o loop principal vai detectar.
            if shutil.disk_usage(config['general']['temp_directory']).free >= required_bytes:
                print(f"✔️ {t.get_string('SUCCESS_SPACE_FREED')}")
                return True
            else:
                continue # Continua no loop se o espaço ainda for insuficiente
        elif choice == 'C':
            return False # Usuário cancelou
        else:
            print(f"   ⚠️ {t.get_string('ERROR_INVALID_CHOICE')}")

def download_rom(rom_details, preferred_mirror):
    """Gerencia o download completo de uma única ROM."""
    title = rom_details.get('title', 'N/A')
    platform = rom_details.get('platform', 'Unknown')
    rom_id = rom_details.get('rom_id', 'N/A')
    
    links = sorted(rom_details.get('links', []), key=lambda x: x.get('host') == preferred_mirror, reverse=True)
    
    base_rom_path = Path(__file__).parent.parent / config['general']['roms_directory']
    temp_download_path = Path(__file__).parent.parent / config['general']['temp_directory'] / 'downloads'
    final_rom_dir = base_rom_path / platform
    
    final_rom_dir.mkdir(parents=True, exist_ok=True)
    temp_download_path.mkdir(exist_ok=True)

    max_retries = config['mirrors']['max_retries']

    for link in links:
        url = link.get('url')
        host = link.get('host')
        filename = link.get('filename')
        expected_size = link.get('size')

        if not all([url, host, filename, expected_size]):
            logging.warning(f"Link inválido para a ROM '{title}', pulando.")
            continue

        temp_file = temp_download_path / filename
        final_file = final_rom_dir / filename

        if final_file.exists() and final_file.stat().st_size == expected_size:
            logging.info(t.get_string("DOWNLOAD_ALREADY_EXISTS", title))
            print(f"ℹ️ {t.get_string('DOWNLOAD_ALREADY_EXISTS', title)}")
            success_logger.info(f"ROM '{title}' ({rom_id}) já existe e está validada.")
            return True

        if shutil.disk_usage(temp_download_path).free < expected_size:
            if not _handle_insufficient_space(expected_size):
                logging.error(t.get_string("DOWNLOAD_CANCELLED_BY_USER_NO_SPACE", title))
                return False

        for attempt in range(max_retries):
            print(f"⌁ {t.get_string('DOWNLOAD_ATTEMPTING', title, host)} ({attempt + 1}/{max_retries})")
            try:
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', expected_size))

                    with open(temp_file, 'wb') as f:
                        pbar_desc = t.get_string("DOWNLOAD_PROGRESS_DESC", title)
                        with tqdm(total=total_size, desc=pbar_desc[:30], unit='B', unit_scale=True, unit_divisor=1024, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]') as pbar:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                                pbar.update(len(chunk))

                downloaded_size = temp_file.stat().st_size
                if downloaded_size == expected_size:
                    logging.info(t.get_string("DOWNLOAD_SUCCESS", title))
                    success_logger.info(f"'{title}' ({rom_id}) baixada com sucesso de '{host}'.")
                    
                    print(f"→ {t.get_string('MOVE_STARTING', title)}")
                    shutil.move(temp_file, final_file)
                    print(f"✔️ {t.get_string('MOVE_SUCCESS', str(final_file))}")
                    success_logger.info(f"'{title}' movida para '{final_file}'.")
                    return True
                else:
                    logging.error(t.get_string("DOWNLOAD_SIZE_MISMATCH", title, expected_size, downloaded_size))
                    if temp_file.exists(): temp_file.unlink()
                    continue

            except requests.RequestException as e:
                logging.error(t.get_string("DOWNLOAD_HOST_ERROR", host, e))
                time.sleep(config['mirrors']['retry_delay'])
            
            if temp_file.exists():
                temp_file.unlink()

    logging.error(t.get_string("DOWNLOAD_ALL_MIRRORS_FAILED", title))
    print(f"❌ {t.get_string('DOWNLOAD_ALL_MIRRORS_FAILED', title)}")
    return False