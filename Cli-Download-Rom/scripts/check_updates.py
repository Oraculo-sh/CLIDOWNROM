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
        logging.warning(t.get_string('UPDATE_TOOL_NOT_A_GIT_REPO'))
        return
    print(f"ℹ️ {t.get_string('UPDATE_CHECKING_TOOL')}")
    _run_git_command(['git', 'fetch'], project_dir)
    local_hash = _run_git_command(['git', 'rev-parse', 'HEAD'], project_dir)
    remote_hash = _run_git_command(['git', 'rev-parse', '@{u}'], project_dir)
    if local_hash and remote_hash and local_hash != remote_hash:
        print(f"✨ {t.get_string('UPDATE_TOOL_AVAILABLE')}")
        logging.info(t.get_string('LOG_UPDATE_TOOL_AVAILABLE'))
    else:
        logging.info(t.get_string('LOG_TOOL_UP_TO_DATE'))