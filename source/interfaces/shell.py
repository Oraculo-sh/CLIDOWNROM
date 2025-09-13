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
import asyncio
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

from loguru import logger
from ..core import DirectoryManager, ConfigManager, LogManager, SearchEngine, SearchFilter
from ..core.crocdb_client import CrocDBClient
from ..core import DownloadManager
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
            self.dirs,
            max_concurrent=self.config.get('download', {}).get('max_concurrent', 4),
            chunk_size=self.config.get('download', {}).get('chunk_size', 8192),
            timeout=self.config.get('download', {}).get('timeout', 300),
            max_retries=self.config.get('api', {}).get('max_retries', 3),
            verify_downloads=self.config.get('download', {}).get('verify_downloads', True),
        )
        pref_hosts = self.config.get('download', {}).get('preferred_hosts', []) or []
        if pref_hosts:
            self.download_manager.set_preferred_hosts(pref_hosts)
        
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
        # History file now goes to TEMP folder
        history_file = self.dirs.get_path('temp') / 'shell_history.txt'
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
                'save': None,
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
        Register available commands and their handlers.
        
        Returns:
            Dictionary mapping command names to handler functions
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
        Run the interactive shell loop.
        
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        self._print_welcome()
        
        try:
            while self.running:
                try:
                    # Show prompt with current path
                    cwd = os.getcwd()
                    prompt_text = HTML(f"<prompt>{t('app.name')}</prompt> <path>{cwd}</path> > ")
                    command_line = self.session.prompt(prompt_text)
                    self._execute_command(command_line)
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
            # Audit log of typed command
            logger.info(f"[SHELL] command entered: {command_line}")
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
        try:
            # Defaults from config
            search_conf = self.config.get('search', {}) or {}
            per_page = int(search_conf.get('results_per_page', 10))
            max_results = int(search_conf.get('max_results', 100))

            # Parse keywords until first flag starting with '-'
            keywords: List[str] = []
            platforms: List[str] = []
            regions: List[str] = []
            year: Optional[int] = None

            i = 0
            while i < len(args) and not args[i].startswith('-'):
                keywords.append(args[i])
                i += 1

            # Parse remaining flags
            while i < len(args):
                token = args[i]
                if token in ('--platform', '-p'):
                    if i + 1 < len(args):
                        platforms.append(args[i + 1])
                        i += 2
                    else:
                        print(f"{t('errors.invalid_input')}: --platform requires a value")
                        return
                elif token in ('--region', '-r'):
                    if i + 1 < len(args):
                        regions.append(args[i + 1])
                        i += 2
                    else:
                        print(f"{t('errors.invalid_input')}: --region requires a value")
                        return
                elif token in ('--limit', '-l'):
                    if i + 1 < len(args):
                        try:
                            max_results = int(args[i + 1])
                            i += 2
                        except ValueError:
                            print(f"{t('errors.invalid_input')}: --limit must be a number")
                            return
                    else:
                        print(f"{t('errors.invalid_input')}: --limit requires a value")
                        return
                elif token in ('--per-page', '-pp'):
                    if i + 1 < len(args):
                        try:
                            per_page = int(args[i + 1])
                            i += 2
                        except ValueError:
                            print(f"{t('errors.invalid_input')}: --per-page must be a number")
                            return
                    else:
                        print(f"{t('errors.invalid_input')}: --per-page requires a value")
                        return
                elif token in ('--year', '-y'):
                    if i + 1 < len(args):
                        try:
                            year = int(args[i + 1])
                            i += 2
                        except ValueError:
                            print(f"{t('errors.invalid_input')}: --year must be a number")
                            return
                    else:
                        print(f"{t('errors.invalid_input')}: --year requires a value")
                        return
                else:
                    # Unknown token, skip
                    i += 1

            if not keywords:
                print(f"{t('help.usage')}: search <keywords...> [--platform <platform>] [--region <region>] [--limit <limit>] [--per-page <n>]")
                return

            query = " ".join(keywords).strip()

            search_filter = SearchFilter(
                platforms=platforms or None,
                regions=regions or None,
                year_min=year if year is not None else None,
                year_max=year if year is not None else None,
            )
            
            print(f"{t('search.searching')}...")

            # Reset cache for a new search
            self.current_search_results = []  # type: List

            page = 1
            user_quit = False
            while True:
                paged = self.search_engine.search_paged_sync(
                    query=query,
                    search_filter=search_filter,
                    page=page,
                    per_page=per_page,
                    max_results=max_results,
                )

                # If no results at all
                if page == 1 and (not paged.items or paged.total == 0):
                    print(t('search.no_results'))
                    self.current_search_results = []
                    return

                # Update cache with ROM entries at their absolute positions
                start_idx = (page - 1) * per_page
                for j, s in enumerate(paged.items, start=start_idx):
                    rom_entry = getattr(s, 'rom_entry', s)
                    if j < len(self.current_search_results):
                        self.current_search_results[j] = rom_entry
                    else:
                        self.current_search_results.append(rom_entry)

                # Display current page with continuous numbering
                self._display_search_results(items=paged.items, total=paged.total, page=page, per_page=per_page)

                # Prompt de ação combinado: seleção por índices ou navegação
                start_num = (page - 1) * per_page + 1
                end_num = min(paged.total, page * per_page)
                action_prompt = "> Digite o(s) número(s) referentes as roms para baixar (separados por vírgula), ou [n] próxima pág, [p] pág anterior, [0] cancelar, [q] sair: "
                sys.stdout.write(action_prompt)
                sys.stdout.flush()
                choice = sys.stdin.readline()
                if not choice:
                    break
                choice = choice.strip().lower()

                # Navegação
                if choice in ('n', 'p', 'q', '0'):
                    if choice == 'n' and paged.has_next:
                        page += 1
                        continue
                    elif choice == 'p' and paged.has_prev:
                        page = max(1, page - 1)
                        continue
                    elif choice in ('q', '0'):
                        user_quit = True
                        break
                    else:
                        print("Opção inválida nesta página.")
                        continue

                # Seleção por índices
                tokens = [tok.strip() for tok in choice.replace(' ', '').split(',') if tok.strip()]
                if not tokens or any(not tok.isdigit() for tok in tokens):
                    print("Entrada inválida. Use números separados por vírgula (ex.: 1,3,5) ou comandos [n],[p],[0],[q].")
                    continue

                indices = [int(tok) for tok in tokens]
                invalid = [idx for idx in indices if idx < start_num or idx > end_num]
                if invalid:
                    print(f"Índices fora do intervalo da página atual: {invalid}. Intervalo: {start_num}-{end_num}.")
                    continue

                seen = set()
                unique_indices = []
                for idx in indices:
                    if idx not in seen:
                        seen.add(idx)
                        unique_indices.append(idx)

                # Efetuar downloads via comando 'download' para cada índice
                for idx in unique_indices:
                    self._cmd_download([str(idx)])
                return

            # If user chose to quit navigation, do not proceed to download prompt
            if user_quit:
                return

            # Prompt for download selection by indices
            if not self.current_search_results:
                return

            while True:
                try:
                    print("\nQuais ROMs deseja baixar? Digite os números separados por vírgula (ou 0 para cancelar): ", end='')
                    sys.stdout.flush()
                    selection_line = sys.stdin.readline()
                    if not selection_line:
                        # EOF or no input => cancel
                        print(t('messages.cancel'))
                        return
                    selection_line = selection_line.strip()

                    if selection_line == '0' or selection_line.lower() in ('q', 'cancelar', 'cancel'):
                        print(t('messages.cancel'))
                        return

                    # Remove spaces before splitting by comma
                    tokens = [tok.strip() for tok in selection_line.replace(' ', '').split(',') if tok.strip()]
                    if not tokens:
                        print(f"{t('errors.invalid_input')}: entrada vazia. Tente novamente ou digite 0 para cancelar.")
                        continue

                    # Validate tokens are digits
                    if any(not tok.isdigit() for tok in tokens):
                        print(f"{t('errors.invalid_input')}: use apenas números separados por vírgula. Ex: 1,3,5")
                        continue

                    indices = [int(tok) for tok in tokens]
                    # Validate ranges
                    invalid = [idx for idx in indices if idx < 1 or idx > len(self.current_search_results)]
                    if invalid:
                        print(f"{t('errors.invalid_input')}: índices fora do intervalo: {invalid}. Total de resultados: {len(self.current_search_results)}")
                        continue

                    # Deduplicate preserving order
                    seen = set()
                    unique_indices = []
                    for idx in indices:
                        if idx not in seen:
                            seen.add(idx)
                            unique_indices.append(idx)

                    # Build selection
                    selected_roms = [self.current_search_results[idx - 1] for idx in unique_indices]

                    # Show selected
                    print("\nROMs selecionadas:")
                    for idx in unique_indices:
                        rom = self.current_search_results[idx - 1]
                        platform = getattr(rom, 'platform', '') or ''
                        print(f"  {idx}. {getattr(rom, 'title', '')} [{platform}]")

                    # Confirm
                    sys.stdout.write("\nConfirmar download? [s] Sim, [c] Corrigir, [0] Cancelar > ")
                    sys.stdout.flush()
                    confirm_choice = sys.stdin.readline().strip().lower()
                    if confirm_choice in ('0', 'q', 'n', 'nao', 'não', 'cancel', 'cancelar'):
                        print(t('messages.cancel'))
                        return
                    if confirm_choice in ('c', 'corrigir', 'edit', 'e'):
                        # Loop back to re-enter numbers
                        continue
                    if confirm_choice not in ('s', 'sim', 'y', 'yes'):
                        # Unrecognized => re-enter
                        print(f"{t('errors.invalid_input')}: opção inválida. Digite 's' para confirmar, 'c' para corrigir ou '0' para cancelar.")
                        continue

                    # Start downloads sequentially
                    successful_downloads = 0
                    total_downloads = len(selected_roms)

                    for i, rom in enumerate(selected_roms, 1):
                        print(f"\n[{i}/{total_downloads}] {t('download.starting')}: {getattr(rom, 'title', '')}")
                        try:
                            result = asyncio.run(
                                self.download_manager.download_rom(
                                    rom,
                                    download_boxart=True
                                )
                            )

                            if result.success:
                                print(f"\n{t('download.completed')}: {result.final_path}")
                                successful_downloads += 1
                            else:
                                print(f"\n{t('download.failed')}: {result.error}")
                        except Exception as e:
                            print(f"\n{t('download.failed')}: {e}")

                    if total_downloads > 1:
                        print(f"\n{t('download.multiple.completed', successful=successful_downloads, total=total_downloads)}")
                    return
                except KeyboardInterrupt:
                    print(f"\n{t('messages.cancel')}")
                    return
                except Exception as e:
                    print(f"{t('errors.general')}: {e}")
        except Exception as e:
            print(f"{t('errors.general')}: {e}")

    def _cmd_download(self, args: List[str]) -> None:
        """
        Download ROM(s) based on last search results or ROM ID.
        
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
                index = int(target)
                if 1 <= index <= len(self.current_search_results):
                    roms_to_download = [self.current_search_results[index - 1]]
                else:
                    print(f"{t('errors.invalid_input')}: {target}")
                    return
            else:
                # Assume ROM ID
                rom_entry = self.api_client.get_entry(target)
                if rom_entry:
                    roms_to_download = [rom_entry]
                else:
                    print(f"{t('rom.not_found')}: {target}")
                    return
            
            successful_downloads = 0
            total_downloads = len(roms_to_download)
            
            if total_downloads > 1:
                if not confirm(f"Download {total_downloads} ROMs?"):
                    print(t('messages.cancel'))
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
                        print(f"\n{t('download.completed')}: {result.final_path}")
                        successful_downloads += 1
                    else:
                        print(f"\n{t('download.failed')}: {result.error}")
                        
                except Exception as e:
                    print(f"\n{t('download.failed')}: {e}")
            
            if total_downloads > 1:
                print(f"\n{t('download.multiple.completed', successful=successful_downloads, total=total_downloads)}")
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_info(self, args: List[str]) -> None:
        """
        Show ROM information by ID or index from last search.
        
        Args:
            args: Command arguments
        """
        if not args:
            print(f"{t('help.usage')}: info <rom_id|index>")
            return
        
        try:
            target = args[0]
            
            if target.isdigit():
                index = int(target)
                if 1 <= index <= len(self.current_search_results):
                    rom = self.current_search_results[index - 1]
                    self._display_rom_info(rom)
                else:
                    print(f"{t('errors.invalid_input')}: {target}")
                return
            
            rom = self.api_client.get_entry(target)
            if rom:
                self._display_rom_info(rom)
            else:
                print(f"{t('rom.not_found')}: {target}")
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_random(self, args: List[str]) -> None:
        """
        Get random ROM(s) based on optional filters.
        
        Args:
            args: Command arguments
        """
        try:
            count = 1
            platforms = []
            regions = []
            
            if args:
                i = 0
                while i < len(args):
                    if args[i] == '--count' or args[i] == '-n':
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
                    elif args[i] == '--platform' or args[i] == '-p':
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
                    else:
                        i += 1
            
            print(t('search.searching'))
            # Build filter and use sync random wrapper
            search_filter = SearchFilter(platforms=platforms, regions=regions)
            results = self.search_engine.get_random_roms_sync(count=count, search_filter=search_filter)
            
            if not results:
                print(t('search.no_results'))
                return
            
            # Optionally cache these as the current results for follow-up commands
            self.current_search_results = results
            
            self._display_search_results(results)
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
    
    def _cmd_config(self, args: List[str]) -> None:
        """
        Manage configuration values.
        
        Args:
            args: Command arguments
        """
        if not args:
            print(f"{t('help.usage')}: config <get|set|save|reset> [args]")
            return
        
        try:
            action = args[0].lower()
            
            if action == 'get':
                if len(args) < 2:
                    print(f"{t('help.usage')}: config get <section.key>")
                    return
                key = args[1]
                value = self.config.get(key, None)
                print(f"{key} = {value}")
                
            elif action == 'set':
                if len(args) < 3:
                    print(f"{t('help.usage')}: config set <section.key> <value>")
                    return
                key = args[1]
                value = args[2]
                # Tenta converter números automaticamente
                if value.isdigit():
                    value = int(value)
                self.config.set(key, value)
                print(t('config.saved'))
                
            elif action == 'save':
                if self.config.save_config():
                    print(t('config.saved'))
                else:
                    print(t('errors.config_error'))
                
            elif action == 'reset':
                if self.config.create_default_config():
                    print(t('config.reset'))
                else:
                    print(t('errors.config_error'))
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
            if self.platforms_cache is None:
                print(f"{t('platforms.loading')}...")
                self.platforms_cache = self.search_engine.get_platforms_sync()
            
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
            if self.regions_cache is None:
                print(f"{t('regions.loading')}...")
                self.regions_cache = self.search_engine.get_regions_sync()
            
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
            history_file = self.dirs.get_path('temp') / 'shell_history.txt'
            if not history_file.exists():
                print("No command history available")
                return
            
            # Default: show last 20 commands
            num = 20
            if args and len(args) > 0:
                try:
                    num = int(args[0])
                except ValueError:
                    print(f"{t('errors.invalid_input')}: {args[0]}")
                    return
            
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Show last N entries
            for line in lines[-num:]:
                print(line.strip())
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            self.logger.error(f"History error: {e}")
    
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
        
        print("\nOptions for 'search':")
        print("  --platform, -p <code>       - Filter by platform (e.g., nes, snes, n64)")
        print("  --region, -r <code>         - Filter by region (e.g., usa, eur, jpn)")
        print("  --limit, -l <num>           - Max results (default from config)")
        print("  --per-page, -pp <num>       - Results per page (default from config)")
        print("  --year, -y <year|range>     - Filter by year (e.g., 1995 or 1990-1999)")
        print("  --no-score                  - Hide similarity score column")
        
        print("\nNavigation in search results:")
        print("  n / next    - Next page")
        print("  p / prev    - Previous page")
        print("  q / quit    - Exit results view")
        print("  1,3,5       - Select indices to download (comma-separated)")
        
        print("\nOptions for 'random':")
        print("  --count, -n <num>           - Number of ROMs to return (default: 1)")
        print("  --platform, -p <code>       - Filter by platform code (e.g., nes, snes, n64)")
        print("  --region, -r <code>         - Filter by region code (e.g., usa, eur, jpn)")
        
        print(f"\n{t('help.examples')}:")
        print('  search "Super Mario" --platform snes --per-page 10')
        print("  download 1")
        print("  download all --no-boxart")
        print("  random --platform nes --count 3")
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
    
    def _display_search_results(self, results: List = None, *, items: List = None, total: Optional[int] = None, page: int = 1, per_page: int = 10) -> None:
        """
        Display search results in a formatted way.
        
        Supports two call modes:
        - Legacy: _display_search_results(results=[ROMEntry])
        - Paged:  _display_search_results(items=[ROMScore|ROMEntry], total=int, page=int, per_page=int)
        """
        try:
            # Determine mode and normalize list of tuples (rom_entry, score or None)
            entries: List = []
            start_num = 1
            end_num = 0
            show_scores = False

            if items is not None:
                # Paged mode
                if not items:
                    print(t('search.no_results'))
                    return
                start_num = (page - 1) * per_page + 1
                # Normalize each item
                norm = []
                for it in items:
                    if hasattr(it, 'rom_entry'):
                        norm.append((it.rom_entry, getattr(it, 'total_score', None)))
                    else:
                        norm.append((it, None))
                entries = norm
                end_num = min(total or len(entries), start_num + len(entries) - 1)
                show_scores = any(score is not None for _, score in entries)
            else:
                # Legacy mode
                if not results:
                    print(t('search.no_results'))
                    return
                entries = [(rom, None) for rom in results]
                total = len(entries)
                end_num = total
                show_scores = False

            # Header
            if total is None:
                total = len(entries)
            print()
            total_pages = max(1, (total + per_page - 1) // per_page)
            print(f"Resultados {start_num}-{end_num} de {total} (Página {page} de {total_pages})")
            # Column widths
            w_idx = 3
            w_title = 40
            w_id = 14
            w_platform = 12
            w_regions = 12
            w_hosts = 16
            w_format = 8
            w_size = 10
            
            if show_scores:
                header = (
                    f"#".rjust(w_idx) + " " +
                    "Título".ljust(w_title) + " " +
                    "ID".ljust(w_id) + " " +
                    "Platform".ljust(w_platform) + " " +
                    "Regions".ljust(w_regions) + " " +
                    "Hosts".ljust(w_hosts) + " " +
                    "Format".ljust(w_format) + " " +
                    "Size".rjust(w_size) + " " +
                    "Score"
                )
                sep = (
                    "-" * w_idx + " " +
                    "-" * w_title + " " +
                    "-" * w_id + " " +
                    "-" * w_platform + " " +
                    "-" * w_regions + " " +
                    "-" * w_hosts + " " +
                    "-" * w_format + " " +
                    "-" * w_size + " " +
                    "-" * 5
                )
            else:
                header = (
                    f"#".rjust(w_idx) + " " +
                    "Título".ljust(w_title) + " " +
                    "ID".ljust(w_id) + " " +
                    "Platform".ljust(w_platform) + " " +
                    "Regions".ljust(w_regions) + " " +
                    "Hosts".ljust(w_hosts) + " " +
                    "Format".ljust(w_format) + " " +
                    "Size".rjust(w_size)
                )
                sep = (
                    "-" * w_idx + " " +
                    "-" * w_title + " " +
                    "-" * w_id + " " +
                    "-" * w_platform + " " +
                    "-" * w_regions + " " +
                    "-" * w_hosts + " " +
                    "-" * w_format + " " +
                    "-" * w_size
                )
            print(header)
            print(sep)

            # Rows
            for idx_offset, (rom, score) in enumerate(entries):
                idx = start_num + idx_offset
                title = (getattr(rom, 'title', '') or '')
                title = (title[:w_title-2] + '…') if len(title) > w_title else title
                title = title.ljust(w_title)
                platform = (getattr(rom, 'platform', '') or '')[:w_platform].ljust(w_platform)

                # Regions list or single region
                regions_val = getattr(rom, 'regions', None)
                if not regions_val:
                    region_single = getattr(rom, 'region', None)
                    if region_single:
                        regions_val = [region_single]
                regions_str = ",".join(regions_val or [])
                regions_str = (regions_str[:w_regions-1] + '…') if len(regions_str) > w_regions else regions_str
                regions_str = regions_str.ljust(w_regions)

                # ID (slug preferred)
                rom_id = getattr(rom, 'slug', None) or getattr(rom, 'rom_id', '') or ''
                rom_id_disp = (str(rom_id)[:w_id-1] + '…') if len(str(rom_id)) > w_id else str(rom_id)
                rom_id_disp = rom_id_disp.ljust(w_id)

                # Hosts
                hosts = getattr(rom, 'hosts', '') or ''
                hosts_disp = (hosts[:w_hosts-1] + '…') if len(hosts) > w_hosts else hosts
                hosts_disp = hosts_disp.ljust(w_hosts)

                # Format
                fmt = getattr(rom, 'file_format', '') or ''
                fmt_disp = (fmt[:w_format-1] + '…') if len(fmt) > w_format else fmt
                fmt_disp = fmt_disp.ljust(w_format)

                # Size
                size_val = getattr(rom, 'size', 0) or 0
                size_disp = format_file_size(size_val).rjust(w_size)

                if show_scores:
                    score_str = f"{(score if score is not None else 0):>6.3f}"
                    print(
                        f"{str(idx).rjust(w_idx)} "
                        f"{title} {rom_id_disp} {platform} {regions_str} {hosts_disp} {fmt_disp} {size_disp} {score_str}"
                    )
                else:
                    print(
                        f"{str(idx).rjust(w_idx)} "
                        f"{title} {rom_id_disp} {platform} {regions_str} {hosts_disp} {fmt_disp} {size_disp}"
                    )

            if end_num >= (total or 0):
                print("-- Fim dos resultados --")
        except Exception as e:
            # Fallback to very simple listing if something goes wrong
            try:
                if results:
                    for i, rom in enumerate(results, 1):
                        print(f"{i:3d}. {getattr(rom, 'title', '')}")
                elif items:
                    for i, it in enumerate(items, 1):
                        rom = getattr(it, 'rom_entry', it)
                        print(f"{i:3d}. {getattr(rom, 'title', '')}")
            except Exception:
                pass
    
    def _display_rom_info(self, rom) -> None:
        """
        Display detailed information about a ROM.
        
        Args:
            rom: ROM entry
        """
        print("\n" + t('rom.info'))
        print("=" * 40)
        print(f"{t('rom.title')}: {rom.title}")
        print(f"{t('rom.platform')}: {rom.platform}")
        print(f"{t('rom.region')}: {rom.region}")
        print(f"{t('rom.year')}: {rom.year}")
        print(f"{t('rom.size')}: {format_file_size(rom.size)}")
        # Extras conforme modelo
        try:
            hosts = getattr(rom, 'hosts', '')
            file_format = getattr(rom, 'file_format', '')
            if hosts:
                print(f"Hosts: {hosts}")
            if file_format:
                print(f"Format: {file_format}")
        except Exception:
            pass
        print(f"{t('rom.description')}: {rom.description}")
        
    def _display_config(self, config_data: Dict[str, Any], prefix: str = "") -> None:
        """
        Display configuration values.
        
        Args:
            config_data: Configuration dictionary
            prefix: Prefix for nested keys
        """
        for key, value in config_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                self._display_config(value, full_key)
            else:
                print(f"{full_key}: {value}")
    
    def _download_progress_callback(self, progress) -> None:
        """
        Handle download progress updates.
        
        Args:
            progress: Progress information
        """
        try:
            percent = int(progress.percentage)
            bar_length = 20
            filled_length = int(bar_length * percent // 100)
            bar = '#' * filled_length + '-' * (bar_length - filled_length)
            status = f"{percent}%"
            print(f"\r[{bar}] {status}", end='')
            if percent >= 100:
                print()
        except Exception:
            pass
    
    def _print_welcome(self) -> None:
        """
        Print the welcome message when shell starts.
        """
        print(f"\n{t('messages.welcome')}")
    
    def _print_goodbye(self) -> None:
        """
        Print the goodbye message when shell exits.
        """
        print(f"\n{t('messages.goodbye')}")