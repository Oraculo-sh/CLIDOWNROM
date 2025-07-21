import logging
import subprocess
from pathlib import Path
from ..utils.localization import t
from ..utils.config_loader import config

def _run_git_command(command, cwd):
    try:
        result = subprocess.run(
            command, cwd=str(cwd), check=True, capture_output=True,
            text=True, encoding='utf-8'
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logging.error(f"Erro ao executar Git: {e}")
        return None

def check_for_tool_updates():
    if not config['updates']['check_tool_update_on_startup']: return
    project_dir = Path(__file__).parent.parent.parent
    if not (project_dir / '.git').is_dir():
        logging.warning("O diretório da ferramenta não é um repositório Git. Pulando verificação de update.")
        return
    print(f"ℹ️ {t.get_string('UPDATE_CHECKING_TOOL')}")
    _run_git_command(['git', 'fetch'], project_dir)
    local_hash = _run_git_command(['git', 'rev-parse', 'HEAD'], project_dir)
    remote_hash = _run_git_command(['git', 'rev-parse', '@{u}'], project_dir)
    if local_hash and remote_hash and local_hash != remote_hash:
        print(f"✨ {t.get_string('UPDATE_TOOL_AVAILABLE')}")
        logging.info("Nova versão da ferramenta disponível.")
    else:
        logging.info("A ferramenta já está na versão mais recente.")