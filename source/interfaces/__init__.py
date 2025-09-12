#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaces package for CLI Download ROM.

This package contains all user interface implementations:
- CLI: Command-line interface for scripts and automation
- Shell: Interactive REPL shell with history and completion
- TUI: Full-screen text interface using Textual
- GUI: Graphical interface with gamepad support using PyQt6

Author: Leonne Martins
License: GPL-3.0
"""

__author__ = "Leonne Martins"
__license__ = "GPL-3.0"

from importlib.util import find_spec

# Import core, always lightweight
from .cli import CLIInterface
from .shell import ShellInterface

# Export only always-available interfaces explicitly
__all__ = [
    'CLIInterface',
    'ShellInterface',
]

# Interface availability check functions (without importing heavy modules)

def is_tui_available() -> bool:
    """
    Check if TUI interface is available.
    Returns True if 'textual' is installed without importing our TUI module.
    """
    return find_spec('textual') is not None


def is_gui_available() -> bool:
    """
    Check if GUI interface is available.
    Returns True if 'PyQt6' is installed without importing our GUI module.
    """
    return find_spec('PyQt6') is not None


def get_interface_names() -> list:
    """
    Get a list of available interface names without importing heavy modules.
    """
    names = ['cli', 'shell']
    if is_tui_available():
        names.append('tui')
    if is_gui_available():
        names.append('gui')
    return names


def get_available_interfaces() -> dict:
    """
    Get a dictionary of available interfaces mapped to their classes.
    Will lazily import TUI/GUI only if available and requested by this call.
    """
    interfaces = {
        'cli': CLIInterface,
        'shell': ShellInterface,
    }

    if is_tui_available():
        try:
            from .tui import TUIInterface  # Imported only when needed
            interfaces['tui'] = TUIInterface
        except Exception:
            # If import fails despite textual being present, ignore TUI
            pass

    if is_gui_available():
        try:
            from .gui import GUIInterface  # Imported only when needed
            interfaces['gui'] = GUIInterface
        except Exception:
            # If import fails despite PyQt6 being present, ignore GUI
            pass

    return interfaces


def create_interface(interface_name: str, config_manager, directory_manager, log_manager):
    """
    Create an interface instance by name with lazy imports for TUI/GUI.
    """
    name = interface_name.lower()
    if name == 'cli':
        return CLIInterface(config_manager, directory_manager, log_manager)
    if name == 'shell':
        return ShellInterface(config_manager, directory_manager, log_manager)
    if name == 'tui':
        if not is_tui_available():
            raise ValueError("TUI interface not available (missing 'textual')")
        from .tui import TUIInterface
        return TUIInterface(config_manager, directory_manager, log_manager)
    if name == 'gui':
        if not is_gui_available():
            raise ValueError("GUI interface not available (missing 'PyQt6')")
        from .gui import GUIInterface
        return GUIInterface(config_manager, directory_manager, log_manager)

    available = ', '.join(get_interface_names())
    raise ValueError(f"Interface '{interface_name}' not available. Available: {available}")