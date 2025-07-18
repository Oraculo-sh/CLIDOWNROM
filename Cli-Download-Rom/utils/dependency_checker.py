# Cli-Download-Rom/utils/dependency_checker.py

import logging
import subprocess
import sys
from pathlib import Path
from .localization import t
from .config_loader import config

def is_git_installed():
    """Verifica se o Git está instalado e acessível no PATH do sistema."""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        logging.info("Git is installed and accessible.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.error("Git is not installed or not in the system's PATH.")
        return False

def check_and_clone_dependencies():
    """
    Verifica a existência dos repositórios do CrocDB e os clona se necessário.
    """
    if not is_git_installed():
        print(f"❌ {t.get_string('ERROR_GIT_NOT_FOUND')}")
        print(f"   {t.get_string('ERROR_GIT_NOT_FOUND_INSTRUCTIONS')}")
        sys.exit(1)

    crocdb_base_path = Path(__file__).parent.parent / 'crocdb'
    repos_to_check = {
        'crocdb-db': config['updates']['crocdb-db_repository_url'],
        'crocdb-api': config['updates']['crocdb-api_repository_url']
    }

    for repo_name, repo_url in repos_to_check.items():
        repo_path = crocdb_base_path / repo_name

        if repo_path.is_dir() and any(repo_path.iterdir()):
            logging.info(f"O repositório '{repo_name}' já existe. Pulando a clonagem.")
            continue

        print(f"ℹ️ {t.get_string('CLONING_REPO_NOTICE', repo_name)}")
        logging.info(f"O repositório '{repo_name}' não foi encontrado. Clonando de {repo_url}...")

        try:
            subprocess.run(
                ['git', 'clone', repo_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✔️ {t.get_string('CLONING_REPO_SUCCESS', repo_name)}")
            logging.info(f"Repositório '{repo_name}' clonado com sucesso.")
        except subprocess.CalledProcessError as e:
            print(f"❌ {t.get_string('CLONING_REPO_FAILED', repo_name)}")
            logging.error(f"Falha ao clonar '{repo_name}'. Erro: {e.stderr}")
            sys.exit(1)