import pytest
from uuid import UUID
from src.models.effects_chain import EffectsChain
from src.models.audio_effect import AudioEffect, EffectType


class TestEffectsChain:
    def test_create_empty_effects_chain(self):
        """Test creating an empty effects chain"""
        chain = EffectsChain(name="Test Chain")

        assert chain.name == "Test Chain"
        assert isinstance(chain.id, UUID)
        assert len(chain.effects) == 0
        assert not chain.active
        assert chain.created_at is not None
        assert chain.modified_at is not None

    def test_add_effect_to_chain(self):
        """Test adding an effect to the chain"""
        chain = EffectsChain(name="Test Chain")
        effect = AudioEffect(effect_type=EffectType.BOOST)

        chain.add_effect(effect)

        assert len(chain.effects) == 1
        assert chain.effects[0] == effect
        assert effect.position == 0

    def test_remove_effect_from_chain(self):
        """Test removing an effect from the chain"""
        chain = EffectsChain(name="Test Chain")
        effect = AudioEffect(effect_type=EffectType.DISTORTION)

        chain.add_effect(effect)
        chain.remove_effect(effect.id)

        assert len(chain.effects) == 0

    def test_reorder_effects_in_chain(self):
        """Test reordering effects in the chain"""
        chain = EffectsChain(name="Test Chain")
        boost = AudioEffect(effect_type=EffectType.BOOST)
        distortion = AudioEffect(effect_type=EffectType.DISTORTION)

        chain.add_effect(boost)
        chain.add_effect(distortion)

        # Initially: boost at 0, distortion at 1
        assert chain.effects[0] == boost
        assert chain.effects[1] == distortion

        # Reorder: distortion first, then boost
        chain.reorder_effects([distortion.id, boost.id])

        assert chain.effects[0] == distortion
        assert chain.effects[1] == boost
        assert distortion.position == 0
        assert boost.position == 1

    def test_chain_name_validation(self):
        """Test effects chain name validation"""
        # Valid name
        chain = EffectsChain(name="Valid Name")
        assert chain.name == "Valid Name"

        # Empty name should raise error
        with pytest.raises(ValueError, match="Chain name must be 1-50 characters"):
            EffectsChain(name="")

        # Too long name should raise error
        with pytest.raises(ValueError, match="Chain name must be 1-50 characters"):
            EffectsChain(name="x" * 51)

    def test_maximum_effects_limit(self):
        """Test that chain enforces maximum 8 effects limit"""
        chain = EffectsChain(name="Full Chain")

        # Add 8 effects (should work)
        for i in range(8):
            effect = AudioEffect(effect_type=EffectType.BOOST)
            chain.add_effect(effect)

        assert len(chain.effects) == 8

        # Adding 9th effect should raise error
        with pytest.raises(ValueError, match="Maximum 8 effects per chain"):
            ninth_effect = AudioEffect(effect_type=EffectType.DELAY)
            chain.add_effect(ninth_effect)

    def test_activate_deactivate_chain(self):
        """Test activating and deactivating the effects chain"""
        chain = EffectsChain(name="Test Chain")

        # Initially inactive
        assert not chain.active

        # Activate
        chain.activate()
        assert chain.active

        # Deactivate
        chain.deactivate()
        assert not chain.active

    def test_duplicate_effect_prevention(self):
        """Test that duplicate effect instances are prevented"""
        chain = EffectsChain(name="Test Chain")
        effect = AudioEffect(effect_type=EffectType.REVERB)

        chain.add_effect(effect)

        # Adding same effect instance again should raise error
        with pytest.raises(ValueError, match="Cannot have duplicate effect instances"):
            chain.add_effect(effect)