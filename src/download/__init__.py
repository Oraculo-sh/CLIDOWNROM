# -*- coding: utf-8 -*-
"""
CLI Download ROM - Download Module

Módulo responsável pelo gerenciamento de downloads de ROMs,
incluindo teste de mirrors, downloads simultâneos e verificação de integridade.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

from .download_manager import (
    DownloadManager,
    DownloadProgress,
    DownloadResult,
    MirrorTester
)

__all__ = [
    'DownloadManager',
    'DownloadProgress', 
    'DownloadResult',
    'MirrorTester'
]

__author__ = "Leonne Martins (@Oraculo-sh)"
__license__ = "GPL-3.0"