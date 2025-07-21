import logging
import time
import requests
from pathlib import Path
from tqdm import tqdm
from ..utils.localization import t
from ..utils.config_loader import config

def find_fastest_mirror(test_rom_details):
    logging.info(t.get_string("MIRROR_TEST_STARTING"))
    print(f"🔬 {t.get_string('MIRROR_TEST_STARTING')}")

    if not test_rom_details or 'links' not in test_rom_details or not test_rom_details['links']:
        logging.error(t.get_string("MIRROR_TEST_NO_LINKS"))
        return config['mirrors']['default_preferred_mirror'][0]

    temp_dir = Path(__file__).parent.parent / config['general']['temp_directory'] / 'test-mirrors'
    temp_dir.mkdir(exist_ok=True)
    
    results = []
    for link in test_rom_details['links']:
        url, host, filename, size_bytes = link.get('url'), link.get('host'), link.get('filename'), link.get('size')
        if not all([url, host, filename, size_bytes]): continue
        
        temp_file_path = temp_dir / f"{host}_{filename}"
        print(t.get_string("MIRROR_TEST_DOWNLOADING", host))
        try:
            start_time = time.time()
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(temp_file_path, 'wb') as f, tqdm.wrapattr(f, "write", total=size_bytes, desc=t.get_string("MIRROR_TEST_PROGRESS_DESC", host), unit='B', unit_scale=True, unit_divisor=1024) as fout:
                    for chunk in r.iter_content(chunk_size=8192):
                        fout.write(chunk)
            end_time = time.time()
            duration = end_time - start_time
            speed = (size_bytes / (1024 * 1024)) / duration if duration > 0 else 0
            results.append({'host': host, 'duration': duration, 'speed': speed})
            logging.info(t.get_string("MIRROR_TEST_HOST_SUCCESS", host, f"{duration:.2f}s", f"{speed:.2f} MB/s"))
        except requests.RequestException as e:
            logging.error(t.get_string("MIRROR_TEST_HOST_FAILED", host, e))
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()

    if not results:
        logging.warning(t.get_string("MIRROR_TEST_ALL_FAILED"))
        return config['mirrors']['default_preferred_mirror'][0]

    results.sort(key=lambda x: x['speed'], reverse=True)
    fastest = results[0]
    speed_str = f"{fastest['speed']:.2f} MB/s"
    
    logging.info(t.get_string("MIRROR_TEST_CONCLUSION", fastest['host'], speed_str))
    print(f"🏆 {t.get_string('MIRROR_TEST_CONCLUSION', fastest['host'], speed_str)}")
    
    return fastest['host']