import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..models.audio_interface import AudioInterface


class ConfigurationService:
    """Service for application settings and device configuration persistence"""

    def __init__(self, config_directory: Optional[str] = None):
        if config_directory:
            self.config_dir = Path(config_directory)
        else:
            # Default to user's home directory
            self.config_dir = Path.home() / ".pedalboard"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file paths
        self.audio_config_file = self.config_dir / "audio_config.json"
        self.ui_config_file = self.config_dir / "ui_config.json"
        self.app_config_file = self.config_dir / "app_config.json"

        # Default configurations
        self._default_audio_config = {
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_device": "Scarlett 18i8 USB",
            "output_device": "Scarlett 18i8 USB",
            "input_channels": [0, 1],  # Both input 1 (vocal) and input 2 (guitar)
            "output_channels": [0, 1],
            "auto_connect": True,
            "low_latency_mode": True
        }

        self._default_ui_config = {
            "window_width": 800,
            "window_height": 600,
            "window_x": 100,
            "window_y": 100,
            "theme": "dark",
            "show_advanced_controls": False,
            "parameter_update_rate": 60,  # Hz
            "meter_update_rate": 30,      # Hz
            "auto_save_presets": True
        }

        self._default_app_config = {
            "version": "1.0.0",
            "last_preset_id": None,
            "auto_load_last_preset": True,
            "check_for_updates": True,
            "telemetry_enabled": False,
            "log_level": "INFO",
            "max_recent_presets": 10,
            "recent_presets": []
        }

        # Load configurations
        self._audio_config = self._load_or_create_config(
            self.audio_config_file, self._default_audio_config
        )
        self._ui_config = self._load_or_create_config(
            self.ui_config_file, self._default_ui_config
        )
        self._app_config = self._load_or_create_config(
            self.app_config_file, self._default_app_config
        )

    def get_audio_config(self) -> Dict[str, Any]:
        """Get current audio configuration"""
        return self._audio_config.copy()

    def set_audio_config(self, config: Dict[str, Any]) -> None:
        """Update audio configuration"""
        # Validate audio configuration
        self._validate_audio_config(config)

        # Update configuration
        self._audio_config.update(config)

        # Save to file
        self._save_config(self.audio_config_file, self._audio_config)

    def get_ui_config(self) -> Dict[str, Any]:
        """Get current UI configuration"""
        return self._ui_config.copy()

    def set_ui_config(self, config: Dict[str, Any]) -> None:
        """Update UI configuration"""
        # Validate UI configuration
        self._validate_ui_config(config)

        # Update configuration
        self._ui_config.update(config)

        # Save to file
        self._save_config(self.ui_config_file, self._ui_config)

    def get_app_config(self) -> Dict[str, Any]:
        """Get current application configuration"""
        return self._app_config.copy()

    def set_app_config(self, config: Dict[str, Any]) -> None:
        """Update application configuration"""
        # Update configuration
        self._app_config.update(config)

        # Save to file
        self._save_config(self.app_config_file, self._app_config)

    def create_audio_interface(self) -> AudioInterface:
        """Create AudioInterface from current configuration"""
        config = self.get_audio_config()

        # Use default devices if not specified
        input_device = config["input_device"] or "Default Input"
        output_device = config["output_device"] or "Default Output"

        audio_interface = AudioInterface(
            input_device_name=input_device,
            output_device_name=output_device,
            sample_rate=config["sample_rate"],
            buffer_size=config["buffer_size"]
        )

        audio_interface.set_input_channels(config["input_channels"])
        audio_interface.set_output_channels(config["output_channels"])

        return audio_interface

    def save_audio_interface_config(self, audio_interface: AudioInterface) -> None:
        """Save AudioInterface configuration"""
        config = {
            "input_device": audio_interface.input_device_name,
            "output_device": audio_interface.output_device_name,
            "sample_rate": audio_interface.sample_rate,
            "buffer_size": audio_interface.buffer_size,
            "input_channels": audio_interface.input_channels.copy(),
            "output_channels": audio_interface.output_channels.copy()
        }

        self.set_audio_config(config)

    def add_recent_preset(self, preset_id: str, preset_name: str) -> None:
        """Add preset to recent presets list"""
        recent_presets = self._app_config["recent_presets"]
        max_recent = self._app_config["max_recent_presets"]

        # Remove if already exists
        recent_presets = [p for p in recent_presets if p["id"] != preset_id]

        # Add to beginning
        recent_presets.insert(0, {
            "id": preset_id,
            "name": preset_name,
            "timestamp": self._get_current_timestamp()
        })

        # Limit to max recent
        recent_presets = recent_presets[:max_recent]

        # Update config
        self._app_config["recent_presets"] = recent_presets
        self._save_config(self.app_config_file, self._app_config)

    def get_recent_presets(self) -> List[Dict[str, Any]]:
        """Get list of recent presets"""
        return self._app_config["recent_presets"].copy()

    def set_last_preset(self, preset_id: str) -> None:
        """Set the last used preset"""
        self._app_config["last_preset_id"] = preset_id
        self._save_config(self.app_config_file, self._app_config)

    def get_last_preset(self) -> Optional[str]:
        """Get the last used preset ID"""
        return self._app_config.get("last_preset_id")

    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry configuration"""
        return {
            "width": self._ui_config["window_width"],
            "height": self._ui_config["window_height"],
            "x": self._ui_config["window_x"],
            "y": self._ui_config["window_y"]
        }

    def set_window_geometry(self, width: int, height: int, x: int, y: int) -> None:
        """Save window geometry"""
        geometry_config = {
            "window_width": width,
            "window_height": height,
            "window_x": x,
            "window_y": y
        }
        self.set_ui_config(geometry_config)

    def get_theme(self) -> str:
        """Get current theme"""
        return self._ui_config["theme"]

    def set_theme(self, theme: str) -> None:
        """Set UI theme"""
        if theme not in ["light", "dark"]:
            raise ValueError("Theme must be 'light' or 'dark'")

        self.set_ui_config({"theme": theme})

    def reset_to_defaults(self, config_type: str) -> None:
        """Reset configuration to defaults"""
        if config_type == "audio":
            self._audio_config = self._default_audio_config.copy()
            self._save_config(self.audio_config_file, self._audio_config)
        elif config_type == "ui":
            self._ui_config = self._default_ui_config.copy()
            self._save_config(self.ui_config_file, self._ui_config)
        elif config_type == "app":
            self._app_config = self._default_app_config.copy()
            self._save_config(self.app_config_file, self._app_config)
        else:
            raise ValueError("Invalid config type")

    def export_config(self) -> Dict[str, Any]:
        """Export all configuration"""
        return {
            "audio": self._audio_config.copy(),
            "ui": self._ui_config.copy(),
            "app": self._app_config.copy()
        }

    def import_config(self, config_data: Dict[str, Any]) -> None:
        """Import configuration data"""
        if "audio" in config_data:
            self.set_audio_config(config_data["audio"])

        if "ui" in config_data:
            self.set_ui_config(config_data["ui"])

        if "app" in config_data:
            self.set_app_config(config_data["app"])

    def _load_or_create_config(self, file_path: Path, default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration from file or create with defaults"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Merge with defaults to handle new keys
                merged_config = default_config.copy()
                merged_config.update(config)
                return merged_config

            except Exception as e:
                print(f"Error loading config {file_path}: {e}")

        # Create default configuration
        config = default_config.copy()
        self._save_config(file_path, config)
        return config

    def _save_config(self, file_path: Path, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config {file_path}: {e}")

    def _validate_audio_config(self, config: Dict[str, Any]) -> None:
        """Validate audio configuration"""
        if "sample_rate" in config:
            if config["sample_rate"] not in [44100, 48000, 96000]:
                raise ValueError("Invalid sample rate")

        if "buffer_size" in config:
            if config["buffer_size"] not in [32, 64, 128, 256, 512, 1024, 2048]:
                raise ValueError("Invalid buffer size")

        if "input_channels" in config:
            if not isinstance(config["input_channels"], list) or not config["input_channels"]:
                raise ValueError("Input channels must be a non-empty list")

        if "output_channels" in config:
            if not isinstance(config["output_channels"], list) or not config["output_channels"]:
                raise ValueError("Output channels must be a non-empty list")

    def _validate_ui_config(self, config: Dict[str, Any]) -> None:
        """Validate UI configuration"""
        if "window_width" in config:
            if not isinstance(config["window_width"], int) or config["window_width"] < 400:
                raise ValueError("Window width must be at least 400 pixels")

        if "window_height" in config:
            if not isinstance(config["window_height"], int) or config["window_height"] < 300:
                raise ValueError("Window height must be at least 300 pixels")

        if "theme" in config:
            if config["theme"] not in ["light", "dark"]:
                raise ValueError("Theme must be 'light' or 'dark'")

        if "parameter_update_rate" in config:
            if not isinstance(config["parameter_update_rate"], int) or config["parameter_update_rate"] < 1:
                raise ValueError("Parameter update rate must be at least 1 Hz")

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_config_directory(self) -> Path:
        """Get configuration directory path"""
        return self.config_dir

    def backup_config(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of all configuration files"""
        import shutil
        from datetime import datetime

        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"config_backup_{timestamp}"

        backup_dir = self.config_dir / "backups" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy configuration files
        for config_file in [self.audio_config_file, self.ui_config_file, self.app_config_file]:
            if config_file.exists():
                shutil.copy2(config_file, backup_dir)

        return str(backup_dir)

    def restore_config(self, backup_name: str) -> bool:
        """Restore configuration from backup"""
        backup_dir = self.config_dir / "backups" / backup_name

        if not backup_dir.exists():
            return False

        try:
            # Restore configuration files
            for config_file in [self.audio_config_file, self.ui_config_file, self.app_config_file]:
                backup_file = backup_dir / config_file.name
                if backup_file.exists():
                    import shutil
                    shutil.copy2(backup_file, config_file)

            # Reload configurations
            self._audio_config = self._load_or_create_config(
                self.audio_config_file, self._default_audio_config
            )
            self._ui_config = self._load_or_create_config(
                self.ui_config_file, self._default_ui_config
            )
            self._app_config = self._load_or_create_config(
                self.app_config_file, self._default_app_config
            )

            return True

        except Exception as e:
            print(f"Error restoring config: {e}")
            return False