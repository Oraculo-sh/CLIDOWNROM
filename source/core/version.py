# -*- coding: utf-8 -*-
"""
CLI Download ROM - Version Information

Informações de versão da aplicação.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

__version__ = "1.0.0"
__author__ = "Leonne Martins"
__email__ = "leonne.martins@outlook.com"
__license__ = "GPL-3.0"
__copyright__ = "Copyright (c) 2024 Leonne Martins"
__url__ = "https://github.com/Oraculo-sh/CLIDOWNROM"
__description__ = "Advanced CrocDB API client with multiple interfaces"

# Build information
__build_date__ = "2024-01-01"
__build_number__ = "1"

# API compatibility
__api_version__ = "1.0"
__min_python_version__ = "3.12"


def get_version_info():
    """Retorna informações completas da versão."""
    return {
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "url": __url__,
        "description": __description__,
        "build_date": __build_date__,
        "build_number": __build_number__,
        "api_version": __api_version__,
        "min_python_version": __min_python_version__
    }


def get_version_string():
    """Retorna string formatada da versão."""
    try:
        build_num = __build_number__
    except NameError:
        build_num = "1"
    return f"CLI Download ROM v{__version__} (Build {build_num})"


def check_python_version():
    """Verifica se a versão do Python é compatível."""
    import sys
    
    min_version = tuple(map(int, __min_python_version__.split('.')))
    current_version = sys.version_info[:2]
    
    if current_version < min_version:
        raise RuntimeError(
            f"Python {__min_python_version__} ou superior é necessário. "
            f"Versão atual: {sys.version}"
        )
    
    return True