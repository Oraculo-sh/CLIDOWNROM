# -*- coding: utf-8 -*-
"""
CLI Download ROM - Source Package

Pacote principal contendo todos os módulos da aplicação.
Evita reexports desnecessários que possam induzir erros (ex.: 'api' inexistente).

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

__all__ = [
    "core",
    "interfaces",
    "locales",
    "format_file_size",
    "sanitize_filename",
]