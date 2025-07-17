# Cli-Download-Rom/cli.py

import argparse
import logging
import json
import sys
import cmd
import shlex # Usado para parsear argumentos no modo interativo
from pathlib import Path

# Módulos de utilidades
from utils.localization import t
from utils.config_loader import config

# Módulos de scripts com a lógica principal
from scripts.crocdb_api_handler import CrocDBAPIHandler
from scripts.crocdb_db_handler import CrocDBLocalHandler
from scripts.mirror_tester import find_fastest_mirror
from scripts.download_manager import download_rom

# --- Lógica do CLI Padrão (já existente, com pequenas adaptações) ---

def _handle_rom_selection(results):
    # (Esta função auxiliar permanece exatamente a mesma da versão anterior)
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
    # (Esta função permanece a mesma da versão anterior)
    logging.info(t.get_string("SEARCH_START", args.query, args.source))
    handler = CrocDBAPIHandler() if args.source == 'api' else CrocDBLocalHandler()
    results = handler.search_rom(args.query)
    if results is None or not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', args.query)}")
        return
    rom_details_to_download = _handle_rom_selection(results)
    if rom_details_to_download:
        preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
        download_rom(rom_details_to_download, preferred_mirror)

def handle_download_list(args):
    # (Esta função permanece a mesma da versão anterior)
    # ... (toda a lógica de carregar lista, testar mirror e baixar)
    pass # A lógica completa já foi definida anteriormente

# --- Lógica do Shell Interativo (NOVO) ---

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
        except SystemExit: # Impede que o argparse feche o shell
            pass

    def do_download_list(self, arg_string):
        """Baixa ROMs de um arquivo de lista. Uso: download-list <caminho_do_arquivo>"""
        try:
            args = self.parser.parse_args(['download-list'] + shlex.split(arg_string))
            handle_download_list(args)
        except SystemExit:
            pass

    def do_exit(self, arg):
        """Sai do shell interativo."""
        print(t.get_string("INTERACTIVE_SHELL_EXIT"))
        return True # Retornar True encerra o loop do cmd

    def do_quit(self, arg):
        """Alias para o comando 'exit'."""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Manipula o Ctrl+D (em Linux/macOS) para sair."""
        print() # Pula uma linha para ficar mais limpo
        return self.do_exit(arg)

    def emptyline(self):
        """Não faz nada quando o usuário pressiona Enter com a linha vazia."""
        pass

# --- Ponto de Entrada Principal ---

def get_parser():
    """Cria e retorna o parser de argumentos para ser usado em ambos os modos."""
    parser = argparse.ArgumentParser(description=t.get_string("APP_DESCRIPTION"))
    subparsers = parser.add_subparsers(dest='command', help=t.get_string("COMMANDS_HELP"))
    
    # Comando 'search'
    parser_search = subparsers.add_parser('search', help='Busca por uma ROM específica e inicia o download.')
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument('--source', type=str, choices=['api', 'local'], default='api', help='Define a fonte de dados (padrão: api).')
    
    # Comando 'download-list'
    parser_list = subparsers.add_parser('download-list', help='Baixa uma lista de ROMs de um arquivo.')
    parser_list.add_argument('filepath', type=str, help='Caminho para o arquivo .json da lista.')
    
    return parser

def start():
    """Ponto de entrada que decide entre o modo CLI Padrão e o Shell Interativo."""
    parser = get_parser()

    # Se mais de um argumento foi passado (o primeiro é sempre o nome do script),
    # então entramos no modo CLI Padrão.
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.command == 'search':
            handle_search(args)
        elif args.command == 'download-list':
            # Cole aqui a lógica completa da função handle_download_list que definimos anteriormente
            pass 
    else:
        # Se nenhum argumento foi passado, entramos no modo Shell Interativo.
        InteractiveShell(parser).cmdloop()