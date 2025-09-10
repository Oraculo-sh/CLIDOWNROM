#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Shell Interface for CLI Download ROM.

This module implements an interactive shell (REPL) interface with advanced features
like command history, auto-completion, and contextual help.

Author: Leonne Martins
License: GPL-3.0
"""

import os
import sys
import shlex
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter, NestedCompleter
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.shortcuts import confirm
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
except ImportError:
    print("Error: prompt_toolkit is required for shell interface")
    print("Install with: pip install prompt-toolkit")
    sys.exit(1)

from ..core import DirectoryManager, ConfigManager, LogManager, SearchEngine, SearchFilter
from ..api import CrocDBClient
from ..download import DownloadManager
from ..locales import get_i18n, t
from ..utils import format_file_size, sanitize_filename
from .cli import CLIInterface


class ShellInterface:
    """
    Interactive Shell Interface for CLI Download ROM.
    
    Provides a REPL (Read-Eval-Print Loop) with advanced features like
    command history, auto-completion, and contextual help.
    """
    
    def __init__(self, config_manager: ConfigManager, directory_manager: DirectoryManager,
                 log_manager: LogManager):
        """
        Initialize the shell interface.
        
        Args:
            config_manager: Configuration manager instance
            directory_manager: Directory manager instance
            log_manager: Log manager instance
        """
        self.config = config_manager
        self.dirs = directory_manager
        self.logger = log_manager
        
        # Initialize CLI interface for command execution
        self.cli = CLIInterface(config_manager, directory_manager, log_manager)
        
        # Initialize API client
        api_config = self.config.get('api', {}) or {}
        self.api_client = CrocDBClient(
            base_url=api_config.get('base_url'),
            timeout=api_config.get('timeout', 30),
            max_retries=api_config.get('max_retries', 3)
        )
        
        # Initialize search engine
        self.search_engine = SearchEngine(self.api_client)
        
        # Initialize download manager
        self.download_manager = DownloadManager(
            self.dirs
        )
        
        # Shell state
        self.running = True
        self.current_search_results = []
        self.platforms_cache = None
        self.regions_cache = None
        
        # Setup prompt session
        self.session = self._create_prompt_session()
        
        # Command registry
        self.commands = self._register_commands()
    
    def _create_prompt_session(self) -> PromptSession:
        """
        Create and configure the prompt session.
        
        Returns:
            Configured PromptSession instance
        """
        # History file
        history_file = self.dirs.get_path('config') / 'shell_history.txt'
        # Ensure directory exists to avoid errors when FileHistory touches the file
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history = FileHistory(str(history_file))
        
        # Auto-completion
        completer = self._create_completer()
        
        # Style
        style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'path': '#888888',
            'error': '#ff0000 bold',
            'success': '#00aa00',
            'warning': '#ffaa00',
            'info': '#0088ff'
        })
        
        return PromptSession(
            history=history,
            completer=completer,
            complete_while_typing=True,
            style=style
        )
    
    def _create_completer(self) -> NestedCompleter:
        """
        Create auto-completion for shell commands.
        
        Returns:
            Configured NestedCompleter instance
        """
        # Base commands
        commands = {
            'search': None,
            'download': None,
            'info': None,
            'random': None,
            'config': {
                'get': None,
                'set': None,
                'list': None,
                'reset': None
            },
            'platforms': None,
            'regions': None,
            'history': None,
            'clear': None,
            'help': None,
            'exit': None,
            'quit': None
        }
        
        return NestedCompleter.from_nested_dict(commands)
    
    def _register_commands(self) -> Dict[str, Callable]:
        """
        Register shell commands.
        
        Returns:
            Dictionary mapping command names to functions
        """
        return {
            'search': self._cmd_search,
            'download': self._cmd_download,
            'info': self._cmd_info,
            'random': self._cmd_random,
            'config': self._cmd_config,
            'platforms': self._cmd_platforms,
            'regions': self._cmd_regions,
            'history': self._cmd_history,
            'clear': self._cmd_clear,
            'help': self._cmd_help,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit
        }
    
    def run(self) -> int:
        """
        Run the interactive shell.
        
        Returns:
            Exit code
        """
        try:
            self._print_welcome()
            
            while self.running:
                try:
                    # Get user input
                    prompt_text = HTML('<prompt>clidownrom</prompt> <path>></path> ')
                    user_input = self.session.prompt(prompt_text)
                    
                    # Skip empty input
                    if not user_input.strip():
                        continue
                    
                    # Parse and execute command
                    self._execute_command(user_input.strip())
                    
                except KeyboardInterrupt:
                    print("\n" + t('messages.press_enter'))
                    continue
                except EOFError:
                    break
            
            self._print_goodbye()
            return 0
            
        except Exception as e:
            self.logger.error(f"Shell error: {e}")
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def _execute_command(self, command_line: str) -> None:
        """
        Parse and execute a command line.
        
        Args:
            command_line: Raw command line input
        """
        try:
            # Parse command line
            parts = shlex.split(command_line)
            if not parts:
                return
            
            command = parts[0].lower()
            args = parts[1:]
            
            # Execute command
            if command in self.commands:
                self.commands[command](args)
            else:
                print(f"{t('errors.invalid_input')}: {command}")
                print(f"{t('help.usage')}: help")
                
        except ValueError as e:
            print(f"{t('errors.invalid_input')}: {e}")
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            self.logger.error(f"Command execution error: {e}")
    
    def _cmd_search(self, args: List[str]) -> None:
        """
        Execute search command.
        
        Args:
            args: Command arguments
        """
        if not args:
            print(f"{t('help.usage')}: search <query> [--platform <platform>] [--region <region>] [--limit <limit>]")
            return
        
        try:
            # Parse arguments
            query = args[0]
            platforms = []
            regions = []
            limit = 10
            
            i = 1
            while i < len(args):
                if args[i] == '--platform' or args[i] == '-p':
                    if i + 1 < len(args):
                        platforms.append(args[i + 1])
                        i += 2
                    else:
                        print(f"{t('errors.invalid_input')}: --platform requires a value")
                        return
                elif args[i] == '--region' or args[i] == '-r':
                    if i + 1 < len(args):
                        regions.append(args[i + 1])
                        i += 2
                    else:
                        print(f"{t('errors.invalid_input')}: --region requires a value")
                        return
                elif args[i] == '--limit' or args[i] == '-l':
                    if i + 1 < len(args):
                        try:
                            limit = int(args[i + 1])
                            i += 2
                        except ValueError:
                            print(f"{t('errors.invalid_input')}: --limit must be a number")
                            return
                    else:
                        print(f"{t('errors.invalid_input')}: --limit requires a value")
                        return
                else:
                    i += 1
            
            # Create search filter
            search_filter = SearchFilter(
                platforms=platforms,
                regions=regions
            )
            
            print(f"{t('search.searching')}...")
            
            # Perform search
            results = self.search_engine.search(
                query=query,
                search_filter=search_filter,
                limit=limit
            )
            
            if not results.entries:
                print(t('search.no_results'))
                self.current_search_results = []
                return
            
            # Store results for later use
            self.current_search_results = results.entries
            
            # Display results
            self._display_search_results(results.entries)
            
            print(f"\n{t('search.found.plural', count=len(results.entries))}")
            print(f"{t('help.usage')}: download <index> or download all")
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_download(self, args: List[str]) -> None:
        """
        Execute download command.
        
        Args:
            args: Command arguments
        """
        if not args:
            print(f"{t('help.usage')}: download <rom_id|index|all> [--no-boxart]")
            return
        
        try:
            target = args[0]
            no_boxart = '--no-boxart' in args
            
            roms_to_download = []
            
            if target.lower() == 'all':
                if not self.current_search_results:
                    print("No search results available. Use 'search' command first.")
                    return
                roms_to_download = self.current_search_results
            
            elif target.isdigit():
                # Check if it's an index from current results
                index = int(target)
                if 1 <= index <= len(self.current_search_results):
                    roms_to_download = [self.current_search_results[index - 1]]
                else:
                    # Try as ROM ID
                    rom_entry = self.api_client.get_rom(target)
                    if rom_entry:
                        roms_to_download = [rom_entry]
                    else:
                        print(f"{t('rom.not_found')}: {target}")
                        return
            
            else:
                print(f"{t('errors.invalid_input')}: {target}")
                return
            
            # Download ROMs
            successful_downloads = 0
            total_downloads = len(roms_to_download)
            
            if total_downloads > 1:
                if not confirm(f"Download {total_downloads} ROMs?"):
                    print(t('messages.cancelled'))
                    return
            
            for i, rom in enumerate(roms_to_download, 1):
                print(f"\n[{i}/{total_downloads}] {t('download.starting')}: {rom.title}")
                
                try:
                    result = self.download_manager.download_rom(
                        rom,
                        download_boxart=not no_boxart,
                        progress_callback=self._download_progress_callback
                    )
                    
                    if result.success:
                        print(f"\n{t('download.completed')}: {result.file_path}")
                        successful_downloads += 1
                    else:
                        print(f"\n{t('download.failed')}: {result.error}")
                        
                except Exception as e:
                    print(f"\n{t('download.failed')}: {e}")
            
            # Summary
            if total_downloads > 1:
                print(f"\n{t('download.multiple.completed', successful=successful_downloads, total=total_downloads)}")
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_info(self, args: List[str]) -> None:
        """
        Execute info command.
        
        Args:
            args: Command arguments
        """
        if not args:
            print(f"{t('help.usage')}: info <rom_id|index>")
            return
        
        try:
            target = args[0]
            rom_entry = None
            
            if target.isdigit():
                # Check if it's an index from current results
                index = int(target)
                if 1 <= index <= len(self.current_search_results):
                    rom_entry = self.current_search_results[index - 1]
                else:
                    # Try as ROM ID
                    rom_entry = self.api_client.get_rom(target)
            
            if not rom_entry:
                print(f"{t('rom.not_found')}: {target}")
                return
            
            self._display_rom_info(rom_entry)
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_random(self, args: List[str]) -> None:
        """
        Execute random command.
        
        Args:
            args: Command arguments
        """
        try:
            # Parse arguments
            platform = None
            region = None
            count = 5
            download = False
            
            i = 0
            while i < len(args):
                if args[i] == '--platform' or args[i] == '-p':
                    if i + 1 < len(args):
                        platform = args[i + 1]
                        i += 2
                    else:
                        print(f"{t('errors.invalid_input')}: --platform requires a value")
                        return
                elif args[i] == '--region' or args[i] == '-r':
                    if i + 1 < len(args):
                        region = args[i + 1]
                        i += 2
                    else:
                        print(f"{t('errors.invalid_input')}: --region requires a value")
                        return
                elif args[i] == '--count' or args[i] == '-c':
                    if i + 1 < len(args):
                        try:
                            count = int(args[i + 1])
                            i += 2
                        except ValueError:
                            print(f"{t('errors.invalid_input')}: --count must be a number")
                            return
                    else:
                        print(f"{t('errors.invalid_input')}: --count requires a value")
                        return
                elif args[i] == '--download' or args[i] == '-d':
                    download = True
                    i += 1
                else:
                    i += 1
            
            search_filter = SearchFilter(
                platforms=[platform] if platform else [],
                regions=[region] if region else []
            )
            
            print(f"{t('search.searching')}...")
            
            random_roms = self.search_engine.get_random_roms(
                count=count,
                search_filter=search_filter
            )
            
            if not random_roms:
                print(t('search.no_results'))
                return
            
            # Store results
            self.current_search_results = random_roms
            
            # Display random ROMs
            self._display_search_results(random_roms)
            
            # Download if requested
            if download:
                if confirm(f"Download {len(random_roms)} random ROMs?"):
                    self._cmd_download(['all'])
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_config(self, args: List[str]) -> None:
        """
        Execute config command.
        
        Args:
            args: Command arguments
        """
        if not args:
            print(f"{t('help.usage')}: config <get|set|list|reset> [key] [value]")
            return
        
        action = args[0].lower()
        
        try:
            if action == 'get':
                if len(args) < 2:
                    print(f"{t('help.usage')}: config get <key>")
                    return
                
                key = args[1]
                value = self.config.get(key)
                if value is not None:
                    print(f"{key}: {value}")
                else:
                    print(f"{t('config.invalid')}: {key}")
            
            elif action == 'set':
                if len(args) < 3:
                    print(f"{t('help.usage')}: config set <key> <value>")
                    return
                
                key = args[1]
                value = args[2]
                self.config.set(key, value)
                self.config.save_config()
                print(f"{t('config.saved')}: {key} = {value}")
            
            elif action == 'list':
                config_data = self.config.config
                self._display_config(config_data)
            
            elif action == 'reset':
                if confirm("Reset configuration to defaults?"):
                    self.config.reset_to_defaults()
                    self.config.save_config()
                    print(t('config.reset'))
            
            else:
                print(f"{t('errors.invalid_input')}: {action}")
                
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_platforms(self, args: List[str]) -> None:
        """
        List available platforms.
        
        Args:
            args: Command arguments
        """
        try:
            if not self.platforms_cache:
                print(f"{t('platforms.loading')}...")
                self.platforms_cache = self.search_engine.get_platforms()
            
            if self.platforms_cache:
                print(f"\n{t('platforms.available')}:")
                print("-" * 40)
                for platform in sorted(self.platforms_cache):
                    print(f"  {platform}")
                print(f"\nTotal: {len(self.platforms_cache)} platforms")
            else:
                print("No platforms available")
                
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_regions(self, args: List[str]) -> None:
        """
        List available regions.
        
        Args:
            args: Command arguments
        """
        try:
            if not self.regions_cache:
                print(f"{t('regions.loading')}...")
                self.regions_cache = self.search_engine.get_regions()
            
            if self.regions_cache:
                print(f"\n{t('regions.available')}:")
                print("-" * 40)
                for region in sorted(self.regions_cache):
                    print(f"  {region}")
                print(f"\nTotal: {len(self.regions_cache)} regions")
            else:
                print("No regions available")
                
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_history(self, args: List[str]) -> None:
        """
        Show command history.
        
        Args:
            args: Command arguments
        """
        try:
            history_file = self.dirs.get_path('config') / 'shell_history.txt'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Show last 20 commands by default
                limit = 20
                if args and args[0].isdigit():
                    limit = int(args[0])
                
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                print(f"\nCommand History (last {len(recent_lines)}):")
                print("-" * 40)
                for i, line in enumerate(recent_lines, 1):
                    print(f"{i:3d}: {line.strip()}")
            else:
                print("No command history available")
                
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_clear(self, args: List[str]) -> None:
        """
        Clear the screen.
        
        Args:
            args: Command arguments
        """
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _cmd_help(self, args: List[str]) -> None:
        """
        Show help information.
        
        Args:
            args: Command arguments
        """
        print(f"\n{t('app.name')} - {t('interface.shell')}")
        print("=" * 50)
        print(f"\n{t('help.commands')}:")
        print("  search <query> [options]    - Search for ROMs")
        print("  download <id|index|all>     - Download ROMs")
        print("  info <id|index>             - Show ROM information")
        print("  random [options]            - Get random ROMs")
        print("  config <action> [args]      - Manage configuration")
        print("  platforms                   - List available platforms")
        print("  regions                     - List available regions")
        print("  history [count]             - Show command history")
        print("  clear                       - Clear screen")
        print("  help                        - Show this help")
        print("  exit/quit                   - Exit shell")
        
        print(f"\n{t('help.examples')}:")
        print("  search \"Super Mario\" --platform snes")
        print("  download 1")
        print("  download all --no-boxart")
        print("  random --platform nes --count 3 --download")
        print("  config set download.max_concurrent 4")
        
        print("\nTips:")
        print("  - Use Tab for auto-completion")
        print("  - Use Up/Down arrows for command history")
        print("  - Use Ctrl+C to cancel current operation")
        print("  - Use Ctrl+D or 'exit' to quit")
    
    def _cmd_exit(self, args: List[str]) -> None:
        """
        Exit the shell.
        
        Args:
            args: Command arguments
        """
        self.running = False
    
    def _display_search_results(self, results: List) -> None:
        """
        Display search results in a formatted table.
        
        Args:
            results: List of ROM entries
        """
        print(f"\n{'#':<3} {'Title':<40} {'Platform':<15} {'Region':<8} {'Year':<6} {'Size':<10}")
        print("-" * 90)
        
        for i, rom in enumerate(results, 1):
            title = rom.title[:37] + "..." if len(rom.title) > 40 else rom.title
            platform = rom.platform[:12] + "..." if len(rom.platform) > 15 else rom.platform
            size_str = format_file_size(rom.size) if rom.size else 'N/A'
            year_str = str(rom.year) if rom.year else 'N/A'
            
            print(f"{i:<3} {title:<40} {platform:<15} {rom.region:<8} {year_str:<6} {size_str:<10}")
    
    def _display_rom_info(self, rom) -> None:
        """
        Display detailed ROM information.
        
        Args:
            rom: ROM entry
        """
        print(f"\n{t('rom.info')}:")
        print("=" * 50)
        print(f"{t('rom.title')}: {rom.title}")
        print(f"ID: {rom.slug}")
        print(f"{t('rom.platform')}: {rom.platform}")
        region_str = rom.regions[0] if rom.regions else 'N/A'
        print(f"{t('rom.region')}: {region_str}")
        if hasattr(rom, 'year') and rom.year:
            print(f"{t('rom.year')}: {rom.year}")
        size_mb = rom.get_size_mb()
        if size_mb > 0:
            print(f"{t('rom.size')}: {size_mb:.1f} MB")
        if rom.description:
            print(f"{t('rom.description')}: {rom.description}")
        if rom.download_links:
            print(f"{t('rom.links')}: {len(rom.download_links)} available")
        if rom.boxart_url:
            print(f"{t('rom.boxart')}: Available")
    
    def _display_config(self, config_data: Dict[str, Any], prefix: str = "") -> None:
        """
        Display configuration data recursively.
        
        Args:
            config_data: Configuration dictionary
            prefix: Key prefix for nested values
        """
        for key, value in config_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._display_config(value, full_key)
            else:
                print(f"{full_key}: {value}")
    
    def _download_progress_callback(self, progress) -> None:
        """
        Callback for download progress updates.
        
        Args:
            progress: DownloadProgress instance
        """
        if progress.total_size > 0:
            percentage = (progress.downloaded_size / progress.total_size) * 100
            bar_length = 30
            filled_length = int(bar_length * progress.downloaded_size // progress.total_size)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            
            speed_str = f"{format_file_size(progress.speed)}/s" if progress.speed else "N/A"
            eta_str = f"{progress.eta}s" if progress.eta else "N/A"
            
            print(f"\r[{bar}] {percentage:.1f}% | {format_file_size(progress.downloaded_size)}/{format_file_size(progress.total_size)} | {speed_str} | ETA: {eta_str}", end='', flush=True)
        else:
            print(f"\r{t('download.progress')}: {format_file_size(progress.downloaded_size)}", end='', flush=True)
    
    def _print_welcome(self) -> None:
        """
        Print welcome message.
        """
        print(f"\n{t('messages.welcome')}")
        print(f"{t('app.name')} - {t('interface.shell')}")
        print("=" * 50)
        print(f"Type 'help' for available commands.")
        print(f"Type 'exit' or press Ctrl+D to quit.\n")
    
    def _print_goodbye(self) -> None:
        """
        Print goodbye message.
        """
        print(f"\n{t('messages.goodbye')}")