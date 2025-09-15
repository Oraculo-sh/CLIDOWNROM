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
import yaml
from typing import List, Optional
from loguru import logger

from ..core.search_engine import SearchEngine, SearchFilter
from ..core.config_manager import ConfigManager
from ..core.crocdb_client import CrocDBClient
from ..core.helpers import format_file_size
from ..core import DownloadManager, DownloadProgress


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
        # Inicializa DownloadManager conforme configuração
        dl_conf = self.config_manager.get('download', {}) or {}
        self.download_manager = DownloadManager(
            self.dirs,
            max_concurrent=dl_conf.get('max_concurrent', 4),
            chunk_size=dl_conf.get('chunk_size', 8192),
            timeout=dl_conf.get('timeout', 300),
            max_retries=api_config.get('max_retries', 3),
            verify_downloads=dl_conf.get('verify_downloads', True),
        )
        pref_hosts = dl_conf.get('preferred_hosts', []) or []
        if pref_hosts:
            self.download_manager.set_preferred_hosts(pref_hosts)
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
        # novo: alinhado ao model.md
        search_parser.add_argument(
            "--max-results", "-m", type=int, default=None, help="Máximo de resultados por página (padrão 100, máximo 100)"
        )
        search_parser.add_argument(
            "--page", type=int, default=None, help="Número da página inicial (padrão: 1)"
        )
        # legado: mantido por compatibilidade
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
        dl_parser.add_argument("target", nargs='?', default=None, help="Slug/ID ou índice do resultado (ex.: 1, 15)")
        dl_parser.add_argument("--romid", help="ROM ID específico", default=None)
        dl_parser.add_argument("--slug", help="Slug específico", default=None)
        dl_parser.add_argument("--platform", "-p", nargs="*", help="Filtrar por plataforma(s)", default=None)
        dl_parser.add_argument("--region", "-r", nargs="*", help="Filtrar por região(ões)", default=None)
        dl_parser.add_argument("--no-boxart", action="store_true", help="Baixa sem boxart")
        dl_parser.add_argument("--force", "-f", action="store_true", help="Baixa sem confirmação")
        dl_parser.add_argument("--silence", "-s", action="store_true", help="Baixa silenciosamente")
        dl_parser.add_argument("--output", "-o", default=".", help="Diretório de saída")

        # boxart
        box_parser = subparsers.add_parser("boxart", help="Baixar somente a boxart da ROM")
        box_parser.add_argument("target", nargs='?', default=None, help="Slug/ID ou índice do resultado (ex.: 1, 15)")
        box_parser.add_argument("--romid", help="ROM ID específico", default=None)
        box_parser.add_argument("--slug", help="Slug específico", default=None)
        box_parser.add_argument("--platform", "-p", nargs="*", help="Filtrar por plataforma(s)", default=None)
        box_parser.add_argument("--region", "-r", nargs="*", help="Filtrar por região(ões)", default=None)
        box_parser.add_argument("--force", "-f", action="store_true", help="Baixa sem confirmação")
        box_parser.add_argument("--silence", "-s", action="store_true", help="Baixa silenciosamente")

        # random
        rnd_parser = subparsers.add_parser("random", help="Obter ROM(s) aleatória(s)")
        rnd_parser.add_argument("--count", "-n", type=int, default=1, help="Quantidade de ROMs (padrão: 1)")
        rnd_parser.add_argument("--platform", "-p", nargs="*", help="Filtrar por plataforma(s)", default=None)
        rnd_parser.add_argument("--region", "-r", nargs="*", help="Filtrar por região(ões)", default=None)

        # platforms
        subparsers.add_parser("platforms", help="Listar plataformas disponíveis")
        # regions
        subparsers.add_parser("regions", help="Listar regiões disponíveis")

        # config
        cfg_parser = subparsers.add_parser("config", help="Gerenciar configurações")
        cfg_group = cfg_parser.add_mutually_exclusive_group(required=True)
        cfg_group.add_argument("--list", action="store_true", help="Listar todas as configurações")
        cfg_group.add_argument("--get", metavar="KEY", help="Obter valor (formato section.key)")
        cfg_group.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Definir valor (formato section.key VALUE)")
        cfg_group.add_argument("--save", action="store_true", help="Salvar configurações em arquivo")
        cfg_group.add_argument("--reset", action="store_true", help="Resetar arquivo de configuração para o padrão")
        cfg_parser.add_argument("--format", choices=["json", "yaml"], default="json", help="Formato de exibição para --list")

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
        elif command == "boxart":
            return self._cmd_boxart(args)
        elif command == "random":
            return self._cmd_random(args)
        elif command == "platforms":
            return self._cmd_platforms(args)
        elif command == "regions":
            return self._cmd_regions(args)
        elif command == "config":
            return self._cmd_config(args)
        else:
            self.parser.print_help()
            return 1

    # --- Commands ---
    def _cmd_search(self, args):
        # Monta query como string única a partir de múltiplas keywords
        query = " ".join(args.query).strip()

        # Lê config para paginação
        search_conf = self.config_manager.get("search", {})
        # novo: "max-results" define itens por página (padrão 100, máximo 100)
        per_page = (
            args.max_results if getattr(args, 'max_results', None) is not None else (
                args.per_page if getattr(args, 'per_page', None) is not None else search_conf.get("results_per_page", None)
            )
        )
        if per_page is None:
            per_page = 100
        if per_page > 100:
            print("Erro: --max-results deve ser no máximo 100.")
            return 1
        # Limite total legado (mantido por compatibilidade)
        max_results = args.limit if getattr(args, 'limit', None) is not None else search_conf.get("max_results", per_page)

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

        # Página inicial (alinhado ao model.md)
        page = args.page if getattr(args, 'page', None) else 1
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
            # Removido no CLI para evitar pausas: não exibir prompt nem ler entrada
            break
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
                dl_args = _argparse.Namespace(target=str(idx), output='.', romid=None, slug=None, platform=None, region=None, no_boxart=False, force=False, silence=False)
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
        target = getattr(args, 'target', None)
        output_dir = getattr(args, 'output', '.')
        romid = getattr(args, 'romid', None)
        slug = getattr(args, 'slug', None)
        no_boxart = getattr(args, 'no_boxart', False)
        # platform/region flags aceitos para alinhamento, atualmente sem efeito direto aqui
        _platforms = getattr(args, 'platform', None)
        _regions = getattr(args, 'region', None)

        # Resolve ROM
        rom = None
        if romid or slug:
            rom_key = romid or slug
            import asyncio
            rom = asyncio.run(self.search_engine.get_rom_info(rom_key))
            if not rom:
                print("ROM não encontrada pelo identificador informado.")
                return 1
        elif target:
            if target.isdigit():
                idx = int(target) - 1
                if 0 <= idx < len(self.cached_results):
                    rom = self.cached_results[idx].rom_entry
                else:
                    print("Índice fora do intervalo. Execute uma busca primeiro e escolha um índice válido.")
                    return 1
            else:
                import asyncio
                rom = asyncio.run(self.search_engine.get_rom_info(target))
                if not rom:
                    print("ROM não encontrada pelo ID informado.")
                    return 1
        else:
            print("Informe um índice, --romid ou --slug.")
            return 1

        # Realiza download usando DownloadManager
        try:
            import asyncio
            result = asyncio.run(
                self.download_manager.download_rom(
                    rom,
                    download_boxart=(not no_boxart),
                    progress_callback=self._download_progress_callback
                )
            )

            if not result or not result.success:
                err = getattr(result, 'error', 'Falha desconhecida no download') if result else 'Falha desconhecida no download'
                print(f"{err}")
                return 1

            final_path = result.final_path

            # Se usuário especificou diretório de saída customizado, mover arquivo
            if output_dir and output_dir != '.':
                try:
                    os.makedirs(output_dir, exist_ok=True)
                    import shutil
                    dest_path = os.path.join(output_dir, os.path.basename(final_path)) if final_path else os.path.join(output_dir, f"{rom.slug}.zip")
                    # Move para o destino especificado pelo usuário
                    if final_path and os.path.abspath(final_path) != os.path.abspath(dest_path):
                        shutil.move(final_path, dest_path)
                        final_path = dest_path
                except Exception as move_err:
                    logger.warning(f"Não foi possível mover para o diretório de saída especificado: {move_err}")

            print(f"Baixado: {final_path}")
            return 0
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            return 1

    def _cmd_boxart(self, args):
        target = getattr(args, 'target', None)
        romid = getattr(args, 'romid', None)
        slug = getattr(args, 'slug', None)
        # platform/region/force/silence aceitos, porém não utilizados diretamente aqui
        _platforms = getattr(args, 'platform', None)
        _regions = getattr(args, 'region', None)
        _force = getattr(args, 'force', False)
        _silence = getattr(args, 'silence', False)

        # Resolve ROM
        rom = None
        if romid or slug:
            rom_key = romid or slug
            import asyncio
            rom = asyncio.run(self.search_engine.get_rom_info(rom_key))
            if not rom:
                print("ROM não encontrada pelo identificador informado.")
                return 1
        elif target:
            if target.isdigit():
                idx = int(target) - 1
                if 0 <= idx < len(self.cached_results):
                    rom = self.cached_results[idx].rom_entry
                else:
                    print("Índice fora do intervalo. Execute uma busca primeiro e escolha um índice válido.")
                    return 1
            else:
                import asyncio
                rom = asyncio.run(self.search_engine.get_rom_info(target))
                if not rom:
                    print("ROM não encontrada pelo ID informado.")
                    return 1
        else:
            print("Informe um índice, --romid ou --slug.")
            return 1

        if not getattr(rom, 'boxart_url', None):
            print("Boxart não disponível para esta ROM.")
            return 1

        try:
            # Se disponível, usa o método específico do DownloadManager
            if hasattr(self.download_manager, 'download_boxart'):
                import asyncio
                saved_path = asyncio.run(
                    self.download_manager.download_boxart(
                        rom,
                        progress_callback=self._download_progress_callback
                    )
                )
                if not saved_path:
                    print("Falha ao baixar a boxart.")
                    return 1
                print(f"Boxart salva em: {saved_path}")
                return 0
            else:
                print("Operação não suportada nesta versão do gerenciador de download.")
                return 1
        except Exception as e:
            logger.error(f"Erro no download da boxart: {e}")
            return 1

    def _cmd_random(self, args):
        count = max(1, int(getattr(args, 'count', 1) or 1))
        search_filter = SearchFilter(
            platforms=getattr(args, 'platform', None) or None,
            regions=getattr(args, 'region', None) or None,
        )
        try:
            roms = None
            if hasattr(self.search_engine, 'get_random_roms_sync'):
                roms = self.search_engine.get_random_roms_sync(count=count, search_filter=search_filter)
            else:
                import asyncio
                if hasattr(self.search_engine, 'get_random_roms'):
                    roms = asyncio.run(self.search_engine.get_random_roms(count=count, search_filter=search_filter))
            if not roms:
                print("Nenhuma ROM encontrada.")
                return 1
            for i, r in enumerate(roms, start=1):
                regions_str = ",".join(r.regions or [])
                print(f"{i}. {r.title} | {r.platform} | {regions_str} | {r.slug}")
            return 0
        except Exception as e:
            logger.error(f"Erro ao obter ROMs aleatórias: {e}")
            return 1

    def _cmd_platforms(self, args):
        try:
            items = None
            if hasattr(self.search_engine, 'get_platforms_sync'):
                items = self.search_engine.get_platforms_sync() or []
            else:
                import asyncio
                if hasattr(self.search_engine, 'get_platforms'):
                    items = asyncio.run(self.search_engine.get_platforms()) or []
            for p in (items or []):
                print(p)
            return 0
        except Exception as e:
            logger.error(f"Erro ao listar plataformas: {e}")
            return 1

    def _cmd_regions(self, args):
        try:
            items = None
            if hasattr(self.search_engine, 'get_regions_sync'):
                items = self.search_engine.get_regions_sync() or []
            else:
                import asyncio
                if hasattr(self.search_engine, 'get_regions'):
                    items = asyncio.run(self.search_engine.get_regions()) or []
            for r in (items or []):
                print(r)
            return 0
        except Exception as e:
            logger.error(f"Erro ao listar regiões: {e}")
            return 1

    def _cmd_config(self, args):
        """Gerencia configurações via linha de comando."""
        cm = self.config_manager
        try:
            if getattr(args, 'list', False):
                data = cm.get_all()
                if args.format == 'yaml':
                    print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
                else:
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                return 0
            if getattr(args, 'get', None):
                key = args.get
                value = cm.get(key, None)
                if isinstance(value, (dict, list)):
                    print(json.dumps(value, ensure_ascii=False, indent=2))
                else:
                    print(value)
                return 0
            if getattr(args, 'set', None):
                key, value_str = args.set[0], args.set[1]
                # Conversões básicas de tipo
                parsed: Optional[object] = value_str
                low = value_str.strip().lower()
                if low in ('true', 'false'):
                    parsed = (low == 'true')
                elif low in ('null', 'none'):
                    parsed = None
                else:
                    try:
                        if '.' in value_str:
                            parsed = float(value_str)
                        else:
                            parsed = int(value_str)
                    except ValueError:
                        parsed = value_str  # mantém string
                ok = cm.set(key, parsed)
                if not ok:
                    print(f"Falha ao definir {key}")
                    return 1
                # Salva imediatamente
                if cm.save_config():
                    print("Configuração salva.")
                    return 0
                else:
                    print("Falha ao salvar configuração.")
                    return 1
            if getattr(args, 'save', False):
                if cm.save_config():
                    print("Configuração salva.")
                    return 0
                else:
                    print("Falha ao salvar configuração.")
                    return 1
            if getattr(args, 'reset', False):
                if cm.create_default_config():
                    cm.load_config()
                    print("Configuração resetada para o padrão.")
                    return 0
                else:
                    print("Falha ao resetar configuração.")
                    return 1
            # Caso nenhum reconhecido
            print("Ação de configuração não reconhecida.")
            return 1
        except Exception as e:
            logger.error(f"Erro na gestão de configuração: {e}")
            print(f"Erro: {e}")
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

        # Larguras de colunas
        w_title = 38
        w_id = 10
        w_platform = 9
        w_regions = 4
        w_hosts = 12
        w_format = 7
        w_size = 9
        w_score = 6

        # Cabeçalho da tabela
        header = (
            "#".rjust(w_idx) + " " +
            "Título".ljust(w_title) + " " +
            "ID".ljust(w_id) + " " +
            "Platform".ljust(w_platform) + " " +
            "Reg.".ljust(w_regions) + " " +
            "Hosts".ljust(w_hosts) + " " +
            "Format".ljust(w_format) + " " +
            "Size".rjust(w_size) + " " +
            "Score"
        )
        sep = (
            "-" * w_idx + " " +
            "-" * w_title + " " +
            "-" * w_id + " " +
            "-" * w_platform + " " +
            "-" * w_regions + " " +
            "-" * w_hosts + " " +
            "-" * w_format + " " +
            "-" * w_size + " " +
            "-" * 5
        )
        print(header)
        print(sep)

        # Linhas
        for i, s in enumerate(items):
            idx = start_num + i
            rom = s.rom_entry

            title = (getattr(rom, 'title', '') or '')
            title = (title[:w_title-1] + '…') if len(title) > w_title else title
            title = title.ljust(w_title)

            romid = (getattr(rom, 'rom_id', None) or getattr(rom, 'slug', '') or '')
            romid = romid[:w_id].ljust(w_id)

            platform = (getattr(rom, 'platform', '') or '')[:w_platform].ljust(w_platform)

            regions = ",".join(getattr(rom, 'regions', None) or [])
            regions = regions[:w_regions].ljust(w_regions)

            hosts_val = getattr(rom, 'hosts', None) or ""
            hosts_val = str(hosts_val)[:w_hosts].ljust(w_hosts)

            fmt_val = getattr(rom, 'file_format', None) or ""
            fmt_val = str(fmt_val)[:w_format].ljust(w_format)

            size_val = getattr(rom, 'size', None)
            size_str = format_file_size(size_val) if isinstance(size_val, int) and size_val >= 0 else ""
            size_str = size_str[:w_size].rjust(w_size)

            score_str = f"{s.total_score:>{w_score}.3f}"

            print(f"{str(idx).rjust(w_idx)} {title} {romid} {platform} {regions} {hosts_val} {fmt_val} {size_str} {score_str}")

        if end_num >= total:
            # Não imprimir mensagem de fim no CLI para evitar saídas interativas
            # Removido: print("-- Fim dos resultados --")

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

    def _download_progress_callback(self, progress: DownloadProgress):
        """Callback de progresso compatível com DownloadManager."""
        try:
            pct = getattr(progress, 'percentage', None)
            status = getattr(progress, 'status', '')
            if pct is not None:
                sys.stdout.write(f"\rBaixando: {pct:.1f}% ({status})")
            else:
                sys.stdout.write(f"\rBaixando... ({status})")
            sys.stdout.flush()
        except Exception:
            # fallback silencioso para não interromper o fluxo em caso de incompatibilidades
            sys.stdout.write("\rBaixando...")
            sys.stdout.flush()