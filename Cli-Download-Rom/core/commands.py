from ..scripts.crocdb_api_handler import search_roms
from ..scripts.download_manager import download_rom
from ..utils.localization import _
from ..utils.logging_config import setup_logging
from .parser import rank_results
from ..ui.display import display_search_results

def handle_search(args, config):
    """
    Lida com o comando de busca, exibe os resultados e processa a seleção de downloads.
    """
    api_url = config.get("api", {}).get("crocdb_api_url")
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
            selection_input = input(_("input_prompt_select_rom")).strip()
            if not selection_input or selection_input.lower() == 'c':
                print(f"\n{_('info_download_cancelled')}")
                return

            indices_str = selection_input.replace(" ", "").split(',')
            selected_indices = [int(i) - 1 for i in indices_str]

            valid_roms_to_download = []
            for index in selected_indices:
                if 0 <= index < len(search_results):
                    valid_roms_to_download.append(search_results[index])
                else:
                    print(f"\n{_('error_invalid_selection')}")
                    log.warning(f"Seleção de índice inválida: {index + 1}. Abortando downloads.")
                    return
            
            if valid_roms_to_download:
                log.info(_("log_download_queue_created").format(indices=selection_input))
                print(f"\n{_('info_starting_download_queue').format(count=len(valid_roms_to_download))}")
                download_dir = config.get("general", {}).get("roms_directory", "downloads")
                
                for i, rom in enumerate(valid_roms_to_download):
                    print(f"\n--- [{i+1}/{len(valid_roms_to_download)}] ---")
                    log.info(_("log_rom_selected").format(title=rom.get('title'), index=selected_indices[i]))
                    download_rom(rom, download_dir)

        except ValueError:
            print(f"\n{_('error_invalid_input_list')}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{_('info_download_cancelled')}")