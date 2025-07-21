import requests
import logging
from ..utils.config_loader import config
from ..utils.localization import t
from .api_cache import get_cached_search, save_search_to_cache

class CrocDBAPIHandler:
    def __init__(self):
        if not config:
            raise ValueError("Configuração não carregada.")
        self.base_url = config['api']['crocdb_api_url']

    def search_rom(self, query, platforms=None, regions=None):
        search_url = f"{self.base_url}/search"
        payload = {
            "search_key": query or "", "platforms": platforms or [],
            "regions": regions or [], "max_results": 100
        }
        
        # Verifica o cache primeiro
        cached_data = get_cached_search(payload)
        if cached_data:
            logging.info("Resultados da busca encontrados no cache.")
            return cached_data

        all_results, current_page, total_pages = [], 1, 1
        max_pages = config['api'].get('max_search_pages', 5)
        logging.info(t.get_string("API_SEARCH_ATTEMPT", query, search_url))

        while current_page <= total_pages and current_page <= max_pages:
            payload["page"] = current_page
            logging.info(f"Buscando página {current_page}...")
            try:
                response = requests.post(search_url, json=payload, timeout=20)
                response.raise_for_status()
                response_data, data = response.json(), response_data.get('data', {})
                results = data.get('results', [])
                if not results: break
                all_results.extend(results)
                if current_page == 1: total_pages = data.get('total_pages', 1)
                current_page += 1
            except Exception as e:
                logging.error(t.get_string("API_REQUEST_ERROR", search_url, e)); return None
        
        if not all_results: logging.warning(t.get_string("API_SEARCH_NO_RESULTS", query)); return []
        
        logging.info(t.get_string("API_SEARCH_SUCCESS", len(all_results), query))
        save_search_to_cache(payload, all_results) # Salva o resultado final no cache
        return all_results

    def get_rom_details(self, identifier, by='slug'):
        payload = {by: identifier}
        if by not in ['slug', 'rom_id']: return None
        
        # Busca por rom_id é feita no endpoint /search
        url = f"{self.base_url}/search" if by == 'rom_id' else f"{self.base_url}/entry"

        logging.info(t.get_string("API_DETAILS_ATTEMPT", identifier, url))
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json().get('data', {})
            
            if by == 'rom_id':
                # A resposta do /search é uma lista
                entry_details = data.get('results', [{}])[0] if data.get('results') else None
            else: # by slug
                entry_details = data.get('entry')

            if not entry_details: return None
            logging.info(t.get_string("API_DETAILS_SUCCESS", entry_details.get('title', identifier)))
            return entry_details
        except Exception as e:
            logging.error(t.get_string("API_UNEXPECTED_ERROR", "get_rom_details", e)); return None