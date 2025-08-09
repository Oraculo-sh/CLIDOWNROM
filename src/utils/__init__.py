# -*- coding: utf-8 -*-
"""
CLI Download ROM - Utilities Module

Módulo de utilitários com funções auxiliares para formatação,
validação, busca e outras operações comuns.

Author: Leonne Martins (@Oraculo-sh)
License: GPL-3.0
"""

from .version import (
    __version__,
    __author__,
    __license__,
    __build_number__,
    get_version_info,
    get_version_string,
    check_python_version
)

from .helpers import (
    format_file_size,
    format_duration,
    format_speed,
    format_eta,
    sanitize_filename,
    normalize_text,
    calculate_similarity,
    extract_year_from_title,
    extract_region_from_title,
    validate_url,
    get_file_hash,
    get_system_info,
    create_progress_bar,
    truncate_text,
    parse_file_size,
    is_valid_platform,
    find_best_match,
    clean_temp_files,
    get_available_disk_space,
    check_disk_space,
    create_backup_filename
)

__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__license__',
    'get_version_info',
    'get_version_string',
    'check_python_version',
    
    # Helper functions
    'format_file_size',
    'format_duration',
    'format_speed',
    'format_eta',
    'sanitize_filename',
    'normalize_text',
    'calculate_similarity',
    'extract_year_from_title',
    'extract_region_from_title',
    'validate_url',
    'get_file_hash',
    'get_system_info',
    'create_progress_bar',
    'truncate_text',
    'parse_file_size',
    'is_valid_platform',
    'find_best_match',
    'clean_temp_files',
    'get_available_disk_space',
    'check_disk_space',
    'create_backup_filename'
]