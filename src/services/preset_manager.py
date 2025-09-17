import json
import os
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from pathlib import Path

from ..models.preset import Preset
from ..models.effects_chain import EffectsChain


class PresetManager:
    """Service for saving, loading, and managing effect chain presets"""

    def __init__(self, presets_directory: Optional[str] = None):
        if presets_directory:
            self.presets_dir = Path(presets_directory)
        else:
            # Default to user's home directory
            self.presets_dir = Path.home() / ".pedalboard" / "presets"

        # Ensure presets directory exists
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        # In-memory preset storage for quick access
        self._presets: Dict[UUID, Preset] = {}
        self._preset_names: Dict[str, UUID] = {}  # For name uniqueness checking

        # Load existing presets
        self._load_all_presets()

    def list_presets(self, tags: Optional[List[str]] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all presets with optional filtering"""
        preset_summaries = []

        for preset in self._presets.values():
            # Apply tag filter
            if tags:
                if not any(tag in preset.tags for tag in tags):
                    continue

            # Apply search filter
            if search:
                if not preset.matches_search(search):
                    continue

            # Create preset summary
            summary = {
                "id": str(preset.id),
                "name": preset.name,
                "description": preset.description,
                "created_at": preset.created_at.isoformat(),
                "tags": preset.tags.copy(),
                "effect_count": preset.get_effect_count()
            }
            preset_summaries.append(summary)

        # Sort by name
        preset_summaries.sort(key=lambda x: x["name"].lower())
        return preset_summaries

    def save_preset(self, preset_config: Dict[str, Any]) -> Preset:
        """Save a new preset"""
        # Validate required fields
        if "name" not in preset_config:
            raise ValueError("Invalid preset data: missing name")

        if "effects_chain_config" not in preset_config:
            raise ValueError("Invalid preset data: missing effects_chain_config")

        # Check for duplicate name
        if self._preset_name_exists(preset_config["name"]):
            raise ValueError("Preset name already exists")

        try:
            # Create preset from config
            preset = Preset(
                name=preset_config["name"],
                effects_chain_config=preset_config["effects_chain_config"],
                description=preset_config.get("description"),
                tags=preset_config.get("tags"),
                author=preset_config.get("author"),
                version=preset_config.get("version", "1.0.0")
            )

            # Save to file
            self._save_to_file(preset)

            # Add to in-memory storage
            self._presets[preset.id] = preset
            self._preset_names[preset.name] = preset.id

            return preset

        except Exception as e:
            raise RuntimeError(f"Failed to save preset: {e}")

    def get_preset(self, preset_id: UUID) -> Preset:
        """Get a preset by ID"""
        if preset_id not in self._presets:
            # Try to load from file
            preset = self._load_from_file(preset_id)
            if not preset:
                raise ValueError("Preset not found")
            return preset

        return self._presets[preset_id]

    def update_preset(self, preset_id: UUID, update_config: Dict[str, Any]) -> Preset:
        """Update an existing preset"""
        if preset_id not in self._presets:
            raise ValueError("Preset not found")

        preset = self._presets[preset_id]

        # Check for name conflict if name is being changed
        if "name" in update_config and update_config["name"] != preset.name:
            # Check if another preset has this name (excluding current preset)
            existing_id = self._preset_names.get(update_config["name"])
            if existing_id and existing_id != preset_id:
                raise ValueError("Preset name already exists")

            # Update name mapping
            del self._preset_names[preset.name]
            self._preset_names[update_config["name"]] = preset_id

        try:
            # Add small delay to ensure modified time changes
            import time
            time.sleep(0.001)

            # Update preset
            preset.update(
                name=update_config.get("name"),
                description=update_config.get("description"),
                tags=update_config.get("tags"),
                effects_chain_config=update_config.get("effects_chain_config")
            )

            # Save updated preset to file
            self._save_to_file(preset)

            return preset

        except Exception as e:
            raise ValueError(f"Invalid preset data: {e}")

    def delete_preset(self, preset_id: UUID) -> bool:
        """Delete a preset"""
        if preset_id not in self._presets:
            raise ValueError("Preset not found")

        preset = self._presets[preset_id]

        try:
            # Remove file
            preset_file = self.presets_dir / f"{preset_id}.json"
            if preset_file.exists():
                preset_file.unlink()

            # Remove from memory
            del self._presets[preset_id]
            del self._preset_names[preset.name]

            return True

        except Exception as e:
            raise RuntimeError(f"Failed to delete preset: {e}")

    def load_preset(self, preset_id: UUID) -> EffectsChain:
        """Load a preset and create effects chain"""
        preset = self.get_preset(preset_id)

        try:
            return preset.to_effects_chain()
        except Exception as e:
            raise RuntimeError(f"Failed to load preset: {e}")

    def export_presets(self, export_config: Dict[str, Any]) -> bytes:
        """Export multiple presets to a file"""
        if "preset_ids" not in export_config or not export_config["preset_ids"]:
            raise ValueError("Invalid export request: missing or empty preset_ids")

        format_type = export_config.get("format", "json")
        if format_type != "json":
            raise ValueError("Only JSON format is currently supported")

        try:
            presets_data = []

            for preset_id_str in export_config["preset_ids"]:
                preset_id = UUID(preset_id_str) if isinstance(preset_id_str, str) else preset_id_str
                if preset_id in self._presets:
                    preset = self._presets[preset_id]
                    presets_data.append(preset.to_dict())

            # Export as JSON
            export_json = json.dumps(presets_data, indent=2)
            return export_json.encode('utf-8')

        except Exception as e:
            raise RuntimeError(f"Export failed: {e}")

    def import_presets(self, import_config: Dict[str, Any]) -> Dict[str, Any]:
        """Import presets from a file"""
        if "file" not in import_config:
            raise ValueError("Invalid import file: missing file data")

        file_data = import_config["file"]
        overwrite_existing = import_config.get("overwrite_existing", False)

        try:
            # Parse JSON data
            if isinstance(file_data, bytes):
                json_str = file_data.decode('utf-8')
            else:
                json_str = file_data

            presets_data = json.loads(json_str)

            if not isinstance(presets_data, list):
                raise ValueError("Invalid file format: expected list of presets")

            imported_count = 0
            skipped_count = 0
            errors = []

            for preset_data in presets_data:
                try:
                    # Create preset from imported data
                    imported_preset = Preset.from_dict(preset_data)

                    # Check for name conflicts
                    if self._preset_name_exists(imported_preset.name) and not overwrite_existing:
                        skipped_count += 1
                        continue

                    # If overwriting, remove existing preset
                    if self._preset_name_exists(imported_preset.name) and overwrite_existing:
                        existing_id = self._preset_names[imported_preset.name]
                        self.delete_preset(existing_id)

                    # Generate new ID and save
                    imported_preset.id = uuid4()
                    self._save_to_file(imported_preset)
                    self._presets[imported_preset.id] = imported_preset
                    self._preset_names[imported_preset.name] = imported_preset.id

                    imported_count += 1

                except Exception as e:
                    errors.append(f"Failed to import preset '{preset_data.get('name', 'unknown')}': {e}")

            return {
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors
            }

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid import file: invalid JSON format")
        except Exception as e:
            raise ValueError(f"Invalid import file: {e}")

    def _save_to_file(self, preset: Preset) -> None:
        """Save preset to file"""
        preset_file = self.presets_dir / f"{preset.id}.json"

        try:
            with open(preset_file, 'w', encoding='utf-8') as f:
                f.write(preset.to_json())
        except Exception as e:
            raise IOError(f"Failed to save preset file: {e}")

    def _load_from_file(self, preset_id: UUID) -> Optional[Preset]:
        """Load preset from file"""
        preset_file = self.presets_dir / f"{preset_id}.json"

        if not preset_file.exists():
            return None

        try:
            with open(preset_file, 'r', encoding='utf-8') as f:
                json_str = f.read()

            preset = Preset.from_json(json_str)
            # Add to memory cache
            self._presets[preset.id] = preset
            self._preset_names[preset.name] = preset.id

            return preset

        except Exception as e:
            print(f"Error loading preset {preset_id}: {e}")
            return None

    def _load_all_presets(self) -> None:
        """Load all presets from the presets directory"""
        if not self.presets_dir.exists():
            return

        for preset_file in self.presets_dir.glob("*.json"):
            try:
                preset_id = UUID(preset_file.stem)
                self._load_from_file(preset_id)
            except Exception as e:
                print(f"Error loading preset file {preset_file}: {e}")

    def _preset_name_exists(self, name: str) -> bool:
        """Check if a preset name already exists"""
        return name in self._preset_names

    def _get_preset_by_id(self, preset_id: UUID) -> Optional[Preset]:
        """Internal method to get preset by ID (for testing)"""
        return self._presets.get(preset_id)

    def get_presets_directory(self) -> Path:
        """Get the presets directory path"""
        return self.presets_dir

    def get_preset_count(self) -> int:
        """Get total number of presets"""
        return len(self._presets)

    def clear_all_presets(self) -> int:
        """Clear all presets (for testing/debugging)"""
        count = len(self._presets)

        # Remove all files
        for preset_file in self.presets_dir.glob("*.json"):
            try:
                preset_file.unlink()
            except Exception:
                pass

        # Clear memory
        self._presets.clear()
        self._preset_names.clear()

        return count