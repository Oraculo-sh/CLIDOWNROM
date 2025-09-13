# -*- coding: utf-8 -*-
"""
CLI Download ROM - Core Module

Módulo principal contendo as funcionalidades centrais da aplicação.
Para evitar importações pesadas e possíveis ciclos, este pacote usa
carregamento preguiçoso (lazy) dos símbolos reexportados.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

__author__ = "Leonne Martins (@Oraculo-sh)"
__license__ = "GPL-3.0"

# Símbolos públicos reexportados
__all__ = [
    "DirectoryManager",
    "ConfigManager",
    "LogManager",
    "SearchEngine",
    "SearchFilter",
    "ROMScore",
    "DownloadManager",
    "DownloadProgress",
    "DownloadResult",
    "MirrorTester",
    "CrocDBClient",
    "ROMEntry",
    "SearchResult",
]

# Mapa de símbolos -> submódulos para lazy import
_NAME_TO_MODULE = {
    # directory/config/logger
    "DirectoryManager": "directory_manager",
    "ConfigManager": "config",
    "LogManager": "logger",
    # search
    "SearchEngine": "search_engine",
    "SearchFilter": "search_engine",
    "ROMScore": "search_engine",
    # download
    "DownloadManager": "download_manager",
    "DownloadProgress": "download_manager",
    "DownloadResult": "download_manager",
    "MirrorTester": "download_manager",
    # api client
    "CrocDBClient": "crocdb_client",
    "ROMEntry": "crocdb_client",
    "SearchResult": "crocdb_client",
}

if TYPE_CHECKING:
    # Ajuda para type checkers sem custo em runtime
    from .directory_manager import DirectoryManager  # noqa: F401
    from .config import ConfigManager  # noqa: F401
    from .logger import LogManager  # noqa: F401
    from .search_engine import SearchEngine, SearchFilter, ROMScore  # noqa: F401
    from .download_manager import (
        DownloadManager,
        DownloadProgress,
        DownloadResult,
        MirrorTester,
    )  # noqa: F401
    from .crocdb_client import CrocDBClient, ROMEntry, SearchResult  # noqa: F401


def __getattr__(name: str):
    """Carrega o símbolo solicitado sob demanda a partir do submódulo correto.

    Isso evita importações precoces de todos os submódulos, reduz risco de
    circularidade e melhora o tempo de import do pacote core.
    """
    module_name = _NAME_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module 'source.core' has no attribute {name!r}")
    module = import_module(f"{__name__}.{module_name}")
    try:
        return getattr(module, name)
    except AttributeError as exc:
        raise AttributeError(
            f"'{module.__name__}' does not define attribute {name!r}"
        ) from exc


def __dir__():
    return sorted(list(globals().keys()) + __all__)