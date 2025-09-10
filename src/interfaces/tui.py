#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Text User Interface (TUI) for CLI Download ROM.

This module implements a full-screen text-based interface using Textual,
inspired by applications like htop or Clonezilla installer.

Author: Leonne Martins
License: GPL-3.0
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import (
        Header, Footer, Button, Input, DataTable, Static, 
        ProgressBar, Label, ListView, ListItem, Tabs, Tab,
        SelectionList, OptionList, Log, Tree
    )
    from textual.screen import Screen, ModalScreen
    from textual.binding import Binding
    from textual.message import Message
    from textual.reactive import reactive
except ImportError:
    # Textual not available - TUI interface will be disabled
    # Define dummy classes to prevent import errors
    class DummyTextualClass:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return DummyTextualClass()
        def __getattr__(self, name): return DummyTextualClass()
        def __setattr__(self, name, value): pass
        def __iter__(self): return iter([])
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def __getitem__(self, key): return DummyTextualClass()
        def __setitem__(self, key, value): pass
    
    # Create instances that behave like classes but also have attributes
    class DummyTextualMeta(type):
        def __getattr__(cls, name):
            return DummyTextualClass()
    
    class DummyTextualBase(metaclass=DummyTextualMeta):
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return DummyTextualClass()
        def __getattr__(self, name): return DummyTextualClass()
        def __setattr__(self, name, value): pass
        def __iter__(self): return iter([])
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def __getitem__(self, key): return DummyTextualClass()
        def __setitem__(self, key, value): pass
    
    App = DummyTextualBase
    Screen = DummyTextualBase
    ModalScreen = DummyTextualBase
    ComposeResult = DummyTextualBase
    Container = DummyTextualBase
    Horizontal = DummyTextualBase
    Vertical = DummyTextualBase
    ScrollableContainer = DummyTextualBase
    Header = DummyTextualBase
    Footer = DummyTextualBase
    Button = DummyTextualBase
    Input = DummyTextualBase
    DataTable = DummyTextualBase
    Static = DummyTextualBase
    ProgressBar = DummyTextualBase
    Label = DummyTextualBase
    ListView = DummyTextualBase
    ListItem = DummyTextualBase
    Tabs = DummyTextualBase
    Tab = DummyTextualBase
    SelectionList = DummyTextualBase
    OptionList = DummyTextualBase
    Log = DummyTextualBase
    Tree = DummyTextualBase
    Binding = DummyTextualBase
    Message = DummyTextualBase
    def reactive(x): return x

from ..core import DirectoryManager, ConfigManager, LogManager, SearchEngine, SearchFilter
from ..api import CrocDBClient, ROMEntry
from ..download import DownloadManager, DownloadProgress
from ..locales import get_i18n, t
from ..utils import format_file_size, sanitize_filename


class SearchScreen(Screen):
    """
    Screen for searching ROMs.
    """
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("f1", "help", "Help"),
    ]
    
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
        self.search_results = []
    
    def compose(self) -> ComposeResult:
        """Create the search screen layout."""
        yield Header()
        
        with Container(id="search-container"):
            yield Static(t('search.query'), classes="label")
            yield Input(placeholder="Enter game title...", id="search-input")
            
            with Horizontal():
                yield Static(t('search.platform'), classes="label")
                yield Input(placeholder="Platform (optional)", id="platform-input")
                
                yield Static(t('search.region'), classes="label")
                yield Input(placeholder="Region (optional)", id="region-input")
            
            with Horizontal():
                yield Button(t('commands.search'), id="search-btn", variant="primary")
                yield Button("Clear", id="clear-btn")
                yield Button("Random", id="random-btn")
            
            yield Static("Search Results:", classes="section-title")
            yield DataTable(id="results-table")
            
            with Horizontal():
                yield Button("Download Selected", id="download-btn", variant="success")
                yield Button("Download All", id="download-all-btn")
                yield Button("View Info", id="info-btn")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the search screen."""
        table = self.query_one("#results-table", DataTable)
        table.add_columns("#", "Title", "Platform", "Region", "Year", "Size")
        
        # Focus on search input
        self.query_one("#search-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "search-btn":
            self.perform_search()
        elif event.button.id == "clear-btn":
            self.clear_search()
        elif event.button.id == "random-btn":
            self.get_random_roms()
        elif event.button.id == "download-btn":
            self.download_selected()
        elif event.button.id == "download-all-btn":
            self.download_all()
        elif event.button.id == "info-btn":
            self.show_rom_info()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "search-input":
            self.perform_search()
    
    def perform_search(self) -> None:
        """Perform ROM search."""
        query = self.query_one("#search-input", Input).value.strip()
        if not query:
            return
        
        platform = self.query_one("#platform-input", Input).value.strip()
        region = self.query_one("#region-input", Input).value.strip()
        
        # Create search filter
        search_filter = SearchFilter(
            platforms=[platform] if platform else [],
            regions=[region] if region else []
        )
        
        # Show loading message
        table = self.query_one("#results-table", DataTable)
        table.clear()
        table.add_row("Loading...", "", "", "", "", "")
        
        # Perform search in background
        asyncio.create_task(self._search_async(query, search_filter))
    
    async def _search_async(self, query: str, search_filter: SearchFilter) -> None:
        """Perform asynchronous search."""
        try:
            results = await self.tui_app.search_engine.search(
                query, search_filter, 50
            )
            
            self.search_results = [rom.rom_entry for rom in results]
            self.update_results_table()
            
        except Exception as e:
            table = self.query_one("#results-table", DataTable)
            table.clear()
            table.add_row(f"Error: {e}", "", "", "", "", "")
    
    def update_results_table(self) -> None:
        """Update the results table with search results."""
        table = self.query_one("#results-table", DataTable)
        table.clear()
        
        if not self.search_results:
            table.add_row("No results found", "", "", "", "", "")
            return
        
        for i, rom in enumerate(self.search_results, 1):
            title = rom.title[:30] + "..." if len(rom.title) > 30 else rom.title
            platform = rom.platform[:12] + "..." if len(rom.platform) > 12 else rom.platform
            size_mb = rom.get_size_mb()
            size_str = f"{size_mb:.1f} MB" if size_mb > 0 else 'N/A'
            year_str = str(rom.year) if rom.year else 'N/A'
            region_str = rom.regions[0] if rom.regions else 'N/A'
            
            table.add_row(
                str(i), title, platform, region_str, year_str, size_str
            )
    
    def clear_search(self) -> None:
        """Clear search inputs and results."""
        self.query_one("#search-input", Input).value = ""
        self.query_one("#platform-input", Input).value = ""
        self.query_one("#region-input", Input).value = ""
        
        table = self.query_one("#results-table", DataTable)
        table.clear()
        self.search_results = []
    
    def get_random_roms(self) -> None:
        """Get random ROMs."""
        platform = self.query_one("#platform-input", Input).value.strip()
        region = self.query_one("#region-input", Input).value.strip()
        
        search_filter = SearchFilter(
            platforms=[platform] if platform else [],
            regions=[region] if region else []
        )
        
        # Show loading message
        table = self.query_one("#results-table", DataTable)
        table.clear()
        table.add_row("Loading random ROMs...", "", "", "", "", "")
        
        # Get random ROMs in background
        asyncio.create_task(self._random_async(search_filter))
    
    async def _random_async(self, search_filter: SearchFilter) -> None:
        """Get random ROMs asynchronously."""
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.tui_app.search_engine.get_random_roms,
                10, search_filter
            )
            
            self.search_results = results
            self.update_results_table()
            
        except Exception as e:
            table = self.query_one("#results-table", DataTable)
            table.clear()
            table.add_row(f"Error: {e}", "", "", "", "", "")
    
    def download_selected(self) -> None:
        """Download selected ROM."""
        table = self.query_one("#results-table", DataTable)
        if table.cursor_row is None or not self.search_results:
            return
        
        try:
            rom_index = table.cursor_row
            if 0 <= rom_index < len(self.search_results):
                rom = self.search_results[rom_index]
                self.tui_app.push_screen(DownloadScreen(self.tui_app, [rom]))
        except (IndexError, ValueError):
            pass
    
    def download_all(self) -> None:
        """Download all search results."""
        if not self.search_results:
            return
        
        self.tui_app.push_screen(DownloadScreen(self.tui_app, self.search_results))
    
    def show_rom_info(self) -> None:
        """Show detailed ROM information."""
        table = self.query_one("#results-table", DataTable)
        if table.cursor_row is None or not self.search_results:
            return
        
        try:
            rom_index = table.cursor_row
            if 0 <= rom_index < len(self.search_results):
                rom = self.search_results[rom_index]
                self.tui_app.push_screen(ROMInfoScreen(self.tui_app, rom))
        except (IndexError, ValueError):
            pass
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.tui_app.pop_screen()


class DownloadScreen(Screen):
    """
    Screen for downloading ROMs.
    """
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("c", "cancel", "Cancel"),
    ]
    
    def __init__(self, tui_app, roms_to_download: List[ROMEntry]):
        super().__init__()
        self.tui_app = tui_app
        self.roms_to_download = roms_to_download
        self.current_rom_index = 0
        self.download_cancelled = False
        self.successful_downloads = 0
    
    def compose(self) -> ComposeResult:
        """Create the download screen layout."""
        yield Header()
        
        with Container(id="download-container"):
            yield Static(f"Downloading {len(self.roms_to_download)} ROM(s)", classes="section-title")
            
            yield Static("Current ROM:", classes="label")
            yield Static("", id="current-rom")
            
            yield Static("Progress:", classes="label")
            yield ProgressBar(id="progress-bar")
            yield Static("", id="progress-text")
            
            yield Static("Speed:", classes="label")
            yield Static("", id="speed-text")
            
            yield Static("ETA:", classes="label")
            yield Static("", id="eta-text")
            
            yield Static("Overall Progress:", classes="label")
            yield ProgressBar(id="overall-progress")
            yield Static("", id="overall-text")
            
            yield Static("Log:", classes="label")
            yield Log(id="download-log")
            
            with Horizontal():
                yield Button("Cancel", id="cancel-btn", variant="error")
                yield Button("Close", id="close-btn", disabled=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Start downloads when screen is mounted."""
        asyncio.create_task(self.start_downloads())
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.cancel_downloads()
        elif event.button.id == "close-btn":
            self.action_back()
    
    async def start_downloads(self) -> None:
        """Start downloading ROMs."""
        log = self.query_one("#download-log", Log)
        overall_progress = self.query_one("#overall-progress", ProgressBar)
        overall_text = self.query_one("#overall-text", Static)
        
        overall_progress.update(total=len(self.roms_to_download))
        
        for i, rom in enumerate(self.roms_to_download):
            if self.download_cancelled:
                break
            
            self.current_rom_index = i
            
            # Update current ROM display
            current_rom = self.query_one("#current-rom", Static)
            current_rom.update(f"[{i+1}/{len(self.roms_to_download)}] {rom.title}")
            
            log.write_line(f"Starting download: {rom.title}")
            
            try:
                # Download ROM
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.download_rom_sync,
                    rom
                )
                
                if result.success:
                    log.write_line(f"✓ Downloaded: {rom.title}")
                    self.successful_downloads += 1
                else:
                    log.write_line(f"✗ Failed: {rom.title} - {result.error}")
                
            except Exception as e:
                log.write_line(f"✗ Error: {rom.title} - {e}")
            
            # Update overall progress
            overall_progress.update(progress=i + 1)
            overall_text.update(f"{i + 1}/{len(self.roms_to_download)} completed")
        
        # Download completed
        log.write_line(f"\nDownload completed: {self.successful_downloads}/{len(self.roms_to_download)} successful")
        
        # Enable close button
        close_btn = self.query_one("#close-btn", Button)
        close_btn.disabled = False
        
        cancel_btn = self.query_one("#cancel-btn", Button)
        cancel_btn.disabled = True
    
    def download_rom_sync(self, rom: ROMEntry):
        """Download ROM synchronously (for executor)."""
        return self.tui_app.download_manager.download_rom(
            rom,
            progress_callback=self.download_progress_callback
        )
    
    def download_progress_callback(self, progress: DownloadProgress) -> None:
        """Handle download progress updates."""
        if self.download_cancelled:
            return
        
        try:
            # Update progress bar
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            if progress.total_size > 0:
                progress_bar.update(total=progress.total_size, progress=progress.downloaded_size)
            
            # Update progress text
            progress_text = self.query_one("#progress-text", Static)
            if progress.total_size > 0:
                percentage = (progress.downloaded_size / progress.total_size) * 100
                progress_text.update(
                    f"{format_file_size(progress.downloaded_size)}/{format_file_size(progress.total_size)} ({percentage:.1f}%)"
                )
            else:
                progress_text.update(f"{format_file_size(progress.downloaded_size)}")
            
            # Update speed
            speed_text = self.query_one("#speed-text", Static)
            if progress.speed:
                speed_text.update(f"{format_file_size(progress.speed)}/s")
            
            # Update ETA
            eta_text = self.query_one("#eta-text", Static)
            if progress.eta:
                eta_text.update(f"{progress.eta}s")
                
        except Exception:
            # Ignore errors during UI updates
            pass
    
    def cancel_downloads(self) -> None:
        """Cancel ongoing downloads."""
        self.download_cancelled = True
        log = self.query_one("#download-log", Log)
        log.write_line("\nDownload cancelled by user")
        
        # Enable close button
        close_btn = self.query_one("#close-btn", Button)
        close_btn.disabled = False
        
        cancel_btn = self.query_one("#cancel-btn", Button)
        cancel_btn.disabled = True
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.tui_app.pop_screen()
    
    def action_cancel(self) -> None:
        """Cancel downloads."""
        self.cancel_downloads()


class ROMInfoScreen(ModalScreen):
    """
    Modal screen for displaying ROM information.
    """
    
    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]
    
    def __init__(self, tui_app, rom: ROMEntry):
        super().__init__()
        self.tui_app = tui_app
        self.rom = rom
    
    def compose(self) -> ComposeResult:
        """Create the ROM info modal layout."""
        with Container(id="rom-info-modal"):
            yield Static(f"ROM Information: {self.rom.title}", classes="modal-title")
            
            with ScrollableContainer():
                yield Static(f"ID: {self.rom.slug}")
                yield Static(f"Title: {self.rom.title}")
                yield Static(f"Platform: {self.rom.platform}")
                region_str = self.rom.regions[0] if self.rom.regions else 'N/A'
                yield Static(f"Region: {region_str}")
                
                if hasattr(self.rom, 'year') and self.rom.year:
                    yield Static(f"Year: {self.rom.year}")
                
                size_mb = self.rom.get_size_mb()
                if size_mb > 0:
                    yield Static(f"Size: {size_mb:.1f} MB")
                
                if self.rom.description:
                    yield Static(f"Description: {self.rom.description}")
                
                if self.rom.download_links:
                    yield Static(f"Download Links: {len(self.rom.download_links)} available")
                
                if self.rom.boxart_url:
                    yield Static("Box Art: Available")
            
            with Horizontal():
                yield Button("Download", id="download-btn", variant="primary")
                yield Button("Close", id="close-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "download-btn":
            self.tui_app.push_screen(DownloadScreen(self.tui_app, [self.rom]))
            self.dismiss()
        elif event.button.id == "close-btn":
            self.dismiss()
    
    def action_close(self) -> None:
        """Close the modal."""
        self.dismiss()


class ConfigScreen(Screen):
    """
    Screen for managing configuration.
    """
    
    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]
    
    def __init__(self, tui_app):
        super().__init__()
        self.tui_app = tui_app
    
    def compose(self) -> ComposeResult:
        """Create the config screen layout."""
        yield Header()
        
        with Container(id="config-container"):
            yield Static("Configuration", classes="section-title")
            
            with Tabs():
                yield Tab("General", id="general-tab")
                yield Tab("Download", id="download-tab")
                yield Tab("Interface", id="interface-tab")
            
            with Container(id="config-content"):
                # General settings
                with Container(id="general-settings"):
                    yield Static("Language:", classes="label")
                    yield Input(value=self.tui_app.config.get('app.language', 'en'), id="language-input")
                    
                    yield Static("Log Level:", classes="label")
                    yield Input(value=self.tui_app.config.get('logging.level', 'INFO'), id="log-level-input")
                
                # Download settings
                with Container(id="download-settings", classes="hidden"):
                    yield Static("Max Concurrent Downloads:", classes="label")
                    yield Input(value=str(self.tui_app.config.get('download.max_concurrent', 3)), id="max-concurrent-input")
                    
                    yield Static("Timeout (seconds):", classes="label")
                    yield Input(value=str(self.tui_app.config.get('download.timeout', 30)), id="timeout-input")
                    
                    yield Static("Download Box Art:", classes="label")
                    yield Input(value=str(self.tui_app.config.get('download.download_boxart', True)), id="boxart-input")
                
                # Interface settings
                with Container(id="interface-settings", classes="hidden"):
                    yield Static("Default Interface:", classes="label")
                    yield Input(value=self.tui_app.config.get('interface.default', 'cli'), id="default-interface-input")
            
            with Horizontal():
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Reset to Defaults", id="reset-btn", variant="error")
                yield Button("Cancel", id="cancel-btn")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-btn":
            self.save_config()
        elif event.button.id == "reset-btn":
            self.reset_config()
        elif event.button.id == "cancel-btn":
            self.action_back()
    
    def save_config(self) -> None:
        """Save configuration changes."""
        try:
            # Get values from inputs
            language = self.query_one("#language-input", Input).value
            log_level = self.query_one("#log-level-input", Input).value
            max_concurrent = int(self.query_one("#max-concurrent-input", Input).value)
            timeout = int(self.query_one("#timeout-input", Input).value)
            boxart = self.query_one("#boxart-input", Input).value.lower() == 'true'
            default_interface = self.query_one("#default-interface-input", Input).value
            
            # Update configuration
            self.tui_app.config.set('app.language', language)
            self.tui_app.config.set('logging.level', log_level)
            self.tui_app.config.set('download.max_concurrent', max_concurrent)
            self.tui_app.config.set('download.timeout', timeout)
            self.tui_app.config.set('download.download_boxart', boxart)
            self.tui_app.config.set('interface.default', default_interface)
            
            # Save to file
            self.tui_app.config.save_config()
            
            # Show success message
            self.notify("Configuration saved successfully")
            
        except Exception as e:
            self.notify(f"Error saving configuration: {e}", severity="error")
    
    def reset_config(self) -> None:
        """Reset configuration to defaults."""
        try:
            self.tui_app.config.reset_to_defaults()
            self.tui_app.config.save_config()
            self.notify("Configuration reset to defaults")
            
            # Refresh inputs with default values
            self.refresh()
            
        except Exception as e:
            self.notify(f"Error resetting configuration: {e}", severity="error")
    
    def action_back(self) -> None:
        """Go back to main screen."""
        self.tui_app.pop_screen()


class TUIInterface(App):
    """
    Text User Interface for CLI Download ROM.
    
    A full-screen text-based interface using Textual.
    """
    
    CSS = """
    .section-title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    
    .label {
        text-style: bold;
        margin: 1 0 0 0;
    }
    
    .hidden {
        display: none;
    }
    
    #rom-info-modal {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
    }
    
    .modal-title {
        text-style: bold;
        text-align: center;
        color: $accent;
        margin: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("f1", "help", "Help"),
    ]
    
    def __init__(self, config_manager: ConfigManager, directory_manager: DirectoryManager,
                 log_manager: LogManager):
        super().__init__()
        self.config = config_manager
        self.dirs = directory_manager
        self.logger = log_manager
        
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
    
    def compose(self) -> ComposeResult:
        """Create the main application layout."""
        yield Header()
        
        with Container(id="main-container"):
            yield Static(f"{t('app.name')} - {t('interface.tui')}", classes="section-title")
            
            with Vertical():
                yield Button(t('commands.search'), id="search-btn", variant="primary")
                yield Button("Random ROMs", id="random-btn")
                yield Button("Configuration", id="config-btn")
                yield Button("About", id="about-btn")
                yield Button("Exit", id="exit-btn", variant="error")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "search-btn":
            self.push_screen(SearchScreen(self))
        elif event.button.id == "random-btn":
            self.show_random_roms()
        elif event.button.id == "config-btn":
            self.push_screen(ConfigScreen(self))
        elif event.button.id == "about-btn":
            self.show_about()
        elif event.button.id == "exit-btn":
            self.exit()
    
    def show_random_roms(self) -> None:
        """Show random ROMs screen."""
        search_screen = SearchScreen(self)
        search_screen.get_random_roms()
        self.push_screen(search_screen)
    
    def show_about(self) -> None:
        """Show about dialog."""
        about_text = f"""
{t('app.name')}
{t('app.description')}

{t('app.version', version='1.0.0')}
{t('app.author', author='Leonne Martins')}
{t('app.license', license='GPL-3.0')}

Press any key to close...
        """
        
        class AboutScreen(ModalScreen):
            def compose(self) -> ComposeResult:
                with Container(id="about-modal"):
                    yield Static(about_text, classes="modal-content")
            
            def on_key(self, event) -> None:
                self.dismiss()
        
        self.push_screen(AboutScreen())
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_help(self) -> None:
        """Show help information."""
        help_text = """
Keyboard Shortcuts:

F1 - Show this help
Q - Quit application
Escape - Go back/Cancel
Enter - Confirm/Submit
Tab - Navigate between elements
Arrow Keys - Navigate lists/tables

Press any key to close...
        """
        
        class HelpScreen(ModalScreen):
            def compose(self) -> ComposeResult:
                with Container(id="help-modal"):
                    yield Static(help_text, classes="modal-content")
            
            def on_key(self, event) -> None:
                self.dismiss()
        
        self.push_screen(HelpScreen())
    
    def run_interface(self) -> int:
        """
        Run the TUI interface.
        
        Returns:
            Exit code
        """
        try:
            self.run()
            return 0
        except Exception as e:
            self.logger.error(f"TUI error: {e}")
            print(f"{t('errors.general')}: {e}")
            return 1