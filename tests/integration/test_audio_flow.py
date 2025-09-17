import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.services.audio_engine import AudioEngine
from src.services.effects_manager import EffectsManager
from src.models.audio_effect import AudioEffect, EffectType


class TestAudioFlowIntegration:
    """Integration tests for real-time audio processing scenario"""

    def test_end_to_end_audio_processing_flow(self):
        """Test complete audio processing flow from input to output"""
        # Initialize services
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()

        # Create effects chain
        chain_config = {
            "name": "Test Audio Flow",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 6.0, "tone": 0.6}
                },
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 15.0, "tone": 0.4, "level": 0.8}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)

        # Configure audio with mocked devices
        audio_config = {
            "input_device": "Test Input Device",
            "output_device": "Test Output Device",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        # Mock audio stream initialization
        with patch.object(audio_engine, '_initialize_audio_stream'):
            with patch.object(audio_engine, '_setup_effects_chain'):
                # Start audio processing
                status = audio_engine.start_processing(audio_config)
                assert status["active"] is True

                # Apply effects chain to audio engine
                audio_engine.set_effects_chain(effects_chain)

                # Simulate audio processing with test signal
                test_signal = np.sin(2 * np.pi * 440 * np.linspace(0, 0.1, 4800))  # 440Hz sine wave
                audio_frame = {
                    "samples": [test_signal.tolist()],  # Mono input
                    "channels": 1,
                    "sample_rate": 48000,
                    "timestamp": 1234567890.0
                }

                # Process audio frame through effects chain
                with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                    # Mock effects processing (boost + distortion)
                    boosted_signal = test_signal * 2.0  # Simulate boost
                    distorted_signal = np.tanh(boosted_signal * 2.0)  # Simulate distortion
                    mock_effects.return_value = distorted_signal

                    processed_frame = audio_engine.process_frame(audio_frame)

                    # Verify processing occurred
                    assert processed_frame["channels"] == 1
                    assert processed_frame["sample_rate"] == 48000
                    assert len(processed_frame["samples"][0]) == len(test_signal)

                # Stop audio processing
                with patch.object(audio_engine, '_cleanup_audio_stream'):
                    result = audio_engine.stop_processing()
                    assert result is True

    def test_audio_processing_with_effect_bypass(self):
        """Test audio processing with effect bypass functionality"""
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()

        # Create chain with bypassed effect
        chain_config = {
            "name": "Bypass Test Chain",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 12.0}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)
        boost_effect = effects_chain.effects[0]

        # Audio configuration
        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 128,
            "input_channels": [0],
            "output_channels": [0]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            audio_engine.start_processing(audio_config)
            audio_engine.set_effects_chain(effects_chain)

            # Test signal
            test_signal = np.ones(128) * 0.5  # Constant signal for easy testing
            audio_frame = {
                "samples": [test_signal.tolist()],
                "channels": 1,
                "sample_rate": 48000
            }

            # Process with effect active
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal * 4.0  # 12dB boost ≈ 4x

                processed_active = audio_engine.process_frame(audio_frame)
                mock_effects.assert_called_once()

            # Bypass the effect
            effects_manager.toggle_effect_bypass(boost_effect.id, {"bypassed": True})

            # Process with effect bypassed
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal  # No processing when bypassed

                processed_bypassed = audio_engine.process_frame(audio_frame)

                # Verify bypass behavior
                original_samples = audio_frame["samples"][0]
                bypassed_samples = processed_bypassed["samples"][0]

                # When bypassed, output should match input
                assert np.allclose(bypassed_samples, original_samples, rtol=1e-5)

    def test_audio_processing_with_multiple_effects(self):
        """Test audio processing through multiple effects in sequence"""
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()

        # Create complex effects chain
        chain_config = {
            "name": "Multi-Effect Chain",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 6.0, "tone": 0.5}
                },
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 12.0, "tone": 0.6, "level": 0.7}
                },
                {
                    "type": "DELAY",
                    "parameters": {"delay_seconds": 0.2, "feedback": 0.3, "mix": 0.4}
                },
                {
                    "type": "REVERB",
                    "parameters": {"room_size": 0.5, "damping": 0.4, "wet_level": 0.3}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)

        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            audio_engine.start_processing(audio_config)
            audio_engine.set_effects_chain(effects_chain)

            # Test signal - guitar-like frequency content
            t = np.linspace(0, 256/48000, 256)
            guitar_signal = (
                0.5 * np.sin(2 * np.pi * 329.6 * t) +  # E4
                0.3 * np.sin(2 * np.pi * 659.3 * t) +  # E5
                0.2 * np.sin(2 * np.pi * 987.8 * t)    # B5
            )

            audio_frame = {
                "samples": [guitar_signal.tolist()],
                "channels": 1,
                "sample_rate": 48000
            }

            # Mock sequential effects processing
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                # Simulate processing through all effects
                boosted = guitar_signal * 2.0  # Boost
                distorted = np.tanh(boosted)  # Distortion
                # Delay and reverb would add complexity, so we'll mock the final result
                final_signal = distorted * 0.7  # Level adjustment

                mock_effects.return_value = final_signal

                processed_frame = audio_engine.process_frame(audio_frame)

                # Verify processing chain was applied
                mock_effects.assert_called_once()
                assert processed_frame["channels"] == 1
                assert len(processed_frame["samples"][0]) == 256

    def test_audio_processing_error_recovery(self):
        """Test audio processing error handling and recovery"""
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()

        # Create valid effects chain
        chain_config = {
            "name": "Error Recovery Test",
            "effects": [
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 15.0}
                }
            ]
        }

        effects_chain = effects_manager.create_chain(chain_config)

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

            # Test normal processing first
            test_signal = np.sin(2 * np.pi * 440 * np.linspace(0, 0.01, 256))
            audio_frame = {
                "samples": [test_signal.tolist()],
                "channels": 1,
                "sample_rate": 48000
            }

            # Normal processing should work
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal * 2.0
                processed_frame = audio_engine.process_frame(audio_frame)
                assert processed_frame is not None

            # Simulate effects processing error
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.side_effect = RuntimeError("Effects processing error")

                # Audio engine should handle error gracefully
                processed_frame = audio_engine.process_frame(audio_frame)

                # Should return original signal when effects fail
                assert processed_frame is not None
                original_samples = audio_frame["samples"][0]
                processed_samples = processed_frame["samples"][0]
                assert np.allclose(processed_samples, original_samples, rtol=1e-5)

            # Recovery: processing should work again after error
            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal * 1.5
                recovered_frame = audio_engine.process_frame(audio_frame)
                assert recovered_frame is not None

    def test_audio_latency_measurement(self):
        """Test audio latency measurement during processing"""
        audio_engine = AudioEngine()

        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            with patch.object(audio_engine, '_measure_latency') as mock_latency:
                # Mock measured latency
                mock_latency.return_value = 5.3  # 5.3ms latency

                status = audio_engine.start_processing(audio_config)

                # Verify latency is measured and reported
                assert "latency_ms" in status
                assert status["latency_ms"] == 5.3

                # Get status during processing
                current_status = audio_engine.get_status()
                assert current_status["latency_ms"] == 5.3

    def test_cpu_usage_monitoring(self):
        """Test CPU usage monitoring during audio processing"""
        audio_engine = AudioEngine()

        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 128,
            "input_channels": [0],
            "output_channels": [0]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            with patch.object(audio_engine, '_monitor_cpu_usage') as mock_cpu:
                # Mock CPU usage monitoring
                mock_cpu.return_value = 25.7  # 25.7% CPU usage

                audio_engine.start_processing(audio_config)

                # Simulate some processing to update CPU usage
                test_signal = np.random.random(128) * 0.1
                audio_frame = {
                    "samples": [test_signal.tolist()],
                    "channels": 1,
                    "sample_rate": 48000
                }

                with patch.object(audio_engine, '_apply_effects_chain'):
                    audio_engine.process_frame(audio_frame)

                # Verify CPU usage is monitored
                status = audio_engine.get_status()
                assert "cpu_usage" in status
                assert status["cpu_usage"] == 25.7

    def test_buffer_underrun_overrun_detection(self):
        """Test detection and reporting of buffer underruns/overruns"""
        audio_engine = AudioEngine()

        audio_config = {
            "input_device": "Test Input",
            "output_device": "Test Output",
            "sample_rate": 48000,
            "buffer_size": 64,  # Small buffer more prone to issues
            "input_channels": [0],
            "output_channels": [0]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            audio_engine.start_processing(audio_config)

            # Simulate buffer underrun
            with patch.object(audio_engine, '_detect_buffer_issues') as mock_detect:
                mock_detect.return_value = {"underruns": 1, "overruns": 0}

                test_signal = np.random.random(64) * 0.1
                audio_frame = {
                    "samples": [test_signal.tolist()],
                    "channels": 1,
                    "sample_rate": 48000
                }

                # Process frame that triggers buffer issue detection
                with patch.object(audio_engine, '_apply_effects_chain'):
                    audio_engine.process_frame(audio_frame)

                # Verify buffer issues are tracked
                status = audio_engine.get_status()
                assert status["buffer_underruns"] == 1
                assert status["buffer_overruns"] == 0

            # Simulate buffer overrun
            with patch.object(audio_engine, '_detect_buffer_issues') as mock_detect:
                mock_detect.return_value = {"underruns": 1, "overruns": 2}

                # Process another frame
                with patch.object(audio_engine, '_apply_effects_chain'):
                    audio_engine.process_frame(audio_frame)

                # Verify buffer issues are accumulated
                status = audio_engine.get_status()
                assert status["buffer_underruns"] == 1
                assert status["buffer_overruns"] == 2