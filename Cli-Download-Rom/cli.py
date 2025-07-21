import argparse
import logging
import json
import sys
import cmd
import shlex
import os
import subprocess
from pathlib import Path

from .utils.localization import t
from .utils.config_loader import config
from .scripts.crocdb_api_handler import CrocDBAPIHandler
from .scripts.crocdb_db_handler import CrocDBLocalHandler
from .scripts.mirror_tester import find_fastest_mirror
from .scripts.download_manager import download_rom

PLATFORM_KEYWORDS = {
    'nes': ['nes', 'nintendo'], 'snes': ['snes', 'super nintendo'],
    'n64': ['n64', 'nintendo 64'], 'gc': ['gc', 'gamecube'], 'wii': ['wii'],
    'wiiu': ['wiiu'], 'gb': ['gb', 'game boy'], 'gbc': ['gbc', 'game boy color'],
    'gba': ['gba', 'game boy advance'], 'nds': ['nds', 'nintendo ds'], 'dsi': ['dsi'],
    '3ds': ['3ds'], 'n3ds': ['n3ds', 'new 3ds'], 'ps1': ['ps1', 'psx', 'playstation'],
    'ps2': ['ps2', 'playstation 2'], 'ps3': ['ps3', 'playstation 3'],
    'psp': ['psp'], 'psv': ['psv', 'ps vita'], 'smd': ['smd', 'genesis', 'mega drive'],
    'scd': ['scd', 'sega cd'], 'sat': ['sat', 'saturn'], 'dc': ['dc', 'dreamcast']
}

def _rank_search_results(results, query):
    query_lower = query.lower()
    query_words = set(query_lower.split())
    for rom in results:
        score = 0
        title_lower = rom.get('title', '').lower()
        title_words = set(title_lower.split())
        if query_words.issubset(title_words):
            score += 1000
            extra_words = len(title_words) - len(query_words)
            score -= extra_words * 10
        if query_lower in title_lower:
            score += 500
        if title_lower.startswith(query_lower):
            score += 200
        for word in query_words:
            if word in title_lower:
                score += 10
        rom['relevance_score'] = score
    return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)

def _get_roms_details_from_list(rom_list_summary):
    try:
        local_handler = CrocDBLocalHandler()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return []
    api_handler = CrocDBAPIHandler()
    roms_to_download = []
    total_roms = len(rom_list_summary)
    for i, rom_info in enumerate(rom_list_summary):
        rom_id = rom_info.get('rom_id')
        slug = rom_info.get('slug')
        title_for_log = rom_info.get('title', rom_id or slug)
        print(f"\n[{i+1}/{total_roms}] {t.get_string('LIST_PROCESSING_ROM', title_for_log)}")
        if not rom_id and not slug: continue
        details = local_handler.get_rom_details(rom_id) if rom_id else None
        if not details:
            logging.info(t.get_string("FALLBACK_TO_API", rom_id or slug))
            if slug:
                 details = api_handler.get_rom_details(slug)
            else:
                 logging.warning(f"Não foi possível buscar na API sem um 'slug' para a ROM: {title_for_log}")
        if details:
            roms_to_download.append(details)
        else:
            logging.error(t.get_string("ROM_NOT_FOUND_ANYWHERE", rom_id or slug))
    return roms_to_download

def _orchestrate_downloads(roms_to_download, destination_folder=None):
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
        if download_rom(rom_details, preferred_mirror, destination_folder):
            success_count += 1
        else:
            failure_count += 1
    print("\n" + "="*40)
    print(f"✔️ {t.get_string('FINAL_REPORT_SUCCESS', success_count)}")
    print(f"❌ {t.get_string('FINAL_REPORT_FAILURE', failure_count)}")
    print(f"📖 {t.get_string('FINAL_REPORT_LOGS', config['general']['logs_directory'])}")
    print("="*40)

def _handle_rom_selection(results):
    print(f"\n✔️ {t.get_string('SEARCH_RESULTS_TITLE')}")
    for i, rom in enumerate(results[:100]):
        regions = ", ".join(rom.get('regions', []))
        print(f"  [{i+1}] {rom['title']} ({rom['platform']}) [{regions}]")
    while True:
        try:
            choice_str = input(f"\n{t.get_string('PROMPT_SELECT_ROM')} (1-{len(results[:100])}): ")
            if not choice_str:
                print(t.get_string("ACTION_CANCELLED"))
                return None
            choice = int(choice_str)
            if 1 <= choice <= len(results[:100]):
                selected_rom_summary = results[choice - 1]
                logging.info(f"Usuário selecionou a ROM: {selected_rom_summary['title']} ({selected_rom_summary.get('slug', 'N/A')})")
                print(f"\n{t.get_string('ROM_SELECTED_FOR_DOWNLOAD', selected_rom_summary['title'])}")
                api_handler = CrocDBAPIHandler()
                return api_handler.get_rom_details(selected_rom_summary['slug'])
            else:
                print(t.get_string("ERROR_INVALID_SELECTION"))
        except (ValueError, IndexError):
            print(t.get_string("ERROR_INVALID_NUMBER"))
        except (KeyboardInterrupt, EOFError):
            print(f"\n{t.get_string('ACTION_CANCELLED')}")
            return None

def handle_search(args):
    logging.info(t.get_string("SEARCH_START", args.query, args.source))
    original_query = args.query
    platforms_to_filter = args.platform
    search_query = original_query.lower()
    if not platforms_to_filter and args.source == 'api':
        detected_platforms = []
        query_words_without_platforms = []
        for word in search_query.split():
            found_platform = False
            for platform_id, keywords in PLATFORM_KEYWORDS.items():
                if word in keywords:
                    if platform_id not in detected_platforms:
                        detected_platforms.append(platform_id)
                    found_platform = True
                    break
            if not found_platform:
                query_words_without_platforms.append(word)
        if detected_platforms:
            platforms_to_filter = detected_platforms
            search_query = " ".join(query_words_without_platforms) or original_query.split()[0]
            logging.info(f"Filtro de plataforma detectado: {platforms_to_filter}. Nova busca: '{search_query}'")
    try:
        if args.source == 'local':
            handler = CrocDBLocalHandler()
            results = handler.search_rom(original_query)
        else:
            handler = CrocDBAPIHandler()
            results = handler.search_rom(search_query, platforms_to_filter, args.region)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return
    if not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', original_query)}")
        return
    ranked_results = _rank_search_results(results, original_query)
    rom_details_to_download = _handle_rom_selection(ranked_results)
    if rom_details_to_download:
        preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
        if download_rom(rom_details_to_download, preferred_mirror):
             print(f"\n✔️ {t.get_string('FINAL_REPORT_SUCCESS', 1)}")
        else:
             print(f"\n❌ {t.get_string('FINAL_REPORT_FAILURE', 1)}")

def handle_download_list(args):
    filepath = args.filepath
    if not filepath:
        list_dir = Path(__file__).parent.parent / config['general']['lists_directory']
        json_files = list(list_dir.glob('*.json'))
        if not json_files:
            print(f"❌ {t.get_string('LIST_NO_FILES_FOUND')}")
            return
        print(f"\n{t.get_string('LIST_SELECT_PROMPT')}")
        for i, file in enumerate(json_files):
            print(f"  [{i+1}] {file.name}")
        try:
            choice_str = input("> ")
            if not choice_str:
                print(t.get_string("ACTION_CANCELLED")); return
            choice = int(choice_str) - 1
            if 0 <= choice < len(json_files):
                filepath = json_files[choice]
            else:
                print(f"❌ {t.get_string('ERROR_INVALID_SELECTION')}"); return
        except (ValueError, IndexError):
            print(f"❌ {t.get_string('ERROR_INVALID_NUMBER')}"); return
    list_path = Path(filepath)
    try:
        with open(list_path, 'r', encoding='utf-8') as f:
            rom_list_summary = json.load(f)
    except Exception as e:
        print(f"❌ {t.get_string('LIST_FILE_INVALID', e)}"); return
    
    print("\n--- ROMs na lista selecionada ---")
    for rom in rom_list_summary:
        print(f"- {rom.get('title', 'Título desconhecido')}")
    print("---------------------------------")
    
    confirm = input(f"{t.get_string('LIST_CONFIRM_DOWNLOAD', len(rom_list_summary))}").upper()
    if confirm != 'S':
        print(t.get_string('LIST_DOWNLOAD_ABORTED'))
        return
    
    destination_folder = None
    print(f"\n{t.get_string('DOWNLOAD_DESTINATION_PROMPT')}")
    print(f"  {t.get_string('DOWNLOAD_DESTINATION_OPTION_1')}")
    dest_choice_name = list_path.stem
    print(f"  {t.get_string('DOWNLOAD_DESTINATION_OPTION_2', dest_choice_name)}")
    
    dest_choice = input("> ")
    if dest_choice == '2':
        destination_folder = dest_choice_name

    roms_with_details = _get_roms_details_from_list(rom_list_summary)
    _orchestrate_downloads(roms_with_details, destination_folder)

def handle_update_db(args):
    print(t.get_string("DB_UPDATE_STARTING"))
    logging.info("Iniciando o processo de atualização do banco de dados local.")
    crocdb_dir = Path(__file__).parent.parent / 'crocdb' / 'crocdb-db'
    workflow_script = crocdb_dir / 'workflow.py'
    requirements_file = crocdb_dir / 'requirements.txt'
    if not workflow_script.exists():
        logging.error(t.get_string("DB_UPDATE_WORKFLOW_NOT_FOUND", str(workflow_script)))
        print(f"❌ {t.get_string('DB_UPDATE_WORKFLOW_NOT_FOUND', str(workflow_script))}")
        return
    venv_python = Path(sys.executable)
    venv_pip = venv_python.parent / 'pip'
    try:
        print("--- Instalando dependências do construtor de DB ---")
        subprocess.run([str(venv_pip), 'install', '-r', str(requirements_file)], check=True)
        print("--- Executando workflow.py (isso pode demorar muito) ---")
        result = subprocess.run(
            [str(venv_python), str(workflow_script)],
            cwd=str(crocdb_dir),
            capture_output=True, text=True, encoding='utf-8', check=True
        )
        print(f"✔️ {t.get_string('DB_UPDATE_SUCCESS')}")
        logging.info(f"Workflow do crocdb-db concluído com sucesso.\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"❌ {t.get_string('DB_UPDATE_FAILED')}")
        logging.error(f"O script de atualização falhou.\nExit Code: {e.returncode}\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}")
    except Exception as e:
        print(f"❌ {t.get_string('DB_UPDATE_FAILED')}")
        logging.error(f"Ocorreu um erro inesperado ao executar o workflow.py: {e}")

class InteractiveShell(cmd.Cmd):
    intro = t.get_string("INTERACTIVE_SHELL_WELCOME")
    prompt = 'Downloader> '
    def __init__(self, parser):
        super().__init__()
        self.parser = parser

    def help_search(self): print(t.get_string("HELP_SEARCH"))
    def help_download_list(self): print(t.get_string("HELP_DOWNLOAD_LIST"))
    def help_update_db(self): print(t.get_string("HELP_UPDATE_DB"))
    def help_exit(self): print(t.get_string("HELP_EXIT"))

    def do_search(self, arg_string):
        try:
            args = self.parser.parse_args(['search'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_search(args)
        except SystemExit: pass
    def do_download_list(self, arg_string):
        try:
            args = self.parser.parse_args(['download-list'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_download_list(args)
        except SystemExit: pass
    def do_update_db(self, arg_string):
        try:
            args = self.parser.parse_args(['update-db'] + shlex.split(arg_string, posix=(os.name != 'nt')))
            handle_update_db(args)
        except SystemExit: pass
    def do_exit(self, arg):
        print(t.get_string("INTERACTIVE_SHELL_EXIT")); return True
    def do_quit(self, arg): return self.do_exit(arg)
    def do_EOF(self, arg): print(); return self.do_exit(arg)
    def emptyline(self): pass

    def complete_search(self, text, line, begidx, endidx):
        words = line.split()
        current_word = text
        if not text:
            current_word = words[-1] if len(words) > 1 else ''
        
        previous_word = words[-2] if len(words) > 1 and not text else words[-1]

        if current_word.startswith('--'):
            opts = ['--source', '--platform', '--region']
            return [o for o in opts if o.startswith(current_word)]
        if previous_word == '--source':
            opts = ['api', 'local']
            return [o for o in opts if o.startswith(text)]
        return []
    def complete_download_list(self, text, line, begidx, endidx):
        list_dir_str = config['general']['lists_directory']
        full_path_str = text
        base_dir = list_dir_str
        
        if os.path.dirname(text):
            base_dir = os.path.join(list_dir_str, os.path.dirname(text))
        
        filename_part = os.path.basename(text)

        completions = []
        try:
            if os.path.isdir(base_dir):
                for f in os.listdir(base_dir):
                    if f.startswith(filename_part):
                        completed_path = os.path.join(os.path.dirname(full_path_str), f)
                        if os.path.isdir(os.path.join(list_dir_str, completed_path)):
                            completions.append(completed_path + os.sep)
                        else:
                            completions.append(completed_path)
        except OSError:
            pass # Ignora erros de permissão etc
        return completions

def get_parser():
    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest='command')
    
    parser_search = subparsers.add_parser('search', help='Busca por uma ROM específica.')
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument('--source', type=str, choices=['api', 'local'], default='api', help='Define a fonte de dados.')
    parser_search.add_argument('-p', '--platform', nargs='+', metavar='PLATAFORMA', help='Filtra por plataformas.')
    parser_search.add_argument('-r', '--region', nargs='+', metavar='REGIÃO', help='Filtra por regiões.')
    
    parser_list = subparsers.add_parser('download-list', help='Baixa uma lista de ROMs.')
    parser_list.add_argument('filepath', type=str, nargs='?', default=None, help='Caminho opcional do arquivo .json.')
    
    parser_update = subparsers.add_parser('update-db', help='Constrói/atualiza o banco de dados SQLite local.')
    
    return parser

def start():
    parser = get_parser()
    if len(sys.argv) > 1:
        try:
            args = parser.parse_args()
            if hasattr(args, 'command') and args.command:
                if args.command == 'search': handle_search(args)
                elif args.command == 'download-list': handle_download_list(args)
                elif args.command == 'update-db': handle_update_db(args)
            else:
                parser.print_help()
        except argparse.ArgumentError:
             parser.print_help()
    else:
        InteractiveShell(parser).cmdloop()