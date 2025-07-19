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
        Busca por ROMs na API em múltiplas páginas e retorna uma lista agregada.
        """
        search_url = f"{self.base_url}/search"
        all_results = []
        max_pages = config['api'].get('max_search_pages', 3) # Limite de segurança
        current_page = 1
        total_pages = 1 # Inicia com 1 para garantir que o loop rode pelo menos uma vez

        logging.info(t.get_string("API_SEARCH_ATTEMPT", query, search_url))

        while current_page <= total_pages and current_page <= max_pages:
            payload = {
                "search_key": query or "",
                "platforms": platforms or [],
                "regions": regions or [],
                "page": current_page
            }
            
            logging.info(f"Buscando página {current_page} de {total_pages}...")

            try:
                response = requests.post(search_url, json=payload, timeout=20)
                response.raise_for_status()
                
                response_data = response.json()
                data = response_data.get('data', {})
                results = data.get('results', [])
                
                if results:
                    all_results.extend(results)
                
                # Atualiza o total de páginas com a informação do primeiro request bem-sucedido
                if current_page == 1:
                    total_pages = data.get('total_pages', 1)
                
                current_page += 1

            except requests.exceptions.HTTPError as e:
                logging.error(t.get_string("API_HTTP_ERROR", search_url, e.response.status_code))
                return None # Se uma página falhar, interrompe a busca
            except requests.exceptions.RequestException as e:
                logging.error(t.get_string("API_REQUEST_ERROR", search_url, e))
                return None
            except Exception as e:
                logging.error(t.get_string("API_UNEXPECTED_ERROR", "search_rom", e))
                return None
        
        if not all_results:
            logging.warning(t.get_string("API_SEARCH_NO_RESULTS", query))
            return []
        
        logging.info(t.get_string("API_SEARCH_SUCCESS", len(all_results), query))
        return all_results

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