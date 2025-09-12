#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graphical User Interface (GUI) for CLI Download ROM.

This module implements a joystick/gamepad-navigable GUI using PyQt6,
designed for TV/monitor use with large elements and D-pad navigation.

Author: Leonne Martins
License: GPL-3.0
"""

import sys
import asyncio
from typing import List, Optional, Dict, Any, Callable
from pathlib import Path
from threading import Thread
import time
from loguru import logger

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QGridLayout, QLabel, QPushButton, QLineEdit, QListWidget,
        QListWidgetItem, QProgressBar, QTextEdit, QDialog, QMessageBox,
        QFrame, QScrollArea, QStackedWidget, QComboBox, QSpinBox,
        QCheckBox, QGroupBox, QSplitter, QTabWidget
    )
    from PyQt6.QtCore import (
        Qt, QTimer, QThread, pyqtSignal, QObject, QSize, QRect,
        QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
    )
    from PyQt6.QtGui import (
        QFont, QPixmap, QPalette, QColor, QKeyEvent, QFocusEvent,
        QPainter, QBrush, QLinearGradient
    )
except ImportError:
    # PyQt6 not available - GUI interface will be disabled
    # Define dummy classes to prevent import errors
    class DummyQtClass:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return DummyQtClass()
        def __getattr__(self, name): return DummyQtClass()
        def __setattr__(self, name, value): pass
        def __iter__(self): return iter([])
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def __getitem__(self, key): return DummyQtClass()
        def __setitem__(self, key, value): pass
    
    QApplication = DummyQtClass
    QMainWindow = DummyQtClass
    QWidget = DummyQtClass
    QVBoxLayout = DummyQtClass
    QHBoxLayout = DummyQtClass
    QGridLayout = DummyQtClass
    QLabel = DummyQtClass
    QPushButton = DummyQtClass
    QLineEdit = DummyQtClass
    QListWidget = DummyQtClass
    QListWidgetItem = DummyQtClass
    QProgressBar = DummyQtClass
    QTextEdit = DummyQtClass
    QDialog = DummyQtClass
    QMessageBox = DummyQtClass
    QFrame = DummyQtClass
    QScrollArea = DummyQtClass
    QStackedWidget = DummyQtClass
    QComboBox = DummyQtClass
    QSpinBox = DummyQtClass
    QCheckBox = DummyQtClass
    QGroupBox = DummyQtClass
    QSplitter = DummyQtClass
    QTabWidget = DummyQtClass
    Qt = DummyQtClass
    QTimer = DummyQtClass
    QThread = DummyQtClass
    QObject = DummyQtClass
    QSize = DummyQtClass
    QRect = DummyQtClass
    QPropertyAnimation = DummyQtClass
    QEasingCurve = DummyQtClass
    QParallelAnimationGroup = DummyQtClass
    QFont = DummyQtClass
    QPixmap = DummyQtClass
    QPalette = DummyQtClass
    QColor = DummyQtClass
    QKeyEvent = DummyQtClass
    QFocusEvent = DummyQtClass
    QPainter = DummyQtClass
    QBrush = DummyQtClass
    QLinearGradient = DummyQtClass
    def pyqtSignal(*args): return lambda x: x

# Lazy pygame import: only load when GUI initializes gamepad handling
pygame = None

from ..core import DirectoryManager, ConfigManager, LogManager, SearchEngine, SearchFilter
from ..api import CrocDBClient, ROMEntry
from ..core import DownloadManager, DownloadProgress
from ..locales import get_i18n, t
from ..utils import format_file_size, sanitize_filename


class GamepadManager(QObject):
    """
    Manages gamepad/joystick input for GUI navigation.
    """
    
    # Signals for gamepad events
    button_pressed = pyqtSignal(int)  # Button index
    dpad_moved = pyqtSignal(str)  # Direction: 'up', 'down', 'left', 'right'
    analog_moved = pyqtSignal(float, float)  # X, Y values
    
    def __init__(self):
        super().__init__()
        self.joystick = None
        self.running = False
        self.thread = None
        
        # Import pygame lazily and suppress support prompt banner
        global pygame
        if pygame is None:
            try:
                import os
                os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
                import importlib
                pygame = importlib.import_module('pygame')
            except Exception:
                pygame = None
        
        if pygame:
            pygame.init()
            pygame.joystick.init()
            
            # Initialize first available joystick
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
                print(f"Gamepad detected: {self.joystick.get_name()}")
    
    def start(self):
        """Start gamepad monitoring thread."""
        if not self.joystick:
            return
        
        self.running = True
        self.thread = Thread(target=self._monitor_gamepad, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop gamepad monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _monitor_gamepad(self):
        """Monitor gamepad input in separate thread."""
        if not pygame or not self.joystick:
            return
        
        last_dpad = (0, 0)
        button_states = [False] * self.joystick.get_numbuttons()
        
        while self.running:
            try:
                pygame.event.pump()
                
                # Check D-pad
                hat = self.joystick.get_hat(0) if self.joystick.get_numhats() > 0 else (0, 0)
                if hat != last_dpad:
                    if hat[0] == 1:  # Right
                        self.dpad_moved.emit('right')
                    elif hat[0] == -1:  # Left
                        self.dpad_moved.emit('left')
                    
                    if hat[1] == 1:  # Up
                        self.dpad_moved.emit('up')
                    elif hat[1] == -1:  # Down
                        self.dpad_moved.emit('down')
                    
                    last_dpad = hat
                
                # Check buttons
                for i in range(self.joystick.get_numbuttons()):
                    pressed = self.joystick.get_button(i)
                    if pressed and not button_states[i]:
                        self.button_pressed.emit(i)
                    button_states[i] = pressed
                
                # Check analog sticks
                if self.joystick.get_numaxes() >= 2:
                    x_axis = self.joystick.get_axis(0)
                    y_axis = self.joystick.get_axis(1)
                    
                    # Emit only significant movements
                    if abs(x_axis) > 0.3 or abs(y_axis) > 0.3:
                        self.analog_moved.emit(x_axis, y_axis)
                
                time.sleep(0.05)  # 20 FPS polling
                
            except Exception as e:
                print(f"Gamepad error: {e}")
                break


class FocusableWidget(QWidget):
    """
    Base widget with enhanced focus handling for gamepad navigation.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._focused = False
    
    def focusInEvent(self, event: QFocusEvent):
        """Handle focus in event."""
        super().focusInEvent(event)
        self._focused = True
        self.update_style()
    
    def focusOutEvent(self, event: QFocusEvent):
        """Handle focus out event."""
        super().focusOutEvent(event)
        self._focused = False
        self.update_style()
    
    def update_style(self):
        """Update widget style based on focus state."""
        if self._focused:
            self.setStyleSheet("""
                border: 3px solid #00ff00;
                background-color: rgba(0, 255, 0, 30);
            """)
        else:
            self.setStyleSheet("")


class BigButton(FocusableWidget):
    """
    Large button optimized for TV viewing and gamepad navigation.
    """
    
    clicked = pyqtSignal()
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.setMinimumSize(200, 80)
        self.setMaximumSize(400, 120)
        
        layout = QVBoxLayout()
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.setStyleSheet("""
            BigButton {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 10px;
                color: white;
            }
            BigButton:hover {
                background-color: #4a5568;
            }
        """)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ROMListWidget(FocusableWidget):
    """
    Custom list widget for displaying ROM search results.
    """
    
    rom_selected = pyqtSignal(object)  # ROMEntry
    download_requested = pyqtSignal(object)  # ROMEntry
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.roms = []
        self.current_index = 0
        
        layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel("Search Results")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # List container
        self.scroll_area = QScrollArea()
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.scroll_area.setWidget(self.list_widget)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)
        
        # Info label
        self.info_label = QLabel("Use D-pad to navigate, A to select, X to download")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def set_roms(self, roms: List[ROMEntry]):
        """Set the list of ROMs to display."""
        self.roms = roms
        self.current_index = 0
        self.update_display()
    
    def update_display(self):
        """Update the visual display of ROMs."""
        # Clear existing items
        for i in reversed(range(self.list_layout.count())):
            self.list_layout.itemAt(i).widget().setParent(None)
        
        if not self.roms:
            no_results = QLabel("No ROMs found")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results.setFont(QFont("Arial", 12))
            self.list_layout.addWidget(no_results)
            return
        
        # Add ROM items
        for i, rom in enumerate(self.roms):
            item_widget = self.create_rom_item(rom, i == self.current_index)
            self.list_layout.addWidget(item_widget)
        
        # Update title
        self.title_label.setText(f"Search Results ({len(self.roms)} found)")
    
    def create_rom_item(self, rom: ROMEntry, selected: bool) -> QWidget:
        """Create a widget for a ROM item."""
        item = QFrame()
        item.setFrameStyle(QFrame.Shape.Box)
        
        if selected:
            item.setStyleSheet("""
                QFrame {
                    background-color: #4a5568;
                    border: 2px solid #00ff00;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
        else:
            item.setStyleSheet("""
                QFrame {
                    background-color: #2d3748;
                    border: 1px solid #4a5568;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(rom.title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)
        
        # Details
        details = f"Platform: {rom.platform} | Region: {rom.region}"
        if rom.year:
            details += f" | Year: {rom.year}"
        if rom.size:
            details += f" | Size: {format_file_size(rom.size)}"
        
        details_label = QLabel(details)
        details_label.setFont(QFont("Arial", 10))
        details_label.setStyleSheet("color: #a0aec0;")
        layout.addWidget(details_label)
        
        item.setLayout(layout)
        return item
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events for navigation."""
        if not self.roms:
            return
        
        if event.key() == Qt.Key.Key_Up:
            self.move_selection(-1)
        elif event.key() == Qt.Key.Key_Down:
            self.move_selection(1)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if 0 <= self.current_index < len(self.roms):
                self.rom_selected.emit(self.roms[self.current_index])
        elif event.key() == Qt.Key.Key_Space:
            if 0 <= self.current_index < len(self.roms):
                self.download_requested.emit(self.roms[self.current_index])
        else:
            super().keyPressEvent(event)
    
    def move_selection(self, direction: int):
        """Move selection up or down."""
        if not self.roms:
            return
        
        self.current_index = max(0, min(len(self.roms) - 1, self.current_index + direction))
        self.update_display()
        
        # Scroll to current item if needed
        item_height = 80  # Approximate item height
        scroll_position = self.current_index * item_height
        self.scroll_area.verticalScrollBar().setValue(scroll_position)


class DownloadProgressWidget(QWidget):
    """
    Widget for displaying download progress.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel("Download Progress")
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Current ROM
        self.current_rom_label = QLabel("")
        self.current_rom_label.setFont(QFont("Arial", 12))
        self.current_rom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_rom_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4a5568;
                border-radius: 5px;
                text-align: center;
                font-size: 12px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status info
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Speed and ETA
        info_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: --")
        self.eta_label = QLabel("ETA: --")
        info_layout.addWidget(self.speed_label)
        info_layout.addWidget(self.eta_label)
        layout.addLayout(info_layout)
        
        # Overall progress
        self.overall_label = QLabel("Overall Progress")
        self.overall_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.overall_label)
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimumHeight(25)
        layout.addWidget(self.overall_progress)
        
        self.setLayout(layout)
    
    def update_progress(self, progress: DownloadProgress):
        """Update progress display."""
        if progress.total_size > 0:
            percentage = int((progress.downloaded_size / progress.total_size) * 100)
            self.progress_bar.setValue(percentage)
            
            size_text = f"{format_file_size(progress.downloaded_size)}/{format_file_size(progress.total_size)}"
            self.status_label.setText(f"{size_text} ({percentage}%)")
        else:
            self.status_label.setText(f"{format_file_size(progress.downloaded_size)}")
        
        if progress.speed:
            self.speed_label.setText(f"Speed: {format_file_size(progress.speed)}/s")
        
        if progress.eta:
            self.eta_label.setText(f"ETA: {progress.eta}s")
    
    def set_current_rom(self, rom_title: str, index: int, total: int):
        """Set current ROM being downloaded."""
        self.current_rom_label.setText(f"[{index}/{total}] {rom_title}")
        self.overall_progress.setValue(int((index / total) * 100))
    
    def set_completed(self, successful: int, total: int):
        """Set download completion status."""
        self.title_label.setText("Download Completed")
        self.current_rom_label.setText(f"Completed: {successful}/{total} successful")
        self.progress_bar.setValue(100)
        self.overall_progress.setValue(100)


class SearchScreen(QWidget):
    """
    Screen for searching ROMs.
    """
    
    def __init__(self, gui_app):
        super().__init__()
        self.gui_app = gui_app
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the search screen UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("ROM Search")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Search form
        form_layout = QGridLayout()
        
        # Query input
        form_layout.addWidget(QLabel("Game Title:"), 0, 0)
        self.query_input = QLineEdit()
        self.query_input.setMinimumHeight(40)
        self.query_input.setFont(QFont("Arial", 12))
        form_layout.addWidget(self.query_input, 0, 1)
        
        # Platform input
        form_layout.addWidget(QLabel("Platform:"), 1, 0)
        self.platform_input = QLineEdit()
        self.platform_input.setMinimumHeight(40)
        self.platform_input.setFont(QFont("Arial", 12))
        form_layout.addWidget(self.platform_input, 1, 1)
        
        # Region input
        form_layout.addWidget(QLabel("Region:"), 2, 0)
        self.region_input = QLineEdit()
        self.region_input.setMinimumHeight(40)
        self.region_input.setFont(QFont("Arial", 12))
        form_layout.addWidget(self.region_input, 2, 1)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.search_btn = BigButton("Search")
        self.search_btn.clicked.connect(self.perform_search)
        button_layout.addWidget(self.search_btn)
        
        self.random_btn = BigButton("Random")
        self.random_btn.clicked.connect(self.get_random_roms)
        button_layout.addWidget(self.random_btn)
        
        self.clear_btn = BigButton("Clear")
        self.clear_btn.clicked.connect(self.clear_search)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # Results
        self.rom_list = ROMListWidget()
        self.rom_list.rom_selected.connect(self.show_rom_info)
        self.rom_list.download_requested.connect(self.download_rom)
        layout.addWidget(self.rom_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.download_selected_btn = BigButton("Download Selected")
        self.download_selected_btn.clicked.connect(self.download_selected)
        action_layout.addWidget(self.download_selected_btn)
        
        self.download_all_btn = BigButton("Download All")
        self.download_all_btn.clicked.connect(self.download_all)
        action_layout.addWidget(self.download_all_btn)
        
        self.back_btn = BigButton("Back")
        self.back_btn.clicked.connect(self.go_back)
        action_layout.addWidget(self.back_btn)
        
        layout.addLayout(action_layout)
        
        self.setLayout(layout)
        
        # Set initial focus
        self.query_input.setFocus()
    
    def perform_search(self):
        """Perform ROM search."""
        query = self.query_input.text().strip()
        if not query:
            return
        
        platform = self.platform_input.text().strip()
        region = self.region_input.text().strip()
        
        search_filter = SearchFilter(
            platforms=[platform] if platform else [],
            regions=[region] if region else []
        )
        
        # Perform search in background thread
        self.gui_app.perform_search_async(query, search_filter, self.on_search_complete)
    
    def get_random_roms(self):
        """Get random ROMs."""
        platform = self.platform_input.text().strip()
        region = self.region_input.text().strip()
        
        search_filter = SearchFilter(
            platforms=[platform] if platform else [],
            regions=[region] if region else []
        )
        
        # Get random ROMs in background thread
        self.gui_app.get_random_roms_async(search_filter, self.on_search_complete)
    
    def on_search_complete(self, roms: List[ROMEntry]):
        """Handle search completion."""
        self.rom_list.set_roms(roms)
    
    def clear_search(self):
        """Clear search inputs and results."""
        self.query_input.clear()
        self.platform_input.clear()
        self.region_input.clear()
        self.rom_list.set_roms([])
    
    def show_rom_info(self, rom: ROMEntry):
        """Show ROM information dialog."""
        self.gui_app.show_rom_info(rom)
    
    def download_rom(self, rom: ROMEntry):
        """Download a single ROM."""
        self.gui_app.start_download([rom])
    
    def download_selected(self):
        """Download selected ROM."""
        if self.rom_list.roms and 0 <= self.rom_list.current_index < len(self.rom_list.roms):
            rom = self.rom_list.roms[self.rom_list.current_index]
            self.gui_app.start_download([rom])
    
    def download_all(self):
        """Download all search results."""
        if self.rom_list.roms:
            self.gui_app.start_download(self.rom_list.roms)
    
    def go_back(self):
        """Go back to main screen."""
        self.gui_app.show_main_screen()


class DownloadScreen(QWidget):
    """
    Screen for downloading ROMs.
    """
    
    def __init__(self, gui_app, roms_to_download: List[ROMEntry]):
        super().__init__()
        self.gui_app = gui_app
        self.roms_to_download = roms_to_download
        self.current_index = 0
        self.successful_downloads = 0
        self.download_cancelled = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the download screen UI."""
        layout = QVBoxLayout()
        
        # Progress widget
        self.progress_widget = DownloadProgressWidget()
        layout.addWidget(self.progress_widget)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 10))
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = BigButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_download)
        button_layout.addWidget(self.cancel_btn)
        
        self.close_btn = BigButton("Close")
        self.close_btn.clicked.connect(self.close_download)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Start downloads
        QTimer.singleShot(100, self.start_downloads)
    
    def start_downloads(self):
        """Start downloading ROMs."""
        self.gui_app.start_download_process(self.roms_to_download, self.on_progress, self.on_complete)
    
    def on_progress(self, progress: DownloadProgress, rom_title: str, index: int, total: int):
        """Handle download progress updates."""
        self.progress_widget.update_progress(progress)
        self.progress_widget.set_current_rom(rom_title, index, total)
    
    def on_complete(self, successful: int, total: int, log_messages: List[str]):
        """Handle download completion."""
        self.progress_widget.set_completed(successful, total)
        
        # Update log
        for message in log_messages:
            self.log_area.append(message)
        
        # Enable close button
        self.close_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
    
    def cancel_download(self):
        """Cancel ongoing download."""
        self.download_cancelled = True
        self.gui_app.cancel_download()
        self.log_area.append("Download cancelled by user")
        self.close_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
    
    def close_download(self):
        """Close download screen."""
        self.gui_app.show_search_screen()


class ConfigScreen(QWidget):
    """
    Screen for managing configuration.
    """
    
    def __init__(self, gui_app):
        super().__init__()
        self.gui_app = gui_app
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the configuration screen UI."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Configuration")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Configuration tabs
        tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QGridLayout()
        
        general_layout.addWidget(QLabel("Language:"), 0, 0)
        self.language_combo = QComboBox()
        # Use full locale codes
        self.language_combo.addItems(["auto", "en_us", "pt_br"])  # extend here when adding more locales
        self.language_combo.setCurrentText(self.gui_app.config.get('interface.language', 'auto'))
        general_layout.addWidget(self.language_combo, 0, 1)
        
        general_layout.addWidget(QLabel("Log Level:"), 1, 0)
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.gui_app.config.get('logging.level', 'INFO'))
        general_layout.addWidget(self.log_level_combo, 1, 1)
        
        general_tab.setLayout(general_layout)
        tabs.addTab(general_tab, "General")
        
        # Download tab
        download_tab = QWidget()
        download_layout = QGridLayout()
        
        download_layout.addWidget(QLabel("Max Concurrent Downloads:"), 0, 0)
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 10)
        self.max_concurrent_spin.setValue(self.gui_app.config.get('download.max_concurrent', 3))
        download_layout.addWidget(self.max_concurrent_spin, 0, 1)
        
        download_layout.addWidget(QLabel("Timeout (seconds):"), 1, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(self.gui_app.config.get('download.timeout', 30))
        download_layout.addWidget(self.timeout_spin, 1, 1)
        
        download_layout.addWidget(QLabel("Download Box Art:"), 2, 0)
        self.boxart_check = QCheckBox()
        self.boxart_check.setChecked(self.gui_app.config.get('download.download_boxart', True))
        download_layout.addWidget(self.boxart_check, 2, 1)
        
        download_tab.setLayout(download_layout)
        tabs.addTab(download_tab, "Download")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = BigButton("Save")
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)
        
        self.reset_btn = BigButton("Reset")
        self.reset_btn.clicked.connect(self.reset_config)
        button_layout.addWidget(self.reset_btn)
        
        self.back_btn = BigButton("Back")
        self.back_btn.clicked.connect(self.go_back)
        button_layout.addWidget(self.back_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_config(self):
        """Save configuration changes."""
        try:
            self.gui_app.config.set('interface.language', self.language_combo.currentText())
            self.gui_app.config.set('logging.level', self.log_level_combo.currentText())
            self.gui_app.config.set('download.max_concurrent', self.max_concurrent_spin.value())
            self.gui_app.config.set('download.timeout', self.timeout_spin.value())
            self.gui_app.config.set('download.download_boxart', self.boxart_check.isChecked())
            
            self.gui_app.config.save_config()
            
            QMessageBox.information(self, "Success", "Configuration saved successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving configuration: {e}")
    
    def reset_config(self):
        """Reset configuration to defaults."""
        try:
            self.gui_app.config.reset_to_defaults()
            self.gui_app.config.save_config()
            
            # Refresh UI with default values
            self.language_combo.setCurrentText('en_us')
            self.log_level_combo.setCurrentText('INFO')
            self.max_concurrent_spin.setValue(3)
            self.timeout_spin.setValue(30)
            self.boxart_check.setChecked(True)
            
            QMessageBox.information(self, "Success", "Configuration reset to defaults")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error resetting configuration: {e}")
    
    def go_back(self):
        """Go back to main screen."""
        self.gui_app.show_main_screen()


class MainWindow(QMainWindow):
    """
    Main window class for the GUI interface.
    """
    
    def __init__(self, gui_interface):
        super().__init__()
        self.gui_interface = gui_interface
        self.setup_ui()
        self.setup_style()
    
    def setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle(f"{t('app.name')} - {t('interface.gui')}")
        self.setMinimumSize(1024, 768)
        
        # Central widget with stacked layout
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create screens
        self.main_screen = self.gui_interface.create_main_screen()
        self.search_screen = SearchScreen(self.gui_interface)
        self.config_screen = ConfigScreen(self.gui_interface)
        
        # Add screens to stack
        self.central_widget.addWidget(self.main_screen)
        self.central_widget.addWidget(self.search_screen)
        self.central_widget.addWidget(self.config_screen)
    
    def setup_style(self):
        """Setup application styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a202c;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #63b3ed;
            }
            QPushButton {
                background-color: #4299e1;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QPushButton:pressed {
                background-color: #2c5282;
            }
            QPushButton:focus {
                border: 2px solid #63b3ed;
            }
            QListWidget {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #4a5568;
            }
            QListWidget::item:selected {
                background-color: #4299e1;
            }
            QTextEdit {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                color: white;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            QProgressBar {
                border: 2px solid #4a5568;
                border-radius: 8px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #48bb78;
                border-radius: 6px;
            }
            QComboBox {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QComboBox:focus {
                border-color: #63b3ed;
            }
            QSpinBox {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 8px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QSpinBox:focus {
                border-color: #63b3ed;
            }
        """)
    
    def closeEvent(self, event):
        """Handle application close event."""
        self.gui_interface.gamepad.stop()
        if hasattr(self.gui_interface, 'download_cancelled'):
            self.gui_interface.download_cancelled = True
        event.accept()


class GUIInterface:
    """
    Graphical User Interface for CLI Download ROM.
    
    A joystick/gamepad-navigable GUI designed for TV/monitor use.
    """
    
    def __init__(self, config_manager: ConfigManager, directory_manager: DirectoryManager,
                 log_manager: LogManager):
        self.config = config_manager
        self.dirs = directory_manager
        self.logger = log_manager
        
        # Initialize API client
        api_config = self.config.get('api', {}) or {}
        self.api_client = CrocDBClient(
            base_url=api_config.get('base_url', 'https://api.crocdb.net'),
            timeout=api_config.get('timeout', 30)
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
        
        # Initialize gamepad manager
        self.gamepad = GamepadManager()
        
        # Download state
        self.download_thread = None
        self.download_cancelled = False
        
        # Main window will be created in run_interface
        self.main_window = None
    
    def create_main_screen(self) -> QWidget:
        """Create the main menu screen."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"{t('app.name')}")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Gamepad-Navigable ROM Downloader")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Menu buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(20)
        
        search_btn = BigButton("Search ROMs")
        search_btn.clicked.connect(self.show_search_screen)
        button_layout.addWidget(search_btn)
        
        random_btn = BigButton("Random ROMs")
        random_btn.clicked.connect(self.show_random_roms)
        button_layout.addWidget(random_btn)
        
        config_btn = BigButton("Configuration")
        config_btn.clicked.connect(self.show_config_screen)
        button_layout.addWidget(config_btn)
        
        about_btn = BigButton("About")
        about_btn.clicked.connect(self.show_about)
        button_layout.addWidget(about_btn)
        
        exit_btn = BigButton("Exit")
        exit_btn.clicked.connect(self.close)
        button_layout.addWidget(exit_btn)
        
        # Center the buttons
        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setMaximumWidth(400)
        
        container_layout = QHBoxLayout()
        container_layout.addStretch()
        container_layout.addWidget(button_container)
        container_layout.addStretch()
        
        layout.addLayout(container_layout)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    # Removed setup_style method - now handled by MainWindow class
    
    def show_main_screen(self):
        """Show the main menu screen."""
        self.main_window.central_widget.setCurrentWidget(self.main_window.main_screen)
    
    def show_search_screen(self):
        """Show the search screen."""
        self.main_window.central_widget.setCurrentWidget(self.main_window.search_screen)
    
    def show_config_screen(self):
        """Show the configuration screen."""
        self.main_window.central_widget.setCurrentWidget(self.main_window.config_screen)
    
    def show_random_roms(self):
        """Show random ROMs."""
        self.main_window.search_screen.get_random_roms()
        self.show_search_screen()
    
    def show_about(self):
        """Show about dialog."""
        about_text = f"""
{t('app.name')}
{t('app.description')}

{t('app.version', version='1.0.0')}
{t('app.author', author='Leonne Martins')}
{t('app.license', license='GPL-3.0')}

Gamepad Controls:
A Button - Select/Confirm
B Button - Back/Cancel
X Button - Download
Y Button - Info
D-Pad - Navigate
        """
        
        QMessageBox.about(self.main_window, "About", about_text)
    
    def perform_search_async(self, query: str, search_filter: SearchFilter, callback: Callable):
        """Perform search in background thread."""
        def search_worker():
            try:
                # Use synchronous search instead of asyncio
                results = self.search_engine.search_sync(query, search_filter, 50)
                QTimer.singleShot(0, lambda: callback([rom.rom_entry for rom in results]))
            except Exception as e:
                QTimer.singleShot(0, lambda: callback([]))
        
        thread = Thread(target=search_worker, daemon=True)
        thread.start()
    
    def get_random_roms_async(self, search_filter: SearchFilter, callback: Callable):
        """Get random ROMs in background thread."""
        def random_worker():
            try:
                # Use synchronous random search
                results = self.search_engine.get_random_roms_sync(10, search_filter)
                QTimer.singleShot(0, lambda: callback(results))
            except Exception as e:
                QTimer.singleShot(0, lambda: callback([]))
        
        thread = Thread(target=random_worker, daemon=True)
        thread.start()
    
    def show_rom_info(self, rom: ROMEntry):
        """Show ROM information dialog."""
        region_str = rom.regions[0] if rom.regions else 'N/A'
        info_text = f"""
Title: {rom.title}
Platform: {rom.platform}
Region: {region_str}
        """
        
        if hasattr(rom, 'year') and rom.year:
            info_text += f"Year: {rom.year}\n"
        
        size_mb = rom.get_size_mb()
        if size_mb > 0:
            info_text += f"Size: {size_mb:.1f} MB\n"
        
        if rom.description:
            info_text += f"\nDescription: {rom.description}"
        
        QMessageBox.information(self.main_window, f"ROM Info: {rom.title}", info_text)
    
    def start_download(self, roms: List[ROMEntry]):
        """Start downloading ROMs."""
        download_screen = DownloadScreen(self, roms)
        self.main_window.central_widget.addWidget(download_screen)
        self.main_window.central_widget.setCurrentWidget(download_screen)
    
    def start_download_process(self, roms: List[ROMEntry], progress_callback: Callable, complete_callback: Callable):
        """Start download process in background thread."""
        self.download_cancelled = False
        
        def download_worker():
            successful = 0
            log_messages = []
            
            for i, rom in enumerate(roms):
                if self.download_cancelled:
                    break
                
                log_messages.append(f"Starting download: {rom.title}")
                
                try:
                    def progress_handler(progress: DownloadProgress):
                        QTimer.singleShot(0, lambda: progress_callback(progress, rom.title, i + 1, len(roms)))
                    
                    result = self.download_manager.download_rom(rom, progress_callback=progress_handler)
                    
                    if result.success:
                        log_messages.append(f"✓ Downloaded: {rom.title}")
                        successful += 1
                    else:
                        log_messages.append(f"✗ Failed: {rom.title} - {result.error}")
                
                except Exception as e:
                    log_messages.append(f"✗ Error: {rom.title} - {e}")
            
            QTimer.singleShot(0, lambda: complete_callback(successful, len(roms), log_messages))
        
        self.download_thread = Thread(target=download_worker, daemon=True)
        self.download_thread.start()
    
    def cancel_download(self):
        """Cancel ongoing download."""
        self.download_cancelled = True
    
    def handle_gamepad_button(self, button: int):
        """Handle gamepad button presses."""
        # Map common gamepad buttons
        if button == 0:  # A button - Select/Confirm
            self.simulate_key_press(Qt.Key.Key_Return)
        elif button == 1:  # B button - Back/Cancel
            self.simulate_key_press(Qt.Key.Key_Escape)
        elif button == 2:  # X button - Download
            self.simulate_key_press(Qt.Key.Key_Space)
        elif button == 3:  # Y button - Info
            self.simulate_key_press(Qt.Key.Key_I)
    
    def handle_gamepad_dpad(self, direction: str):
        """Handle gamepad D-pad movement."""
        key_map = {
            'up': Qt.Key.Key_Up,
            'down': Qt.Key.Key_Down,
            'left': Qt.Key.Key_Left,
            'right': Qt.Key.Key_Right
        }
        
        if direction in key_map:
            self.simulate_key_press(key_map[direction])
    
    def simulate_key_press(self, key: Qt.Key):
        """Simulate a key press event."""
        focused_widget = QApplication.focusWidget()
        if focused_widget:
            event = QKeyEvent(QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.NoModifier)
            QApplication.postEvent(focused_widget, event)
    
    def close(self):
        """Close the application."""
        if hasattr(self, 'download_cancelled'):
            self.download_cancelled = True
        if hasattr(self, 'main_window'):
            self.main_window.close()
    
    def closeEvent(self, event):
        """Handle application close event."""
        self.gamepad.stop()
        if hasattr(self, 'download_cancelled'):
            self.download_cancelled = True
        event.accept()
    
    def run_interface(self) -> int:
        """
        Run the GUI interface.
        
        Returns:
            Exit code
        """
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # Create main window using the new MainWindow class
            self.main_window = MainWindow(self)
            
            # Set close event handler
            self.main_window.closeEvent = self.closeEvent
            
            self.main_window.show()
            return app.exec()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.logger.error(f"GUI error: {e}")
            print(f"{t('errors.general')}: {e}")
            return 1
    
    def run(self) -> int:
        """
        Alias for run_interface() to maintain compatibility.
        
        Returns:
            Exit code
        """
        return self.run_interface()