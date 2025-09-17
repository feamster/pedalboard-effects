from enum import Enum
from uuid import UUID, uuid4
from typing import Dict, Any, Optional
from datetime import datetime


class EffectType(Enum):
    BOOST = "BOOST"
    DISTORTION = "DISTORTION"
    DELAY = "DELAY"
    REVERB = "REVERB"


class AudioEffect:
    """Individual processing unit with configurable parameters"""

    # Parameter definitions for each effect type
    PARAMETER_DEFINITIONS = {
        EffectType.BOOST: {
            "gain_db": {"min": -20.0, "max": 30.0, "default": 0.0, "units": "dB", "curve": "linear"},
            "tone": {"min": 0.0, "max": 1.0, "default": 0.5, "units": "", "curve": "linear"}
        },
        EffectType.DISTORTION: {
            "drive_db": {"min": 0.0, "max": 30.0, "default": 10.0, "units": "dB", "curve": "linear"},
            "tone": {"min": 0.0, "max": 1.0, "default": 0.5, "units": "", "curve": "linear"},
            "level": {"min": 0.0, "max": 1.0, "default": 0.7, "units": "", "curve": "linear"}
        },
        EffectType.DELAY: {
            "delay_seconds": {"min": 0.0, "max": 2.0, "default": 0.25, "units": "s", "curve": "linear"},
            "feedback": {"min": 0.0, "max": 0.95, "default": 0.3, "units": "", "curve": "linear"},
            "mix": {"min": 0.0, "max": 1.0, "default": 0.3, "units": "", "curve": "linear"},
            "tempo_sync": {"min": 0, "max": 1, "default": False, "units": "bool", "curve": "linear"}
        },
        EffectType.REVERB: {
            "room_size": {"min": 0.0, "max": 1.0, "default": 0.5, "units": "", "curve": "linear"},
            "damping": {"min": 0.0, "max": 1.0, "default": 0.5, "units": "", "curve": "linear"},
            "wet_level": {"min": 0.0, "max": 1.0, "default": 0.3, "units": "", "curve": "linear"},
            "dry_level": {"min": 0.0, "max": 1.0, "default": 0.7, "units": "", "curve": "linear"}
        }
    }

    def __init__(self, effect_type: EffectType, parameters: Optional[Dict[str, Any]] = None):
        if isinstance(effect_type, str):
            try:
                effect_type = EffectType(effect_type)
            except ValueError:
                raise ValueError(f"Invalid effect type: {effect_type}")

        if not isinstance(effect_type, EffectType):
            raise ValueError(f"Invalid effect type: {effect_type}")

        self.id = uuid4()
        self.type = effect_type
        self.bypassed = False
        self.position = 0
        self.preset_name: Optional[str] = None

        # Initialize parameters with defaults
        self.parameters = {}
        param_defs = self.PARAMETER_DEFINITIONS[effect_type]

        for param_name, param_def in param_defs.items():
            self.parameters[param_name] = param_def["default"]

        # Apply custom parameters if provided
        if parameters:
            self.update_parameters(parameters)

    def update_parameters(self, new_parameters: Dict[str, Any]) -> None:
        """Update effect parameters with validation"""
        param_defs = self.PARAMETER_DEFINITIONS[self.type]

        for param_name, param_value in new_parameters.items():
            if param_name not in param_defs:
                raise ValueError(f"Unknown parameter '{param_name}' for effect type {self.type.value}")

            param_def = param_defs[param_name]
            min_val = param_def["min"]
            max_val = param_def["max"]

            # Special handling for boolean parameters
            if param_def["units"] == "bool":
                if param_value not in [True, False, 0, 1]:
                    raise ValueError(f"{param_name} must be a boolean value")
                param_value = bool(param_value)
            else:
                if not isinstance(param_value, (int, float)):
                    raise ValueError(f"{param_name} must be a numeric value")

                if param_value < min_val or param_value > max_val:
                    raise ValueError(f"{param_name} must be between {min_val} and {max_val}")

            self.parameters[param_name] = param_value

    def get_parameter_info(self, param_name: str) -> Dict[str, Any]:
        """Get parameter metadata including value, range, and units"""
        if param_name not in self.parameters:
            raise ValueError(f"Parameter '{param_name}' not found")

        param_def = self.PARAMETER_DEFINITIONS[self.type][param_name]

        return {
            "value": self.parameters[param_name],
            "min_value": param_def["min"],
            "max_value": param_def["max"],
            "default_value": param_def["default"],
            "units": param_def["units"],
            "curve_type": param_def["curve"]
        }

    def get_all_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """Get metadata for all parameters"""
        result = {}
        for param_name in self.parameters.keys():
            result[param_name] = self.get_parameter_info(param_name)
        return result

    def set_bypassed(self, bypassed: bool) -> None:
        """Set effect bypass state"""
        self.bypassed = bypassed

    def set_position(self, position: int) -> None:
        """Set effect position in chain"""
        if position < 0:
            raise ValueError("Position must be non-negative")
        self.position = position

    def set_preset_name(self, preset_name: Optional[str]) -> None:
        """Set preset name for effect"""
        self.preset_name = preset_name

    def to_dict(self) -> Dict[str, Any]:
        """Convert effect to dictionary for serialization"""
        return {
            "id": str(self.id),
            "type": self.type.value,
            "parameters": self.parameters.copy(),
            "bypassed": self.bypassed,
            "position": self.position,
            "preset_name": self.preset_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioEffect':
        """Create effect from dictionary"""
        effect_type = EffectType(data["type"])
        effect = cls(effect_type, data.get("parameters", {}))

        if "id" in data:
            effect.id = UUID(data["id"])
        effect.bypassed = data.get("bypassed", False)
        effect.position = data.get("position", 0)
        effect.preset_name = data.get("preset_name")

        return effect

    def copy(self) -> 'AudioEffect':
        """Create a copy of this effect with new ID"""
        effect_dict = self.to_dict()
        new_effect = self.from_dict(effect_dict)
        new_effect.id = uuid4()  # Generate new ID for copy
        return new_effect

    def __eq__(self, other) -> bool:
        """Compare effects by ID"""
        if not isinstance(other, AudioEffect):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        return f"AudioEffect(type={self.type.value}, id={self.id}, bypassed={self.bypassed})"