# Cli-Download-Rom/scripts/check_updates.py

import logging
import subprocess
from pathlib import Path
from ..utils.localization import t
from ..utils.config_loader import config

def _run_git_command(command, cwd):
    """Executa um comando Git no diretório especificado e retorna o resultado."""
    try:
        # Usamos text=True para decodificar a saída para string
        result = subprocess.run(
            command,
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except FileNotFoundError:
        # Isso acontece se o Git não estiver instalado, mas já verificamos isso.
        logging.error("Comando Git não encontrado. A verificação de updates falhou.")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar comando Git '{' '.join(command)}' em '{cwd}': {e.stderr.strip()}")
        return None

def check_for_tool_updates():
    """Verifica se há uma nova versão da própria ferramenta no repositório Git."""
    if not config['updates']['check_tool_update_on_startup']:
        return

    project_dir = Path(__file__).parent.parent
    if not (project_dir / '.git').is_dir():
        logging.warning("O diretório da ferramenta não é um repositório Git. Pulando verificação de update.")
        return

    print(f"ℹ️ {t.get_string('UPDATE_CHECKING_TOOL')}")
    
    # 1. Busca as últimas informações do repositório remoto
    _run_git_command(['git', 'fetch'], project_dir)
    
    # 2. Compara o hash do commit local com o remoto
    local_hash = _run_git_command(['git', 'rev-parse', 'HEAD'], project_dir)
    remote_hash = _run_git_command(['git', 'rev-parse', '@{u}'], project_dir) # '@{u}' é a referência para o upstream/remoto

    if local_hash and remote_hash and local_hash != remote_hash:
        print(f"✨ {t.get_string('UPDATE_TOOL_AVAILABLE')}")
        logging.info("Nova versão da ferramenta disponível.")
    else:
        logging.info("A ferramenta já está na versão mais recente.")

def check_for_crocdb_updates():
    """Verifica e atualiza os repositórios de dados do CrocDB."""
    if not config['updates']['check_crocdb_update_on_startup']:
        return
        
    print(f"ℹ️ {t.get_string('UPDATE_CHECKING_CROCDB')}")
    
    crocdb_base_path = Path(__file__).parent.parent / 'crocdb'
    repos_to_update = ['crocdb-db']

    for repo_name in repos_to_update:
        repo_path = crocdb_base_path / repo_name
        if repo_path.is_dir():
            logging.info(f"Atualizando o repositório '{repo_name}'...")
            output = _run_git_command(['git', 'pull'], repo_path)
            if output and 'Already up to date.' not in output:
                print(f"✨ {t.get_string('UPDATE_CROCDB_SUCCESS', repo_name)}")
                logging.info(f"Repositório '{repo_name}' foi atualizado.")
            else:
                logging.info(f"Repositório '{repo_name}' já está atualizado.")