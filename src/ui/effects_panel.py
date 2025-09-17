from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSlider, QPushButton, QCheckBox, QGroupBox,
                             QScrollArea, QFrame, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ..models.audio_effect import EffectType
from ..services.effects_manager import EffectsManager
from ..services.audio_engine import AudioEngine


class EffectWidget(QWidget):
    """Widget for controlling a single effect"""

    parameter_changed = pyqtSignal(str, str, float)  # effect_id, param_name, value
    bypass_toggled = pyqtSignal(str, bool)  # effect_id, bypassed
    remove_requested = pyqtSignal(str)  # effect_id

    def __init__(self, effect, parent=None):
        super().__init__(parent)
        self.effect = effect
        self.parameter_sliders = {}
        self.updating_ui = False

        # Timer for delayed signal emission
        self.signal_timer = QTimer()
        self.signal_timer.setSingleShot(True)
        self.signal_timer.timeout.connect(self._emit_delayed_signal)
        self.pending_bypass_state = None

        self.init_ui()

    def init_ui(self):
        """Initialize the effect widget UI"""
        layout = QVBoxLayout(self)

        # Create group box for effect
        self.group_box = QGroupBox(self.effect.type.value)
        layout.addWidget(self.group_box)

        group_layout = QVBoxLayout(self.group_box)

        # Header with bypass and remove buttons
        header_layout = QHBoxLayout()

        # Bypass button
        self.bypass_button = QPushButton("Bypass: OFF")
        self.bypass_button.setCheckable(True)
        self.bypass_button.setChecked(self.effect.bypassed)
        self.bypass_button.clicked.connect(self.on_bypass_clicked)
        header_layout.addWidget(self.bypass_button)

        header_layout.addStretch()

        # Remove button
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.on_remove_clicked)
        header_layout.addWidget(remove_button)

        group_layout.addLayout(header_layout)

        # Parameters
        self.create_parameter_controls(group_layout)

        # Update initial state
        self.update_bypass_state()

    def create_parameter_controls(self, layout):
        """Create parameter control sliders"""
        param_info = self.effect.get_all_parameter_info()

        for param_name, info in param_info.items():
            param_layout = self.create_parameter_slider(param_name, info)
            layout.addLayout(param_layout)

    def create_parameter_slider(self, param_name, param_info):
        """Create a slider for a parameter"""
        layout = QVBoxLayout()

        # Parameter label with value
        value = param_info["value"]
        units = param_info["units"]
        unit_str = f" {units}" if units and units != "bool" else ""

        if units == "bool":
            # Boolean parameter - use checkbox
            checkbox = QCheckBox(param_name.replace("_", " ").title())
            checkbox.setChecked(bool(value))
            checkbox.toggled.connect(
                lambda checked, name=param_name: self.on_parameter_changed(name, float(checked))
            )
            layout.addWidget(checkbox)
            self.parameter_sliders[param_name] = checkbox
        else:
            # Numeric parameter - use slider
            label = QLabel(f"{param_name.replace('_', ' ').title()}: {value:.2f}{unit_str}")
            layout.addWidget(label)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(1000)  # Use 1000 steps for precision

            # Set current value
            min_val = param_info["min_value"]
            max_val = param_info["max_value"]
            normalized_value = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
            slider.setValue(int(normalized_value * 1000))

            slider.valueChanged.connect(
                lambda val, name=param_name, min_v=min_val, max_v=max_val, lbl=label, unit=unit_str:
                self.on_slider_changed(name, val, min_v, max_v, lbl, unit)
            )

            layout.addWidget(slider)
            self.parameter_sliders[param_name] = (slider, label)

        return layout

    def on_slider_changed(self, param_name, slider_value, min_val, max_val, label, unit_str):
        """Handle slider value change"""
        if self.updating_ui:
            return

        # Convert slider value to parameter value
        normalized = slider_value / 1000.0
        param_value = min_val + normalized * (max_val - min_val)

        # Update label
        label.setText(f"{param_name.replace('_', ' ').title()}: {param_value:.2f}{unit_str}")

        # Emit signal
        self.parameter_changed.emit(str(self.effect.id), param_name, param_value)

    def on_parameter_changed(self, param_name, value):
        """Handle parameter change"""
        if self.updating_ui:
            return

        self.parameter_changed.emit(str(self.effect.id), param_name, value)

    def on_bypass_clicked(self):
        """Handle bypass button click"""
        if self.updating_ui:
            return

        # Update effect state immediately
        bypassed = self.bypass_button.isChecked()
        self.effect.set_bypassed(bypassed)
        self.update_bypass_state()

        # Schedule delayed signal emission to prevent UI freezing
        self.pending_bypass_state = bypassed
        self.signal_timer.start(10)  # 10ms delay

    def _emit_delayed_signal(self):
        """Emit the bypass signal after a short delay"""
        if self.pending_bypass_state is not None:
            self.bypass_toggled.emit(str(self.effect.id), self.pending_bypass_state)
            self.pending_bypass_state = None

    def on_remove_clicked(self):
        """Handle remove button click"""
        self.remove_requested.emit(str(self.effect.id))

    def update_bypass_state(self):
        """Update UI based on bypass state"""
        bypassed = self.bypass_button.isChecked()

        # Update button text
        self.bypass_button.setText("Bypass: ON" if bypassed else "Bypass: OFF")

        # DON'T disable the entire group box - just change visual appearance
        # self.group_box.setEnabled(not bypassed)  # This was causing the freeze!

        # Visual indication of bypass
        if bypassed:
            self.group_box.setStyleSheet("QGroupBox { color: #888888; opacity: 0.6; }")
            self.bypass_button.setStyleSheet("QPushButton { background-color: #ff6666; }")
        else:
            self.group_box.setStyleSheet("")
            self.bypass_button.setStyleSheet("")

    def update_parameter_value(self, param_name, value):
        """Update parameter value in UI"""
        self.updating_ui = True

        if param_name in self.parameter_sliders:
            control = self.parameter_sliders[param_name]

            if isinstance(control, QCheckBox):
                # Boolean parameter
                control.setChecked(bool(value))
            else:
                # Numeric parameter
                slider, label = control
                param_info = self.effect.get_parameter_info(param_name)

                min_val = param_info["min_value"]
                max_val = param_info["max_value"]
                units = param_info["units"]
                unit_str = f" {units}" if units else ""

                # Update slider
                normalized_value = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
                slider.setValue(int(normalized_value * 1000))

                # Update label
                label.setText(f"{param_name.replace('_', ' ').title()}: {value:.2f}{unit_str}")

        self.updating_ui = False

    def update_bypass_button(self, bypassed):
        """Update bypass button state from external source"""
        self.updating_ui = True
        self.bypass_button.setChecked(bypassed)
        self.update_bypass_state()
        self.updating_ui = False


class EffectsPanel(QWidget):
    """Panel for managing effects chain"""

    effects_changed = pyqtSignal()

    def __init__(self, effects_manager: EffectsManager, audio_engine: AudioEngine, parent=None):
        super().__init__(parent)
        self.effects_manager = effects_manager
        self.audio_engine = audio_engine
        self.effect_widgets = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the effects panel UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Effects Chain")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Add effect controls
        add_layout = QHBoxLayout()

        add_label = QLabel("Add Effect:")
        add_layout.addWidget(add_label)

        self.effect_combo = QComboBox()
        self.effect_combo.addItems([effect_type.value for effect_type in EffectType])
        add_layout.addWidget(self.effect_combo)

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_effect)
        add_layout.addWidget(add_button)

        add_layout.addStretch()

        layout.addLayout(add_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)

        # Scroll area for effects
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Widget to contain effect widgets
        self.effects_container = QWidget()
        self.effects_layout = QVBoxLayout(self.effects_container)
        self.effects_layout.addStretch()  # Push effects to top

        self.scroll_area.setWidget(self.effects_container)
        layout.addWidget(self.scroll_area)

        # Load initial effects
        self.refresh_effects()

    def add_effect(self):
        """Add a new effect to the chain"""
        effect_type_str = self.effect_combo.currentText()
        effect_type = EffectType(effect_type_str)

        effect_config = {
            "type": effect_type_str,
            "parameters": {}
        }

        try:
            current_chain = self.effects_manager.get_current_chain()
            self.effects_manager.add_effect_to_chain(current_chain.id, effect_config)
            self.refresh_effects()
            self.effects_changed.emit()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to add effect: {e}")

    def refresh_effects(self):
        """Refresh the effects display"""
        # Clear existing widgets
        for widget in self.effect_widgets.values():
            widget.deleteLater()
        self.effect_widgets.clear()

        # Get current effects chain
        current_chain = self.effects_manager.get_current_chain()

        # Create widgets for each effect
        for effect in current_chain.effects:
            widget = EffectWidget(effect, self)

            # Connect signals
            widget.parameter_changed.connect(self.on_parameter_changed)
            widget.bypass_toggled.connect(self.on_bypass_toggled)
            widget.remove_requested.connect(self.on_remove_effect)

            # Add to layout (insert before stretch)
            self.effects_layout.insertWidget(self.effects_layout.count() - 1, widget)
            self.effect_widgets[str(effect.id)] = widget

    def on_parameter_changed(self, effect_id, param_name, value):
        """Handle effect parameter change"""
        try:
            from uuid import UUID
            effect_uuid = UUID(effect_id)
            self.effects_manager.update_effect_parameters(effect_uuid, {param_name: value})
            self.effects_changed.emit()

        except Exception as e:
            print(f"Error updating parameter: {e}")

    def on_bypass_toggled(self, effect_id, bypassed):
        """Handle effect bypass toggle"""
        try:
            # Just emit the effects changed signal
            # The effect state was already updated in the widget
            self.effects_changed.emit()

        except Exception as e:
            print(f"Error toggling bypass: {e}")
            import traceback
            traceback.print_exc()

    def on_remove_effect(self, effect_id):
        """Handle effect removal"""
        try:
            from uuid import UUID
            effect_uuid = UUID(effect_id)
            current_chain = self.effects_manager.get_current_chain()
            self.effects_manager.remove_effect_from_chain(current_chain.id, effect_uuid)
            self.refresh_effects()
            self.effects_changed.emit()

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to remove effect: {e}")