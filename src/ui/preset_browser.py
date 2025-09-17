from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QLineEdit, QTextEdit, QInputDialog, QMessageBox,
                             QGroupBox, QFrame, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from ..services.preset_manager import PresetManager
from ..services.effects_manager import EffectsManager


class PresetBrowser(QWidget):
    """Widget for browsing and managing presets"""

    preset_loaded = pyqtSignal(str)  # preset_name

    def __init__(self, preset_manager: PresetManager, effects_manager: EffectsManager, parent=None):
        super().__init__(parent)
        self.preset_manager = preset_manager
        self.effects_manager = effects_manager
        self.current_presets = []
        self.init_ui()

    def init_ui(self):
        """Initialize the preset browser UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Presets")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter preset name...")
        self.search_input.textChanged.connect(self.filter_presets)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # Preset list
        self.preset_list = QListWidget()
        self.preset_list.itemClicked.connect(self.on_preset_selected)
        self.preset_list.itemDoubleClicked.connect(self.load_selected_preset)
        layout.addWidget(self.preset_list)

        # Preset details
        details_group = QGroupBox("Preset Details")
        layout.addWidget(details_group)

        details_layout = QVBoxLayout(details_group)

        # Preset name
        self.preset_name_label = QLabel("Name: --")
        details_layout.addWidget(self.preset_name_label)

        # Preset description
        self.preset_description = QTextEdit()
        self.preset_description.setMaximumHeight(60)
        self.preset_description.setReadOnly(True)
        details_layout.addWidget(self.preset_description)

        # Effect count
        self.effect_count_label = QLabel("Effects: --")
        details_layout.addWidget(self.effect_count_label)

        # Action buttons
        button_layout = QVBoxLayout()

        # Load button
        self.load_button = QPushButton("Load Preset")
        self.load_button.clicked.connect(self.load_selected_preset)
        self.load_button.setEnabled(False)
        button_layout.addWidget(self.load_button)

        # Save button
        save_button = QPushButton("Save Current")
        save_button.clicked.connect(self.save_current_preset)
        button_layout.addWidget(save_button)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        button_layout.addWidget(separator)

        # Edit button
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_selected_preset)
        self.edit_button.setEnabled(False)
        button_layout.addWidget(self.edit_button)

        # Delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected_preset)
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.delete_button)

        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        button_layout.addWidget(separator2)

        # Export button
        export_button = QPushButton("Export...")
        export_button.clicked.connect(self.export_presets)
        button_layout.addWidget(export_button)

        # Import button
        import_button = QPushButton("Import...")
        import_button.clicked.connect(self.import_presets)
        button_layout.addWidget(import_button)

        layout.addLayout(button_layout)

        # Load initial presets
        self.refresh_presets()

    def refresh_presets(self):
        """Refresh the preset list"""
        try:
            self.current_presets = self.preset_manager.list_presets()
            self.update_preset_list()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load presets: {e}")

    def filter_presets(self):
        """Filter presets based on search text"""
        search_text = self.search_input.text().lower()

        if not search_text:
            # Show all presets
            filtered_presets = self.current_presets
        else:
            # Filter by search text
            filtered_presets = []
            for preset in self.current_presets:
                if (search_text in preset["name"].lower() or
                    (preset["description"] and search_text in preset["description"].lower())):
                    filtered_presets.append(preset)

        self.update_preset_list(filtered_presets)

    def update_preset_list(self, presets=None):
        """Update the preset list widget"""
        if presets is None:
            presets = self.current_presets

        self.preset_list.clear()

        for preset in presets:
            item = QListWidgetItem()

            # Create display text
            name = preset["name"]
            effect_count = preset["effect_count"]
            item_text = f"{name} ({effect_count} effects)"

            item.setText(item_text)
            item.setData(Qt.ItemDataRole.UserRole, preset)

            self.preset_list.addItem(item)

        # Clear selection and details
        self.clear_preset_details()

    def on_preset_selected(self, item):
        """Handle preset selection"""
        preset_data = item.data(Qt.ItemDataRole.UserRole)
        self.update_preset_details(preset_data)

        # Enable action buttons
        self.load_button.setEnabled(True)
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def update_preset_details(self, preset_data):
        """Update preset details display"""
        self.preset_name_label.setText(f"Name: {preset_data['name']}")

        description = preset_data.get("description", "")
        self.preset_description.setText(description if description else "No description")

        effect_count = preset_data["effect_count"]
        self.effect_count_label.setText(f"Effects: {effect_count}")

    def clear_preset_details(self):
        """Clear preset details display"""
        self.preset_name_label.setText("Name: --")
        self.preset_description.setText("")
        self.effect_count_label.setText("Effects: --")

        # Disable action buttons
        self.load_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def load_selected_preset(self):
        """Load the selected preset"""
        current_item = self.preset_list.currentItem()
        if not current_item:
            return

        preset_data = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            from uuid import UUID
            preset_id = UUID(preset_data["id"])

            # Load preset into effects manager
            effects_chain = self.preset_manager.load_preset(preset_id)

            # Set as current chain in effects manager
            # This is a simplified approach - in a real implementation,
            # you'd want to replace the current chain
            self.effects_manager._current_chain = effects_chain
            self.effects_manager._chains[effects_chain.id] = effects_chain

            # Emit signal
            self.preset_loaded.emit(preset_data["name"])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preset: {e}")

    def save_current_preset(self):
        """Save the current effects chain as a new preset"""
        # Get preset name from user
        name, ok = QInputDialog.getText(
            self,
            "Save Preset",
            "Enter preset name:",
            QLineEdit.EchoMode.Normal
        )

        if not ok or not name.strip():
            return

        # Get description from user
        description, ok = QInputDialog.getMultiLineText(
            self,
            "Save Preset",
            "Enter preset description (optional):",
            ""
        )

        if not ok:
            return

        try:
            # Get current effects chain
            current_chain = self.effects_manager.get_current_chain()

            # Create preset configuration
            preset_config = {
                "name": name.strip(),
                "description": description.strip() if description.strip() else None,
                "effects_chain_config": {
                    "name": current_chain.name,
                    "effects": [
                        {
                            "type": effect.type.value,
                            "parameters": effect.parameters.copy(),
                            "bypassed": effect.bypassed
                        }
                        for effect in current_chain.effects
                    ]
                },
                "tags": []
            }

            # Save preset
            self.preset_manager.save_preset(preset_config)

            # Refresh preset list
            self.refresh_presets()

            QMessageBox.information(self, "Success", f"Preset '{name}' saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preset: {e}")

    def edit_selected_preset(self):
        """Edit the selected preset"""
        current_item = self.preset_list.currentItem()
        if not current_item:
            return

        preset_data = current_item.data(Qt.ItemDataRole.UserRole)

        # Get new name
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Preset",
            "Enter new preset name:",
            QLineEdit.EchoMode.Normal,
            preset_data["name"]
        )

        if not ok:
            return

        # Get new description
        old_description = preset_data.get("description", "")
        new_description, ok = QInputDialog.getMultiLineText(
            self,
            "Edit Preset",
            "Enter preset description:",
            old_description
        )

        if not ok:
            return

        try:
            from uuid import UUID
            preset_id = UUID(preset_data["id"])

            # Update preset
            update_config = {
                "name": new_name.strip(),
                "description": new_description.strip() if new_description.strip() else None
            }

            self.preset_manager.update_preset(preset_id, update_config)

            # Refresh preset list
            self.refresh_presets()

            QMessageBox.information(self, "Success", "Preset updated successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update preset: {e}")

    def delete_selected_preset(self):
        """Delete the selected preset"""
        current_item = self.preset_list.currentItem()
        if not current_item:
            return

        preset_data = current_item.data(Qt.ItemDataRole.UserRole)

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete the preset '{preset_data['name']}'?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from uuid import UUID
            preset_id = UUID(preset_data["id"])

            # Delete preset
            self.preset_manager.delete_preset(preset_id)

            # Refresh preset list
            self.refresh_presets()

            QMessageBox.information(self, "Success", "Preset deleted successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete preset: {e}")

    def new_preset(self):
        """Create a new preset from current settings"""
        self.save_current_preset()

    def export_presets(self):
        """Export selected presets"""
        # For now, just show a message
        QMessageBox.information(
            self,
            "Export Presets",
            "Export functionality will be implemented in a future version."
        )

    def import_presets(self):
        """Import presets from file"""
        # For now, just show a message
        QMessageBox.information(
            self,
            "Import Presets",
            "Import functionality will be implemented in a future version."
        )