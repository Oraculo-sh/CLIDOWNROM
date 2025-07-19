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

# DICIONÁRIO DE PALAVRAS-CHAVE DE PLATAFORMAS
PLATFORM_KEYWORDS = {
    'nes': ['nes', 'nintendo'],
    'snes': ['snes', 'super nintendo'],
    'n64': ['n64', 'nintendo 64'],
    'gc': ['gc', 'gamecube'],
    'wii': ['wii'],
    'wiiu': ['wiiu'],
    'gb': ['gb', 'game boy'],
    'gbc': ['gbc', 'game boy color'],
    'gba': ['gba', 'game boy advance'],
    'nds': ['nds', 'nintendo ds'],
    'dsi': ['dsi'],
    '3ds': ['3ds'],
    'n3ds': ['n3ds', 'new 3ds'],
    'ps1': ['ps1', 'psx', 'playstation'],
    'ps2': ['ps2', 'playstation 2'],
    'ps3': ['ps3', 'playstation 3'],
    'psp': ['psp'],
    'psv': ['psv', 'ps vita'],
    'smd': ['smd', 'genesis', 'mega drive'],
    'scd': ['scd', 'sega cd'],
    'sat': ['sat', 'saturn'],
    'dc': ['dc', 'dreamcast']
}

def _rank_search_results(results, query):
    """Reordena os resultados da busca com base em um score de relevância aprimorado."""
    query = query.lower()
    query_words = set(query.split())
    
    for rom in results:
        score = 0
        title_lower = rom.get('title', '').lower()
        
        # 1. Bônus mais alto se a busca completa for uma frase exata no título
        if query in title_lower:
            score += 1000
        
        # 2. Bônus por cada palavra da busca encontrada no título
        words_found_count = 0
        for word in query_words:
            if word in title_lower:
                words_found_count += 1
        score += words_found_count * 20
        
        # 3. Bônus massivo se TODAS as palavras da busca estiverem no título
        if words_found_count == len(query_words):
            score += 200
            
        # 4. Bônus se o título começar com a busca
        if title_lower.startswith(query):
            score += 50
            
        # 5. Penalidade por títulos muito longos (menos diretos)
        score -= len(title_lower)
        
        rom['relevance_score'] = score
        
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)

def _get_roms_details_from_list(rom_list_summary):
    """Busca os detalhes completos para uma lista de ROMs (local com fallback para API)."""
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

def _orchestrate_downloads(roms_to_download):
    """Orquestra o teste de mirror e o loop de downloads."""
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

def _handle_rom_selection(results):
    """Exibe resultados e gerencia a seleção interativa do usuário."""
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
    """Lida com o comando 'search', com filtros automáticos e ranking."""
    logging.info(t.get_string("SEARCH_START", args.query, args.source))
    
    query = args.query
    platforms_to_filter = args.platform
    
    if not platforms_to_filter:
        query_words = query.lower().split()
        detected_platforms = []
        for word in query_words:
            for platform_id, keywords in PLATFORM_KEYWORDS.items():
                if word in keywords:
                    if platform_id not in detected_platforms:
                        detected_platforms.append(platform_id)
        if detected_platforms:
            platforms_to_filter = detected_platforms
            logging.info(f"Filtro de plataforma detectado: {platforms_to_filter}")

    try:
        if args.source == 'local':
            handler = CrocDBLocalHandler()
            results = handler.search_rom(query)
        else:
            handler = CrocDBAPIHandler()
            results = handler.search_rom(query, platforms_to_filter, args.region)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    if not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', query)}")
        return

    ranked_results = _rank_search_results(results, query)
    rom_details_to_download = _handle_rom_selection(ranked_results)

    if rom_details_to_download:
        preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
        if download_rom(rom_details_to_download, preferred_mirror):
             print(f"\n✔️ {t.get_string('FINAL_REPORT_SUCCESS', 1)}")
        else:
             print(f"\n❌ {t.get_string('FINAL_REPORT_FAILURE', 1)}")

def handle_download_list(args):
    """Lida com o comando 'download-list'."""
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

def handle_update_db(args):
    """Executa o workflow para construir/atualizar o banco de dados SQLite."""
    print(t.get_string("DB_UPDATE_STARTING"))
    logging.info("Iniciando o processo de atualização do banco de dados local.")

    crocdb_dir = Path(__file__).parent / 'crocdb' / 'crocdb-db'
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

# --- Classe do Shell Interativo e Função 'start' ---

class InteractiveShell(cmd.Cmd):
    intro = t.get_string("INTERACTIVE_SHELL_WELCOME")
    prompt = 'Downloader> '
    def __init__(self, parser):
        super().__init__()
        self.parser = parser

    def do_search(self, arg_string):
        """Busca por uma ROM. Uso: search <termo> [--source local|api] [-p PLATAFORMA] [-r REGIAO]"""
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
    
    def do_update_db(self, arg_string):
        """Constrói/atualiza o banco de dados SQLite local."""
        try:
            args = self.parser.parse_args(['update-db'] + shlex.split(arg_string))
            handle_update_db(args)
        except SystemExit: pass

    def do_exit(self, arg):
        """Sai do shell interativo."""
        print(t.get_string("INTERACTIVE_SHELL_EXIT"))
        return True
    
    def do_quit(self, arg):
        """Alias para o comando 'exit'."""
        return self.do_exit(arg)

    def do_EOF(self, arg):
        """Manipula o Ctrl+D para sair."""
        print()
        return self.do_exit(arg)

    def emptyline(self):
        pass

def get_parser():
    """Cria e retorna o parser de argumentos."""
    parser = argparse.ArgumentParser(description=t.get_string("APP_DESCRIPTION"), add_help=False)
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
        if hasattr(args, 'command'):
            if args.command == 'search':
                handle_search(args)
            elif args.command == 'download-list':
                handle_download_list(args)
            elif args.command == 'update-db':
                handle_update_db(args)
        else:
            parser.print_help()
    else:
        InteractiveShell(parser).cmdloop()