import json
import re
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from datetime import datetime

from .effects_chain import EffectsChain
from .audio_effect import AudioEffect, EffectType


class Preset:
    """Saved configuration of complete effects chain"""

    def __init__(
        self,
        name: str,
        effects_chain_config: Dict[str, Any],
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        version: str = "1.0.0"
    ):
        # Validate name
        if not name or len(name) < 1 or len(name) > 100:
            raise ValueError("Preset name must be 1-100 characters")

        # Validate description
        if description is not None and len(description) > 500:
            raise ValueError("Description maximum 500 characters")

        # Validate tags
        if tags:
            for tag in tags:
                if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                    raise ValueError("Tags must be alphanumeric with hyphens/underscores only")

        self.id = uuid4()
        self.name = name
        self.description = description
        self.effects_chain_config = effects_chain_config
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        self.tags = tags or []
        self.author = author
        self.version = version

    @classmethod
    def from_effects_chain(
        cls,
        effects_chain: EffectsChain,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        version: str = "1.0.0"
    ) -> 'Preset':
        """Create a preset from an existing effects chain"""
        effects_config = []

        for effect in effects_chain.effects:
            effect_config = {
                "type": effect.type.value,
                "parameters": effect.parameters.copy(),
                "bypassed": effect.bypassed
            }
            if effect.preset_name:
                effect_config["preset_name"] = effect.preset_name

            effects_config.append(effect_config)

        chain_config = {
            "name": effects_chain.name,
            "effects": effects_config
        }

        return cls(
            name=name,
            effects_chain_config=chain_config,
            description=description,
            tags=tags,
            author=author,
            version=version
        )

    def to_effects_chain(self) -> EffectsChain:
        """Create an effects chain from this preset"""
        # Use preset name as chain name
        chain = EffectsChain(name=self.name)

        for effect_config in self.effects_chain_config.get("effects", []):
            effect_type = EffectType(effect_config["type"])
            effect = AudioEffect(
                effect_type=effect_type,
                parameters=effect_config.get("parameters", {})
            )

            # Set additional properties
            effect.set_bypassed(effect_config.get("bypassed", False))

            if "preset_name" in effect_config:
                effect.set_preset_name(effect_config["preset_name"])

            chain.add_effect(effect)

        return chain

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "effects_chain_config": self.effects_chain_config.copy(),
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "tags": self.tags.copy(),
            "author": self.author,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Preset':
        """Create preset from dictionary"""
        preset = cls(
            name=data["name"],
            effects_chain_config=data["effects_chain_config"],
            description=data.get("description"),
            tags=data.get("tags", []),
            author=data.get("author"),
            version=data.get("version", "1.0.0")
        )

        if "id" in data:
            preset.id = UUID(data["id"])

        if "created_at" in data:
            preset.created_at = datetime.fromisoformat(data["created_at"])

        if "modified_at" in data:
            preset.modified_at = datetime.fromisoformat(data["modified_at"])

        return preset

    def to_json(self) -> str:
        """Convert preset to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Preset':
        """Create preset from JSON string"""
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Invalid preset data: {e}")

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        effects_chain_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update preset properties"""
        if name is not None:
            if len(name) < 1 or len(name) > 100:
                raise ValueError("Preset name must be 1-100 characters")
            self.name = name

        if description is not None:
            if len(description) > 500:
                raise ValueError("Description maximum 500 characters")
            self.description = description

        if tags is not None:
            for tag in tags:
                if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                    raise ValueError("Tags must be alphanumeric with hyphens/underscores only")
            self.tags = tags

        if effects_chain_config is not None:
            self.effects_chain_config = effects_chain_config

        self.modified_at = datetime.now()

    def get_effect_count(self) -> int:
        """Get number of effects in this preset"""
        return len(self.effects_chain_config.get("effects", []))

    def has_tag(self, tag: str) -> bool:
        """Check if preset has a specific tag"""
        return tag in self.tags

    def matches_search(self, search_term: str) -> bool:
        """Check if preset matches search term in name or description"""
        search_lower = search_term.lower()
        name_match = search_lower in self.name.lower()
        desc_match = (
            self.description is not None and
            search_lower in self.description.lower()
        )
        return name_match or desc_match

    def copy(self, new_name: Optional[str] = None) -> 'Preset':
        """Create a copy of this preset with new ID"""
        copy_name = new_name if new_name else f"{self.name} (Copy)"

        preset_copy = Preset(
            name=copy_name,
            effects_chain_config=self.effects_chain_config.copy(),
            description=self.description,
            tags=self.tags.copy() if self.tags else None,
            author=self.author,
            version=self.version
        )

        return preset_copy

    def __eq__(self, other) -> bool:
        """Compare presets by ID"""
        if not isinstance(other, Preset):
            return False
        return self.id == other.id

    def __repr__(self) -> str:
        effect_count = self.get_effect_count()
        return f"Preset(name='{self.name}', effects={effect_count}, tags={self.tags})"