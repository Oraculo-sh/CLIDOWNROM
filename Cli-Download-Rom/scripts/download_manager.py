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
from ..utils.dependency_checker import _is_command_installed, _get_aria2c_executable_name

def _get_aria2c_path():
    """Encontra o caminho para o executável multiplataforma do aria2c."""
    executable_name = _get_aria2c_executable_name()
    local_path = Path(__file__).parent.parent / 'bin' / executable_name
    if local_path.exists():
        return str(local_path)
    if _is_command_installed(executable_name):
        return executable_name
    return None

def _get_aria2_client():
    """Inicia o servidor aria2c se necessário e retorna um cliente conectado."""
    global aria2_client, aria2_process
    if aria2_client:
        return aria2_client

    aria2c_path = _get_aria2c_path()
    if not aria2c_path:
        raise FileNotFoundError("aria2c não pôde ser encontrado.")

def _get_aria2_client():
    """Inicia o servidor aria2c se necessário e retorna um cliente conectado."""
    global aria2_client, aria2_process
    if aria2_client:
        return aria2_client

    aria2c_path = _get_aria2c_path()
    if not aria2c_path:
        raise FileNotFoundError("aria2c.exe não pôde ser encontrado.")

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

def _handle_insufficient_space(required_bytes):
    """Lida com o erro de espaço insuficiente de forma interativa."""
    while True:
        available_bytes = shutil.disk_usage(config['general']['temp_directory']).free
        required_mb_str = f"{required_bytes / (1024*1024):.2f} MB"
        available_mb_str = f"{available_bytes / (1024*1024):.2f} MB"
        
        print(f"\n❌ {t.get_string('ERROR_INSUFFICIENT_SPACE', required_mb_str, available_mb_str)}")
        choice = input(f"   {t.get_string('PROMPT_INSUFFICIENT_SPACE')} ").upper()

        if choice == 'R':
            print(f"   {t.get_string('RECHECKING_SPACE')}")
            if shutil.disk_usage(config['general']['temp_directory']).free >= required_bytes:
                print(f"✔️ {t.get_string('SUCCESS_SPACE_FREED')}")
                return True
        elif choice == 'C':
            return False
        else:
            print(f"   ⚠️ {t.get_string('ERROR_INVALID_CHOICE')}")

def download_rom(rom_details, preferred_mirror, destination_folder=None):
    """Gerencia o download de uma ROM usando aria2c com opções customizadas."""
    try:
        aria2 = _get_aria2_client()
    except Exception as e:
        logging.error(f"Não foi possível iniciar ou conectar ao aria2c: {e}")
        print(f"❌ {t.get_string('ERROR_ARIA2C_NOT_FOUND')}")
        return False
        
    title = rom_details.get('title', 'N/A')
    platform = rom_details.get('platform', 'Unknown')
    rom_id = rom_details.get('rom_id', 'N/A')
    
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
        url = link.get('url')
        host = link.get('host')
        filename = link.get('filename')
        expected_size = link.get('size')

        if not all([url, host, filename, expected_size]):
            logging.warning(f"Link inválido para a ROM '{title}', pulando.")
            continue

        final_file = final_rom_dir / filename
        if final_file.exists():
            print(f"ℹ️ {t.get_string('DOWNLOAD_ALREADY_EXISTS', title)}")
            success_logger.info(f"ROM '{title}' ({rom_id}) já existe.")
            return True

        if shutil.disk_usage(temp_download_path).free < expected_size:
            if not _handle_insufficient_space(expected_size):
                logging.error(t.get_string("DOWNLOAD_CANCELLED_BY_USER_NO_SPACE", title))
                return False

        print(f"⌁ {t.get_string('DOWNLOAD_ATTEMPTING', title, host)}")
        
        download_options = {
            'dir': str(temp_download_path), 'out': filename,
            'split': str(config['mirrors'].get('download_splits', 5)),
            'max-connection-per-server': str(config['mirrors'].get('connections_per_server', 5))
        }
        
        try:
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
                temp_file = temp_download_path / filename
                print(f"→ {t.get_string('MOVE_STARTING', title)}")
                shutil.move(temp_file, final_file)
                print(f"✔️ {t.get_string('MOVE_SUCCESS', str(final_file))}")
                success_logger.info(f"'{title}' ({rom_id}) baixada, validada e movida com sucesso de '{host}'.")
                return True
            else:
                # Se o download terminou mas o status não é 'complete', é um erro.
                logging.error(f"Erro no download com aria2c para '{title}': {download.error_message}")
                continue # Tenta o próximo mirror

        except Exception as e:
            logging.error(f"Falha ao gerenciar download com aria2c para '{title}'. Erro: {e}")
            continue # Tenta o próximo mirror

    logging.error(t.get_string("DOWNLOAD_ALL_MIRRORS_FAILED", title))
    print(f"❌ {t.get_string('DOWNLOAD_ALL_MIRRORS_FAILED', title)}")
    return False