#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Interface for CLI Download ROM.

This module implements the command-line interface (CLI) for the application.
It provides a non-interactive mode suitable for scripts and automation.

Author: Leonne Martins
License: GPL-3.0
"""

import argparse
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..core import DirectoryManager, ConfigManager, LogManager, SearchEngine, SearchFilter
from ..api import CrocDBClient
from ..download import DownloadManager
from ..locales import get_i18n, t
from ..utils import format_file_size, sanitize_filename


class CLIInterface:
    """
    Command Line Interface for CLI Download ROM.
    
    Provides a non-interactive interface suitable for automation and scripting.
    """
    
    def __init__(self, config_manager: ConfigManager, directory_manager: DirectoryManager,
                 log_manager: LogManager):
        """
        Initialize the CLI interface.
        
        Args:
            config_manager: Configuration manager instance
            directory_manager: Directory manager instance
            log_manager: Log manager instance
        """
        self.config = config_manager
        self.dirs = directory_manager
        self.logger = log_manager
        
        # Initialize API client
        api_config = self.config.get('api', {})
        self.api_client = CrocDBClient(
            base_url=api_config.get('base_url'),
            timeout=api_config.get('timeout', 30),
            max_retries=api_config.get('max_retries', 3)
        )
        
        # Initialize search engine
        self.search_engine = SearchEngine(self.api_client, self.config)
        
        # Initialize download manager
        self.download_manager = DownloadManager(
            self.config, self.dirs, self.logger
        )
        
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        Create the argument parser for CLI commands.
        
        Returns:
            Configured ArgumentParser instance
        """
        parser = argparse.ArgumentParser(
            prog='clidownrom',
            description=t('app.description'),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument(
            '--version', '-v',
            action='version',
            version=f"CLI Download ROM {self.config.get('app.version', '1.0.0')}"
        )
        
        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Path to configuration file'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress output except errors'
        )
        
        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Search command
        search_parser = subparsers.add_parser(
            'search',
            help=t('commands.search'),
            description='Search for ROMs in the CrocDB database'
        )
        search_parser.add_argument(
            'query',
            type=str,
            help='Search query (game title)'
        )
        search_parser.add_argument(
            '--platform', '-p',
            type=str,
            action='append',
            help='Filter by platform (can be used multiple times)'
        )
        search_parser.add_argument(
            '--region', '-r',
            type=str,
            action='append',
            help='Filter by region (can be used multiple times)'
        )
        search_parser.add_argument(
            '--year',
            type=int,
            help='Filter by year'
        )
        search_parser.add_argument(
            '--limit', '-l',
            type=int,
            default=10,
            help='Maximum number of results (default: 10)'
        )
        search_parser.add_argument(
            '--format', '-f',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format (default: table)'
        )
        
        # Download command
        download_parser = subparsers.add_parser(
            'download',
            help=t('commands.download'),
            description='Download ROMs by ID or search query'
        )
        download_parser.add_argument(
            'target',
            type=str,
            help='ROM ID or search query'
        )
        download_parser.add_argument(
            '--platform', '-p',
            type=str,
            help='Platform filter (when using search query)'
        )
        download_parser.add_argument(
            '--region', '-r',
            type=str,
            help='Region filter (when using search query)'
        )
        download_parser.add_argument(
            '--all', '-a',
            action='store_true',
            help='Download all search results'
        )
        download_parser.add_argument(
            '--no-boxart',
            action='store_true',
            help='Skip downloading box art'
        )
        download_parser.add_argument(
            '--output', '-o',
            type=str,
            help='Custom output directory'
        )
        
        # Info command
        info_parser = subparsers.add_parser(
            'info',
            help=t('commands.info'),
            description='Show detailed information about a ROM'
        )
        info_parser.add_argument(
            'rom_id',
            type=str,
            help='ROM ID'
        )
        info_parser.add_argument(
            '--format', '-f',
            choices=['table', 'json'],
            default='table',
            help='Output format (default: table)'
        )
        
        # Random command
        random_parser = subparsers.add_parser(
            'random',
            help=t('commands.random'),
            description='Get random ROMs'
        )
        random_parser.add_argument(
            '--platform', '-p',
            type=str,
            help='Filter by platform'
        )
        random_parser.add_argument(
            '--region', '-r',
            type=str,
            help='Filter by region'
        )
        random_parser.add_argument(
            '--count', '-c',
            type=int,
            default=5,
            help='Number of random ROMs (default: 5)'
        )
        random_parser.add_argument(
            '--download', '-d',
            action='store_true',
            help='Download the random ROMs'
        )
        
        # Config command
        config_parser = subparsers.add_parser(
            'config',
            help=t('commands.config'),
            description='Manage application configuration'
        )
        config_subparsers = config_parser.add_subparsers(
            dest='config_action',
            help='Configuration actions'
        )
        
        # Config get
        config_get = config_subparsers.add_parser(
            'get',
            help='Get configuration value'
        )
        config_get.add_argument(
            'key',
            type=str,
            help='Configuration key'
        )
        
        # Config set
        config_set = config_subparsers.add_parser(
            'set',
            help='Set configuration value'
        )
        config_set.add_argument(
            'key',
            type=str,
            help='Configuration key'
        )
        config_set.add_argument(
            'value',
            type=str,
            help='Configuration value'
        )
        
        # Config list
        config_subparsers.add_parser(
            'list',
            help='List all configuration values'
        )
        
        # Config reset
        config_subparsers.add_parser(
            'reset',
            help='Reset configuration to defaults'
        )
        
        return parser
    
    def run(self, args: List[str]) -> int:
        """
        Run the CLI interface with the given arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Set logging level based on verbosity
            if parsed_args.quiet:
                self.logger.set_level('ERROR')
            elif parsed_args.verbose:
                self.logger.set_level('DEBUG')
            
            # Load custom config if specified
            if parsed_args.config:
                self.config.load_config(Path(parsed_args.config))
            
            # Execute command
            if not parsed_args.command:
                self.parser.print_help()
                return 1
            
            return self._execute_command(parsed_args)
            
        except KeyboardInterrupt:
            print(f"\n{t('messages.cancelled')}")
            return 130
        except Exception as e:
            self.logger.error(f"CLI error: {e}")
            if parsed_args.verbose if 'parsed_args' in locals() else False:
                import traceback
                traceback.print_exc()
            return 1
    
    def _execute_command(self, args: argparse.Namespace) -> int:
        """
        Execute the specified command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        command_map = {
            'search': self._cmd_search,
            'download': self._cmd_download,
            'info': self._cmd_info,
            'random': self._cmd_random,
            'config': self._cmd_config
        }
        
        command_func = command_map.get(args.command)
        if command_func:
            return command_func(args)
        else:
            print(f"{t('errors.invalid_input')}: {args.command}")
            return 1
    
    def _cmd_search(self, args: argparse.Namespace) -> int:
        """
        Execute search command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Create search filter
            search_filter = SearchFilter(
                platforms=args.platform or [],
                regions=args.region or [],
                year=args.year
            )
            
            print(f"{t('search.searching')}")
            
            # Perform search
            results = self.search_engine.search(
                query=args.query,
                search_filter=search_filter,
                limit=args.limit
            )
            
            if not results.entries:
                print(t('search.no_results'))
                return 0
            
            # Display results
            self._display_search_results(results.entries, args.format)
            
            print(f"\n{t('search.found.plural', count=len(results.entries))}")
            return 0
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def _cmd_download(self, args: argparse.Namespace) -> int:
        """
        Execute download command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Check if target is a ROM ID or search query
            if args.target.isdigit():
                # Direct ROM ID
                rom_entry = self.api_client.get_rom(args.target)
                if not rom_entry:
                    print(f"{t('rom.not_found')}: {args.target}")
                    return 1
                roms_to_download = [rom_entry]
            else:
                # Search query
                search_filter = SearchFilter(
                    platforms=[args.platform] if args.platform else [],
                    regions=[args.region] if args.region else []
                )
                
                results = self.search_engine.search(
                    query=args.target,
                    search_filter=search_filter,
                    limit=50 if args.all else 1
                )
                
                if not results.entries:
                    print(t('search.no_results'))
                    return 0
                
                roms_to_download = results.entries if args.all else [results.entries[0]]
            
            # Download ROMs
            successful_downloads = 0
            total_downloads = len(roms_to_download)
            
            for i, rom in enumerate(roms_to_download, 1):
                print(f"\n[{i}/{total_downloads}] {t('download.starting')}: {rom.title}")
                
                # Set custom output directory if specified
                if args.output:
                    original_roms_dir = self.dirs.roms_dir
                    self.dirs.roms_dir = Path(args.output)
                
                try:
                    result = self.download_manager.download_rom(
                        rom,
                        download_boxart=not args.no_boxart,
                        progress_callback=self._download_progress_callback
                    )
                    
                    if result.success:
                        print(f"\n{t('download.completed')}: {result.file_path}")
                        successful_downloads += 1
                    else:
                        print(f"\n{t('download.failed')}: {result.error}")
                        
                except Exception as e:
                    print(f"\n{t('download.failed')}: {e}")
                
                finally:
                    # Restore original directory
                    if args.output:
                        self.dirs.roms_dir = original_roms_dir
            
            # Summary
            if total_downloads > 1:
                print(f"\n{t('download.multiple.completed', successful=successful_downloads, total=total_downloads)}")
            
            return 0 if successful_downloads > 0 else 1
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def _cmd_info(self, args: argparse.Namespace) -> int:
        """
        Execute info command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            rom_entry = self.api_client.get_rom(args.rom_id)
            if not rom_entry:
                print(f"{t('rom.not_found')}: {args.rom_id}")
                return 1
            
            self._display_rom_info(rom_entry, args.format)
            return 0
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def _cmd_random(self, args: argparse.Namespace) -> int:
        """
        Execute random command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            search_filter = SearchFilter(
                platforms=[args.platform] if args.platform else [],
                regions=[args.region] if args.region else []
            )
            
            print(f"{t('search.searching')}...")
            
            random_roms = self.search_engine.get_random_roms(
                count=args.count,
                search_filter=search_filter
            )
            
            if not random_roms:
                print(t('search.no_results'))
                return 0
            
            # Display random ROMs
            self._display_search_results(random_roms, 'table')
            
            # Download if requested
            if args.download:
                print(f"\n{t('download.multiple.starting', count=len(random_roms))}")
                
                successful_downloads = 0
                for i, rom in enumerate(random_roms, 1):
                    print(f"\n[{i}/{len(random_roms)}] {t('download.starting')}: {rom.title}")
                    
                    try:
                        result = self.download_manager.download_rom(
                            rom,
                            progress_callback=self._download_progress_callback
                        )
                        
                        if result.success:
                            print(f"\n{t('download.completed')}: {result.file_path}")
                            successful_downloads += 1
                        else:
                            print(f"\n{t('download.failed')}: {result.error}")
                            
                    except Exception as e:
                        print(f"\n{t('download.failed')}: {e}")
                
                print(f"\n{t('download.multiple.completed', successful=successful_downloads, total=len(random_roms))}")
            
            return 0
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def _cmd_config(self, args: argparse.Namespace) -> int:
        """
        Execute config command.
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            if args.config_action == 'get':
                value = self.config.get(args.key)
                if value is not None:
                    print(f"{args.key}: {value}")
                else:
                    print(f"{t('config.invalid')}: {args.key}")
                    return 1
            
            elif args.config_action == 'set':
                self.config.set(args.key, args.value)
                self.config.save_config()
                print(f"{t('config.saved')}: {args.key} = {args.value}")
            
            elif args.config_action == 'list':
                config_data = self.config.config
                self._display_config(config_data)
            
            elif args.config_action == 'reset':
                self.config.reset_to_defaults()
                self.config.save_config()
                print(t('config.reset'))
            
            else:
                print(f"{t('errors.invalid_input')}: {args.config_action}")
                return 1
            
            return 0
            
        except Exception as e:
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def _display_search_results(self, results: List, format_type: str) -> None:
        """
        Display search results in the specified format.
        
        Args:
            results: List of ROM entries
            format_type: Output format ('table', 'json', 'csv')
        """
        if format_type == 'json':
            import json
            data = [{
                'id': rom.id,
                'title': rom.title,
                'platform': rom.platform,
                'region': rom.region,
                'year': rom.year,
                'size': rom.size
            } for rom in results]
            print(json.dumps(data, indent=2))
        
        elif format_type == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['ID', 'Title', 'Platform', 'Region', 'Year', 'Size'])
            for rom in results:
                writer.writerow([
                    rom.id, rom.title, rom.platform, rom.region,
                    rom.year or '', format_file_size(rom.size) if rom.size else ''
                ])
            print(output.getvalue().strip())
        
        else:  # table format
            # Simple table display
            print(f"\n{'ID':<8} {'Title':<40} {'Platform':<15} {'Region':<8} {'Year':<6} {'Size':<10}")
            print("-" * 95)
            
            for rom in results:
                title = rom.title[:37] + "..." if len(rom.title) > 40 else rom.title
                platform = rom.platform[:12] + "..." if len(rom.platform) > 15 else rom.platform
                size_str = format_file_size(rom.size) if rom.size else 'N/A'
                year_str = str(rom.year) if rom.year else 'N/A'
                
                print(f"{rom.id:<8} {title:<40} {platform:<15} {rom.region:<8} {year_str:<6} {size_str:<10}")
    
    def _display_rom_info(self, rom, format_type: str) -> None:
        """
        Display detailed ROM information.
        
        Args:
            rom: ROM entry
            format_type: Output format ('table', 'json')
        """
        if format_type == 'json':
            import json
            data = {
                'id': rom.id,
                'title': rom.title,
                'platform': rom.platform,
                'region': rom.region,
                'year': rom.year,
                'size': rom.size,
                'description': rom.description,
                'download_links': rom.download_links,
                'boxart_url': rom.boxart_url
            }
            print(json.dumps(data, indent=2))
        else:
            # Table format
            print(f"\n{t('rom.info')}:")
            print("-" * 50)
            print(f"{t('rom.title')}: {rom.title}")
            print(f"ID: {rom.id}")
            print(f"{t('rom.platform')}: {rom.platform}")
            print(f"{t('rom.region')}: {rom.region}")
            if rom.year:
                print(f"{t('rom.year')}: {rom.year}")
            if rom.size:
                print(f"{t('rom.size')}: {format_file_size(rom.size)}")
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