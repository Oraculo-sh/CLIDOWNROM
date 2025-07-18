import logging
import subprocess
import sys
import shutil
from pathlib import Path
from ..utils.localization import t
from ..utils.config_loader import config

def _is_command_installed(command):
    """Verifica se um comando existe no PATH do sistema."""
    return shutil.which(command) is not None

def check_system_dependencies():
    """Verifica se todas as dependências de linha de comando (Git, aria2c) estão instaladas."""
    dependencies = {'git': 'ERROR_GIT_NOT_FOUND', 'aria2c': 'ERROR_ARIA2C_NOT_FOUND'}
    all_found = True
    
    for cmd, error_key in dependencies.items():
        if not _is_command_installed(cmd):
            print(f"❌ {t.get_string(error_key)}")
            logging.error(f"{cmd} não foi encontrado no PATH do sistema.")
            all_found = False

    if not all_found:
        print(f"   {t.get_string('ERROR_DEPS_NOT_FOUND_INSTRUCTIONS')}")
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