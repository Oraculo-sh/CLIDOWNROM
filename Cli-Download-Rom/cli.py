# Cli-Download-Rom/cli.py (VERSÃO CORRIGIDA E COMPLETA)

import argparse
import logging
import json
import sys
import cmd
import shlex
from pathlib import Path
from .utils.localization import t
from .utils.config_loader import config
from .scripts.crocdb_api_handler import CrocDBAPIHandler
from .scripts.crocdb_db_handler import CrocDBLocalHandler
from .scripts.mirror_tester import find_fastest_mirror
from .scripts.download_manager import download_rom

def _handle_rom_selection(results):
    print(f"\n✔️ {t.get_string('SEARCH_RESULTS_TITLE')}")
    for i, rom in enumerate(results):
        regions = ", ".join(rom.get('regions', []))
        print(f"  [{i+1}] {rom['title']} ({rom['platform']}) [{regions}]")
    while True:
        try:
            choice_str = input(f"\n{t.get_string('PROMPT_SELECT_ROM')} (1-{len(results)}): ")
            if not choice_str:
                print(t.get_string("ACTION_CANCELLED"))
                return None
            choice = int(choice_str)
            if 1 <= choice <= len(results):
                selected_rom_summary = results[choice - 1]
                logging.info(f"Usuário selecionou a ROM: {selected_rom_summary['title']} ({selected_rom_summary['rom_id']})")
                print(f"\n{t.get_string('ROM_SELECTED_FOR_DOWNLOAD', selected_rom_summary['title'])}")
                api_handler = CrocDBAPIHandler()
                return api_handler.get_rom_details(selected_rom_summary['rom_id'])
            else:
                print(t.get_string("ERROR_INVALID_SELECTION"))
        except (ValueError, IndexError):
            print(t.get_string("ERROR_INVALID_NUMBER"))
        except (KeyboardInterrupt, EOFError):
            print(f"\n{t.get_string('ACTION_CANCELLED')}")
            return None

def handle_search(args):
    logging.info(t.get_string("SEARCH_START", args.query, args.source))
    handler = CrocDBAPIHandler() if args.source == 'api' else CrocDBLocalHandler()
    results = handler.search_rom(args.query)
    if not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', args.query)}")
        return
    rom_details_to_download = _handle_rom_selection(results)
    if rom_details_to_download:
        preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
        if download_rom(rom_details_to_download, preferred_mirror):
             print(f"\n✔️ {t.get_string('FINAL_REPORT_SUCCESS', 1)}")
        else:
             print(f"\n❌ {t.get_string('FINAL_REPORT_FAILURE', 1)}")

def _get_roms_details_from_list(rom_list_summary):
    local_handler = CrocDBLocalHandler()
    api_handler = CrocDBAPIHandler()
    roms_to_download = []
    total_roms = len(rom_list_summary)
    for i, rom_info in enumerate(rom_list_summary):
        rom_id = rom_info.get('rom_id')
        title_for_log = rom_info.get('title', rom_id)
        print(f"\n[{i+1}/{total_roms}] {t.get_string('LIST_PROCESSING_ROM', title_for_log)}")
        if not rom_id: continue
        details = local_handler.get_rom_details(rom_id)
        if not details:
            logging.info(t.get_string("FALLBACK_TO_API", rom_id))
            details = api_handler.get_rom_details(rom_id)
        if details:
            roms_to_download.append(details)
        else:
            logging.error(t.get_string("ROM_NOT_FOUND_ANYWHERE", rom_id))
    return roms_to_download

def _orchestrate_downloads(roms_to_download):
    if not roms_to_download:
        logging.info("Nenhuma ROM para baixar.")
        return
    preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
    if config['mirrors']['enable_mirror_test']:
        preferred_mirror = find_fastest_mirror(roms_to_download[0])
    else:
        logging.info("Teste de mirror desabilitado. Usando o mirror padrão.")
    success_count, failure_count = 0, 0
    for rom_details in roms_to_download:
        if download_rom(rom_details, preferred_mirror):
            success_count += 1
        else:
            failure_count += 1
    print("\n" + "="*40)
    print(f"✔️ {t.get_string('FINAL_REPORT_SUCCESS', success_count)}")
    print(f"❌ {t.get_string('FINAL_REPORT_FAILURE', failure_count)}")
    print(f"📖 {t.get_string('FINAL_REPORT_LOGS', config['general']['logs_directory'])}")
    print("="*40)

def handle_download_list(args):
    logging.info(t.get_string("PROCESSING_LIST_FILE", args.filepath))
    list_path = Path(args.filepath)
    if not list_path.exists():
        logging.error(t.get_string("LIST_FILE_NOT_FOUND", list_path))
        print(f"❌ {t.get_string('LIST_FILE_NOT_FOUND', list_path)}")
        return
    try:
        with open(list_path, 'r', encoding='utf-8') as f:
            rom_list_summary = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(t.get_string("LIST_FILE_INVALID", e))
        print(f"❌ {t.get_string('LIST_FILE_INVALID', e)}")
        return
    roms_with_details = _get_roms_details_from_list(rom_list_summary)
    _orchestrate_downloads(roms_with_details)

class InteractiveShell(cmd.Cmd):
    intro = t.get_string("INTERACTIVE_SHELL_WELCOME")
    prompt = 'Downloader> '
    def __init__(self, parser):
        super().__init__()
        self.parser = parser
    def do_search(self, arg_string):
        """Busca por uma ROM. Uso: search <termo> [--source local|api]"""
        try:
            args = self.parser.parse_args(['search'] + shlex.split(arg_string))
            handle_search(args)
        except SystemExit: pass
    def do_download_list(self, arg_string):
        """Baixa ROMs de um arquivo de lista. Uso: download-list <caminho_do_arquivo>"""
        try:
            args = self.parser.parse_args(['download-list'] + shlex.split(arg_string))
            handle_download_list(args)
        except SystemExit: pass
    def do_exit(self, arg):
        """Sai do shell interativo."""
        print(t.get_string("INTERACTIVE_SHELL_EXIT"))
        return True
    def do_quit(self, arg):
        """Alias para o comando 'exit'."""
        return self.do_exit(arg)
    def do_EOF(self, arg):
        """Manipula o Ctrl+D (em Linux/macOS) para sair."""
        print()
        return self.do_exit(arg)
    def emptyline(self):
        """Não faz nada quando o usuário pressiona Enter com a linha vazia."""
        pass

def get_parser():
    parser = argparse.ArgumentParser(description=t.get_string("APP_DESCRIPTION"))
    subparsers = parser.add_subparsers(dest='command', help=t.get_string("COMMANDS_HELP"))
    parser_search = subparsers.add_parser('search', help='Busca por uma ROM específica e inicia o download.')
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument('--source', type=str, choices=['api', 'local'], default='api', help='Define a fonte de dados (padrão: api).')
    parser_list = subparsers.add_parser('download-list', help='Baixa uma lista de ROMs de um arquivo.')
    parser_list.add_argument('filepath', type=str, help='Caminho para o arquivo .json da lista.')
    return parser

def start():
    parser = get_parser()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if hasattr(args, 'command'):
            if args.command == 'search':
                handle_search(args)
            elif args.command == 'download-list':
                handle_download_list(args)
    else:
        InteractiveShell(parser).cmdloop()