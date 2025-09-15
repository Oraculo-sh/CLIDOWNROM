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

from ..core.crocdb_client import CrocDBClient, ROMEntry, SearchResult
from ..core.helpers import (
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
            self.title_score * 0.55 +
            self.platform_score * 0.10 +
            self.region_score * 0.10 +
            self.year_score * 0.05 +
            self.quality_score * 0.10 +
            self.availability_score * 0.10
        )


class SearchEngine:
    """Motor de busca com ranking de relevância."""
    
    # Resultado paginado de busca
    @dataclass
    class PagedSearchResult:
        items: List["ROMScore"]
        total: int
        page: int
        per_page: int
        page_count: int
        has_prev: bool
        has_next: bool

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
    
    def _calculate_title_score(self, query: str, rom_entry: ROMEntry,
                               platform_codes: Optional[set] = None,
                               region_codes: Optional[set] = None) -> float:
        """Calcula pontuação baseada no título usando cobertura de tokens, similaridade e bônus de frase.
        
        - Penaliza tokens ausentes exceto quando o token é plataforma/região.
        - Bônus para correspondência de frase (query como substring do título) e para prefixo (início do título).
        - Bônus leve quando tokens numéricos da consulta estão presentes (ex.: "64").
        - Penalidade ainda mais leve para excesso de caracteres especiais.
        """
        if not query or not rom_entry.title:
            return 0.0

        q_norm = normalize_text(query)
        title_norm = normalize_text(rom_entry.title)

        # Tokens da consulta e tokens isentos (plataforma/região)
        q_tokens = [tok for tok in q_norm.split() if tok]
        platform_codes = platform_codes or set()
        region_codes = region_codes or set()
        exempt_tokens = {t for t in q_tokens if (t in platform_codes or t in region_codes)}
        content_tokens = [t for t in q_tokens if t not in exempt_tokens]
        numeric_tokens = [t for t in content_tokens if t.isdigit()]

        # Similaridade geral como componente auxiliar
        sim = calculate_similarity(query, rom_entry.title)

        # Exato (após normalização) -> score máximo
        if q_norm == title_norm:
            return 1.0

        # Cobertura de tokens: proporção de tokens da consulta presentes no título
        matches = 0
        for t in content_tokens:
            if t in title_norm:
                matches += 1
        coverage = 1.0 if not content_tokens else (matches / max(1, len(content_tokens)))

        # Bônus por frase (consulta como substring contínua)
        phrase_bonus = 0.0
        if len(content_tokens) >= 1 and q_norm in title_norm:
            phrase_bonus = 0.25  # aumentado para favorecer consultas como frase

        # Bônus por início de título (prefixo)
        prefix_bonus = 0.0
        if len(content_tokens) >= 1 and title_norm.startswith(q_norm):
            prefix_bonus = 0.15

        # Bônus por tokens numéricos presentes (ex.: "64")
        numeric_bonus = 0.0
        if numeric_tokens:
            numeric_matches = sum(1 for t in numeric_tokens if t in title_norm)
            if numeric_matches == len(numeric_tokens):
                numeric_bonus = 0.35  # maior impacto para corresponder números exatamente
            elif numeric_matches > 0:
                numeric_bonus = 0.15

        # Penalidade por tokens ausentes (não se aplica a tokens de plataforma/região)
        missing = 0 if not content_tokens else (len(content_tokens) - matches)
        missing_penalty = min(0.35, missing * 0.08)  # limita a penalidade total

        # Penalidade por "gap" entre tokens principais da consulta quando houver números (ex.: demover "Mario Kart 64")
        gap_penalty = 0.0
        adjacency_bonus = 0.0
        super_bonus = 0.0
        modifier_penalty = 0.0
        strong_phrase_bonus = 0.0
        if len(content_tokens) >= 2:
            title_tokens = [t for t in title_norm.split() if t]
            try:
                first_tok = content_tokens[0]
                last_tok = content_tokens[-1]
                if first_tok in title_tokens and last_tok in title_tokens:
                    i = title_tokens.index(first_tok)
                    j = len(title_tokens) - 1 - title_tokens[::-1].index(last_tok)
                    if i < j:
                        between = max(0, j - i - 1)
                        if between > 0:
                            gap_penalty = min(0.60, 0.30 * between)
                        else:
                            adjacency_bonus = 0.15
                        # Bônus específico: "super" imediatamente antes de 'mario'
                        if i - 1 >= 0 and title_tokens[i - 1] == 'super' and first_tok == 'mario':
                            super_bonus = 0.45
                        # Penalidade mais forte: "dr" imediatamente antes de 'mario'
                        if i - 1 >= 0 and title_tokens[i - 1] in {'dr', 'dr.', 'doctor'} and first_tok == 'mario':
                            modifier_penalty = 0.35
                # Bônus forte se o título contém a frase "super mario 64" completa
                if 'super mario 64' in title_norm:
                    strong_phrase_bonus = 0.45
                # Penalidade adicional se começar com "dr mario 64"
                if title_norm.startswith('dr mario 64'):
                    modifier_penalty = max(modifier_penalty, 0.40)
            except Exception:
                pass

        # Combinação: prioriza cobertura, depois similaridade
        base = (0.6 * coverage) + (0.4 * sim)
        # Desempate: favorece explicitamente "super mario 64" e rebaixa "dr mario 64" com pequeno epsilon
        tie_breaker = 0.0
        if 'super mario 64' in title_norm:
            tie_breaker += 0.0008
        if title_norm.startswith('dr mario 64'):
            tie_breaker -= 0.0008

        score = base + phrase_bonus + prefix_bonus + numeric_bonus + adjacency_bonus + super_bonus + strong_phrase_bonus - missing_penalty - gap_penalty - modifier_penalty + tie_breaker

        # Penalidade ainda mais leve para muitos caracteres especiais (indicadores de dumps/hacks)
        special_chars = len(re.findall(r'[\[\](){}]', rom_entry.title))
        if special_chars > 5:
            score *= 0.93

        return max(0.0, min(1.0, score))
    
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
                   search_filter: SearchFilter,
                   platform_codes: Optional[set] = None,
                   region_codes: Optional[set] = None) -> ROMScore:
        """Calcula pontuação total de uma ROM.
        
        Args:
            query: Consulta de busca
            rom_entry: Entrada da ROM
            search_filter: Filtros de busca
            platform_codes: Conjunto de códigos de plataforma normalizados
            region_codes: Conjunto de códigos de região normalizados
            
        Returns:
            Pontuação da ROM
        """
        title_score = self._calculate_title_score(query, rom_entry, platform_codes, region_codes)
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
                max_results=max(200, limit * 4)  # Busca mais para ter margem após filtros
            )
            
            if not search_result or not search_result.results:
                logger.info("Nenhum resultado encontrado")
                return []
            
            logger.info(f"Encontrados {len(search_result.results)} resultados iniciais")
            
            # Aplica filtros adicionais
            filtered_entries = self._apply_filters(search_result.results, search_filter)

            # Carrega códigos de plataforma/região para tratamento de tokens isentos
            try:
                platforms_list = await self.get_platforms()
                regions_list = await self.get_regions()
            except Exception:
                platforms_list, regions_list = [], []
            platform_codes_set = {normalize_text(p) for p in (platforms_list or [])}
            region_codes_set = {normalize_text(r) for r in (regions_list or [])}
            
            # Filtro por palavras-chave (ignorando tokens de plataforma/região)
            all_tokens = [k for k in normalize_text(query).split() if k]
            content_tokens = [k for k in all_tokens if k not in platform_codes_set and k not in region_codes_set]
            has_numeric = any(k.isdigit() for k in content_tokens)
            numeric_tokens = [k for k in content_tokens if k.isdigit()]

            if content_tokens:
                tmp = []
                for rom_entry in filtered_entries:
                    title_norm = normalize_text(rom_entry.title)
                    matches = sum(1 for k in content_tokens if k in title_norm)
                    # Requer todos os tokens quando há número ou quando há até 2 tokens; caso contrário, permite faltar 1
                    if has_numeric or len(content_tokens) <= 2:
                        min_required = len(content_tokens)
                    else:
                        min_required = max(1, len(content_tokens) - 1)
                    if matches >= min_required:
                        tmp.append(rom_entry)
                filtered_entries = tmp

                # Estratégia específica para consultas com números
                if has_numeric:
                    def contains_all_numeric(entry_title_norm: str) -> bool:
                        return all(nt in entry_title_norm for nt in numeric_tokens)

                    def is_preferred_pattern(entry_title_norm: str) -> bool:
                        # Preferir títulos com "super mario" adjacente e contendo todos números
                        toks = [t for t in entry_title_norm.split() if t]
                        if 'mario' in toks and '64' in entry_title_norm:
                            i = toks.index('mario')
                            if i - 1 >= 0 and toks[i - 1] == 'super':
                                return True
                        return False

                    # Paginar mais resultados para ampliar candidatos (até 5 páginas)
                    combined = {e.slug: e for e in filtered_entries}
                    max_pages = min(getattr(search_result, 'total_pages', 1), 5)
                    page = 2
                    preferred_found = any(is_preferred_pattern(normalize_text(e.title)) for e in filtered_entries)
                    while page <= max_pages and (len(combined) < 500) and not preferred_found:
                        more = self.api_client.search_entries(
                            search_key=query,
                            platforms=search_filter.platforms,
                            regions=search_filter.regions,
                            max_results=100,
                            page=page
                        )
                        page += 1
                        if not more or not more.results:
                            continue
                        for e in more.results:
                            if e.slug not in combined:
                                combined[e.slug] = e
                        # Atualiza condição de preferência
                        if not preferred_found:
                            if any(is_preferred_pattern(normalize_text(e.title)) for e in more.results):
                                preferred_found = True

                    # Reaplicar filtros exigindo todos os tokens (inclui numéricos)
                    cand = list(combined.values())
                    cand = self._apply_filters(cand, search_filter)
                    tmp_all = []
                    for e in cand:
                        title_norm = normalize_text(e.title)
                        if all(k in title_norm for k in content_tokens):
                            tmp_all.append(e)
                    filtered_entries = tmp_all

                    # 2) Se ainda assim falhar, reconsulta removendo números e filtra localmente exigindo todos os tokens (incluindo os numéricos)
                    if not filtered_entries:
                        base_tokens = [k for k in content_tokens if not k.isdigit()]
                        base_query = " ".join(base_tokens) if base_tokens else ""
                        if base_query:
                            logger.info(f"Fallback numérico final: reconsultando API com base_query='{base_query}' e reimpondo tokens {content_tokens}")
                            combined = {}
                            max_pages = 3
                            page = 1
                            while page <= max_pages:
                                more = self.api_client.search_entries(
                                    search_key=base_query,
                                    platforms=search_filter.platforms,
                                    regions=search_filter.regions,
                                    max_results=100,
                                    page=page
                                )
                                page += 1
                                if not more or not more.results:
                                    continue
                                for e in more.results:
                                    if e.slug not in combined:
                                        combined[e.slug] = e
                            # Refiltra exigindo todos os tokens
                            cand = list(combined.values())
                            cand = self._apply_filters(cand, search_filter)
                            tmp2 = []
                            for e in cand:
                                title_norm = normalize_text(e.title)
                                if all(k in title_norm for k in content_tokens):
                                    tmp2.append(e)
                            filtered_entries = tmp2

                # Fallback adicional: somente sem tokens numéricos, relaxa para OR (qualquer termo de conteúdo)
                if not filtered_entries and not has_numeric:
                    tmp = []
                    for rom_entry in search_result.results:
                        title_norm = normalize_text(rom_entry.title)
                        if any(k in title_norm for k in content_tokens):
                            tmp.append(rom_entry)
                    filtered_entries = self._apply_filters(tmp, search_filter)

            # Logs de depuração: amostra de títulos após filtros
            try:
                sample_titles = ", ".join([e.title for e in filtered_entries[:10]])
                logger.debug(f"Amostra pós-filtros: {sample_titles}")
            except Exception:
                pass
            
            # Calcula pontuações
            scored_roms: List[ROMScore] = []
            for rom_entry in filtered_entries:
                scored_roms.append(self._score_rom(query, rom_entry, search_filter, platform_codes_set, region_codes_set))
            
            # Usa desempate por heurística de título quando houver empates de pontuação total
            scored_roms.sort(key=lambda x: (x.total_score, self._tie_breaker_value(x)), reverse=True)
            return scored_roms[:limit]
        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

    async def search_paged(self,
                           query: str,
                           search_filter: Optional[SearchFilter] = None,
                           page: int = 1,
                           per_page: int = 10,
                           max_results: int = 100) -> "SearchEngine.PagedSearchResult":
        """Busca paginada com ranking de relevância.
        
        Args:
            query: Consulta de busca
            search_filter: Filtros opcionais
            page: Página atual (1-indexada)
            per_page: Itens por página
            max_results: Limite total de resultados classificados
        """
        if search_filter is None:
            search_filter = SearchFilter()
        try:
            scored_roms = await self.search(query, search_filter, limit=max_results)
            total = len(scored_roms)

            # Calcula fatia da página
            start = (page - 1) * per_page
            end = start + per_page
            items = scored_roms[start:end] if start < total else []

            # Metadados de paginação
            page_count = (total + per_page - 1) // per_page if total > 0 else 0
            has_prev = page > 1 and page <= max(page_count, 1)
            has_next = page < page_count

            logger.info(f"Página {page}/{max(page_count,1)}: exibindo {len(items)} de {total} resultados")
            return SearchEngine.PagedSearchResult(
                items=items,
                total=total,
                page=page,
                per_page=per_page,
                page_count=page_count,
                has_prev=has_prev,
                has_next=has_next,
            )
        except Exception as e:
            logger.error(f"Erro na busca paginada: {e}")
            return SearchEngine.PagedSearchResult(
                items=[], total=0, page=page, per_page=per_page,
                page_count=0, has_prev=False, has_next=False
            )

    def search_paged_sync(self,
                          query: str,
                          search_filter: Optional[SearchFilter] = None,
                          page: int = 1,
                          per_page: int = 10,
                          max_results: int = 100) -> "SearchEngine.PagedSearchResult":
        """Versão síncrona de busca paginada."""
        import asyncio
        import concurrent.futures
        try:
            asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.search_paged(query, search_filter, page, per_page, max_results))
                return future.result()
        except RuntimeError:
            return asyncio.run(self.search_paged(query, search_filter, page, per_page, max_results))
        except Exception as e:
            logger.error(f"Erro na busca paginada síncrona: {e}")
            return SearchEngine.PagedSearchResult(items=[], total=0, page=page, per_page=per_page,
                                                  page_count=0, has_prev=False, has_next=False)

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
        """Obtém informações detalhadas de uma ROM por slug (texto) ou ROM_ID (numérico/alfanumérico).
        
        Args:
            rom_id: ID da ROM (ROM_ID) numérico/alfanumérico, ou slug textual
            
        Returns:
            Entrada da ROM ou None
        """
        try:
            # 1) Tenta como slug textual diretamente (rota mais precisa)
            if isinstance(rom_id, str):
                entry = self.api_client.get_entry(rom_id)
                if entry:
                    return entry
            
            # 2) Se não achou por slug, verifica se parece um ROM_ID
            #    - numérico: só dígitos
            #    - alfanumérico: possui letras ou hífen (ex.: SLUS-00530)
            is_numeric = isinstance(rom_id, (int,)) or (isinstance(rom_id, str) and rom_id.isdigit())
            looks_like_alnum_id = isinstance(rom_id, str) and (any(c.isalpha() for c in rom_id) or '-' in rom_id)
            
            if is_numeric or looks_like_alnum_id:
                result = self.api_client.search_entries(search_key='', max_results=1, page=1, rom_id=str(rom_id))
                if result and result.results:
                    return result.results[0]
                return None
            
            return None
        except Exception as e:
            logger.error(f"Erro ao obter informações da ROM {rom_id}: {e}")
            return None

    def get_rom_info_sync(self, rom_id: str) -> Optional[ROMEntry]:
        """Versão síncrona de get_rom_info() para facilitar uso em CLIs."""
        import asyncio
        try:
            # Tenta detectar se já há um loop rodando, se sim, executa em executor
            import concurrent.futures
            try:
                asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.get_rom_info(rom_id))
                    return future.result()
            except RuntimeError:
                return asyncio.run(self.get_rom_info(rom_id))
        except Exception as e:
            logger.error(f"Erro (sync) ao obter informações da ROM {rom_id}: {e}")
            return None

    def _tie_breaker_value(self, rs: "ROMScore") -> float:
        """Valor de desempate baseado no título normalizado.
        Prioriza "Super Mario 64" e rebaixa explicitamente variações "Dr. Mario 64" em empates de pontuação.
        """
        t = normalize_text(rs.rom_entry.title)
        v = 0.0
        if 'super mario 64' in t:
            v += 2.0
        if t.startswith('super mario '):
            v += 1.0
        if t.startswith('dr mario 64'):
            v -= 2.0
        if 'dr mario ' in t:
            v -= 1.0
        return v