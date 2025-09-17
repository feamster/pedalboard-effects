import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QMenuBar, QMenu, QStatusBar, QLabel, QPushButton,
                             QApplication, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction

from .effects_panel import EffectsPanel
from .audio_settings import AudioSettingsDialog
from .preset_browser import PresetBrowser
from ..services.effects_manager import EffectsManager
from ..services.audio_engine import AudioEngine
from ..services.preset_manager import PresetManager
from ..services.config_service import ConfigurationService


class MainWindow(QMainWindow):
    """Main application window with PyQt6"""

    status_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        # Services
        self.effects_manager = EffectsManager()
        self.audio_engine = AudioEngine()
        self.preset_manager = PresetManager()
        self.config_service = ConfigurationService()

        # UI Components
        self.effects_panel = None
        self.preset_browser = None
        self.audio_settings_dialog = None

        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)

        # Initialize UI
        self.init_ui()
        self.setup_connections()
        self.restore_window_geometry()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Pedalboard Effects Chain")
        self.setMinimumSize(800, 600)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Effects controls
        self.effects_panel = EffectsPanel(
            self.effects_manager,
            self.audio_engine,
            parent=self
        )
        splitter.addWidget(self.effects_panel)

        # Right panel - Preset browser
        self.preset_browser = PresetBrowser(
            self.preset_manager,
            self.effects_manager,
            parent=self
        )
        splitter.addWidget(self.preset_browser)

        # Set splitter proportions (70% effects, 30% presets)
        splitter.setSizes([560, 240])

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.create_status_bar()

        # Apply dark theme
        self.apply_theme()

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        # New preset action
        new_preset_action = QAction('&New Preset', self)
        new_preset_action.setShortcut('Ctrl+N')
        new_preset_action.triggered.connect(self.new_preset)
        file_menu.addAction(new_preset_action)

        # Load preset action
        load_preset_action = QAction('&Load Preset...', self)
        load_preset_action.setShortcut('Ctrl+O')
        load_preset_action.triggered.connect(self.load_preset)
        file_menu.addAction(load_preset_action)

        # Save preset action
        save_preset_action = QAction('&Save Preset...', self)
        save_preset_action.setShortcut('Ctrl+S')
        save_preset_action.triggered.connect(self.save_preset)
        file_menu.addAction(save_preset_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Audio menu
        audio_menu = menubar.addMenu('&Audio')

        # Start/Stop audio
        self.start_audio_action = QAction('&Start Audio', self)
        self.start_audio_action.triggered.connect(self.toggle_audio)
        audio_menu.addAction(self.start_audio_action)

        audio_menu.addSeparator()

        # Audio settings
        audio_settings_action = QAction('Audio &Settings...', self)
        audio_settings_action.triggered.connect(self.show_audio_settings)
        audio_menu.addAction(audio_settings_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """Create application status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Audio status labels
        self.audio_status_label = QLabel("Audio: Stopped")
        self.latency_label = QLabel("Latency: -- ms")
        self.cpu_label = QLabel("CPU: --%")

        # Add labels to status bar
        self.status_bar.addWidget(self.audio_status_label)
        self.status_bar.addPermanentWidget(self.latency_label)
        self.status_bar.addPermanentWidget(self.cpu_label)

    def setup_connections(self):
        """Setup signal connections between components"""
        # Connect effects panel signals
        self.effects_panel.effects_changed.connect(self.on_effects_changed)

        # Connect preset browser signals
        self.preset_browser.preset_loaded.connect(self.on_preset_loaded)

        # Connect audio engine status updates
        self.audio_engine.set_status_callback(self.on_audio_status_update)

        # Start status update timer
        self.status_timer.start(100)  # Update every 100ms

    def apply_theme(self):
        """Apply dark theme to the application"""
        theme = self.config_service.get_theme()

        if theme == "dark":
            dark_style = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QFrame {
                border: 1px solid #555555;
            }
            QPushButton {
                background-color: #404040;
                border: 2px solid #606060;
                border-radius: 4px;
                padding: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #707070;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QMenuBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #404040;
            }
            QStatusBar {
                background-color: #2b2b2b;
                border-top: 1px solid #555555;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 6px;
                background: #404040;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #808080;
                border: 1px solid #606060;
                width: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #909090;
            }
            """
            self.setStyleSheet(dark_style)

    def new_preset(self):
        """Create a new preset"""
        if self.preset_browser:
            self.preset_browser.new_preset()

    def load_preset(self):
        """Load a preset"""
        if self.preset_browser:
            self.preset_browser.load_selected_preset()

    def save_preset(self):
        """Save current configuration as preset"""
        if self.preset_browser:
            self.preset_browser.save_current_preset()

    def toggle_audio(self):
        """Toggle audio processing on/off"""
        try:
            status = self.audio_engine.get_status()

            if status["active"]:
                # Stop audio
                self.audio_engine.stop_processing()
                self.start_audio_action.setText("&Start Audio")
                self.audio_status_label.setText("Audio: Stopped")
            else:
                # Start audio with current configuration
                audio_config = self.config_service.get_audio_config()
                self.audio_engine.start_processing(audio_config)

                # Set current effects chain
                current_chain = self.effects_manager.get_current_chain()
                self.audio_engine.set_effects_chain(current_chain)

                self.start_audio_action.setText("&Stop Audio")
                self.audio_status_label.setText("Audio: Running")

        except Exception as e:
            self.show_error(f"Audio error: {e}")

    def show_audio_settings(self):
        """Show audio settings dialog"""
        if not self.audio_settings_dialog:
            self.audio_settings_dialog = AudioSettingsDialog(
                self.config_service,
                self.audio_engine,
                parent=self
            )

        result = self.audio_settings_dialog.exec()
        if result:
            # Audio settings were changed, restart audio if running
            status = self.audio_engine.get_status()
            if status["active"]:
                self.audio_engine.stop_processing()
                audio_config = self.config_service.get_audio_config()
                self.audio_engine.start_processing(audio_config)

    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Pedalboard Effects",
            "Pedalboard Effects Chain v1.0.0\n\n"
            "A real-time guitar effects processor built with\n"
            "Python and Spotify's Pedalboard library.\n\n"
            "© 2025 Pedalboard Effects Project"
        )

    def show_error(self, message: str):
        """Show error message"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.critical(self, "Error", message)

    def on_effects_changed(self):
        """Handle effects chain changes"""
        # Update audio engine with new effects chain
        current_chain = self.effects_manager.get_current_chain()
        self.audio_engine.set_effects_chain(current_chain)

        # Debug info (throttled)
        if not hasattr(self, '_last_effects_debug'):
            self._last_effects_debug = ""

        active_effects = [f"{e.type.value}{'(bypassed)' if e.bypassed else ''}"
                         for e in current_chain.effects]
        effects_str = str(active_effects)

        if effects_str != self._last_effects_debug:
            print(f"Effects chain updated: {active_effects}")
            self._last_effects_debug = effects_str

    def on_preset_loaded(self, preset_name: str):
        """Handle preset loaded"""
        # Refresh effects panel to show loaded preset
        if self.effects_panel:
            self.effects_panel.refresh_effects()

        # Update status
        self.status_bar.showMessage(f"Loaded preset: {preset_name}", 3000)

    def on_audio_status_update(self, status: dict):
        """Handle audio status updates"""
        self.status_updated.emit(status)

    def update_status(self):
        """Update status bar with current information"""
        try:
            status = self.audio_engine.get_status()

            # Update latency
            latency = status.get("latency_ms", 0)
            self.latency_label.setText(f"Latency: {latency:.1f} ms")

            # Update CPU usage
            cpu = status.get("cpu_usage", 0)
            self.cpu_label.setText(f"CPU: {cpu:.0f}%")

        except Exception:
            pass  # Ignore status update errors

    def restore_window_geometry(self):
        """Restore window geometry from configuration"""
        try:
            geometry = self.config_service.get_window_geometry()
            self.resize(geometry["width"], geometry["height"])
            self.move(geometry["x"], geometry["y"])
        except Exception:
            # Use defaults if restoration fails
            pass

    def save_window_geometry(self):
        """Save current window geometry"""
        try:
            geometry = self.geometry()
            self.config_service.set_window_geometry(
                geometry.width(),
                geometry.height(),
                geometry.x(),
                geometry.y()
            )
        except Exception:
            pass  # Ignore save errors

    def closeEvent(self, event):
        """Handle application close event"""
        # Stop audio processing
        try:
            if self.audio_engine.get_status()["active"]:
                self.audio_engine.stop_processing()
        except Exception:
            pass

        # Save window geometry
        self.save_window_geometry()

        # Accept close event
        event.accept()

    def get_effects_manager(self):
        """Get effects manager (for CLI integration)"""
        return self.effects_manager

    def get_audio_engine(self):
        """Get audio engine (for CLI integration)"""
        return self.audio_engine

    def get_preset_manager(self):
        """Get preset manager (for CLI integration)"""
        return self.preset_manager