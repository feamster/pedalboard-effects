import pytest
import json
from uuid import UUID
from datetime import datetime
from src.models.preset import Preset
from src.models.effects_chain import EffectsChain
from src.models.audio_effect import AudioEffect, EffectType


class TestPreset:
    def test_create_preset_from_effects_chain(self):
        """Test creating a preset from an effects chain"""
        # Create effects chain
        chain = EffectsChain(name="Rock Chain")
        boost = AudioEffect(effect_type=EffectType.BOOST)
        boost.update_parameters({"gain_db": 6.0, "tone": 0.6})
        distortion = AudioEffect(effect_type=EffectType.DISTORTION)
        distortion.update_parameters({"drive_db": 15.0, "tone": 0.4})

        chain.add_effect(boost)
        chain.add_effect(distortion)

        # Create preset
        preset = Preset.from_effects_chain(
            chain,
            name="My Rock Tone",
            description="Crunchy distortion with boost",
            tags=["rock", "distortion"]
        )

        assert preset.name == "My Rock Tone"
        assert preset.description == "Crunchy distortion with boost"
        assert isinstance(preset.id, UUID)
        assert preset.tags == ["rock", "distortion"]
        assert preset.author is None
        assert isinstance(preset.created_at, datetime)
        assert preset.version == "1.0.0"

    def test_preset_name_validation(self):
        """Test preset name validation"""
        chain = EffectsChain(name="Test Chain")

        # Valid name
        preset = Preset.from_effects_chain(chain, name="Valid Name")
        assert preset.name == "Valid Name"

        # Empty name should raise error
        with pytest.raises(ValueError, match="Preset name must be 1-100 characters"):
            Preset.from_effects_chain(chain, name="")

        # Too long name should raise error
        with pytest.raises(ValueError, match="Preset name must be 1-100 characters"):
            Preset.from_effects_chain(chain, name="x" * 101)

    def test_preset_description_validation(self):
        """Test preset description validation"""
        chain = EffectsChain(name="Test Chain")

        # Valid description
        preset = Preset.from_effects_chain(
            chain,
            name="Test Preset",
            description="A" * 500  # Maximum length
        )
        assert len(preset.description) == 500

        # Too long description should raise error
        with pytest.raises(ValueError, match="Description maximum 500 characters"):
            Preset.from_effects_chain(
                chain,
                name="Test Preset",
                description="A" * 501
            )

    def test_preset_tags_validation(self):
        """Test preset tags validation"""
        chain = EffectsChain(name="Test Chain")

        # Valid tags
        preset = Preset.from_effects_chain(
            chain,
            name="Test Preset",
            tags=["rock", "metal", "lead-guitar", "effect_1"]
        )
        assert preset.tags == ["rock", "metal", "lead-guitar", "effect_1"]

        # Invalid tags should raise error
        with pytest.raises(ValueError, match="Tags must be alphanumeric with hyphens/underscores only"):
            Preset.from_effects_chain(
                chain,
                name="Test Preset",
                tags=["invalid tag with spaces"]
            )

        with pytest.raises(ValueError, match="Tags must be alphanumeric with hyphens/underscores only"):
            Preset.from_effects_chain(
                chain,
                name="Test Preset",
                tags=["invalid@tag"]
            )

    def test_save_and_load_preset(self):
        """Test saving and loading preset to/from JSON"""
        # Create complex effects chain
        chain = EffectsChain(name="Full Chain")
        boost = AudioEffect(effect_type=EffectType.BOOST)
        boost.update_parameters({"gain_db": 8.0, "tone": 0.7})
        distortion = AudioEffect(effect_type=EffectType.DISTORTION)
        distortion.update_parameters({"drive_db": 20.0, "tone": 0.3, "level": 0.8})
        delay = AudioEffect(effect_type=EffectType.DELAY)
        delay.update_parameters({"delay_seconds": 0.4, "feedback": 0.5, "mix": 0.4})
        reverb = AudioEffect(effect_type=EffectType.REVERB)
        reverb.update_parameters({"room_size": 0.6, "damping": 0.4, "wet_level": 0.4})

        chain.add_effect(boost)
        chain.add_effect(distortion)
        chain.add_effect(delay)
        chain.add_effect(reverb)

        # Create preset
        original_preset = Preset.from_effects_chain(
            chain,
            name="Full Effect Chain",
            description="All four effects configured",
            tags=["complete", "lead"],
            author="Test User"
        )

        # Save to JSON
        json_data = original_preset.to_json()

        # Verify JSON is valid
        parsed_json = json.loads(json_data)
        assert parsed_json["name"] == "Full Effect Chain"
        assert len(parsed_json["effects_chain_config"]["effects"]) == 4

        # Load from JSON
        loaded_preset = Preset.from_json(json_data)

        # Verify loaded preset matches original
        assert loaded_preset.name == original_preset.name
        assert loaded_preset.description == original_preset.description
        assert loaded_preset.tags == original_preset.tags
        assert loaded_preset.author == original_preset.author
        assert loaded_preset.version == original_preset.version

        # Verify effects chain configuration
        loaded_config = loaded_preset.effects_chain_config
        original_config = original_preset.effects_chain_config

        assert loaded_config["name"] == original_config["name"]
        assert len(loaded_config["effects"]) == len(original_config["effects"])

    def test_restore_effects_chain_from_preset(self):
        """Test restoring an effects chain from a preset"""
        # Create original chain
        original_chain = EffectsChain(name="Original Chain")
        boost = AudioEffect(effect_type=EffectType.BOOST)
        boost.update_parameters({"gain_db": 12.0, "tone": 0.9})
        distortion = AudioEffect(effect_type=EffectType.DISTORTION)
        distortion.update_parameters({"drive_db": 25.0})

        original_chain.add_effect(boost)
        original_chain.add_effect(distortion)

        # Create preset
        preset = Preset.from_effects_chain(original_chain, name="Test Restore")

        # Restore chain from preset
        restored_chain = preset.to_effects_chain()

        # Verify restored chain matches original
        assert restored_chain.name == "Test Restore"  # Uses preset name
        assert len(restored_chain.effects) == 2

        # Verify first effect (boost)
        restored_boost = restored_chain.effects[0]
        assert restored_boost.type == EffectType.BOOST
        assert restored_boost.parameters["gain_db"] == 12.0
        assert restored_boost.parameters["tone"] == 0.9

        # Verify second effect (distortion)
        restored_distortion = restored_chain.effects[1]
        assert restored_distortion.type == EffectType.DISTORTION
        assert restored_distortion.parameters["drive_db"] == 25.0

    def test_preset_unique_name_requirement(self):
        """Test that preset names should be unique (business rule)"""
        # This test documents the requirement - actual uniqueness
        # enforcement would be in the PresetManager service
        chain = EffectsChain(name="Test Chain")

        preset1 = Preset.from_effects_chain(chain, name="Unique Name")
        preset2 = Preset.from_effects_chain(chain, name="Unique Name")

        # Two presets can have same name (different IDs)
        # but PresetManager should enforce uniqueness
        assert preset1.name == preset2.name
        assert preset1.id != preset2.id

    def test_preset_version_handling(self):
        """Test preset version handling for compatibility"""
        chain = EffectsChain(name="Version Test")
        preset = Preset.from_effects_chain(chain, name="Version Test")

        # Default version
        assert preset.version == "1.0.0"

        # Custom version (for future compatibility)
        preset_custom = Preset.from_effects_chain(
            chain,
            name="Custom Version",
            version="2.1.0"
        )
        assert preset_custom.version == "2.1.0"