# -*- coding: utf-8 -*-
"""
CLI Download ROM - Search Engine

Motor de busca com algoritmo de ranking de relevância para ROMs.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from ..api.crocdb_client import CrocDBClient, ROMEntry, SearchResult
from ..utils.helpers import (
    normalize_text,
    calculate_similarity,
    extract_year_from_title,
    extract_region_from_title
)


@dataclass
class SearchFilter:
    """Filtros para busca de ROMs."""
    platforms: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    languages: Optional[List[str]] = None
    exclude_hacks: bool = False
    exclude_homebrew: bool = False
    exclude_prototypes: bool = False


@dataclass
class ROMScore:
    """Pontuação de relevância de uma ROM."""
    rom_entry: ROMEntry
    total_score: float
    title_score: float
    platform_score: float
    region_score: float
    year_score: float
    quality_score: float
    availability_score: float
    
    def __post_init__(self):
        """Calcula pontuação total."""
        self.total_score = (
            self.title_score * 0.4 +
            self.platform_score * 0.15 +
            self.region_score * 0.15 +
            self.year_score * 0.1 +
            self.quality_score * 0.1 +
            self.availability_score * 0.1
        )


class SearchEngine:
    """Motor de busca com ranking de relevância."""
    
    def __init__(self, api_client: CrocDBClient):
        """Inicializa o motor de busca.
        
        Args:
            api_client: Cliente da API CrocDB
        """
        self.api_client = api_client
        self.platforms_cache = None
        self.regions_cache = None
        
        logger.debug("Search Engine inicializado")
    
    async def get_platforms(self) -> List[str]:
        """Obtém lista de plataformas disponíveis.
        
        Returns:
            Lista de plataformas
        """
        if self.platforms_cache is None:
            try:
                # CrocDBClient.get_platforms() é síncrono e retorna um dicionário {code: {name: ...}}
                platforms_dict = self.api_client.get_platforms() or {}
                self.platforms_cache = list(platforms_dict.keys())
                logger.debug(f"Plataformas carregadas: {len(self.platforms_cache)}")
            except Exception as e:
                logger.error(f"Erro ao carregar plataformas: {e}")
                self.platforms_cache = []
        
        return self.platforms_cache
    
    async def get_regions(self) -> List[str]:
        """Obtém lista de regiões disponíveis.
        
        Returns:
            Lista de regiões
        """
        if self.regions_cache is None:
            try:
                # CrocDBClient.get_regions() é síncrono e retorna um dicionário {code: name}
                regions_dict = self.api_client.get_regions() or {}
                self.regions_cache = list(regions_dict.keys())
                logger.debug(f"Regiões carregadas: {len(self.regions_cache)}")
            except Exception as e:
                logger.error(f"Erro ao carregar regiões: {e}")
                self.regions_cache = []
        
        return self.regions_cache
    
    def _calculate_title_score(self, query: str, rom_entry: ROMEntry) -> float:
        """Calcula pontuação baseada na similaridade do título.
        
        Args:
            query: Consulta de busca
            rom_entry: Entrada da ROM
            
        Returns:
            Pontuação do título (0.0 - 1.0)
        """
        if not query or not rom_entry.title:
            return 0.0
        
        # Pontuação base por similaridade
        base_score = calculate_similarity(query, rom_entry.title)
        
        # Bônus para correspondência exata
        if normalize_text(query) == normalize_text(rom_entry.title):
            base_score = 1.0
        
        # Bônus para correspondência de palavras-chave
        query_words = normalize_text(query).split()
        title_words = normalize_text(rom_entry.title).split()
        
        keyword_matches = 0
        for query_word in query_words:
            if len(query_word) > 2:  # Ignora palavras muito curtas
                for title_word in title_words:
                    if query_word in title_word or title_word in query_word:
                        keyword_matches += 1
                        break
        
        if query_words:
            keyword_bonus = (keyword_matches / len(query_words)) * 0.3
            base_score = min(1.0, base_score + keyword_bonus)
        
        # Penalidade para títulos com muitos caracteres especiais (possíveis hacks)
        special_chars = len(re.findall(r'[\[\](){}]', rom_entry.title))
        if special_chars > 3:
            base_score *= 0.8
        
        return base_score
    
    def _calculate_platform_score(self, 
                                 preferred_platforms: Optional[List[str]], 
                                 rom_entry: ROMEntry) -> float:
        """Calcula pontuação baseada na plataforma.
        
        Args:
            preferred_platforms: Plataformas preferidas
            rom_entry: Entrada da ROM
            
        Returns:
            Pontuação da plataforma (0.0 - 1.0)
        """
        if not preferred_platforms:
            return 0.5  # Pontuação neutra
        
        platform_normalized = normalize_text(rom_entry.platform)
        
        for i, preferred in enumerate(preferred_platforms):
            if normalize_text(preferred) == platform_normalized:
                # Primeira plataforma preferida tem pontuação máxima
                return 1.0 - (i * 0.1)
        
        return 0.2  # Pontuação baixa para plataformas não preferidas
    
    def _calculate_region_score(self, 
                               preferred_regions: Optional[List[str]], 
                               rom_entry: ROMEntry) -> float:
        """Calcula pontuação baseada na região.
        
        Args:
            preferred_regions: Regiões preferidas
            rom_entry: Entrada da ROM
            
        Returns:
            Pontuação da região (0.0 - 1.0)
        """
        if not preferred_regions:
            return 0.5  # Pontuação neutra
        
        # Extrai regiões do título
        title_regions = extract_region_from_title(rom_entry.title)
        
        # Verifica região da entrada
        if rom_entry.regions:
            title_regions.extend(rom_entry.regions)
        
        if not title_regions:
            return 0.3  # Pontuação baixa para região desconhecida
        
        best_score = 0.0
        for region in title_regions:
            region_normalized = normalize_text(region)
            
            for i, preferred in enumerate(preferred_regions):
                if normalize_text(preferred) == region_normalized:
                    score = 1.0 - (i * 0.1)
                    best_score = max(best_score, score)
        
        return best_score if best_score > 0 else 0.2
    
    def _calculate_year_score(self, 
                             target_year: Optional[int], 
                             rom_entry: ROMEntry) -> float:
        """Calcula pontuação baseada no ano.
        
        Args:
            target_year: Ano alvo
            rom_entry: Entrada da ROM
            
        Returns:
            Pontuação do ano (0.0 - 1.0)
        """
        if not target_year:
            return 0.5  # Pontuação neutra
        
        # Tenta extrair ano do título
        rom_year = extract_year_from_title(rom_entry.title)
        
        if not rom_year:
            return 0.3  # Pontuação baixa para ano desconhecido
        
        # Calcula diferença de anos
        year_diff = abs(target_year - rom_year)
        
        if year_diff == 0:
            return 1.0
        elif year_diff <= 2:
            return 0.8
        elif year_diff <= 5:
            return 0.6
        elif year_diff <= 10:
            return 0.4
        else:
            return 0.2
    
    def _calculate_quality_score(self, rom_entry: ROMEntry) -> float:
        """Calcula pontuação baseada na qualidade da ROM.
        
        Args:
            rom_entry: Entrada da ROM
            
        Returns:
            Pontuação de qualidade (0.0 - 1.0)
        """
        score = 0.5  # Pontuação base
        title_lower = rom_entry.title.lower()
        
        # Penalidades para indicadores de baixa qualidade
        quality_penalties = {
            'hack': -0.3,
            'homebrew': -0.2,
            'prototype': -0.2,
            'beta': -0.1,
            'demo': -0.1,
            'sample': -0.2,
            'pirate': -0.4,
            'bad': -0.3,
            'corrupt': -0.5
        }
        
        for indicator, penalty in quality_penalties.items():
            if indicator in title_lower:
                score += penalty
        
        # Bônus para indicadores de qualidade
        quality_bonuses = {
            'final': 0.1,
            'complete': 0.1,
            'special edition': 0.1,
            'deluxe': 0.1,
            'goty': 0.1,  # Game of the Year
            'remaster': 0.1
        }
        
        for indicator, bonus in quality_bonuses.items():
            if indicator in title_lower:
                score += bonus
        
        # Penalidade para muitos caracteres especiais
        special_chars = len(re.findall(r'[\[\](){}]', rom_entry.title))
        if special_chars > 5:
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_availability_score(self, rom_entry: ROMEntry) -> float:
        """Calcula pontuação baseada na disponibilidade de downloads.
        
        Args:
            rom_entry: Entrada da ROM
            
        Returns:
            Pontuação de disponibilidade (0.0 - 1.0)
        """
        if not rom_entry.links:
            return 0.0
        
        # Conta links de download válidos
        download_links = [link for link in rom_entry.links 
                         if link.get('type') == 'Game' and link.get('url')]
        
        if not download_links:
            return 0.0
        
        # Pontuação baseada no número de mirrors
        if len(download_links) >= 3:
            return 1.0
        elif len(download_links) == 2:
            return 0.8
        else:
            return 0.6
    
    def _score_rom(self, 
                   query: str, 
                   rom_entry: ROMEntry, 
                   search_filter: SearchFilter) -> ROMScore:
        """Calcula pontuação total de uma ROM.
        
        Args:
            query: Consulta de busca
            rom_entry: Entrada da ROM
            search_filter: Filtros de busca
            
        Returns:
            Pontuação da ROM
        """
        title_score = self._calculate_title_score(query, rom_entry)
        platform_score = self._calculate_platform_score(search_filter.platforms, rom_entry)
        region_score = self._calculate_region_score(search_filter.regions, rom_entry)
        
        # Calcula ano alvo (média se houver range)
        target_year = None
        if search_filter.year_min and search_filter.year_max:
            target_year = (search_filter.year_min + search_filter.year_max) // 2
        elif search_filter.year_min:
            target_year = search_filter.year_min
        elif search_filter.year_max:
            target_year = search_filter.year_max
        
        year_score = self._calculate_year_score(target_year, rom_entry)
        quality_score = self._calculate_quality_score(rom_entry)
        availability_score = self._calculate_availability_score(rom_entry)
        
        return ROMScore(
            rom_entry=rom_entry,
            total_score=0.0,  # Será calculado no __post_init__
            title_score=title_score,
            platform_score=platform_score,
            region_score=region_score,
            year_score=year_score,
            quality_score=quality_score,
            availability_score=availability_score
        )
    
    def _apply_filters(self, rom_entries: List[ROMEntry], search_filter: SearchFilter) -> List[ROMEntry]:
        """Aplica filtros às entradas de ROM.
        
        Args:
            rom_entries: Lista de entradas
            search_filter: Filtros a aplicar
            
        Returns:
            Lista filtrada
        """
        filtered = []
        
        for rom_entry in rom_entries:
            # Filtro de plataforma
            if search_filter.platforms:
                platform_match = False
                for platform in search_filter.platforms:
                    if normalize_text(platform) == normalize_text(rom_entry.platform):
                        platform_match = True
                        break
                if not platform_match:
                    continue
            
            # Filtro de região
            if search_filter.regions:
                title_regions = extract_region_from_title(rom_entry.title)
                if rom_entry.regions:
                    title_regions.extend(rom_entry.regions)
                
                region_match = False
                for region in search_filter.regions:
                    for title_region in title_regions:
                        if normalize_text(region) == normalize_text(title_region):
                            region_match = True
                            break
                    if region_match:
                        break
                
                if not region_match:
                    continue
            
            # Filtro de ano
            if search_filter.year_min or search_filter.year_max:
                rom_year = extract_year_from_title(rom_entry.title)
                if rom_year:
                    if search_filter.year_min and rom_year < search_filter.year_min:
                        continue
                    if search_filter.year_max and rom_year > search_filter.year_max:
                        continue
            
            # Filtros de exclusão
            title_lower = rom_entry.title.lower()
            
            if search_filter.exclude_hacks and 'hack' in title_lower:
                continue
            
            if search_filter.exclude_homebrew and 'homebrew' in title_lower:
                continue
            
            if search_filter.exclude_prototypes and 'prototype' in title_lower:
                continue
            
            filtered.append(rom_entry)
        
        return filtered
    
    async def search(self, 
                    query: str, 
                    search_filter: Optional[SearchFilter] = None,
                    limit: int = 50) -> List[ROMScore]:
        """Busca ROMs com ranking de relevância.
        
        Args:
            query: Consulta de busca
            search_filter: Filtros opcionais
            limit: Número máximo de resultados
            
        Returns:
            Lista de ROMs ordenadas por relevância
        """
        if not query.strip():
            logger.warning("Consulta de busca vazia")
            return []
        
        if search_filter is None:
            search_filter = SearchFilter()
        
        logger.info(f"Buscando: '{query}' com filtros: {search_filter}")
        
        try:
            # Busca na API
            search_result = self.api_client.search_entries(
                search_key=query,
                platforms=search_filter.platforms,
                regions=search_filter.regions,
                max_results=limit * 2  # Busca mais para ter margem após filtros
            )
            
            if not search_result or not search_result.results:
                logger.info("Nenhum resultado encontrado")
                return []
            
            logger.info(f"Encontrados {len(search_result.results)} resultados iniciais")
            
            # Aplica filtros adicionais
            filtered_entries = self._apply_filters(search_result.results, search_filter)
            
            logger.info(f"Após filtros: {len(filtered_entries)} resultados")
            
            # Calcula pontuações
            scored_roms = []
            for rom_entry in filtered_entries:
                score = self._score_rom(query, rom_entry, search_filter)
                scored_roms.append(score)
            
            # Ordena por pontuação (maior primeiro)
            scored_roms.sort(key=lambda x: x.total_score, reverse=True)
            
            # Limita resultados
            final_results = scored_roms[:limit]
            
            logger.info(f"Retornando {len(final_results)} resultados ordenados por relevância")
            
            # Log das melhores pontuações para debug
            for i, scored_rom in enumerate(final_results[:5]):
                logger.debug(f"#{i+1}: {scored_rom.rom_entry.title} - Score: {scored_rom.total_score:.3f}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []
    
    async def search_random(self, 
                           search_filter: Optional[SearchFilter] = None,
                           count: int = 10) -> List[ROMEntry]:
        """Busca ROMs aleatórias.
        
        Args:
            search_filter: Filtros opcionais
            count: Número de ROMs aleatórias
            
        Returns:
            Lista de ROMs aleatórias
        """
        logger.info(f"Buscando {count} ROMs aleatórias")
        
        try:
            random_entries = []
            attempts = 0
            max_attempts = count * 3  # Máximo de tentativas para evitar loop infinito
            
            # Busca ROMs aleatórias uma por vez
            while len(random_entries) < count and attempts < max_attempts:
                attempts += 1
                random_entry = self.api_client.get_random_entry()
                
                if random_entry:
                    # Verifica se já temos esta ROM (evita duplicatas)
                    if not any(entry.slug == random_entry.slug for entry in random_entries):
                        # Aplica filtros se fornecidos
                        if search_filter:
                            filtered = self._apply_filters([random_entry], search_filter)
                            if filtered:
                                random_entries.extend(filtered)
                        else:
                            random_entries.append(random_entry)
            
            if not random_entries:
                logger.info("Nenhuma ROM aleatória encontrada")
                return []
            
            # Limita resultados
            final_results = random_entries[:count]
            
            logger.info(f"Retornando {len(final_results)} ROMs aleatórias")
            return final_results
            
        except Exception as e:
            logger.error(f"Erro na busca aleatória: {e}")
            return []
    
    def search_sync(self, 
                   query: str, 
                   search_filter: Optional[SearchFilter] = None,
                   limit: int = 50) -> List[ROMScore]:
        """Busca ROMs com ranking de relevância (versão síncrona).
        
        Args:
            query: Consulta de busca
            search_filter: Filtros opcionais
            limit: Número máximo de resultados
            
        Returns:
            Lista de ROMs ordenadas por relevância
        """
        import asyncio
        import concurrent.futures
        try:
            # Executa a versão assíncrona de forma síncrona (compatível com Python 3.12)
            asyncio.get_running_loop()
            # Já estamos em um loop: offload para thread separada
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.search(query, search_filter, limit))
                return future.result()
        except RuntimeError:
            # Sem loop em andamento: podemos rodar diretamente
            return asyncio.run(self.search(query, search_filter, limit))
        except Exception as e:
            logger.error(f"Erro na busca síncrona: {e}")
            return []
    
    def get_random_roms_sync(self, count: int = 10, search_filter: Optional[SearchFilter] = None) -> List[ROMEntry]:
        """Busca ROMs aleatórias (versão síncrona).
        
        Args:
            count: Número de ROMs aleatórias
            search_filter: Filtros opcionais
            
        Returns:
            Lista de ROMs aleatórias
        """
        import asyncio
        import concurrent.futures
        try:
            asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.search_random(search_filter, count))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.search_random(search_filter, count))
        except Exception as e:
            logger.error(f"Erro na busca aleatória síncrona: {e}")
            return []
    
    def get_random_roms(self, count: int = 10, search_filter: Optional[SearchFilter] = None) -> List[ROMEntry]:
        """Busca ROMs aleatórias (versão síncrona) - alias para compatibilidade.
        
        Args:
            count: Número de ROMs aleatórias
            search_filter: Filtros opcionais
            
        Returns:
            Lista de ROMs aleatórias
        """
        return self.get_random_roms_sync(count, search_filter)
    
    def get_platforms_sync(self) -> List[str]:
        """Obtém a lista de plataformas (versão síncrona)."""
        # Fast path: return from cache if available
        if self.platforms_cache is not None:
            return self.platforms_cache
        import asyncio
        import concurrent.futures
        try:
            # Python 3.12: get_running_loop() raises if no loop is running
            asyncio.get_running_loop()
            # We are inside a running loop; offload to a separate thread
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.get_platforms())
                return future.result() or []
        except RuntimeError:
            # No running loop; safe to run directly
            return asyncio.run(self.get_platforms()) or []
        except Exception as e:
            logger.error(f"Erro ao obter plataformas (síncrono): {e}")
            return []

    def get_regions_sync(self) -> List[str]:
        """Obtém a lista de regiões (versão síncrona)."""
        # Fast path: return from cache if available
        if self.regions_cache is not None:
            return self.regions_cache
        import asyncio
        import concurrent.futures
        try:
            asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.get_regions())
                return future.result() or []
        except RuntimeError:
            return asyncio.run(self.get_regions()) or []
        except Exception as e:
            logger.error(f"Erro ao obter regiões (síncrono): {e}")
            return []
    
    async def get_rom_info(self, rom_id: str) -> Optional[ROMEntry]:
        """Obtém informações detalhadas de uma ROM.
        
        Args:
            rom_id: ID da ROM
            
        Returns:
            Entrada da ROM ou None
        """
        try:
            # CrocDBClient methods are synchronous; use get_entry(slug) directly.
            return self.api_client.get_entry(rom_id)
        except Exception as e:
            logger.error(f"Erro ao obter informações da ROM {rom_id}: {e}")
            return None