#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Locales package for CLI Download ROM.

This package holds translation resource files (YAML). The i18n code lives in src/core/locales_manager.py.
"""

from ..core.locales_manager import I18nManager, init_i18n, get_i18n, t, tn

__all__ = [
    'I18nManager',
    'init_i18n',
    'get_i18n',
    't',
    'tn'
]

__author__ = "Leonne Martins"
__license__ = "GPL-3.0"