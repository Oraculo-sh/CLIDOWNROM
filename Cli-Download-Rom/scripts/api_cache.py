import json
import time
from pathlib import Path
from ..utils.config_loader import config

CACHE_DIR = Path(__file__).parent.parent / config['general']['temp_directory'] / 'api_cache'
CACHE_EXPIRY_SECONDS = 3600  # 1 hora

def _get_cache_filepath(payload):
    # Cria um nome de ficheiro a partir do payload da busca
    search_key = payload.get('search_key', '')
    platforms = "_".join(sorted(payload.get('platforms', [])))
    regions = "_".join(sorted(payload.get('regions', [])))
    filename = f"{search_key}_{platforms}_{regions}.json"
    # Remove caracteres inválidos para nomes de ficheiro
    filename = "".join([c for c in filename if c.isalnum() or c in (' ', '_', '-')]).rstrip()
    return CACHE_DIR / filename

def get_cached_search(payload):
    CACHE_DIR.mkdir(exist_ok=True)
    filepath = _get_cache_filepath(payload)
    if filepath.exists():
        mod_time = filepath.stat().st_mtime
        if (time.time() - mod_time) < CACHE_EXPIRY_SECONDS:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    return None

def save_search_to_cache(payload, data):
    CACHE_DIR.mkdir(exist_ok=True)
    filepath = _get_cache_filepath(payload)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f)