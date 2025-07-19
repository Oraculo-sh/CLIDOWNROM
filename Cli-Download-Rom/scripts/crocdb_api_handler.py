# Cli-Download-Rom/scripts/crocdb_api_handler.py (VERSÃO CORRIGIDA)

import requests
import logging
from ..utils.config_loader import config
from ..utils.localization import t

class CrocDBAPIHandler:
    """
    Gerencia a comunicação com a API oficial do CrocDB.
    """
    def __init__(self):
        if not config:
            raise ValueError("Configuração não carregada.")
        self.base_url = config['api']['crocdb_api_url']

    def search_rom(self, query, platforms=None, regions=None):
        """
        Busca por ROMs na API usando o método POST e filtros.
        """
        search_url = f"{self.base_url}/search"
        # Adiciona os filtros ao payload se eles forem fornecidos
        payload = {
            "search_key": query,
            "platforms": platforms or [],
            "regions": regions or []
        }
        
        logging.info(t.get_string("API_SEARCH_ATTEMPT", query, search_url))

        try:
            response = requests.post(search_url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json().get('data', {})
            results = data.get('results', [])

            if not results:
                logging.warning(t.get_string("API_SEARCH_NO_RESULTS", query))
                return []
            
            logging.info(t.get_string("API_SEARCH_SUCCESS", len(results), query))
            return results

        except requests.exceptions.HTTPError as e:
            logging.error(t.get_string("API_HTTP_ERROR", search_url, e.response.status_code))
        except requests.exceptions.RequestException as e:
            logging.error(t.get_string("API_REQUEST_ERROR", search_url, e))
        except Exception as e:
            logging.error(t.get_string("API_UNEXPECTED_ERROR", "search_rom", e))
        
        return None

    def get_rom_details(self, slug):
        """
        Obtém os detalhes completos de uma ROM usando seu slug.
        """
        details_url = f"{self.base_url}/entry"
        payload = {"slug": slug}

        logging.info(t.get_string("API_DETAILS_ATTEMPT", slug, details_url))

        try:
            response = requests.post(details_url, json=payload, timeout=15)
            response.raise_for_status()

            data = response.json().get('data', {})
            entry_details = data.get('entry')

            if not entry_details:
                logging.error(f"Nenhum 'entry' encontrado na resposta da API para o slug: {slug}")
                return None
            
            logging.info(t.get_string("API_DETAILS_SUCCESS", entry_details.get('title', slug)))
            return entry_details

        except requests.exceptions.HTTPError as e:
            logging.error(t.get_string("API_HTTP_ERROR", details_url, e.response.status_code))
        except requests.exceptions.RequestException as e:
            logging.error(t.get_string("API_REQUEST_ERROR", details_url, e))
        except Exception as e:
            logging.error(t.get_string("API_UNEXPECTED_ERROR", "get_rom_details", e))
            
        return None