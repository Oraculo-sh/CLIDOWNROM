# -*- coding: utf-8 -*-
"""
CLI Download ROM - Core Module

Módulo principal contendo as funcionalidades centrais da aplicação:
- Gerenciamento de diretórios
- Sistema de configuração
- Sistema de logging
- Motor de busca com ranking

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

from .directory_manager import DirectoryManager
from .config import ConfigManager
from .logger import LogManager
from .search_engine import SearchEngine, SearchFilter, ROMScore
from .download_manager import DownloadManager, DownloadProgress, DownloadResult, MirrorTester

__all__ = [
    'DirectoryManager',
    'ConfigManager',
    'LogManager',
    'SearchEngine',
    'SearchFilter',
    'ROMScore',
    'DownloadManager',
    'DownloadProgress',
    'DownloadResult',
    'MirrorTester'
]

__author__ = "Leonne Martins (@Oraculo-sh)"
__license__ = "GPL-3.0"