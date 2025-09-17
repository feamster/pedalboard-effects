from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime

from .audio_effect import AudioEffect


class EffectsChain:
    """Manages ordered sequence of audio effects and their processing flow"""

    MAX_EFFECTS = 8  # Performance constraint

    def __init__(self, name: str):
        if not name or len(name) < 1 or len(name) > 50:
            raise ValueError("Chain name must be 1-50 characters")

        self.id = uuid4()
        self.name = name
        self.effects: List[AudioEffect] = []
        self.active = False
        self.created_at = datetime.now()
        self.modified_at = datetime.now()

    def add_effect(self, effect: AudioEffect) -> None:
        """Add an effect to the end of the chain"""
        if len(self.effects) >= self.MAX_EFFECTS:
            raise ValueError(f"Maximum {self.MAX_EFFECTS} effects per chain")

        # Check for duplicate effect instances
        if effect in self.effects:
            raise ValueError("Cannot have duplicate effect instances")

        # Set position for new effect
        effect.set_position(len(self.effects))
        self.effects.append(effect)
        self._update_modified_time()

    def remove_effect(self, effect_id: UUID) -> bool:
        """Remove an effect from the chain by ID"""
        for i, effect in enumerate(self.effects):
            if effect.id == effect_id:
                removed_effect = self.effects.pop(i)
                # Update positions of remaining effects
                self._update_positions()
                self._update_modified_time()
                return True
        return False

    def reorder_effects(self, effect_ids: List[UUID]) -> None:
        """Reorder effects according to provided ID list"""
        if len(effect_ids) != len(self.effects):
            raise ValueError("Effect ID list must contain all current effects")

        # Create new effects list in specified order
        new_effects = []
        for effect_id in effect_ids:
            effect_found = False
            for effect in self.effects:
                if effect.id == effect_id:
                    new_effects.append(effect)
                    effect_found = True
                    break
            if not effect_found:
                raise ValueError(f"Effect ID {effect_id} not found in chain")

        # Update the effects list and positions
        self.effects = new_effects
        self._update_positions()
        self._update_modified_time()

    def get_effect_by_id(self, effect_id: UUID) -> Optional[AudioEffect]:
        """Get an effect by its ID"""
        for effect in self.effects:
            if effect.id == effect_id:
                return effect
        return None

    def get_effects_by_type(self, effect_type) -> List[AudioEffect]:
        """Get all effects of a specific type"""
        return [effect for effect in self.effects if effect.type == effect_type]

    def activate(self) -> None:
        """Activate the effects chain for audio processing"""
        self.active = True
        self._update_modified_time()

    def deactivate(self) -> None:
        """Deactivate the effects chain"""
        self.active = False
        self._update_modified_time()

    def clear_effects(self) -> None:
        """Remove all effects from the chain"""
        self.effects.clear()
        self._update_modified_time()

    def copy(self, new_name: Optional[str] = None) -> 'EffectsChain':
        """Create a copy of this effects chain"""
        copy_name = new_name if new_name else f"{self.name} (Copy)"
        new_chain = EffectsChain(copy_name)

        # Copy all effects
        for effect in self.effects:
            effect_copy = effect.copy()
            new_chain.add_effect(effect_copy)

        return new_chain

    def get_total_effects_count(self) -> int:
        """Get total number of effects in chain"""
        return len(self.effects)

    def get_active_effects_count(self) -> int:
        """Get number of non-bypassed effects"""
        return len([effect for effect in self.effects if not effect.bypassed])

    def has_effect_type(self, effect_type) -> bool:
        """Check if chain contains any effect of specified type"""
        return any(effect.type == effect_type for effect in self.effects)

    def _update_positions(self) -> None:
        """Update position values for all effects"""
        for i, effect in enumerate(self.effects):
            effect.set_position(i)

    def _update_modified_time(self) -> None:
        """Update the modified timestamp"""
        self.modified_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert effects chain to dictionary for serialization"""
        return {
            "id": str(self.id),
            "name": self.name,
            "effects": [effect.to_dict() for effect in self.effects],
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EffectsChain':
        """Create effects chain from dictionary"""
        chain = cls(data["name"])

        if "id" in data:
            chain.id = UUID(data["id"])

        chain.active = data.get("active", False)

        if "created_at" in data:
            chain.created_at = datetime.fromisoformat(data["created_at"])

        if "modified_at" in data:
            chain.modified_at = datetime.fromisoformat(data["modified_at"])

        # Add effects
        for effect_data in data.get("effects", []):
            effect = AudioEffect.from_dict(effect_data)
            chain.effects.append(effect)

        return chain

    def __len__(self) -> int:
        """Return number of effects in chain"""
        return len(self.effects)

    def __getitem__(self, index: int) -> AudioEffect:
        """Get effect by index"""
        return self.effects[index]

    def __iter__(self):
        """Iterate over effects in chain"""
        return iter(self.effects)

    def __repr__(self) -> str:
        return f"EffectsChain(name='{self.name}', effects={len(self.effects)}, active={self.active})"