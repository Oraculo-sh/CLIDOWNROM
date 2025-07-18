import json
import logging
from pathlib import Path
from ..utils.localization import t

class CrocDBLocalHandler:
    """
    Gerencia a busca de dados no banco de dados local do CrocDB.
    """
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'crocdb' / 'crocdb-db' / 'db'
        if not self.db_path.is_dir():
            logging.error(t.get_string("LOCAL_DB_DIR_NOT_FOUND", self.db_path))
            raise FileNotFoundError(t.get_string("LOCAL_DB_DIR_NOT_FOUND", self.db_path))
        
        self.json_files = list(self.db_path.glob('*.json'))
        if not self.json_files:
            logging.warning(t.get_string("LOCAL_DB_NO_FILES", self.db_path))

    def search_rom(self, query):
        """
        Busca por ROMs no DB local.
        """
        logging.info(t.get_string("LOCAL_DB_SEARCH_START", query))
        results = []
        query_lower = query.lower()
        for file_path in self.json_files:
            logging.debug(t.get_string("LOCAL_DB_FILE_PROCESSING", file_path.name))
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for rom in data:
                    if query_lower in rom.get('title', '').lower():
                        results.append({
                            'rom_id': rom.get('rom_id'),
                            'title': rom.get('title'),
                            'platform': rom.get('platform'),
                            'regions': rom.get('regions', [])
                        })
            except (json.JSONDecodeError, IOError) as e:
                logging.error(t.get_string("LOCAL_DB_FILE_ERROR", file_path.name, e))
                continue
        logging.info(t.get_string("LOCAL_DB_SEARCH_COMPLETE", len(results), query))
        return results

    def get_rom_details(self, rom_id):
        """
        Obtém os detalhes completos de uma ROM do DB local.
        """
        logging.debug(t.get_string("LOCAL_DB_DETAILS_ATTEMPT", rom_id))
        for file_path in self.json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for rom in data:
                    if rom.get('rom_id') == rom_id:
                        logging.info(t.get_string("LOCAL_DB_DETAILS_SUCCESS", rom.get('title', rom_id)))
                        return rom
            except (json.JSONDecodeError, IOError) as e:
                logging.error(t.get_string("LOCAL_DB_FILE_ERROR", file_path.name, e))
                continue
        logging.warning(t.get_string("LOCAL_DB_ROM_NOT_FOUND", rom_id))
        return None