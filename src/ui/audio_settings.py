from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QGroupBox, QSpinBox,
                             QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt

from ..services.config_service import ConfigurationService
from ..services.audio_engine import AudioEngine


class AudioSettingsDialog(QDialog):
    """Dialog for configuring audio settings"""

    def __init__(self, config_service: ConfigurationService, audio_engine: AudioEngine, parent=None):
        super().__init__(parent)
        self.config_service = config_service
        self.audio_engine = audio_engine
        self.original_config = config_service.get_audio_config()
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Audio Settings")
        self.setModal(True)
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)

        # Device selection group
        device_group = QGroupBox("Audio Devices")
        layout.addWidget(device_group)

        device_layout = QVBoxLayout(device_group)

        # Input device
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Device:"))

        self.input_combo = QComboBox()
        self.populate_input_devices()
        input_layout.addWidget(self.input_combo)

        device_layout.addLayout(input_layout)

        # Output device
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Device:"))

        self.output_combo = QComboBox()
        self.populate_output_devices()
        output_layout.addWidget(self.output_combo)

        device_layout.addLayout(output_layout)

        # Refresh devices button
        refresh_button = QPushButton("Refresh Devices")
        refresh_button.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_button)

        # Audio parameters group
        params_group = QGroupBox("Audio Parameters")
        layout.addWidget(params_group)

        params_layout = QVBoxLayout(params_group)

        # Sample rate
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Sample Rate:"))

        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["44100", "48000", "96000"])
        sample_rate_layout.addWidget(self.sample_rate_combo)

        sample_rate_layout.addWidget(QLabel("Hz"))
        sample_rate_layout.addStretch()

        params_layout.addLayout(sample_rate_layout)

        # Buffer size
        buffer_size_layout = QHBoxLayout()
        buffer_size_layout.addWidget(QLabel("Buffer Size:"))

        self.buffer_size_combo = QComboBox()
        self.buffer_size_combo.addItems(["32", "64", "128", "256", "512", "1024", "2048"])
        buffer_size_layout.addWidget(self.buffer_size_combo)

        buffer_size_layout.addWidget(QLabel("samples"))
        buffer_size_layout.addStretch()

        params_layout.addLayout(buffer_size_layout)

        # Latency info
        self.latency_label = QLabel("Estimated latency: -- ms")
        params_layout.addWidget(self.latency_label)

        # Advanced settings group
        advanced_group = QGroupBox("Advanced Settings")
        layout.addWidget(advanced_group)

        advanced_layout = QVBoxLayout(advanced_group)

        # Input channels
        input_channels_layout = QHBoxLayout()
        input_channels_layout.addWidget(QLabel("Input Channels:"))

        self.input_channels_spin = QSpinBox()
        self.input_channels_spin.setMinimum(1)
        self.input_channels_spin.setMaximum(8)
        input_channels_layout.addWidget(self.input_channels_spin)

        input_channels_layout.addStretch()
        advanced_layout.addLayout(input_channels_layout)

        # Output channels
        output_channels_layout = QHBoxLayout()
        output_channels_layout.addWidget(QLabel("Output Channels:"))

        self.output_channels_spin = QSpinBox()
        self.output_channels_spin.setMinimum(1)
        self.output_channels_spin.setMaximum(8)
        output_channels_layout.addWidget(self.output_channels_spin)

        output_channels_layout.addStretch()
        advanced_layout.addLayout(output_channels_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)

        layout.addWidget(button_box)

        # Load current settings
        self.load_current_settings()

        # Connect signals
        self.sample_rate_combo.currentTextChanged.connect(self.update_latency_estimate)
        self.buffer_size_combo.currentTextChanged.connect(self.update_latency_estimate)

        # Update initial latency estimate
        self.update_latency_estimate()

    def populate_input_devices(self):
        """Populate input device combo box"""
        devices = self.audio_engine.get_available_devices()
        self.input_combo.clear()
        self.input_combo.addItems(devices.get("input_devices", ["Default Input"]))

    def populate_output_devices(self):
        """Populate output device combo box"""
        devices = self.audio_engine.get_available_devices()
        self.output_combo.clear()
        self.output_combo.addItems(devices.get("output_devices", ["Default Output"]))

    def refresh_devices(self):
        """Refresh the device lists"""
        current_input = self.input_combo.currentText()
        current_output = self.output_combo.currentText()

        self.populate_input_devices()
        self.populate_output_devices()

        # Try to restore previous selections
        input_index = self.input_combo.findText(current_input)
        if input_index >= 0:
            self.input_combo.setCurrentIndex(input_index)

        output_index = self.output_combo.findText(current_output)
        if output_index >= 0:
            self.output_combo.setCurrentIndex(output_index)

    def load_current_settings(self):
        """Load current audio settings into the dialog"""
        config = self.config_service.get_audio_config()

        # Set device selections
        input_device = config.get("input_device", "")
        output_device = config.get("output_device", "")

        input_index = self.input_combo.findText(input_device)
        if input_index >= 0:
            self.input_combo.setCurrentIndex(input_index)

        output_index = self.output_combo.findText(output_device)
        if output_index >= 0:
            self.output_combo.setCurrentIndex(output_index)

        # Set audio parameters
        sample_rate = str(config.get("sample_rate", 48000))
        sample_rate_index = self.sample_rate_combo.findText(sample_rate)
        if sample_rate_index >= 0:
            self.sample_rate_combo.setCurrentIndex(sample_rate_index)

        buffer_size = str(config.get("buffer_size", 256))
        buffer_size_index = self.buffer_size_combo.findText(buffer_size)
        if buffer_size_index >= 0:
            self.buffer_size_combo.setCurrentIndex(buffer_size_index)

        # Set channel counts
        input_channels = config.get("input_channels", [0])
        output_channels = config.get("output_channels", [0, 1])

        self.input_channels_spin.setValue(len(input_channels))
        self.output_channels_spin.setValue(len(output_channels))

    def get_current_settings(self):
        """Get current settings from the dialog"""
        # Generate channel lists
        input_channels = list(range(self.input_channels_spin.value()))
        output_channels = list(range(self.output_channels_spin.value()))

        return {
            "input_device": self.input_combo.currentText(),
            "output_device": self.output_combo.currentText(),
            "sample_rate": int(self.sample_rate_combo.currentText()),
            "buffer_size": int(self.buffer_size_combo.currentText()),
            "input_channels": input_channels,
            "output_channels": output_channels
        }

    def update_latency_estimate(self):
        """Update the latency estimate label"""
        try:
            sample_rate = int(self.sample_rate_combo.currentText())
            buffer_size = int(self.buffer_size_combo.currentText())

            # Calculate theoretical latency
            latency_ms = (buffer_size / sample_rate) * 1000

            self.latency_label.setText(f"Estimated latency: {latency_ms:.1f} ms")

            # Add warning for high latency
            if latency_ms > 20:
                self.latency_label.setStyleSheet("color: orange;")
                self.latency_label.setText(f"Estimated latency: {latency_ms:.1f} ms (High)")
            elif latency_ms > 10:
                self.latency_label.setStyleSheet("color: yellow;")
                self.latency_label.setText(f"Estimated latency: {latency_ms:.1f} ms (Moderate)")
            else:
                self.latency_label.setStyleSheet("color: green;")
                self.latency_label.setText(f"Estimated latency: {latency_ms:.1f} ms (Low)")

        except ValueError:
            self.latency_label.setText("Estimated latency: -- ms")
            self.latency_label.setStyleSheet("")

    def apply_settings(self):
        """Apply settings without closing dialog"""
        try:
            new_config = self.get_current_settings()
            self.config_service.set_audio_config(new_config)

            QMessageBox.information(
                self,
                "Settings Applied",
                "Audio settings have been applied successfully.\n\n"
                "Note: If audio is currently running, you may need to\n"
                "restart it for changes to take effect."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply audio settings:\n{e}"
            )

    def accept(self):
        """Accept dialog and save settings"""
        try:
            new_config = self.get_current_settings()
            self.config_service.set_audio_config(new_config)
            super().accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save audio settings:\n{e}"
            )

    def reject(self):
        """Reject dialog and restore original settings"""
        # Restore original configuration
        self.config_service.set_audio_config(self.original_config)
        super().reject()

    def test_audio_configuration(self):
        """Test the current audio configuration"""
        try:
            config = self.get_current_settings()

            # Validate configuration
            self.audio_engine._validate_audio_config(config)

            QMessageBox.information(
                self,
                "Test Successful",
                "Audio configuration is valid and should work correctly."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Test Failed",
                f"Audio configuration test failed:\n{e}\n\n"
                "Please check your device selections and try again."
            )