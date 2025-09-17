import pytest
from uuid import UUID
from src.models.audio_effect import AudioEffect, EffectType


class TestAudioEffect:
    def test_create_boost_effect(self):
        """Test creating a boost effect with default parameters"""
        effect = AudioEffect(effect_type=EffectType.BOOST)

        assert effect.type == EffectType.BOOST
        assert isinstance(effect.id, UUID)
        assert not effect.bypassed
        assert effect.position == 0
        assert effect.preset_name is None

        # Check default boost parameters
        assert effect.parameters["gain_db"] == 0.0
        assert effect.parameters["tone"] == 0.5

    def test_create_distortion_effect(self):
        """Test creating a distortion effect with default parameters"""
        effect = AudioEffect(effect_type=EffectType.DISTORTION)

        assert effect.type == EffectType.DISTORTION

        # Check default distortion parameters
        assert effect.parameters["drive_db"] == 10.0
        assert effect.parameters["tone"] == 0.5
        assert effect.parameters["level"] == 0.7

    def test_create_delay_effect(self):
        """Test creating a delay effect with default parameters"""
        effect = AudioEffect(effect_type=EffectType.DELAY)

        assert effect.type == EffectType.DELAY

        # Check default delay parameters
        assert effect.parameters["delay_seconds"] == 0.25
        assert effect.parameters["feedback"] == 0.3
        assert effect.parameters["mix"] == 0.3
        assert effect.parameters["tempo_sync"] is False

    def test_create_reverb_effect(self):
        """Test creating a reverb effect with default parameters"""
        effect = AudioEffect(effect_type=EffectType.REVERB)

        assert effect.type == EffectType.REVERB

        # Check default reverb parameters
        assert effect.parameters["room_size"] == 0.5
        assert effect.parameters["damping"] == 0.5
        assert effect.parameters["wet_level"] == 0.3
        assert effect.parameters["dry_level"] == 0.7

    def test_update_effect_parameters(self):
        """Test updating effect parameters"""
        effect = AudioEffect(effect_type=EffectType.BOOST)

        # Update valid parameters
        effect.update_parameters({"gain_db": 12.0, "tone": 0.8})

        assert effect.parameters["gain_db"] == 12.0
        assert effect.parameters["tone"] == 0.8

    def test_parameter_validation_boost(self):
        """Test parameter validation for boost effect"""
        effect = AudioEffect(effect_type=EffectType.BOOST)

        # Valid parameter ranges
        effect.update_parameters({"gain_db": -20.0})  # Minimum
        effect.update_parameters({"gain_db": 30.0})   # Maximum
        effect.update_parameters({"tone": 0.0})       # Minimum
        effect.update_parameters({"tone": 1.0})       # Maximum

        # Invalid parameter ranges should raise errors
        with pytest.raises(ValueError, match="gain_db must be between -20.0 and 30.0"):
            effect.update_parameters({"gain_db": -21.0})

        with pytest.raises(ValueError, match="gain_db must be between -20.0 and 30.0"):
            effect.update_parameters({"gain_db": 31.0})

        with pytest.raises(ValueError, match="tone must be between 0.0 and 1.0"):
            effect.update_parameters({"tone": -0.1})

        with pytest.raises(ValueError, match="tone must be between 0.0 and 1.0"):
            effect.update_parameters({"tone": 1.1})

    def test_parameter_validation_distortion(self):
        """Test parameter validation for distortion effect"""
        effect = AudioEffect(effect_type=EffectType.DISTORTION)

        # Invalid drive_db range
        with pytest.raises(ValueError, match="drive_db must be between 0.0 and 30.0"):
            effect.update_parameters({"drive_db": -1.0})

        with pytest.raises(ValueError, match="drive_db must be between 0.0 and 30.0"):
            effect.update_parameters({"drive_db": 31.0})

        # Invalid level range
        with pytest.raises(ValueError, match="level must be between 0.0 and 1.0"):
            effect.update_parameters({"level": -0.1})

        with pytest.raises(ValueError, match="level must be between 0.0 and 1.0"):
            effect.update_parameters({"level": 1.1})

    def test_parameter_validation_delay(self):
        """Test parameter validation for delay effect"""
        effect = AudioEffect(effect_type=EffectType.DELAY)

        # Invalid delay_seconds range
        with pytest.raises(ValueError, match="delay_seconds must be between 0.0 and 2.0"):
            effect.update_parameters({"delay_seconds": -0.1})

        with pytest.raises(ValueError, match="delay_seconds must be between 0.0 and 2.0"):
            effect.update_parameters({"delay_seconds": 2.1})

        # Invalid feedback range
        with pytest.raises(ValueError, match="feedback must be between 0.0 and 0.95"):
            effect.update_parameters({"feedback": -0.1})

        with pytest.raises(ValueError, match="feedback must be between 0.0 and 0.95"):
            effect.update_parameters({"feedback": 0.96})

    def test_bypass_effect(self):
        """Test bypassing and enabling effects"""
        effect = AudioEffect(effect_type=EffectType.REVERB)

        # Initially not bypassed
        assert not effect.bypassed

        # Bypass effect
        effect.set_bypassed(True)
        assert effect.bypassed

        # Enable effect
        effect.set_bypassed(False)
        assert not effect.bypassed

    def test_effect_position(self):
        """Test setting effect position in chain"""
        effect = AudioEffect(effect_type=EffectType.DELAY)

        # Initial position
        assert effect.position == 0

        # Set new position
        effect.set_position(3)
        assert effect.position == 3

        # Invalid position should raise error
        with pytest.raises(ValueError, match="Position must be non-negative"):
            effect.set_position(-1)

    def test_preset_name(self):
        """Test setting and getting preset name"""
        effect = AudioEffect(effect_type=EffectType.DISTORTION)

        # Initially no preset name
        assert effect.preset_name is None

        # Set preset name
        effect.set_preset_name("Heavy Distortion")
        assert effect.preset_name == "Heavy Distortion"

        # Clear preset name
        effect.set_preset_name(None)
        assert effect.preset_name is None

    def test_invalid_effect_type(self):
        """Test that invalid effect types raise an error"""
        with pytest.raises(ValueError, match="Invalid effect type"):
            AudioEffect(effect_type="INVALID_TYPE")