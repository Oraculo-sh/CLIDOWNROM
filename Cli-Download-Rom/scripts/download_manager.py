import logging
import shutil
import aria2p
import time
import subprocess
import atexit
import os
from pathlib import Path
from tqdm import tqdm
from ..utils.localization import t
from ..utils.config_loader import config
from ..utils.dependency_checker import _get_aria2c_executable_name

success_logger = logging.getLogger('success_logger')
aria2_client = None
aria2_process = None

def _get_aria2c_path():
    executable_name = _get_aria2c_executable_name()
    local_path = Path(__file__).parent.parent / 'bin' / executable_name
    if local_path.exists():
        return str(local_path)
    if shutil.which(executable_name):
        return executable_name
    return None

def _shutdown_aria2c():
    global aria2_client, aria2_process
    if aria2_client:
        try:
            aria2_client.shutdown()
            logging.info("Servidor aria2c desligado via RPC.")
        except Exception:
            if aria2_process and aria2_process.poll() is None:
                aria2_process.terminate()
                logging.info("Processo aria2c terminado forçadamente.")

def _get_aria2_client():
    global aria2_client, aria2_process
    if aria2_client:
        return aria2_client
    aria2c_path = _get_aria2c_path()
    if not aria2c_path:
        raise FileNotFoundError("aria2c executável não pôde ser encontrado.")
    try:
        client = aria2p.API(aria2p.Client())
        client.get_stats()
        logging.info("Conectado a uma instância existente do aria2c.")
        aria2_client = client
        return aria2_client
    except Exception:
        logging.info("Nenhuma instância do aria2c encontrada. Iniciando um novo processo...")
    command = [
        aria2c_path, "--enable-rpc", "--rpc-listen-all=false",
        "--rpc-listen-port=6800", "--console-log-level=warn"
    ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    aria2_process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logging.info(f"Processo aria2c iniciado com PID: {aria2_process.pid}")
    atexit.register(_shutdown_aria2c)
    time.sleep(1)
    aria2_client = aria2p.API(aria2p.Client())
    return aria2_client

def download_rom_normal(url, temp_file_path):
    """Fallback para download via requests se noaria2c for especificado."""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(temp_file_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        if total_size != 0 and temp_file_path.stat().st_size != total_size:
            raise IOError("Download incompleto: tamanho do ficheiro não corresponde.")
        return True
    except requests.RequestException as e:
        logging.error(f"Erro de download com requests: {e}")
        return False

def download_rom_aria2c(url, temp_download_path, filename, title):
    """Download principal via aria2c."""
    try:
        aria2 = _get_aria2_client()
        download_options = {
            'dir': str(temp_download_path), 'out': filename,
            'split': str(config['mirrors'].get('download_splits', 5)),
            'max-connection-per-server': str(config['mirrors'].get('connections_per_server', 5))
        }
        download = aria2.add_uris([url], options=download_options)
        with tqdm(total=100, desc=f"Baixando {title[:30]}", unit='%', bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            while not download.is_complete:
                download.update()
                progress = int(download.progress)
                if pbar.n != progress:
                    pbar.n = progress
                    pbar.refresh()
                time.sleep(0.5)
            pbar.n = 100
            pbar.refresh()
        download.update()
        if download.is_complete and download.status == 'complete':
            return True
        else:
            logging.error(f"Erro no download com aria2c para '{title}': {download.error_message}")
            return False
    except Exception as e:
        logging.error(f"Falha ao gerir download com aria2c para '{title}'. Erro: {e}")
        return False

def download_rom(rom_details, preferred_mirror, destination_folder=None, no_aria2c=False, no_boxart=False):
    title, platform, rom_id = rom_details.get('title', 'N/A'), rom_details.get('platform', 'Unknown'), rom_details.get('rom_id', 'N/A')
    links = sorted(rom_details.get('links', []), key=lambda x: x.get('host') == preferred_mirror, reverse=True)
    
    base_rom_path = Path(__file__).parent.parent / config['general']['roms_directory']
    temp_download_path = Path(__file__).parent.parent / config['general']['temp_directory'] / 'downloads'
    
    if destination_folder:
        final_rom_dir = base_rom_path / destination_folder
    else:
        final_rom_dir = base_rom_path / platform
    
    final_rom_dir.mkdir(parents=True, exist_ok=True)
    temp_download_path.mkdir(parents=True, exist_ok=True)

    for link in links:
        url, host, filename = link.get('url'), link.get('host'), link.get('filename')
        if not all([url, host, filename]): continue

        final_file = final_rom_dir / filename
        if final_file.exists():
            print(f"ℹ️ {t.get_string('DOWNLOAD_ALREADY_EXISTS', title)}")
            return True

        print(f"⌁ {t.get_string('DOWNLOAD_ATTEMPTING', title, host)}")
        
        temp_file = temp_download_path / filename
        download_success = False
        if no_aria2c:
            download_success = download_rom_normal(url, temp_file)
        else:
            download_success = download_rom_aria2c(url, temp_download_path, filename, title)
        
        if download_success:
            print(f"→ {t.get_string('MOVE_STARTING', title)}")
            shutil.move(temp_file, final_file)
            print(f"✔️ {t.get_string('MOVE_SUCCESS', str(final_file))}")
            success_logger.info(f"'{title}' ({rom_id}) baixada e movida com sucesso de '{host}'.")
            
            # Baixar Boxart
            if not no_boxart and rom_details.get('boxart_url'):
                try:
                    boxart_url = rom_details['boxart_url']
                    boxart_ext = Path(boxart_url).suffix
                    boxart_path = final_rom_dir / (Path(filename).stem + boxart_ext)
                    response = requests.get(boxart_url, stream=True)
                    if response.ok:
                        with open(boxart_path, 'wb') as f:
                            f.write(response.content)
                        logging.info(f"Boxart para '{title}' baixada com sucesso.")
                except Exception as e:
                    logging.warning(f"Não foi possível baixar a boxart para '{title}': {e}")

            return True
        else: # Se o download falhou, tenta o próximo mirror
            if temp_file.exists(): temp_file.unlink()
            continue

    logging.error(t.get_string("DOWNLOAD_ALL_MIRRORS_FAILED", title))
    print(f"❌ {t.get_string('DOWNLOAD_ALL_MIRRORS_FAILED', title)}")
    return False