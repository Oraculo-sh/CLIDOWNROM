#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Locales package for CLI Download ROM.

This package handles internationalization (i18n) for the application,
providing support for multiple languages and locales.

Author: Leonne Martins
License: GPL-3.0
"""

from .i18n import I18nManager, init_i18n, get_i18n, t, tn

__all__ = [
    'I18nManager',
    'init_i18n',
    'get_i18n',
    't',
    'tn'
]

__author__ = "Leonne Martins"
__license__ = "GPL-3.0"