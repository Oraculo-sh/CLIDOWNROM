# Cli-Download-Rom/scripts/download_manager.py

import logging
import requests
import shutil
import time
from pathlib import Path
from tqdm import tqdm
from utils.localization import t
from utils.config_loader import config

success_logger = logging.getLogger('success_logger')

def download_rom(rom_details, preferred_mirror):
    """
    Gerencia o download completo de uma única ROM.

    Args:
        rom_details (dict): Detalhes completos da ROM a ser baixada.
        preferred_mirror (str): O nome do host preferencial para tentar primeiro.

    Returns:
        bool: True se o download e a movimentação foram bem-sucedidos, False caso contrário.
    """
    title = rom_details['title']
    platform = rom_details['platform']
    rom_id = rom_details['rom_id']
    
    # Ordena os links para que o preferencial venha primeiro
    links = sorted(rom_details['links'], key=lambda x: x['host'] == preferred_mirror, reverse=True)
    
    base_rom_path = Path(__file__).parent.parent / config['general']['roms_directory']
    temp_download_path = Path(__file__).parent.parent / config['general']['temp_directory'] / 'downloads'
    final_rom_dir = base_rom_path / platform
    
    # Cria os diretórios necessários
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

        for attempt in range(max_retries):
            print(f"⌁ {t.get_string('DOWNLOAD_ATTEMPTING', title, host)} ({attempt + 1}/{max_retries})")
            try:
                with requests.get(url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    total_size = int(r.headers.get('content-length', expected_size))

                    with open(temp_file, 'wb') as f:
                        pbar_desc = t.get_string("DOWNLOAD_PROGRESS_DESC", title)
                        with tqdm(total=total_size,
                                  desc=pbar_desc[:30], # Limita o tamanho da descrição
                                  unit='B', unit_scale=True, unit_divisor=1024,
                                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]'
                                  ) as pbar:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                                pbar.update(len(chunk))

                # Validação do tamanho do arquivo
                downloaded_size = temp_file.stat().st_size
                if downloaded_size == expected_size:
                    logging.info(t.get_string("DOWNLOAD_SUCCESS", title))
                    success_logger.info(f"'{title}' ({rom_id}) baixada com sucesso de '{host}'.")
                    
                    # Mover o arquivo
                    print(f"→ {t.get_string('MOVE_STARTING', title)}")
                    shutil.move(temp_file, final_file)
                    print(f"✔️ {t.get_string('MOVE_SUCCESS', str(final_file))}")
                    success_logger.info(f"'{title}' movida para '{final_file}'.")
                    return True
                else:
                    logging.error(t.get_string("DOWNLOAD_SIZE_MISMATCH", title, expected_size, downloaded_size))
                    temp_file.unlink() # Deleta arquivo corrompido
                    continue # Próxima tentativa ou próximo mirror

            except requests.RequestException as e:
                logging.error(t.get_string("DOWNLOAD_HOST_ERROR", host, e))
                time.sleep(config['mirrors']['retry_delay'])
            
            if temp_file.exists():
                temp_file.unlink() # Garante limpeza entre tentativas

    logging.error(t.get_string("DOWNLOAD_ALL_MIRRORS_FAILED", title))
    print(f"❌ {t.get_string('DOWNLOAD_ALL_MIRRORS_FAILED', title)}")
    return False