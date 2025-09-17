from typing import Dict, Any, List, Optional
from uuid import UUID

from ..models.effects_chain import EffectsChain
from ..models.audio_effect import AudioEffect, EffectType


class EffectsManager:
    """Service for managing guitar effects chain and parameters"""

    def __init__(self):
        self._current_chain: Optional[EffectsChain] = None
        self._chains: Dict[UUID, EffectsChain] = {}

        # Create default empty chain
        self._current_chain = EffectsChain("Default Chain")
        self._chains[self._current_chain.id] = self._current_chain

    def get_current_chain(self) -> EffectsChain:
        """Get the current active effects chain"""
        if self._current_chain is None:
            # Create default chain if none exists
            self._current_chain = EffectsChain("Default Chain")
            self._chains[self._current_chain.id] = self._current_chain

        return self._current_chain

    def create_chain(self, chain_config: Dict[str, Any]) -> EffectsChain:
        """Create a new effects chain from configuration"""
        if "name" not in chain_config:
            raise ValueError("Invalid effects chain configuration: missing name")

        try:
            # Create new chain
            chain = EffectsChain(chain_config["name"])

            # Add effects if provided
            for effect_config in chain_config.get("effects", []):
                self._create_and_add_effect(chain, effect_config)

            # Store chain and set as current
            self._chains[chain.id] = chain
            self._current_chain = chain

            return chain

        except Exception as e:
            raise ValueError(f"Invalid effects chain configuration: {e}")

    def update_chain(self, chain_id: UUID, update_config: Dict[str, Any]) -> EffectsChain:
        """Update an existing effects chain"""
        if chain_id not in self._chains:
            raise ValueError("Effects chain not found")

        chain = self._chains[chain_id]

        # Update name if provided
        if "name" in update_config:
            chain.name = update_config["name"]

        # Update active state if provided
        if "active" in update_config:
            if update_config["active"]:
                chain.activate()
            else:
                chain.deactivate()

        return chain

    def add_effect_to_chain(self, chain_id: UUID, effect_config: Dict[str, Any]) -> AudioEffect:
        """Add a new effect to the specified effects chain"""
        if chain_id not in self._chains:
            raise ValueError("Effects chain not found")

        if "type" not in effect_config:
            raise ValueError("Invalid effect configuration: missing type")

        try:
            chain = self._chains[chain_id]
            effect = self._create_effect_from_config(effect_config)
            chain.add_effect(effect)
            return effect

        except Exception as e:
            raise ValueError(f"Invalid effect configuration: {e}")

    def remove_effect_from_chain(self, chain_id: UUID, effect_id: UUID) -> None:
        """Remove an effect from the effects chain"""
        if chain_id not in self._chains:
            raise ValueError("Effect or chain not found")

        chain = self._chains[chain_id]
        if not chain.remove_effect(effect_id):
            raise ValueError("Effect or chain not found")

    def reorder_effects(self, chain_id: UUID, reorder_config: Dict[str, Any]) -> EffectsChain:
        """Reorder effects in the chain"""
        if chain_id not in self._chains:
            raise ValueError("Effects chain not found")

        if "effect_ids" not in reorder_config:
            raise ValueError("Invalid reorder configuration: missing effect_ids")

        try:
            chain = self._chains[chain_id]
            effect_ids = [UUID(id_str) if isinstance(id_str, str) else id_str
                         for id_str in reorder_config["effect_ids"]]
            chain.reorder_effects(effect_ids)
            return chain

        except Exception as e:
            raise ValueError(f"Invalid reorder configuration: {e}")

    def get_effect_parameters(self, effect_id: UUID) -> Dict[str, Dict[str, Any]]:
        """Get all parameters for a specific effect with metadata"""
        effect = self._find_effect_by_id(effect_id)
        if not effect:
            raise ValueError("Effect not found")

        return effect.get_all_parameter_info()

    def update_effect_parameters(self, effect_id: UUID, parameter_updates: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Update one or more parameters for an effect"""
        effect = self._find_effect_by_id(effect_id)
        if not effect:
            raise ValueError("Effect not found")

        try:
            effect.update_parameters(parameter_updates)
            return effect.get_all_parameter_info()

        except Exception as e:
            raise ValueError(f"Invalid parameter values: {e}")

    def toggle_effect_bypass(self, effect_id: UUID, bypass_config: Dict[str, Any]) -> AudioEffect:
        """Toggle effect bypass state"""
        effect = self._find_effect_by_id(effect_id)
        if not effect:
            raise ValueError("Effect not found")

        if "bypassed" not in bypass_config:
            raise ValueError("Invalid bypass configuration: missing bypassed")

        effect.set_bypassed(bypass_config["bypassed"])
        return effect

    def get_chain_by_id(self, chain_id: UUID) -> Optional[EffectsChain]:
        """Get a chain by its ID"""
        return self._chains.get(chain_id)

    def delete_chain(self, chain_id: UUID) -> bool:
        """Delete a chain by ID"""
        if chain_id not in self._chains:
            return False

        # Don't delete the current chain without replacement
        if self._current_chain and self._current_chain.id == chain_id:
            if len(self._chains) > 1:
                # Set another chain as current
                remaining_chains = [c for c in self._chains.values() if c.id != chain_id]
                self._current_chain = remaining_chains[0]
            else:
                # Create new default chain
                self._current_chain = EffectsChain("Default Chain")
                self._chains[self._current_chain.id] = self._current_chain

        del self._chains[chain_id]
        return True

    def set_current_chain(self, chain_id: UUID) -> bool:
        """Set the current active chain"""
        if chain_id not in self._chains:
            return False

        self._current_chain = self._chains[chain_id]
        return True

    def get_all_chains(self) -> List[EffectsChain]:
        """Get all stored chains"""
        return list(self._chains.values())

    def _create_and_add_effect(self, chain: EffectsChain, effect_config: Dict[str, Any]) -> None:
        """Create an effect from config and add to chain"""
        effect = self._create_effect_from_config(effect_config)
        chain.add_effect(effect)

    def _create_effect_from_config(self, effect_config: Dict[str, Any]) -> AudioEffect:
        """Create an AudioEffect from configuration dictionary"""
        effect_type = EffectType(effect_config["type"])
        parameters = effect_config.get("parameters", {})

        effect = AudioEffect(effect_type, parameters)

        # Set additional properties
        if "position" in effect_config:
            effect.set_position(effect_config["position"])

        if "bypassed" in effect_config:
            effect.set_bypassed(effect_config["bypassed"])

        if "preset_name" in effect_config:
            effect.set_preset_name(effect_config["preset_name"])

        return effect

    def _find_effect_by_id(self, effect_id: UUID) -> Optional[AudioEffect]:
        """Find an effect by ID across all chains"""
        for chain in self._chains.values():
            effect = chain.get_effect_by_id(effect_id)
            if effect:
                return effect
        return None

    def get_effects_statistics(self) -> Dict[str, Any]:
        """Get statistics about current effects usage"""
        current_chain = self.get_current_chain()

        stats = {
            "total_chains": len(self._chains),
            "current_chain_name": current_chain.name,
            "current_chain_effects": len(current_chain.effects),
            "current_chain_active_effects": current_chain.get_active_effects_count(),
            "effect_types_in_current_chain": {}
        }

        # Count effect types in current chain
        for effect in current_chain.effects:
            effect_type = effect.type.value
            if effect_type not in stats["effect_types_in_current_chain"]:
                stats["effect_types_in_current_chain"][effect_type] = 0
            stats["effect_types_in_current_chain"][effect_type] += 1

        return stats