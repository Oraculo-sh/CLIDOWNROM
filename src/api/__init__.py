# -*- coding: utf-8 -*-
"""
CLI Download ROM - API Package

Pacote contendo clientes e utilitários para APIs externas.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

from .crocdb_client import CrocDBClient, ROMEntry, SearchResult

__all__ = [
    'CrocDBClient',
    'ROMEntry', 
    'SearchResult'
]