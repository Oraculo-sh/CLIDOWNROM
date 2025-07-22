from scripts.crocdb_api_handler import search_roms
from scripts.download_manager import download_rom
from utils.localization import _
from utils.logging_config import setup_logging
from core.parser import rank_results
from ui.display import display_search_results

log = setup_logging()

def handle_search(args, config):
    """
    Lida com o comando de busca, exibe os resultados e solicita a seleção do utilizador.
    """
    api_url = config.get("api_url")
    search_term = " ".join(args.search_key)
    log.info(_("log_performing_search").format(term=search_term, platforms=args.platforms, regions=args.regions))

    response = search_roms(api_url, search_term, args.platforms, args.regions)

    if not response or "data" not in response or "results" not in response["data"]:
        print(f"\n{_('error_search_failed')}")
        return

    search_results = rank_results(response["data"]["results"], search_term)

    display_search_results(search_results)

    if search_results:
        try:
            selection = input(_("input_prompt_select_rom")).strip()
            if not selection:
                print(_("info_download_cancelled"))
                return

            if selection.lower() == 'c':
                print(_("info_download_cancelled"))
                return

            selected_index = int(selection) - 1
            if 0 <= selected_index < len(search_results):
                selected_rom = search_results[selected_index]
                download_dir = config.get("download_directory", "downloads")
                log.info(_("log_rom_selected").format(title=selected_rom.get('title'), index=selected_index))
                download_rom(selected_rom, download_dir)
            else:
                print(f"\n{_('error_invalid_selection')}")
        except (ValueError, IndexError):
            print(f"\n{_('error_invalid_selection')}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{_('info_download_cancelled')}")