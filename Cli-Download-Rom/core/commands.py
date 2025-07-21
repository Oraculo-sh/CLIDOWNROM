import logging
import json
from pathlib import Path

from ..utils.localization import t
from ..utils.config_loader import config
from ..scripts.crocdb_api_handler import CrocDBAPIHandler
from ..scripts.mirror_tester import find_fastest_mirror
from ..scripts.download_manager import download_rom
from .constants import PLATFORM_KEYWORDS

def _rank_search_results(results, query):
    query_lower = query.lower()
    query_words = set(query_lower.split())
    for rom in results:
        score = 0
        title_lower = rom.get('title', '').lower()
        title_words = set(title_lower.split())
        if query_words.issubset(title_words):
            score += 1000
            score -= (len(title_words) - len(query_words)) * 10
        if query_lower in title_lower:
            score += 500
        if title_lower.startswith(query_lower):
            score += 200
        platform_lower = rom.get('platform', '').lower()
        if platform_lower in query_words:
            score += 100
        score -= len(title_lower)
        rom['relevance_score'] = score
    return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)

def _get_roms_details_from_list(rom_list_summary):
    api_handler = CrocDBAPIHandler()
    roms_to_download = []
    total_roms = len(rom_list_summary)
    for i, rom_info in enumerate(rom_list_summary):
        slug = rom_info.get('slug')
        title_for_log = rom_info.get('title', slug)
        print(f"\n[{i+1}/{total_roms}] {t.get_string('LIST_PROCESSING_ROM', title_for_log)}")
        if not slug: continue
        details = api_handler.get_rom_details(slug)
        if details:
            roms_to_download.append(details)
        else:
            logging.error(t.get_string("ROM_NOT_FOUND_ANYWHERE", slug))
    return roms_to_download

def _orchestrate_downloads(roms_to_download, args):
    if not roms_to_download:
        logging.info("Nenhuma ROM para baixar."); return
    
    preferred_mirror = args.mirror or config['mirrors']['default_preferred_mirror'][0]
    if not args.mirror and config['mirrors']['enable_mirror_test']:
        preferred_mirror = find_fastest_mirror(roms_to_download[0])
    
    success_count, failure_count = 0, 0
    for rom_details in roms_to_download:
        if download_rom(rom_details, preferred_mirror, args.destination_folder, args.noaria2c, args.noboxart):
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
            if not choice_str: print(t.get_string("ACTION_CANCELLED")); return None
            choice = int(choice_str)
            if 1 <= choice <= len(results[:100]):
                selected_rom = results[choice - 1]
                logging.info(f"Usuário selecionou: {selected_rom['title']} ({selected_rom.get('slug', 'N/A')})")
                print(f"\n{t.get_string('ROM_SELECTED_FOR_DOWNLOAD', selected_rom['title'])}")
                api_handler = CrocDBAPIHandler()
                return api_handler.get_rom_details(selected_rom['slug'])
            else:
                print(t.get_string("ERROR_INVALID_SELECTION"))
        except (ValueError, IndexError): print(t.get_string("ERROR_INVALID_NUMBER"))
        except (KeyboardInterrupt, EOFError): print(f"\n{t.get_string('ACTION_CANCELLED')}"); return None

def handle_search(args):
    logging.info(t.get_string("SEARCH_START", args.query, "api"))
    api_handler = CrocDBAPIHandler()

    if args.slug or args.rom_id:
        identifier = args.slug or args.rom_id
        id_type = 'slug' if args.slug else 'rom_id'
        results = [api_handler.get_rom_details(identifier, by=id_type)]
        if not results[0]: results = []
    else:
        results = api_handler.search_rom(args.query, args.platform, args.region)

    if not results:
        print(f"\nℹ️ {t.get_string('SEARCH_NO_RESULTS_FOUND', args.query)}"); return
    
    ranked_results = _rank_search_results(results, args.query)
    rom_to_download = _handle_rom_selection(ranked_results)
    if rom_to_download:
        # Cria um objeto 'args' simples para passar para a orquestração
        download_args = argparse.Namespace(
            mirror=None, noboxart=False, noaria2c=False, destination_folder=None
        )
        _orchestrate_downloads([rom_to_download], download_args)

def handle_download(args):
    logging.info(f"Download direto solicitado para: slug='{args.slug}', rom_id='{args.rom_id}'")
    api_handler = CrocDBAPIHandler()
    identifier = args.slug or args.rom_id
    id_type = 'slug' if args.slug else 'rom_id'

    rom_details = api_handler.get_rom_details(identifier, by=id_type)
    if not rom_details:
        print(f"❌ {t.get_string('ROM_NOT_FOUND_ANYWHERE', identifier)}"); return

    # Cria um objeto 'args' para passar para a orquestração
    download_args = argparse.Namespace(
        mirror=args.mirror, noboxart=args.noboxart, noaria2c=args.noaria2c, destination_folder=None
    )
    _orchestrate_downloads([rom_details], download_args)

def handle_download_list(args):
    filepath = args.filepath
    list_dir = Path(__file__).parent.parent / config['general']['lists_directory']
    if not filepath:
        json_files = sorted(list(list_dir.glob('*.json')))
        if not json_files: print(f"❌ {t.get_string('LIST_NO_FILES_FOUND')}"); return
        print(f"\n{t.get_string('LIST_SELECT_PROMPT')}")
        for i, file in enumerate(json_files): print(f"  [{i+1}] {file.name}")
        try:
            choice_str = input("> ")
            if not choice_str: print(t.get_string("ACTION_CANCELLED")); return
            choice = int(choice_str) - 1
            if 0 <= choice < len(json_files): filepath = json_files[choice]
            else: print(f"❌ {t.get_string('ERROR_INVALID_SELECTION')}"); return
        except (ValueError, IndexError): print(f"❌ {t.get_string('ERROR_INVALID_NUMBER')}"); return
    
    list_path = Path(filepath)
    if not list_path.is_absolute() and not list_path.exists(): list_path = list_dir / list_path.name
    
    try:
        with open(list_path, 'r', encoding='utf-8') as f: rom_list_summary = json.load(f)
    except FileNotFoundError: print(f"❌ {t.get_string('LIST_FILE_NOT_FOUND', str(filepath))}"); return
    except Exception as e: print(f"❌ {t.get_string('LIST_FILE_INVALID', e)}"); return
    
    print("\n--- ROMs na lista selecionada ---")
    for rom in rom_list_summary: print(f"- {rom.get('title', 'Título desconhecido')}")
    print("---------------------------------")
    
    prompt_text = t.get_string('LIST_CONFIRM_DOWNLOAD_TEXT', len(rom_list_summary)) + " " + t.get_string('LIST_CONFIRM_DOWNLOAD_PROMPT')
    confirm = input(prompt_text).upper()
    yes_answers = ['S', 'SIM', 'Y', 'YES']
    if confirm not in yes_answers:
        print(t.get_string('LIST_DOWNLOAD_ABORTED')); return
    
    destination_folder = None
    print(f"\n{t.get_string('DOWNLOAD_DESTINATION_PROMPT')}")
    print(f"  {t.get_string('DOWNLOAD_DESTINATION_OPTION_1')}")
    dest_choice_name = list_path.stem
    print(f"  {t.get_string('DOWNLOAD_DESTINATION_OPTION_2', dest_choice_name)}")
    
    dest_choice = input("> ")
    if dest_choice == '2': destination_folder = dest_choice_name

    # Cria um objeto 'args' para passar para a orquestração
    download_args = argparse.Namespace(
        mirror=args.mirror, noboxart=args.noboxart, noaria2c=args.noaria2c, destination_folder=destination_folder
    )
    roms_with_details = _get_roms_details_from_list(rom_list_summary)
    _orchestrate_downloads(roms_with_details, download_args)