import requests
import logging
from utils.config_loader import config
from utils.localization import t

class CrocDBAPIHandler:
    """
    Gerencia a comunicação com a API oficial do CrocDB.
    """
    def __init__(self):
        if not config:
            raise ValueError("Configuração não carregada.")
        self.base_url = config['api']['crocdb_api_url']

    def search_rom(self, query):
        """
        Busca por ROMs na API usando um termo de pesquisa.

        Args:
            query (str): O termo para a busca.

        Returns:
            list: Uma lista de dicionários com os resultados da busca, ou None em caso de erro.
                  Formato esperado: [{"rom_id":"","title":"","platform":"","regions":""}]
        """
        search_url = f"{self.base_url}/search/{query}"
        logging.info(t.get_string("API_SEARCH_ATTEMPT", query, search_url))

        try:
            response = requests.get(search_url, timeout=15)
            response.raise_for_status()  # Lança uma exceção para códigos de erro HTTP (4xx ou 5xx)
            
            data = response.json()
            if not data:
                logging.warning(t.get_string("API_SEARCH_NO_RESULTS", query))
                return []
            
            logging.info(t.get_string("API_SEARCH_SUCCESS", len(data), query))
            return data

        except requests.exceptions.HTTPError as e:
            logging.error(t.get_string("API_HTTP_ERROR", search_url, e.response.status_code))
        except requests.exceptions.RequestException as e:
            logging.error(t.get_string("API_REQUEST_ERROR", search_url, e))
        except Exception as e:
            logging.error(t.get_string("API_UNEXPECTED_ERROR", "search_rom", e))
        
        return None


    def get_rom_details(self, rom_id):
        """
        Obtém os detalhes completos de uma ROM usando seu ID.

        Args:
            rom_id (str): O ID da ROM.

        Returns:
            dict: Um dicionário com todos os detalhes da ROM, ou None em caso de erro.
                  Formato esperado: {"slug":"","rom_id":"", ... ,"links":[{"name":"","url":"",...}]}
        """
        details_url = f"{self.base_url}/rom/{rom_id}"
        logging.info(t.get_string("API_DETAILS_ATTEMPT", rom_id, details_url))

        try:
            response = requests.get(details_url, timeout=15)
            response.raise_for_status()

            data = response.json()
            logging.info(t.get_string("API_DETAILS_SUCCESS", data.get('title', rom_id)))
            return data

        except requests.exceptions.HTTPError as e:
            logging.error(t.get_string("API_HTTP_ERROR", details_url, e.response.status_code))
        except requests.exceptions.RequestException as e:
            logging.error(t.get_string("API_REQUEST_ERROR", details_url, e))
        except Exception as e:
            logging.error(t.get_string("API_UNEXPECTED_ERROR", "get_rom_details", e))
            
        return None