import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.services.audio_engine import AudioEngine
from src.services.effects_manager import EffectsManager


class TestParameterControlIntegration:
    """Integration tests for real-time effect parameter adjustment"""

    def test_real_time_parameter_updates(self):
        """Test real-time parameter updates during audio processing"""
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()

        # Create effects chain with distortion
        chain_config = {
            "name": "Parameter Test Chain",
            "effects": [
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 10.0, "tone": 0.5, "level": 0.7}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        distortion_effect = effects_chain.effects[0]

        # Start audio processing
        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            audio_engine.start_processing(audio_config)
            audio_engine.set_effects_chain(effects_chain)

            # Test signal
            test_signal = np.sin(2 * np.pi * 440 * np.linspace(0, 0.01, 256))
            audio_frame = {
                "samples": [test_signal.tolist()],
                "channels": 1,
                "sample_rate": 48000
            }

            # Process with initial parameters
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal * 2.0  # Moderate distortion
                initial_frame = audio_engine.process_frame(audio_frame)

            # Update distortion drive parameter in real-time
            new_parameters = {"drive_db": 25.0}  # Increase drive
            effects_manager.update_effect_parameters(distortion_effect.id, new_parameters)

            # Verify parameter was updated
            updated_params = effects_manager.get_effect_parameters(distortion_effect.id)
            assert updated_params["drive_db"]["value"] == 25.0

            # Process with updated parameters
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal * 4.0  # Heavier distortion
                updated_frame = audio_engine.process_frame(audio_frame)

            # Verify both processing calls succeeded
            assert initial_frame is not None
            assert updated_frame is not None

    def test_parameter_update_responsiveness(self):
        """Test parameter update responsiveness (< 100ms)"""
        import time
        effects_manager = EffectsManager()

        # Create effects chain
        chain_config = {
            "name": "Responsiveness Test",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 0.0, "tone": 0.5}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        boost_effect = effects_chain.effects[0]

        # Measure parameter update time
        start_time = time.time()
        effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": 15.0})
        update_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Verify update was fast (< 100ms requirement)
        assert update_time < 100, f"Parameter update took {update_time:.2f}ms, exceeds 100ms requirement"

        # Verify parameter was actually updated
        updated_params = effects_manager.get_effect_parameters(boost_effect.id)
        assert updated_params["gain_db"]["value"] == 15.0

    def test_multiple_parameter_updates(self):
        """Test updating multiple parameters simultaneously"""
        effects_manager = EffectsManager()

        # Create effects chain with reverb (multiple parameters)
        chain_config = {
            "name": "Multi-Parameter Test",
            "effects": [
                {
                    "type": "REVERB",
                    "parameters": {
                        "room_size": 0.5,
                        "damping": 0.5,
                        "wet_level": 0.3,
                        "dry_level": 0.7
                    }
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        reverb_effect = effects_chain.effects[0]

        # Update multiple parameters at once
        parameter_updates = {
            "room_size": 0.8,
            "damping": 0.2,
            "wet_level": 0.5,
            "dry_level": 0.5
        }

        updated_params = effects_manager.update_effect_parameters(
            reverb_effect.id,
            parameter_updates
        )

        # Verify all parameters were updated correctly
        assert updated_params["room_size"]["value"] == 0.8
        assert updated_params["damping"]["value"] == 0.2
        assert updated_params["wet_level"]["value"] == 0.5
        assert updated_params["dry_level"]["value"] == 0.5

    def test_parameter_validation_during_updates(self):
        """Test parameter validation during real-time updates"""
        effects_manager = EffectsManager()

        # Create effects chain
        chain_config = {
            "name": "Validation Test",
            "effects": [
                {
                    "type": "DELAY",
                    "parameters": {"delay_seconds": 0.3, "feedback": 0.4, "mix": 0.5}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        delay_effect = effects_chain.effects[0]

        # Test valid parameter updates
        valid_updates = {"delay_seconds": 1.5, "feedback": 0.8}
        effects_manager.update_effect_parameters(delay_effect.id, valid_updates)

        # Verify valid updates succeeded
        params = effects_manager.get_effect_parameters(delay_effect.id)
        assert params["delay_seconds"]["value"] == 1.5
        assert params["feedback"]["value"] == 0.8

        # Test invalid parameter updates
        invalid_updates = {"delay_seconds": 3.0}  # Exceeds 2.0 maximum

        with pytest.raises(ValueError, match="Invalid parameter values"):
            effects_manager.update_effect_parameters(delay_effect.id, invalid_updates)

        # Verify invalid update didn't change parameter
        params = effects_manager.get_effect_parameters(delay_effect.id)
        assert params["delay_seconds"]["value"] == 1.5  # Still previous valid value

    def test_parameter_updates_across_multiple_effects(self):
        """Test parameter updates across multiple effects in chain"""
        effects_manager = EffectsManager()

        # Create complex effects chain
        chain_config = {
            "name": "Multi-Effect Parameter Test",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 0.0, "tone": 0.5}
                },
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 10.0, "tone": 0.5, "level": 0.7}
                },
                {
                    "type": "DELAY",
                    "parameters": {"delay_seconds": 0.25, "feedback": 0.3, "mix": 0.3}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        boost_effect = effects_chain.effects[0]
        distortion_effect = effects_chain.effects[1]
        delay_effect = effects_chain.effects[2]

        # Update parameters on different effects
        effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": 8.0})
        effects_manager.update_effect_parameters(distortion_effect.id, {"drive_db": 20.0})
        effects_manager.update_effect_parameters(delay_effect.id, {"feedback": 0.6})

        # Verify all updates were applied correctly
        boost_params = effects_manager.get_effect_parameters(boost_effect.id)
        distortion_params = effects_manager.get_effect_parameters(distortion_effect.id)
        delay_params = effects_manager.get_effect_parameters(delay_effect.id)

        assert boost_params["gain_db"]["value"] == 8.0
        assert distortion_params["drive_db"]["value"] == 20.0
        assert delay_params["feedback"]["value"] == 0.6

    def test_parameter_automation_scenario(self):
        """Test parameter automation scenario (simulated sweeps)"""
        import time
        effects_manager = EffectsManager()

        # Create effects chain with filter-like effect
        chain_config = {
            "name": "Automation Test",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 0.0, "tone": 0.0}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        boost_effect = effects_chain.effects[0]

        # Simulate parameter automation (tone sweep)
        tone_values = [0.0, 0.25, 0.5, 0.75, 1.0]
        update_times = []

        for tone_value in tone_values:
            start_time = time.time()
            effects_manager.update_effect_parameters(boost_effect.id, {"tone": tone_value})
            update_time = (time.time() - start_time) * 1000
            update_times.append(update_time)

            # Verify parameter was updated
            params = effects_manager.get_effect_parameters(boost_effect.id)
            assert abs(params["tone"]["value"] - tone_value) < 1e-6

        # Verify all updates were fast enough for automation
        avg_update_time = sum(update_times) / len(update_times)
        assert avg_update_time < 50, f"Average update time {avg_update_time:.2f}ms too slow for automation"

    def test_parameter_updates_with_audio_processing(self):
        """Test parameter updates while audio processing is active"""
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()

        # Create effects chain
        chain_config = {
            "name": "Live Update Test",
            "effects": [
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 5.0, "level": 0.5}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        distortion_effect = effects_chain.effects[0]

        # Start audio processing
        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            audio_engine.start_processing(audio_config)
            audio_engine.set_effects_chain(effects_chain)

            # Simulate continuous audio processing
            test_signal = np.sin(2 * np.pi * 440 * np.linspace(0, 0.01, 256))
            audio_frame = {
                "samples": [test_signal.tolist()],
                "channels": 1,
                "sample_rate": 48000
            }

            # Process several frames while updating parameters
            for drive_value in [5.0, 10.0, 15.0, 20.0, 25.0]:
                # Update parameter
                effects_manager.update_effect_parameters(
                    distortion_effect.id,
                    {"drive_db": drive_value}
                )

                # Process audio frame with updated parameter
                with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                    mock_effects.return_value = test_signal  # Mock processing
                    processed_frame = audio_engine.process_frame(audio_frame)
                    assert processed_frame is not None

                # Verify parameter was updated
                params = effects_manager.get_effect_parameters(distortion_effect.id)
                assert params["drive_db"]["value"] == drive_value

    def test_parameter_bounds_enforcement(self):
        """Test parameter bounds enforcement during updates"""
        effects_manager = EffectsManager()

        # Create effects chain
        chain_config = {
            "name": "Bounds Test",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 0.0, "tone": 0.5}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        boost_effect = effects_chain.effects[0]

        # Test minimum bounds
        effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": -20.0})  # Minimum
        params = effects_manager.get_effect_parameters(boost_effect.id)
        assert params["gain_db"]["value"] == -20.0

        # Test maximum bounds
        effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": 30.0})  # Maximum
        params = effects_manager.get_effect_parameters(boost_effect.id)
        assert params["gain_db"]["value"] == 30.0

        # Test below minimum (should fail)
        with pytest.raises(ValueError):
            effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": -21.0})

        # Test above maximum (should fail)
        with pytest.raises(ValueError):
            effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": 31.0})

        # Verify parameter remained at last valid value
        params = effects_manager.get_effect_parameters(boost_effect.id)
        assert params["gain_db"]["value"] == 30.0

    def test_parameter_curve_types(self):
        """Test different parameter curve types for UI mapping"""
        effects_manager = EffectsManager()

        # Create effects chain
        chain_config = {
            "name": "Curve Test",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 0.0, "tone": 0.5}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        boost_effect = effects_chain.effects[0]

        # Get parameter metadata including curve types
        params = effects_manager.get_effect_parameters(boost_effect.id)

        # Verify curve type information is available
        gain_param = params["gain_db"]
        tone_param = params["tone"]

        assert "curve_type" in gain_param
        assert "curve_type" in tone_param

        # Gain typically uses linear curve for dB values
        assert gain_param["curve_type"] in ["linear", "logarithmic"]

        # Tone typically uses linear curve
        assert tone_param["curve_type"] == "linear"

        # Test updating with curve type consideration
        # (Implementation would map UI slider position to actual parameter value based on curve)
        effects_manager.update_effect_parameters(boost_effect.id, {"tone": 0.25})

        updated_params = effects_manager.get_effect_parameters(boost_effect.id)
        assert updated_params["tone"]["value"] == 0.25