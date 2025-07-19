# Cli-Download-Rom/scripts/download_manager.py (VERSÃO FINAL COM CONTROLE DE VELOCIDADE)

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
from ..utils.dependency_checker import _is_command_installed

success_logger = logging.getLogger('success_logger')

# Variáveis globais para gerenciar o cliente e o processo do aria2c
aria2_client = None
aria2_process = None

def _get_aria2c_path():
    """Encontra o caminho para o executável do aria2c."""
    local_path = Path(__file__).parent.parent / 'bin' / 'aria2c.exe'
    if local_path.exists():
        return str(local_path)
    if _is_command_installed('aria2c'):
        return 'aria2c'
    return None

def _shutdown_aria2c():
    """Função para ser chamada na saída do programa para garantir que o aria2c seja encerrado."""
    global aria2_client, aria2_process
    if aria2_client:
        try:
            aria2_client.shutdown()
            logging.info("Servidor aria2c desligado via RPC.")
        except Exception:
            if aria2_process:
                aria2_process.terminate()
                logging.info("Processo aria2c terminado forçadamente.")

def _get_aria2_client():
    """
    Inicia o servidor aria2c se necessário e retorna um cliente conectado.
    """
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
        aria2c_path,
        "--enable-rpc",
        "--rpc-listen-all=false",
        "--rpc-listen-port=6800",
        "--console-log-level=warn"
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

def download_rom(rom_details, preferred_mirror):
    """Gerencia o download de uma ROM usando aria2c com opções customizadas."""
    try:
        aria2 = _get_aria2_client()
    except Exception as e:
        logging.error(f"Não foi possível iniciar ou conectar ao aria2c: {e}")
        print(f"❌ {t.get_string('ERROR_ARIA2C_NOT_FOUND')}")
        return False
        
    title = rom_details.get('title', 'N/A')
    platform = rom_details.get('platform', 'Unknown')
    
    links = sorted(rom_details.get('links', []), key=lambda x: x.get('host') == preferred_mirror, reverse=True)
    if not links:
        logging.error(f"Nenhum link de download encontrado para '{title}'.")
        return False
    
    link = links[0]
    url = link.get('url')
    host = link.get('host')
    filename = link.get('filename')
    
    temp_download_path = Path(__file__).parent.parent / config['general']['temp_directory'] / 'downloads'
    final_rom_dir = Path(__file__).parent.parent / config['general']['roms_directory'] / platform
    final_file = final_rom_dir / filename
    
    final_rom_dir.mkdir(parents=True, exist_ok=True)
    temp_download_path.mkdir(parents=True, exist_ok=True)

    if final_file.exists():
        print(f"ℹ️ {t.get_string('DOWNLOAD_ALREADY_EXISTS', title)}")
        return True

    print(f"⌁ {t.get_string('DOWNLOAD_ATTEMPTING', title, host)}")
    
    # --- LÓGICA DE OPÇÕES CUSTOMIZADAS ---
    download_options = {
        'dir': str(temp_download_path),
        'out': filename,
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

        if download.is_complete and not download.has_error:
            temp_file = temp_download_path / filename
            print(f"→ {t.get_string('MOVE_STARTING', title)}")
            shutil.move(temp_file, final_file)
            print(f"✔️ {t.get_string('MOVE_SUCCESS', str(final_file))}")
            success_logger.info(f"'{title}' baixada e movida com sucesso.")
            return True
        else:
            logging.error(f"Erro no download com aria2c para '{title}': {download.error_message}")
            return False

    except Exception as e:
        logging.error(f"Falha ao iniciar download com aria2c para '{title}'. Erro: {e}")
        return False