#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Download ROM - Main Entry Point

A multi-platform ROM downloader client for CrocDB API with multiple user interfaces.

Author: Leonne Martins
License: GPL-3.0
"""

import sys
import os
import argparse
from pathlib import Path
from loguru import logger

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Core imports
from src.core import DirectoryManager, ConfigManager, LogManager
from src.locales import init_i18n, t
from src.utils import __version__, get_version_string
from src.interfaces import (
    CLIInterface, 
    ShellInterface,
    get_available_interfaces,
    create_interface,
    is_tui_available,
    is_gui_available
)

def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Setup the main argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="clidownrom",
        description="CLI Download ROM - Advanced ROM downloader for CrocDB API",
        epilog="For more information, visit: https://github.com/Oraculo-sh/CLIDOWNROM"
    )
    
    # Version
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"CLI Download ROM {get_version_string()}"
    )
    
    # Interface selection
    available_interfaces = list(get_available_interfaces().keys())
    parser.add_argument(
        "--interface", "-i",
        choices=available_interfaces,
        default="cli",
        help="Interface to use (default: cli)"
    )
    
    # Configuration file
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to custom configuration file"
    )
    
    # Language override
    parser.add_argument(
        "--language", "-l",
        choices=["auto", "en_us", "pt_br"],
        help="Language override (auto/en_us/pt_br)"
    )
    
    # Debug mode
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    
    # Quiet mode
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode - minimal output"
    )
    
    # Working directory
    parser.add_argument(
        "--workdir", "-w",
        type=str,
        help="Working directory for the application"
    )
    
    # CLI-specific arguments (when interface is cli)
    cli_group = parser.add_argument_group("CLI Commands")
    
    # Subcommands for CLI mode
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands (CLI mode only)",
        metavar="COMMAND"
    )
    
    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for ROMs"
    )
    search_parser.add_argument(
        "query",
        help="Search query"
    )
    search_parser.add_argument(
        "--platform", "-p",
        help="Filter by platform"
    )
    search_parser.add_argument(
        "--region", "-r",
        help="Filter by region"
    )
    search_parser.add_argument(
        "--year", "-y",
        type=int,
        help="Filter by year"
    )
    search_parser.add_argument(
        "--limit", "-n",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)"
    )
    search_parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table)"
    )
    search_parser.add_argument(
        "--download",
        action="store_true",
        help="Download all found ROMs"
    )
    
    # Download command
    download_parser = subparsers.add_parser(
        "download",
        help="Download ROMs"
    )
    download_parser.add_argument(
        "--id",
        type=str,
        help="ROM ID to download"
    )
    download_parser.add_argument(
        "--platform", "-p",
        help="Download all ROMs from platform"
    )
    download_parser.add_argument(
        "--region", "-r",
        help="Filter by region when downloading by platform"
    )
    download_parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available ROMs (use with caution!)"
    )
    download_parser.add_argument(
        "--no-boxart",
        action="store_true",
        help="Skip downloading box art"
    )
    download_parser.add_argument(
        "--output", "-o",
        help="Custom output directory"
    )
    
    # Info command
    info_parser = subparsers.add_parser(
        "info",
        help="Get ROM information"
    )
    info_parser.add_argument(
        "id",
        help="ROM ID"
    )
    info_parser.add_argument(
        "--format", "-f",
        choices=["table", "json", "yaml"],
        default="table",
        help="Output format (default: table)"
    )
    
    # Random command
    random_parser = subparsers.add_parser(
        "random",
        help="Get random ROMs"
    )
    random_parser.add_argument(
        "--platform", "-p",
        help="Filter by platform"
    )
    random_parser.add_argument(
        "--region", "-r",
        help="Filter by region"
    )
    random_parser.add_argument(
        "--count", "-n",
        type=int,
        default=5,
        help="Number of random ROMs (default: 5)"
    )
    random_parser.add_argument(
        "--download",
        action="store_true",
        help="Download the random ROMs"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration"
    )
    config_group = config_parser.add_mutually_exclusive_group(required=False)
    config_group.add_argument(
        "--get",
        help="Get configuration value"
    )
    config_group.add_argument(
        "--set",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Set configuration value"
    )
    config_group.add_argument(
        "--list",
        action="store_true",
        help="List all configuration values"
    )
    config_group.add_argument(
        "--reset",
        action="store_true",
        help="Reset configuration to defaults"
    )
    
    return parser

def initialize_application(args) -> tuple:
    """
    Initialize the application with core managers.
    
    Args:
        args: Parsed command line arguments
    
    Returns:
        Tuple of (config_manager, directory_manager, log_manager)
    """
    # Set working directory if specified
    if args.workdir:
        os.chdir(args.workdir)
    
    # Initialize directory manager
    directory_manager = DirectoryManager()
    
    # Initialize configuration manager
    config_manager = ConfigManager(args.config)
    
    # Override language if specified
    if args.language:
        config_manager.set("interface", "language", args.language)
    
    # Initialize internationalization
    from src.locales import get_i18n
    language = config_manager.get("interface", "language", "auto")
    # Always initialize with default fallback 'en_us'
    init_i18n(directory_manager.get_path('locales'), 'en_us')
    # If user/config specifies a fixed language (not auto), enforce it
    if language and language != 'auto':
        try:
            get_i18n().set_language(language)
        except Exception as e:
            logger.warning(f"Failed to set configured language '{language}', using auto/system detection. Error: {e}")
    
    # Initialize logging
    log_manager = LogManager(str(directory_manager.get_path('logs')))
    
    # Set debug/quiet modes
    if args.debug:
        log_manager.setup_logging(level="DEBUG")
        config_manager.set("logging", "level", "DEBUG")
    elif args.quiet:
        log_manager.setup_logging(level="ERROR", console_enabled=False)
        config_manager.set("logging", "console_enabled", False)
    
    # Log application start
    logger.info(f"CLI Download ROM iniciado - {get_version_string()}")
    
    return config_manager, directory_manager, log_manager

def main():
    """
    Main entry point of the application.
    """
    try:
        # Parse command line arguments
        parser = setup_argument_parser()
        args, unknown = parser.parse_known_args()
        
        # Initialize application
        config_manager, directory_manager, log_manager = initialize_application(args)
        
        # Check interface availability
        if args.interface == "tui" and not is_tui_available():
            print("Error: TUI interface not available. Install 'textual' package.")
            sys.exit(1)
        
        if args.interface == "gui" and not is_gui_available():
            print("Error: GUI interface not available. Install 'PyQt6' and 'pygame' packages.")
            sys.exit(1)
        
        # Create and run the appropriate interface
        if args.interface == "cli":
            # CLI mode - handle commands directly
            interface = CLIInterface(config_manager, directory_manager, log_manager)

            # Build argument list for CLIInterface
            cli_args = []
            if args.command == 'config':
                # Map main-level flags to CLI subcommands for compatibility
                if hasattr(args, 'list') and args.list:
                    cli_args = ['config', 'list']
                elif hasattr(args, 'reset') and args.reset:
                    cli_args = ['config', 'reset']
                elif hasattr(args, 'get') and args.get:
                    cli_args = ['config', 'get', args.get]
                elif hasattr(args, 'set') and args.set:
                    # args.set is [KEY, VALUE]
                    key_value = args.set if isinstance(args.set, (list, tuple)) else []
                    cli_args = ['config', 'set', *key_value]
                else:
                    # Support "config list" style captured as unknown
                    if unknown:
                        cli_args = ['config', *unknown]
                    else:
                        cli_args = ['config']
            else:
                # Prefer unknown tokens (e.g., "search ...", "download ...")
                if unknown:
                    cli_args = unknown
                elif args.command:
                    # Pass the command token if present; CLIInterface will show help if insufficient
                    cli_args = [args.command]
            
            if cli_args:
                exit_code = interface.run(cli_args)
                sys.exit(exit_code)
            else:
                # No command specified, show help for CLI interface
                interface.run(['-h'])
                sys.exit(0)
        
        elif args.interface == "shell":
            # Shell mode - interactive REPL
            interface = ShellInterface(config_manager, directory_manager, log_manager)
            interface.run()
        
        else:
            # TUI or GUI mode
            interface = create_interface(
                args.interface,
                config_manager,
                directory_manager,
                log_manager
            )
            interface.run()
    
    except KeyboardInterrupt:
        print("\n" + t("app.interrupted"))
        sys.exit(130)
    
    except Exception as e:
        print(f"Error: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()