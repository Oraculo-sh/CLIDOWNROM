# Cli-Download-Rom/scripts/mirror_tester.py

import logging
import time
import requests
from pathlib import Path
from tqdm import tqdm
from ..utils.localization import t
from ..utils.config_loader import config

def find_fastest_mirror(test_rom_details):
    """
    Testa a velocidade de download de todos os links disponíveis para uma ROM de teste.

    Args:
        test_rom_details (dict): Os detalhes completos da ROM a ser usada para o teste.

    Returns:
        str: O nome do host (mirror) mais rápido. Retorna o mirror padrão se o teste falhar.
    """
    logging.info(t.get_string("MIRROR_TEST_STARTING"))
    print(f"🔬 {t.get_string('MIRROR_TEST_STARTING')}")

    if not test_rom_details or 'links' not in test_rom_details:
        logging.error(t.get_string("MIRROR_TEST_NO_LINKS"))
        return config['mirrors']['default_preferred_mirror'][0]

    temp_dir = Path(__file__).parent.parent / config['general']['temp_directory'] / 'test-mirrors'
    temp_dir.mkdir(exist_ok=True)
    
    results = []

    for link in test_rom_details['links']:
        url = link['url']
        host = link['host']
        filename = link['filename']
        size_bytes = link['size']
        temp_file_path = temp_dir / f"{host}_{filename}"

        print(t.get_string("MIRROR_TEST_DOWNLOADING", host))
        try:
            start_time = time.time()
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(temp_file_path, 'wb') as f:
                    with tqdm.wrapattr(f, "write",
                                     total=size_bytes,
                                     desc=t.get_string("MIRROR_TEST_PROGRESS_DESC", host),
                                     unit='B', unit_scale=True, unit_divisor=1024) as fout:
                        for chunk in r.iter_content(chunk_size=8192):
                            fout.write(chunk)

            end_time = time.time()
            duration = end_time - start_time
            # Speed in MB/s
            speed = (size_bytes / (1024 * 1024)) / duration if duration > 0 else 0
            results.append({'host': host, 'duration': duration, 'speed': speed})
            logging.info(t.get_string("MIRROR_TEST_HOST_SUCCESS", host, f"{duration:.2f}s", f"{speed:.2f} MB/s"))

        except requests.RequestException as e:
            logging.error(t.get_string("MIRROR_TEST_HOST_FAILED", host, e))
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink() # Limpa o arquivo de teste

    if not results:
        logging.warning(t.get_string("MIRROR_TEST_ALL_FAILED"))
        return config['mirrors']['default_preferred_mirror'][0]

    # Ordena por velocidade (maior é melhor)
    results.sort(key=lambda x: x['speed'], reverse=True)
    fastest = results[0]
    
    logging.info(t.get_string("MIRROR_TEST_CONCLUSION", fastest['host'], f"{fastest['speed']:.2f} MB/s"))
    print(f"🏆 {t.get_string('MIRROR_TEST_CONCLUSION', fastest['host'], f'{fastest['speed']:.2f} MB/s')}")
    
    return fastest['host']