#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Download ROM - CLI Interface

Interface de linha de comando para busca e download de ROMs.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

import argparse
import json
import os
import sys
from typing import List, Optional
from loguru import logger

from ..core.search_engine import SearchEngine, SearchFilter
from ..core.config import ConfigManager
from ..api import CrocDBClient
from ..utils import format_file_size


class CLIInterface:
    """Interface de linha de comando com comandos estruturados."""

    def __init__(self, config_manager: ConfigManager, directory_manager, log_manager):
        self.config_manager = config_manager
        self.dirs = directory_manager
        self.logger = log_manager
        # Inicializa API client conforme configuração
        api_config = self.config_manager.get('api', {}) or {}
        self.api_client = CrocDBClient(
            base_url=api_config.get('base_url'),
            timeout=api_config.get('timeout', 30),
            max_retries=api_config.get('max_retries', 3),
            retry_delay=api_config.get('retry_delay', 1)
        )
        self.search_engine = SearchEngine(self.api_client)
        self.cached_results = []  # Cache de ROMScore para numeração contínua e downloads
        self.cached_query = ""
        self.cached_filter = None
        self.cached_total = 0
        self.parser = self._create_parser()

    def _create_parser(self):
        parser = argparse.ArgumentParser(
            prog="clidownrom",
            description="Busque e baixe ROMs da CrocDB diretamente no terminal.",
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        # search
        search_parser = subparsers.add_parser(
            "search", help="Buscar ROMs por palavras-chave e filtros"
        )
        search_parser.add_argument(
            "query",
            nargs='+',
            help="Palavras-chave da busca (use múltiplas para correspondência AND)"
        )
        search_parser.add_argument(
            "--platform", "-p", nargs="*", help="Filtrar por plataforma(s)"
        )
        search_parser.add_argument(
            "--region", "-r", nargs="*", help="Filtrar por região(ões)"
        )
        search_parser.add_argument(
            "--year", "-y", type=int, help="Ano alvo (aproximação)"
        )
        search_parser.add_argument(
            "--limit", "-l", type=int, default=None, help="Limite total de resultados (sobrepõe config)"
        )
        search_parser.add_argument(
            "--per-page", "-pp", type=int, default=None, help="Resultados por página (sobrepõe config)"
        )
        search_parser.add_argument(
            "--format", "-f", choices=["table", "json", "csv"], default="table",
            help="Formato de saída"
        )

        # info
        info_parser = subparsers.add_parser("info", help="Mostrar informações detalhadas de uma ROM")
        info_parser.add_argument("rom_id", help="Slug/ID da ROM")
        info_parser.add_argument(
            "--format", "-f", choices=["table", "json"], default="table", help="Formato de saída"
        )

        # download
        dl_parser = subparsers.add_parser("download", help="Baixar ROM por ID ou por posição nos resultados")
        dl_parser.add_argument("target", help="Slug/ID ou índice do resultado (ex.: 1, 15)")
        dl_parser.add_argument("--output", "-o", default=".", help="Diretório de saída")

        return parser

    def run(self, args: Optional[List[str]] = None):
        parsed_args = self.parser.parse_args(args)
        return self._execute_command(parsed_args)

    def _execute_command(self, args):
        command = args.command
        if command == "search":
            return self._cmd_search(args)
        elif command == "info":
            return self._cmd_info(args)
        elif command == "download":
            return self._cmd_download(args)
        else:
            self.parser.print_help()
            return 1

    # --- Commands ---
    def _cmd_search(self, args):
        # Monta query como string única a partir de múltiplas keywords
        query = " ".join(args.query).strip()

        # Lê config para paginação
        search_conf = self.config_manager.get("search", {})
        max_results = args.limit if args.limit is not None else search_conf.get("max_results", 100)
        per_page = args.per_page if args.per_page is not None else search_conf.get("results_per_page", 10)

        # Filtros
        search_filter = SearchFilter(
            platforms=args.platform if getattr(args, 'platform', None) else None,
            regions=args.region if getattr(args, 'region', None) else None,
            year_min=args.year if getattr(args, 'year', None) else None,
            year_max=args.year if getattr(args, 'year', None) else None,
        )

        # Reseta cache para nova busca
        self.cached_results = []
        self.cached_query = query
        self.cached_filter = search_filter
        self.cached_total = 0

        page = 1
        while True:
            paged = self.search_engine.search_paged_sync(
                query=query,
                search_filter=search_filter,
                page=page,
                per_page=per_page,
                max_results=max_results,
            )

            # Atualiza cache agregando itens para numeração contínua
            # Garante que cached_results tenha espaço até o índice exibido
            start_idx = (page - 1) * per_page
            # Insere/atualiza posições com itens da página
            for i, item in enumerate(paged.items, start=start_idx):
                if i < len(self.cached_results):
                    self.cached_results[i] = item
                else:
                    self.cached_results.append(item)
            self.cached_total = paged.total

            # Exibição
            self._display_search_results(
                items=paged.items,
                total=paged.total,
                page=page,
                per_page=per_page,
                format_type=args.format,
            )

            # Se não for tabela, não faz navegação nem seleção
            if args.format != "table":
                break

            # Prompt de ação combinado: seleção por índices ou navegação
            start_num = (page - 1) * per_page + 1
            end_num = min(paged.total, page * per_page)
            action_prompt = "> Digite o(s) número(s) referentes as roms para baixar (separados por vírgula), ou [n] próxima pág, [p] pág anterior, [0] cancelar, [q] sair: "
            sys.stdout.write(action_prompt)
            sys.stdout.flush()
            choice = sys.stdin.readline()
            if not choice:
                break
            choice = choice.strip().lower()

            # Navegação
            if choice in ('n', 'p', 'q', '0'):
                if choice == 'n' and paged.has_next:
                    page += 1
                    continue
                elif choice == 'p' and paged.has_prev:
                    page = max(1, page - 1)
                    continue
                elif choice in ('q', '0'):
                    break
                else:
                    # opção inválida para o estado atual
                    print("Opção inválida nesta página.")
                    continue

            # Tentativa de seleção por índices (números separados por vírgula)
            tokens = [tok.strip() for tok in choice.replace(' ', '').split(',') if tok.strip()]
            if not tokens or any(not tok.isdigit() for tok in tokens):
                print("Entrada inválida. Use números separados por vírgula (ex.: 1,3,5) ou comandos [n],[p],[0],[q].")
                continue

            indices = [int(tok) for tok in tokens]
            # Validar se índices pertencem à página atual
            invalid = [idx for idx in indices if idx < start_num or idx > end_num]
            if invalid:
                print(f"Índices fora do intervalo da página atual: {invalid}. Intervalo: {start_num}-{end_num}.")
                continue

            # Remover duplicados preservando ordem
            seen = set()
            unique_indices = []
            for idx in indices:
                if idx not in seen:
                    seen.add(idx)
                    unique_indices.append(idx)

            # Efetuar downloads sequenciais usando o comando 'download'
            import argparse as _argparse
            for idx in unique_indices:
                dl_args = _argparse.Namespace(target=str(idx), output='.')
                self._cmd_download(dl_args)
            break

        return 0

    def _cmd_info(self, args):
        rom_id = args.rom_id
        info = self.search_engine.get_rom_info_sync(rom_id) if hasattr(self.search_engine, 'get_rom_info_sync') else None
        # Fallback assíncrono caso não exista método sync específico
        if info is None:
            import asyncio
            info = asyncio.run(self.search_engine.get_rom_info(rom_id))
        if not info:
            print("ROM não encontrada.")
            return 1
        self._display_rom_info(info, format_type=args.format)
        return 0

    def _cmd_download(self, args):
        target = args.target
        output_dir = args.output

        # Se for índice numérico, busca no cache
        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(self.cached_results):
                rom = self.cached_results[idx].rom_entry
            else:
                print("Índice fora do intervalo. Execute uma busca primeiro e escolha um índice válido.")
                return 1
        else:
            # Trata como slug/ID direto
            rom = None
            import asyncio
            rom = asyncio.run(self.search_engine.get_rom_info(target))
            if not rom:
                print("ROM não encontrada pelo ID informado.")
                return 1

        # Realiza download via api_client
        try:
            os.makedirs(output_dir, exist_ok=True)
            download_url = None
            for link in (rom.links or []):
                if link.get('type') == 'Game' and link.get('url'):
                    download_url = link['url']
                    break
            if not download_url:
                print("Nenhum link de download disponível para esta ROM.")
                return 1
            filename = f"{rom.slug}.zip"
            dest_path = os.path.join(output_dir, filename)
            from ..utils.downloader import download_file
            download_file(download_url, dest_path, progress_callback=self._download_progress_callback)
            print(f"Baixado: {dest_path}")
            return 0
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return 1

    # --- Display helpers ---
    def _display_search_results(self, items, total: int, page: int, per_page: int, format_type: str = "table"):
        if format_type == "json":
            out = [
                {
                    "index": (page - 1) * per_page + i + 1,
                    "slug": s.rom_entry.slug,
                    "title": s.rom_entry.title,
                    "platform": s.rom_entry.platform,
                    "regions": s.rom_entry.regions,
                    "year": s.rom_entry.year if hasattr(s.rom_entry, 'year') else None,
                    "hosts": getattr(s.rom_entry, 'hosts', None),
                    "format": getattr(s.rom_entry, 'file_format', None),
                    "size": getattr(s.rom_entry, 'size', None),
                    "score": round(s.total_score, 3),
                }
                for i, s in enumerate(items)
            ]
            print(json.dumps({"total": total, "page": page, "per_page": per_page, "items": out}, ensure_ascii=False, indent=2))
            return
        elif format_type == "csv":
            import csv
            import io
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(["index", "slug", "title", "platform", "regions", "hosts", "format", "size_bytes", "score"])
            for i, s in enumerate(items):
                idx = (page - 1) * per_page + i + 1
                regions_str = ",".join(s.rom_entry.regions or [])
                hosts_val = getattr(s.rom_entry, 'hosts', None) or ""
                fmt_val = getattr(s.rom_entry, 'file_format', None) or ""
                size_val = getattr(s.rom_entry, 'size', None)
                writer.writerow([idx, s.rom_entry.slug, s.rom_entry.title, s.rom_entry.platform, regions_str, hosts_val, fmt_val, size_val if size_val is not None else "", f"{s.total_score:.3f}"])
            print(buffer.getvalue().rstrip("\n"))
            return

        # Tabela: cabeçalho de paginação
        start_num = (page - 1) * per_page + 1
        end_num = min(total, page * per_page)
        total_pages = max(1, (total + per_page - 1) // per_page)
        print(f"Resultados {start_num}-{end_num} de {total} (Página {page} de {total_pages})")

        # Larguras das colunas
        w_idx = 2
        w_title = 38
        w_id = 14
        w_platform = 12
        w_regions = 15
        w_hosts = 12
        w_format = 8
        w_size = 10
        w_score = 6

        header = (
            f"#".rjust(w_idx) + " "
            f"Título".ljust(w_title) + " "
            f"ID".ljust(w_id) + " "
            f"Plataforma".ljust(w_platform) + " "
            f"Regiões".ljust(w_regions) + " "
            f"Hosts".ljust(w_hosts) + " "
            f"Formato".ljust(w_format) + " "
            f"Tamanho".ljust(w_size) + " "
            f"Score".rjust(w_score)
        )
        sep = (
            "-" * w_idx + " "
            + "-" * w_title + " "
            + "-" * w_id + " "
            + "-" * w_platform + " "
            + "-" * w_regions + " "
            + "-" * w_hosts + " "
            + "-" * w_format + " "
            + "-" * w_size + " "
            + "-" * w_score
        )
        print(header)
        print(sep)

        for i, s in enumerate(items):
            idx = start_num + i
            rom = s.rom_entry
            title = (rom.title or "")[:w_title].ljust(w_title)
            slug = (rom.slug or "")[:w_id].ljust(w_id)
            platform = (rom.platform or "")[:w_platform].ljust(w_platform)
            regions = ",".join(rom.regions or [])
            regions = regions[:w_regions].ljust(w_regions)
            hosts_val = getattr(rom, 'hosts', None) or ""
            hosts_val = str(hosts_val)[:w_hosts].ljust(w_hosts)
            fmt_val = getattr(rom, 'file_format', None) or ""
            fmt_val = str(fmt_val)[:w_format].ljust(w_format)
            size_val = getattr(rom, 'size', None)
            size_str = format_file_size(size_val) if isinstance(size_val, int) and size_val >= 0 else ""
            size_str = size_str[:w_size].ljust(w_size)
            score_str = f"{s.total_score:>{w_score}.3f}"
            print(f"{str(idx).rjust(w_idx)} {title} {slug} {platform} {regions} {hosts_val} {fmt_val} {size_str} {score_str}")
        if end_num >= total:
            print("-- Fim dos resultados --")

    def _display_rom_info(self, rom, format_type: str = "table"):
        if format_type == "json":
            print(json.dumps(rom.__dict__, ensure_ascii=False, indent=2))
            return
        # tabela
        print(f"Slug: {rom.slug}")
        print(f"Título: {rom.title}")
        print(f"Plataforma: {rom.platform}")
        print(f"Regiões: {', '.join(rom.regions or [])}")
        size = getattr(rom, 'size', None)
        if size is not None:
            print(f"Tamanho: {format_file_size(size)}")
        print("Links:")
        for link in (rom.links or []):
            print(f"- {link.get('type')}: {link.get('url')}")

    def _download_progress_callback(self, downloaded, total_size):
        if total_size > 0:
            percent = downloaded / total_size * 100
            sys.stdout.write(f"\rBaixando: {percent:.1f}%")
            sys.stdout.flush()
        else:
            sys.stdout.write("\rBaixando...")
            sys.stdout.flush()