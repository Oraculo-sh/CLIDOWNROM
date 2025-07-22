import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from utils.localization import _
from utils.logging_config import setup_logging

log = setup_logging()

retry_strategy = Retry(
    total=3,  
    status_forcelist=[429, 500, 502, 503, 504], 
    backoff_factor=1 
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http_session = requests.Session()
http_session.mount("https://", adapter)
http_session.mount("http://", adapter)

def _make_request(method, url, json_data=None, timeout=10):
    """
    Função centralizada para fazer requisições HTTP com tratamento de erros e retentativas.
    """
    try:
        log.info(_("log_making_request").format(method=method.upper(), url=url))
        if json_data:
            log.debug(_("log_request_payload").format(data=json_data))

        response = http_session.request(method, url, json=json_data, timeout=timeout)
        response.raise_for_status() 

        log.info(_("log_request_successful").format(url=url))
        return response.json()

    except requests.exceptions.Timeout:
        log.error(_("log_request_timeout").format(url=url))
        print(f"\n{_('error_request_timeout')}")
        return None
    except requests.exceptions.ConnectionError:
        log.error(_("log_connection_error").format(url=url))
        print(f"\n{_('error_connection_error')}")
        return None
    except requests.exceptions.HTTPError as http_err:
        log.error(_("log_http_error").format(status_code=http_err.response.status_code, url=url))
        print(f"\n{_('error_http_error').format(status_code=http_err.response.status_code)}")
        return None
    except requests.exceptions.RequestException as err:
        log.critical(_("log_unexpected_error").format(error=err, url=url))
        print(f"\n{_('error_unexpected_request_error')}")
        return None

def search_roms(api_url, search_key, platforms=None, regions=None, max_results=100, page=1):
    """
    Busca ROMs na API CrocDB.
    """
    search_payload = {
        "search_key": search_key,
        "platforms": platforms or [],
        "regions": regions or [],
        "max_results": max_results,
        "page": page
    }
    return _make_request("POST", f"{api_url}/search", json_data=search_payload)

def get_platforms(api_url):
    """
    Obtém a lista de plataformas disponíveis.
    """
    return _make_request("GET", f"{api_url}/platforms")

def get_regions(api_url):
    """
    Obtém a lista de regiões disponíveis.
    """
    return _make_request("GET", f"{api_url}/regions")