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

# Import all interface classes
from .cli import CLIInterface
from .shell import ShellInterface

# Optional imports with fallback for missing dependencies
try:
    from .tui import TUIInterface
except ImportError:
    TUIInterface = None

try:
    from .gui import GUIInterface
except ImportError:
    GUIInterface = None

# Export all available interfaces
__all__ = [
    'CLIInterface',
    'ShellInterface',
    'TUIInterface',
    'GUIInterface'
]

# Interface availability check functions
def is_tui_available() -> bool:
    """
    Check if TUI interface is available.
    
    Returns:
        True if textual is installed and TUI can be used
    """
    return TUIInterface is not None

def is_gui_available() -> bool:
    """
    Check if GUI interface is available.
    
    Returns:
        True if PyQt6 is installed and GUI can be used
    """
    return GUIInterface is not None

def get_available_interfaces() -> dict:
    """
    Get a dictionary of available interfaces.
    
    Returns:
        Dictionary mapping interface names to their classes
    """
    interfaces = {
        'cli': CLIInterface,
        'shell': ShellInterface
    }
    
    if is_tui_available():
        interfaces['tui'] = TUIInterface
    
    if is_gui_available():
        interfaces['gui'] = GUIInterface
    
    return interfaces

def get_interface_names() -> list:
    """
    Get a list of available interface names.
    
    Returns:
        List of interface names
    """
    return list(get_available_interfaces().keys())

def create_interface(interface_name: str, config_manager, directory_manager, log_manager):
    """
    Create an interface instance by name.
    
    Args:
        interface_name: Name of the interface ('cli', 'shell', 'tui', 'gui')
        config_manager: ConfigManager instance
        directory_manager: DirectoryManager instance
        log_manager: LogManager instance
    
    Returns:
        Interface instance
    
    Raises:
        ValueError: If interface name is not available
    """
    interfaces = get_available_interfaces()
    
    if interface_name not in interfaces:
        available = ', '.join(interfaces.keys())
        raise ValueError(f"Interface '{interface_name}' not available. Available: {available}")
    
    interface_class = interfaces[interface_name]
    return interface_class(config_manager, directory_manager, log_manager)