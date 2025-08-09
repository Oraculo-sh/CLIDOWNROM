# -*- coding: utf-8 -*-
"""
CLI Download ROM - CrocDB API Client

Cliente para a API CrocDB.
Implementa todas as funcionalidades de busca e obtenção de dados da API.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import time
import requests
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin
from loguru import logger
from dataclasses import dataclass


@dataclass
class ROMEntry:
    """Representa uma entrada de ROM da API."""
    slug: str
    rom_id: Optional[str]
    title: str
    platform: str
    boxart_url: Optional[str]
    regions: List[str]
    links: List[Dict[str, Any]]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ROMEntry':
        """Cria uma instância a partir de dados da API."""
        return cls(
            slug=data.get('slug', ''),
            rom_id=data.get('rom_id'),
            title=data.get('title', ''),
            platform=data.get('platform', ''),
            boxart_url=data.get('boxart_url'),
            regions=data.get('regions', []),
            links=data.get('links', [])
        )
    
    def get_best_download_link(self, preferred_hosts: List[str] = None) -> Optional[Dict[str, Any]]:
        """Retorna o melhor link de download baseado nas preferências.
        
        Args:
            preferred_hosts: Lista de hosts preferidos em ordem de prioridade
            
        Returns:
            Dicionário com informações do link ou None se não encontrado.
        """
        if not self.links:
            return None
        
        # Filtra apenas links de jogos
        game_links = [link for link in self.links if link.get('type') == 'Game']
        
        if not game_links:
            return None
        
        # Se há hosts preferidos, tenta encontrar um deles
        if preferred_hosts:
            for host in preferred_hosts:
                for link in game_links:
                    if link.get('host', '').lower() == host.lower():
                        return link
        
        # Retorna o primeiro link disponível
        return game_links[0]
    
    def get_size_mb(self) -> float:
        """Retorna o tamanho do arquivo em MB."""
        best_link = self.get_best_download_link()
        if best_link and 'size' in best_link:
            return best_link['size'] / (1024 * 1024)
        return 0.0


@dataclass
class SearchResult:
    """Representa o resultado de uma busca."""
    results: List[ROMEntry]
    current_results: int
    total_results: int
    current_page: int
    total_pages: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResult':
        """Cria uma instância a partir de dados da API."""
        results_data = data.get('data', {})
        
        return cls(
            results=[ROMEntry.from_dict(entry) for entry in results_data.get('results', [])],
            current_results=results_data.get('current_results', 0),
            total_results=results_data.get('total_results', 0),
            current_page=results_data.get('current_page', 1),
            total_pages=results_data.get('total_pages', 1)
        )


class CrocDBClient:
    """Cliente para a API CrocDB."""
    
    def __init__(self, 
                 base_url: str = "https://api.crocdb.net",
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_delay: float = 1.0):
        """Inicializa o cliente da API.
        
        Args:
            base_url: URL base da API
            timeout: Timeout para requisições em segundos
            max_retries: Número máximo de tentativas
            retry_delay: Delay entre tentativas em segundos
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Configura sessão HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CLI-Download-ROM/1.0.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        logger.debug(f"Cliente CrocDB inicializado: {self.base_url}")
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     data: Dict[str, Any] = None,
                     params: Dict[str, Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """Faz uma requisição à API com retry automático.
        
        Args:
            method: Método HTTP (GET, POST)
            endpoint: Endpoint da API
            data: Dados para enviar no corpo da requisição
            params: Parâmetros de query string
            
        Returns:
            Tupla (sucesso, dados_resposta)
        """
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                logger.debug(f"Requisição {method} para {url} (tentativa {attempt + 1})")
                
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, params=params, timeout=self.timeout)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")
                
                response_time = time.time() - start_time
                logger.debug(f"Resposta recebida: {response.status_code} em {response_time:.3f}s")
                
                # Verifica se a resposta foi bem-sucedida
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        return True, json_data
                    except ValueError as e:
                        logger.error(f"Erro ao decodificar JSON: {e}")
                        return False, {'error': 'Resposta inválida da API'}
                
                elif response.status_code == 404:
                    logger.warning(f"Recurso não encontrado: {url}")
                    return False, {'error': 'Recurso não encontrado'}
                
                elif response.status_code >= 500:
                    logger.warning(f"Erro do servidor: {response.status_code}")
                    if attempt < self.max_retries:
                        logger.info(f"Tentando novamente em {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                
                else:
                    logger.error(f"Erro HTTP: {response.status_code}")
                    return False, {'error': f'Erro HTTP {response.status_code}'}
            
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout na requisição (tentativa {attempt + 1})")
                if attempt < self.max_retries:
                    logger.info(f"Tentando novamente em {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
            
            except requests.exceptions.ConnectionError:
                logger.warning(f"Erro de conexão (tentativa {attempt + 1})")
                if attempt < self.max_retries:
                    logger.info(f"Tentando novamente em {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
            
            except Exception as e:
                logger.error(f"Erro inesperado na requisição: {e}")
                return False, {'error': str(e)}
        
        return False, {'error': 'Máximo de tentativas excedido'}
    
    def search_entries(self, 
                      search_key: str,
                      platforms: List[str] = None,
                      regions: List[str] = None,
                      max_results: int = 50,
                      page: int = 1) -> Optional[SearchResult]:
        """Busca entradas de ROM na API.
        
        Args:
            search_key: Termo de busca
            platforms: Lista de plataformas para filtrar
            regions: Lista de regiões para filtrar
            max_results: Número máximo de resultados
            page: Página dos resultados
            
        Returns:
            Objeto SearchResult ou None em caso de erro.
        """
        data = {
            'search_key': search_key,
            'max_results': max_results,
            'page': page
        }
        
        if platforms:
            data['platforms'] = platforms
        
        if regions:
            data['regions'] = regions
        
        logger.info(f"Buscando ROMs: '{search_key}'")
        logger.debug(f"Parâmetros de busca: {data}")
        
        success, response_data = self._make_request('POST', '/search', data=data)
        
        if success:
            try:
                result = SearchResult.from_dict(response_data)
                logger.info(f"Busca concluída: {result.current_results} de {result.total_results} resultados")
                return result
            except Exception as e:
                logger.error(f"Erro ao processar resultados da busca: {e}")
                return None
        else:
            logger.error(f"Erro na busca: {response_data.get('error', 'Erro desconhecido')}")
            return None
    
    def get_entry(self, slug: str) -> Optional[ROMEntry]:
        """Obtém uma entrada específica pelo slug.
        
        Args:
            slug: Identificador único da entrada
            
        Returns:
            Objeto ROMEntry ou None em caso de erro.
        """
        data = {'slug': slug}
        
        logger.debug(f"Obtendo entrada: {slug}")
        
        success, response_data = self._make_request('POST', '/entry', data=data)
        
        if success:
            try:
                entry_data = response_data.get('data', {}).get('entry', {})
                if entry_data:
                    entry = ROMEntry.from_dict(entry_data)
                    logger.debug(f"Entrada obtida: {entry.title}")
                    return entry
                else:
                    logger.warning(f"Entrada não encontrada: {slug}")
                    return None
            except Exception as e:
                logger.error(f"Erro ao processar entrada: {e}")
                return None
        else:
            logger.error(f"Erro ao obter entrada: {response_data.get('error', 'Erro desconhecido')}")
            return None
    
    def get_random_entry(self) -> Optional[ROMEntry]:
        """Obtém uma entrada aleatória.
        
        Returns:
            Objeto ROMEntry ou None em caso de erro.
        """
        logger.debug("Obtendo entrada aleatória")
        
        success, response_data = self._make_request('GET', '/entry/random')
        
        if success:
            try:
                entry_data = response_data.get('data', {}).get('entry', {})
                if entry_data:
                    entry = ROMEntry.from_dict(entry_data)
                    logger.info(f"Entrada aleatória obtida: {entry.title} ({entry.platform})")
                    return entry
                else:
                    logger.warning("Nenhuma entrada aleatória retornada")
                    return None
            except Exception as e:
                logger.error(f"Erro ao processar entrada aleatória: {e}")
                return None
        else:
            logger.error(f"Erro ao obter entrada aleatória: {response_data.get('error', 'Erro desconhecido')}")
            return None
    
    def get_platforms(self) -> Optional[Dict[str, Dict[str, str]]]:
        """Obtém lista de plataformas disponíveis.
        
        Returns:
            Dicionário com plataformas ou None em caso de erro.
        """
        logger.debug("Obtendo lista de plataformas")
        
        success, response_data = self._make_request('GET', '/platforms')
        
        if success:
            try:
                platforms = response_data.get('data', {}).get('platforms', {})
                logger.info(f"Obtidas {len(platforms)} plataformas")
                return platforms
            except Exception as e:
                logger.error(f"Erro ao processar plataformas: {e}")
                return None
        else:
            logger.error(f"Erro ao obter plataformas: {response_data.get('error', 'Erro desconhecido')}")
            return None
    
    def get_regions(self) -> Optional[Dict[str, str]]:
        """Obtém lista de regiões disponíveis.
        
        Returns:
            Dicionário com regiões ou None em caso de erro.
        """
        logger.debug("Obtendo lista de regiões")
        
        success, response_data = self._make_request('GET', '/regions')
        
        if success:
            try:
                regions = response_data.get('data', {}).get('regions', {})
                logger.info(f"Obtidas {len(regions)} regiões")
                return regions
            except Exception as e:
                logger.error(f"Erro ao processar regiões: {e}")
                return None
        else:
            logger.error(f"Erro ao obter regiões: {response_data.get('error', 'Erro desconhecido')}")
            return None
    
    def get_database_info(self) -> Optional[Dict[str, Any]]:
        """Obtém informações gerais da base de dados.
        
        Returns:
            Dicionário com informações ou None em caso de erro.
        """
        logger.debug("Obtendo informações da base de dados")
        
        success, response_data = self._make_request('GET', '/info')
        
        if success:
            try:
                info = response_data.get('data', {})
                logger.info(f"Informações da base de dados obtidas")
                return info
            except Exception as e:
                logger.error(f"Erro ao processar informações da base de dados: {e}")
                return None
        else:
            logger.error(f"Erro ao obter informações: {response_data.get('error', 'Erro desconhecido')}")
            return None
    
    def test_connection(self) -> bool:
        """Testa a conexão com a API.
        
        Returns:
            True se a conexão foi bem-sucedida.
        """
        logger.debug("Testando conexão com a API")
        
        success, response_data = self._make_request('GET', '/info')
        
        if success:
            logger.info("Conexão com a API estabelecida com sucesso")
            return True
        else:
            logger.error(f"Falha na conexão com a API: {response_data.get('error', 'Erro desconhecido')}")
            return False
    
    def close(self):
        """Fecha a sessão HTTP."""
        if self.session:
            self.session.close()
            logger.debug("Sessão HTTP fechada")
    
    def __enter__(self):
        """Suporte para context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Suporte para context manager."""
        self.close()