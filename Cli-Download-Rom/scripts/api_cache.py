import json
import os
from datetime import datetime, timedelta
from utils.logging_config import setup_logging

log = setup_logging()

def save_to_cache(filename, data):
    """
    Salva os dados no cache junto com um timestamp.
    """
    cache_dir = os.path.dirname(filename)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    cache_content = {
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cache_content, f, indent=4)
        log.info(f"Cache salvo com sucesso em {filename}")
    except IOError as e:
        log.error(f"Não foi possível escrever no ficheiro de cache {filename}: {e}")

def load_from_cache(filename, max_age_hours):
    """
    Carrega os dados do cache se ele existir e não estiver expirado.
    """
    if not os.path.exists(filename):
        log.info(f"Ficheiro de cache não encontrado: {filename}")
        return None

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cache_content = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        log.error(f"Erro ao ler ou decodificar o ficheiro de cache {filename}: {e}")
        return None

    timestamp_str = cache_content.get("timestamp")
    if not timestamp_str:
        log.warning("Cache não contém timestamp. Considerado inválido.")
        return None

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        cache_age = datetime.now() - timestamp
        if cache_age > timedelta(hours=max_age_hours):
            log.info(f"Cache expirado. Idade: {cache_age}, Máximo: {max_age_hours} horas.")
            return None
    except ValueError:
        log.error("Formato de timestamp inválido no cache.")
        return None


    log.info(f"Cache válido encontrado. Carregando dados de {filename}")
    return cache_content.get("data")