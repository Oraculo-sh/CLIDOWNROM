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

def _rank_search_results(results, query):
    """Reordena os resultados da busca com base em um score de relevância."""
    query_words = set(query.lower().split())
    
    for rom in results:
        score = 0
        title_lower = rom.get('title', '').lower()
        
        for word in query_words:
            if word in title_lower:
                score += 20
        
        if title_lower.startswith(query.lower()):
            score += 50
            
        score -= len(title_lower) * 0.1
        rom['relevance_score'] = score
        
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)

def _get_roms_details_from_list(rom_list_summary):
    # ... (código desta função permanece o mesmo da versão anterior)
    
def _orchestrate_downloads(roms_to_download):
    # ... (código desta função permanece o mesmo da versão anterior)

def _handle_rom_selection(results):
    # ... (código desta função permanece o mesmo da versão anterior)

def handle_search(args):
    """Lida com o comando 'search', com filtros e ranking."""
    logging.info(t.get_string("SEARCH_START", args.query, args.source))
    
    try:
        if args.source == 'local':
            handler = CrocDBLocalHandler()
            results = handler.search_rom(args.query)
        else:
            handler = CrocDBAPIHandler()
            results = handler.search_rom(args.query, args.platform, args.region)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    if not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', args.query)}")
        return

    ranked_results = _rank_search_results(results, args.query)
    rom_details_to_download = _handle_rom_selection(ranked_results)

    if rom_details_to_download:
        preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
        if download_rom(rom_details_to_download, preferred_mirror):
             print(f"\n✔️ {t.get_string('FINAL_REPORT_SUCCESS', 1)}")
        else:
             print(f"\n❌ {t.get_string('FINAL_REPORT_FAILURE', 1)}")

def handle_download_list(args):
    # ... (código desta função permanece o mesmo da versão anterior)

def handle_update_db(args):
    # ... (código desta função permanece o mesmo da versão anterior)

class InteractiveShell(cmd.Cmd):
    # ... (código desta classe permanece o mesmo da versão anterior)

def get_parser():
    """Cria e retorna o parser de argumentos com as flags de filtro."""
    parser = argparse.ArgumentParser(description=t.get_string("APP_DESCRIPTION"))
    subparsers = parser.add_subparsers(dest='command', help=t.get_string("COMMANDS_HELP"))
    
    parser_search = subparsers.add_parser('search', help='Busca por uma ROM específica.')
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument('--source', type=str, choices=['api', 'local'], default='api', help='Define a fonte de dados.')
    parser_search.add_argument('-p', '--platform', nargs='+', metavar='PLATAFORMA', help='Filtra por uma ou mais plataformas (ex: n64 snes).')
    parser_search.add_argument('-r', '--region', nargs='+', metavar='REGIÃO', help='Filtra por uma ou mais regiões (ex: us eu jp).')
    
    parser_list = subparsers.add_parser('download-list', help='Baixa uma lista de ROMs de um arquivo.')
    parser_list.add_argument('filepath', type=str, help='Caminho para o arquivo .json da lista.')
    
    parser_update = subparsers.add_parser('update-db', help='Constrói/atualiza o banco de dados SQLite local.')
    
    return parser

def start():
    """Ponto de entrada que decide entre o modo CLI Padrão e o Shell Interativo."""
    parser = get_parser()

    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.command == 'search':
            handle_search(args)
        elif args.command == 'download-list':
            handle_download_list(args)
        elif args.command == 'update-db':
            handle_update_db(args)
    else:
        InteractiveShell(parser).cmdloop()