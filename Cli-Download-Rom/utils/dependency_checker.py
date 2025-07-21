import logging
import subprocess
import sys
import shutil
import requests
import zipfile
import io
import platform
from pathlib import Path
from ..utils.localization import t
from ..utils.config_loader import config

def _get_aria2c_executable_name():
    """Retorna o nome do executável (aria2c.exe no Windows, aria2c em outros)."""
    return "aria2c.exe" if sys.platform == "win32" else "aria2c"

def _is_command_installed(command):
    """Verifica se um comando existe no PATH ou na nossa pasta bin local."""
    local_bin_path = Path(__file__).parent.parent / 'bin'
    if (local_bin_path / command).exists():
        return True
    return shutil.which(command) is not None

def _download_and_install_aria2c_windows():
    """Baixa e extrai o aria2c para Windows (64 ou 32 bits)."""
    print(f"ℹ️ {t.get_string('ARIA2C_AUTOINSTALL_START')}")
    
    is_64bit = platform.machine().endswith('64')
    if is_64bit:
        url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip"
    else:
        url = "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-32bit-build1.zip"
    
    bin_dir = Path(__file__).parent.parent / 'bin'
    bin_dir.mkdir(exist_ok=True)
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for member in zf.infolist():
                if member.filename.endswith('aria2c.exe'):
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
    """Verifica as dependências do sistema e instrui ou instala conforme o SO."""
    # Verifica o Git (necessário para todos)
    if not _is_command_installed('git'):
        print(f"❌ {t.get_string('ERROR_GIT_NOT_FOUND')}")
        print(f"   {t.get_string('ERROR_GIT_NOT_FOUND_INSTRUCTIONS')}")
        sys.exit(1)

    # Verifica o aria2c
    executable_name = _get_aria2c_executable_name()
    if not _is_command_installed(executable_name):
        if sys.platform == "win32":
            # Para Windows, tenta o download automático
            if not _download_and_install_aria2c_windows():
                sys.exit(1)
        elif sys.platform == "linux":
            # Para Linux, instrui o usuário
            print(f"❌ {t.get_string('ERROR_ARIA2C_NOT_FOUND')}")
            print(f"   {t.get_string('ERROR_ARIA2C_LINUX_INSTRUCTIONS')}")
            sys.exit(1)
        elif sys.platform == "darwin": # macOS
            # Para macOS, instrui o usuário
            print(f"❌ {t.get_string('ERROR_ARIA2C_NOT_FOUND')}")
            print(f"   {t.get_string('ERROR_ARIA2C_MACOS_INSTRUCTIONS')}")
            sys.exit(1)
        else:
            print(f"❌ Sistema operacional '{sys.platform}' não suportado para instalação automática do aria2c.")
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