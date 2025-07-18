# Cli-Download-Rom/scripts/crocdb_db_handler.py (VERSÃO REESCRITA COM SQLITE)

import sqlite3
import logging
from pathlib import Path
from ..utils.localization import t

class CrocDBLocalHandler:
    """
    Gerencia a busca de dados no banco de dados SQLite gerado pelo crocdb-db.
    """
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / 'crocdb' / 'crocdb-db' / 'database' / 'roms.db'
        if not self.db_path.exists():
            logging.error(t.get_string("LOCAL_DB_SQLITE_NOT_FOUND", self.db_path))
            # Lança um erro que será pego pela CLI e mostrado ao usuário
            raise FileNotFoundError(t.get_string("LOCAL_DB_SQLITE_NOT_FOUND_USER_MSG"))

    def _execute_query(self, query, params=(), fetch_one=False):
        """Executa uma consulta no banco de dados e retorna os resultados."""
        try:
            # Conecta em modo read-only (uri=True)
            with sqlite3.connect(f'file:{self.db_path}?mode=ro', uri=True) as con:
                con.row_factory = sqlite3.Row # Permite acessar colunas por nome
                cur = con.cursor()
                cur.execute(query, params)
                if fetch_one:
                    return cur.fetchone()
                return cur.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Erro de banco de dados: {e}\nQuery: {query}\nParams: {params}")
            return None

    def _get_links_and_regions_for_entry(self, slug):
        """Busca os links e regiões para uma entrada específica."""
        regions_query = "SELECT region FROM regions_entries WHERE entry = ?"
        links_query = "SELECT name, type, format, url, filename, host, size, size_str, source_url FROM links WHERE entry = ?"
        
        region_rows = self._execute_query(regions_query, (slug,))
        link_rows = self._execute_query(links_query, (slug,))

        regions = [row['region'] for row in region_rows] if region_rows else []
        links = [dict(row) for row in link_rows] if link_rows else []
        
        return regions, links

    def search_rom(self, query):
        """Busca por ROMs no DB local usando FTS5 (Full-Text Search)."""
        logging.info(t.get_string("LOCAL_DB_SEARCH_START", query))
        
        # O FTS espera um formato específico para a busca
        search_query = f'"{query}"*'
        sql = """
            SELECT e.slug, e.rom_id, e.title, e.platform
            FROM entries_fts fts
            JOIN entries e ON fts.rowid = e.rowid
            WHERE fts.search_key MATCH ?
            ORDER BY rank
            LIMIT 100;
        """
        
        results = []
        rows = self._execute_query(sql, (search_query,))
        if rows is None: return None # Erro no DB

        for row in rows:
            entry = dict(row)
            # Para a lista de busca, apenas as regiões são necessárias
            regions, _ = self._get_links_and_regions_for_entry(entry['slug'])
            entry['regions'] = regions
            results.append(entry)
            
        logging.info(t.get_string("LOCAL_DB_SEARCH_COMPLETE", len(results), query))
        return results

    def get_rom_details(self, rom_id):
        """Obtém os detalhes completos de uma ROM do DB local usando seu ID."""
        logging.debug(t.get_string("LOCAL_DB_DETAILS_ATTEMPT", rom_id))
        
        sql = "SELECT slug, rom_id, title, platform, boxart_url FROM entries WHERE rom_id = ?"
        
        row = self._execute_query(sql, (rom_id,), fetch_one=True)
        
        if row:
            entry = dict(row)
            regions, links = self._get_links_and_regions_for_entry(entry['slug'])
            entry['regions'] = regions
            entry['links'] = links
            logging.info(t.get_string("LOCAL_DB_DETAILS_SUCCESS", entry.get('title', rom_id)))
            return entry
            
        logging.warning(t.get_string("LOCAL_DB_ROM_NOT_FOUND", rom_id))
        return None