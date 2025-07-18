# Cli-Download-Rom/utils/dependency_checker.py (VERSÃO COM AUTO-INSTALL DO ARIA2C)

import logging
import subprocess
import sys
import shutil
import requests
import zipfile
import io
from pathlib import Path
from ..utils.localization import t
from ..utils.config_loader import config

def _is_command_installed(command):
    """Verifica se um comando existe no PATH do sistema ou em nossa pasta bin local."""
    local_bin_path = Path(__file__).parent.parent / 'bin'
    # Prioriza a versão local se existir
    if (local_bin_path / f"{command}.exe").exists():
        return True
    return shutil.which(command) is not None

def _download_and_install_aria2c():
    """Baixa e extrai o aria2c para uma pasta bin local."""
    print(f"ℹ️ {t.get_string('ARIA2C_AUTOINSTALL_START')}")
    # URL para a última versão estável do aria2c para Windows 64-bit
    # Idealmente, isso poderia ser mais dinâmico, mas para nosso caso é suficiente.
    ARIA2C_URL = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    
    bin_dir = Path(__file__).parent.parent / 'bin'
    bin_dir.mkdir(exist_ok=True)
    
    try:
        response = requests.get(ARIA2C_URL, stream=True)
        response.raise_for_status()
        
        # Extrai o conteúdo do ZIP em memória
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # Encontra o executável dentro do ZIP
            for member in zf.infolist():
                if member.filename.endswith('aria2c.exe'):
                    # Extrai apenas o executável para nossa pasta bin
                    with zf.open(member) as source, open(bin_dir / 'aria2c.exe', 'wb') as target:
                        shutil.copyfileobj(source, target)
                    print(f"✔️ {t.get_string('ARIA2C_AUTOINSTALL_SUCCESS')}")
                    return True
        raise FileNotFoundError("aria2c.exe not found in the downloaded archive.")
        
    except Exception as e:
        logging.error(f"Falha no download automático do aria2c: {e}")
        print(f"❌ {t.get_string('ARIA2C_AUTOINSTALL_FAILED')}")
        return False

def check_system_dependencies():
    """Verifica se todas as dependências de sistema estão disponíveis ou as instala."""
    if not _is_command_installed('git'):
        print(f"❌ {t.get_string('ERROR_GIT_NOT_FOUND')}")
        print(f"   {t.get_string('ERROR_GIT_NOT_FOUND_INSTRUCTIONS')}")
        sys.exit(1)

    if not _is_command_installed('aria2c'):
        if not _download_and_install_aria2c():
            sys.exit(1)

def check_and_clone_dependencies():
    """Verifica e clona o repositório do CrocDB se necessário."""
    crocdb_base_path = Path(__file__).parent.parent / 'crocdb'
    repo_name = 'crocdb-db'
    repo_url = config['updates']['crocdb-db_repository_url']
    repo_path = crocdb_base_path / repo_name
    
    if repo_path.is_dir() and any(repo_path.iterdir()):
        logging.info(f"O repositório '{repo_name}' já existe. Pulando a clonagem.")
        return
    
    print(f"ℹ️ {t.get_string('CLONING_REPO_NOTICE', repo_name)}")
    logging.info(f"Clonando {repo_url}...")

    try:
        subprocess.run(
            ['git', 'clone', repo_url, str(repo_path)],
            check=True, capture_output=True, text=True
        )
        print(f"✔️ {t.get_string('CLONING_REPO_SUCCESS', repo_name)}")
        logging.info(f"Repositório '{repo_name}' clonado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"❌ {t.get_string('CLONING_REPO_FAILED', repo_name)}")
        logging.error(f"Falha ao clonar '{repo_name}'. Erro: {e.stderr}")
        sys.exit(1)