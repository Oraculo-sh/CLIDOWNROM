import argparse
from Levenshtein import distance
from utils.localization import _
from utils.logging_config import setup_logging
from scripts.api_cache import load_from_cache, save_to_cache
from scripts.crocdb_api_handler import get_platforms, get_regions

log = setup_logging()

def get_choices(cache_file_key, fetch_function, config, cache_key):
    """
    Obtém as escolhas (plataformas/regiões) do cache ou da API.
    """
    api_url = config.get("api", {}).get("crocdb_api_url")
    cache_config = config.get("cache", {}) # Acessa o grupo 'cache'
    
    cache_file = cache_config.get(cache_file_key)
    cache_duration_hours = cache_config.get("cache_duration_hours", 24)
    
    if not cache_file:
        log.error(f"A chave de configuração '{cache_file_key}' não foi encontrada na secção 'cache' do config.yml.")
        return []

    # Tenta carregar do cache
    cached_data = load_from_cache(cache_file, cache_duration_hours)
    if cached_data:
        return list(cached_data.keys())

    # Se não houver cache, busca da API
    print(_(f"info_updating_{cache_key}")) # Ex: info_updating_platforms
    response = fetch_function(api_url)
    if response and "data" in response and response["data"].get(cache_key):
        data_to_cache = response["data"][cache_key]
        save_to_cache(cache_file, data_to_cache)
        return list(data_to_cache.keys())
    
    log.warning(f"Não foi possível obter {cache_key} da API. As opções estarão vazias.")
    return []

def create_parser(config):
    """
    Cria e configura o parser de argumentos da linha de comando.
    """
    parser = argparse.ArgumentParser(description=_("app_description"))

    platform_choices = get_choices("platforms_cache_file", get_platforms, config, "platforms")
    region_choices = get_choices("regions_cache_file", get_regions, config, "regions")

    parser.add_argument(
        "search_key",
        nargs="*",
        help=_("help_search_key")
    )
    parser.add_argument(
        "-p", "--platforms",
        nargs="+",
        metavar="PLATFORM",
        choices=platform_choices,
        help=_("help_platforms").format(choices=", ".join(platform_choices))
    )
    parser.add_argument(
        "-r", "--regions",
        nargs="+",
        metavar="REGION",
        choices=region_choices,
        help=_("help_regions").format(choices=", ".join(region_choices))
    )
    return parser

def rank_results(results, search_term):
    """
    Classifica os resultados da busca com base na similaridade do título.
    """
    if not search_term:
        return results
    
    search_term_lower = search_term.lower()
    
    def sort_key(result):
        title = result.get("title", "").lower()
        dist = distance(search_term_lower, title)
        # Prioriza correspondências exatas e de prefixo
        if title == search_term_lower:
            return -2
        if title.startswith(search_term_lower):
            return -1
        return dist

    return sorted(results, key=sort_key)