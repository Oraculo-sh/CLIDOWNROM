# Cli-Download-Rom/cli.py

import argparse
import logging
import json
from pathlib import Path

# Módulos de utilidades
from utils.localization import t
from utils.config_loader import config

# Módulos de scripts com a lógica principal
from scripts.crocdb_api_handler import CrocDBAPIHandler
from scripts.crocdb_db_handler import CrocDBLocalHandler
from scripts.mirror_tester import find_fastest_mirror
from scripts.download_manager import download_rom


def _handle_rom_selection(results):
    """
    Função auxiliar para exibir resultados e gerenciar a seleção interativa do usuário.
    Retorna os detalhes completos da ROM selecionada.
    """
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
                
                # Para um download único, sempre usamos a API para obter os detalhes mais recentes
                api_handler = CrocDBAPIHandler()
                return api_handler.get_rom_details(selected_rom_summary['rom_id'])
            else:
                print(t.get_string("ERROR_INVALID_SELECTION"))
        except ValueError:
            print(t.get_string("ERROR_INVALID_NUMBER"))
        except (KeyboardInterrupt, EOFError):
            print(f"\n{t.get_string('ACTION_CANCELLED')}")
            return None


def handle_search(args):
    """Função para o comando 'search' que busca e inicia o download de uma ROM."""
    logging.info(t.get_string("SEARCH_START", args.query, args.source))
    
    handler = CrocDBAPIHandler() if args.source == 'api' else CrocDBLocalHandler()
    results = handler.search_rom(args.query)
        
    if results is None:
        print(f"\n❌ {t.get_string('SEARCH_FAILED')}")
        return
        
    if not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', args.query)}")
        return
    
    # Gerencia a seleção e obtém os detalhes da ROM escolhida
    rom_details_to_download = _handle_rom_selection(results)
    
    if rom_details_to_download:
        # Para um download único, usamos o mirror preferencial do config, sem rodar o teste
        preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
        download_rom(rom_details_to_download, preferred_mirror)
        
        # Imprime um mini relatório final
        print("\n" + "="*40)
        print(f"✔️ {t.get_string('FINAL_REPORT_SINGLE_DOWNLOAD')}")
        print(f"📖 {t.get_string('FINAL_REPORT_LOGS', config['general']['logs_directory'])}")
        print("="*40)


def handle_download_list(args):
    """Processa um arquivo de lista e gerencia o download das ROMs."""
    logging.info(t.get_string("PROCESSING_LIST_FILE", args.filepath))
    
    # 1. Carregar e validar o arquivo da lista
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

    # 2. Obter detalhes completos de cada ROM (Local DB com fallback para API)
    local_handler = CrocDBLocalHandler()
    api_handler = CrocDBAPIHandler()
    roms_to_download = []
    total_roms = len(rom_list_summary)

    for i, rom_info in enumerate(rom_list_summary):
        rom_id = rom_info.get('rom_id')
        title_for_log = rom_info.get('title', rom_id)
        print(f"\n[{i+1}/{total_roms}] {t.get_string('LIST_PROCESSING_ROM', title_for_log)}")

        details = local_handler.get_rom_details(rom_id)
        if not details:
            logging.info(t.get_string("FALLBACK_TO_API", rom_id))
            details = api_handler.get_rom_details(rom_id)

        if details:
            roms_to_download.append(details)
        else:
            logging.error(t.get_string("ROM_NOT_FOUND_ANYWHERE", rom_id))
    
    print(f"\n✔️ {t.get_string('LIST_PROCESSING_COMPLETE', len(roms_to_download), total_roms)}")

    if not roms_to_download:
        return

    # 3. Testar mirrors (se habilitado)
    preferred_mirror = config['mirrors']['default_preferred_mirror'][0]
    if config['mirrors']['enable_mirror_test']:
        preferred_mirror = find_fastest_mirror(roms_to_download[0])
    else:
        logging.info("Teste de mirror desabilitado. Usando o mirror padrão.")

    # 4. Loop de Download
    success_count = 0
    failure_count = 0
    for rom_details in roms_to_download:
        if download_rom(rom_details, preferred_mirror):
            success_count += 1
        else:
            failure_count += 1
            
    # 5. Relatório Final
    print("\n" + "="*40)
    print(f"✔️ {t.get_string('FINAL_REPORT_SUCCESS', success_count)}")
    print(f"❌ {t.get_string('FINAL_REPORT_FAILURE', failure_count)}")
    print(f"📖 {t.get_string('FINAL_REPORT_LOGS', config['general']['logs_directory'])}")
    print("="*40)


def start():
    """Configura e inicia o parser de argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Ferramenta de linha de comando para download de ROMs via CrocDB."
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Comandos disponíveis')

    # Comando 'search'
    parser_search = subparsers.add_parser('search', help='Busca por uma ROM específica e inicia o download.')
    parser_search.add_argument('query', type=str, help='O título da ROM a ser buscada.')
    parser_search.add_argument(
        '--source', type=str, choices=['api', 'local'], default='api',
        help='Define a fonte de dados para a busca (padrão: api).'
    )
    parser_search.set_defaults(func=handle_search)

    # Comando 'download-list'
    parser_list = subparsers.add_parser('download-list', help='Baixa uma lista de ROMs de um arquivo.')
    parser_list.add_argument('filepath', type=str, help='Caminho para o arquivo .json da lista.')
    parser_list.set_defaults(func=handle_download_list)

    args = parser.parse_args()
    args.func(args)