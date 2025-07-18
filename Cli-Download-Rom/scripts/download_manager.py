import logging
import shutil
import aria2p
from pathlib import Path
from tqdm import tqdm
from ..utils.localization import t
from ..utils.config_loader import config

success_logger = logging.getLogger('success_logger')

# Inicializa a API do aria2. A porta pode ser configurada se necessário.
aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret=""
    )
)

def download_rom(rom_details, preferred_mirror):
    """Gerencia o download de uma ROM usando aria2c para alta velocidade."""
    title = rom_details.get('title', 'N/A')
    platform = rom_details.get('platform', 'Unknown')
    rom_id = rom_details.get('rom_id', 'N/A')
    
    links = sorted(rom_details.get('links', []), key=lambda x: x.get('host') == preferred_mirror, reverse=True)
    
    base_rom_path = Path(__file__).parent.parent / config['general']['roms_directory']
    temp_download_path = Path(__file__).parent.parent / config['general']['temp_directory'] / 'downloads'
    final_rom_dir = base_rom_path / platform
    
    final_rom_dir.mkdir(parents=True, exist_ok=True)
    temp_download_path.mkdir(parents=True, exist_ok=True)

    for link in links:
        url = link.get('url')
        host = link.get('host')
        filename = link.get('filename')

        if not all([url, host, filename]):
            continue

        final_file = final_rom_dir / filename
        if final_file.exists():
            print(f"ℹ️ {t.get_string('DOWNLOAD_ALREADY_EXISTS', title)}")
            return True

        print(f"⌁ {t.get_string('DOWNLOAD_ATTEMPTING', title, host)}")
        
        try:
            download = aria2.add_uris([url], options={'dir': str(temp_download_path), 'out': filename})
            
            with tqdm(total=100, desc=f"Baixando {title[:30]}", unit='%') as pbar:
                while not download.is_complete:
                    download.update()
                    pbar.n = int(download.progress)
                    pbar.refresh()
            
            if download.is_complete and not download.has_error:
                logging.info(t.get_string("DOWNLOAD_SUCCESS", title))
                success_logger.info(f"'{title}' ({rom_id}) baixada com sucesso de '{host}'.")
                
                temp_file = temp_download_path / filename
                print(f"→ {t.get_string('MOVE_STARTING', title)}")
                shutil.move(temp_file, final_file)
                print(f"✔️ {t.get_string('MOVE_SUCCESS', str(final_file))}")
                success_logger.info(f"'{title}' movida para '{final_file}'.")
                return True
            else:
                logging.error(f"Erro no download com aria2c para '{title}': {download.error_message}")
                continue

        except Exception as e:
            logging.error(f"Falha ao iniciar download com aria2c para '{title}'. Erro: {e}")
            # Tenta o próximo mirror se a API do aria2c falhar
            continue

    logging.error(t.get_string("DOWNLOAD_ALL_MIRRORS_FAILED", title))
    print(f"❌ {t.get_string('DOWNLOAD_ALL_MIRRORS_FAILED', title)}")
    return False