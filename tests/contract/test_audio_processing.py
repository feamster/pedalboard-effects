import pytest
from unittest.mock import Mock, patch
from src.services.audio_engine import AudioEngine


class TestAudioProcessingContract:
    """Contract tests for audio processing interface"""

    def test_start_audio_processing_contract(self):
        """Test audio processing start contract"""
        audio_engine = AudioEngine()

        # Valid audio configuration
        audio_config = {
            "input_device": "Scarlett 2i2 USB",
            "output_device": "BlackHole 2ch",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        # Should return audio status on successful start
        with patch.object(audio_engine, '_initialize_audio_stream'):
            status = audio_engine.start_processing(audio_config)

            assert status["active"] is True
            assert status["sample_rate"] == 48000
            assert status["buffer_size"] == 256
            assert status["input_device"] == "Scarlett 2i2 USB"
            assert status["output_device"] == "BlackHole 2ch"
            assert "latency_ms" in status
            assert "cpu_usage" in status
            assert status["buffer_underruns"] == 0
            assert status["buffer_overruns"] == 0

    def test_start_audio_processing_invalid_config(self):
        """Test audio processing start with invalid configuration"""
        audio_engine = AudioEngine()

        # Invalid sample rate
        invalid_config = {
            "input_device": "Scarlett 2i2 USB",
            "output_device": "BlackHole 2ch",
            "sample_rate": 99999,  # Invalid sample rate
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        with pytest.raises(ValueError, match="Invalid audio configuration"):
            audio_engine.start_processing(invalid_config)

        # Missing required fields
        incomplete_config = {
            "input_device": "Scarlett 2i2 USB"
            # Missing other required fields
        }

        with pytest.raises(ValueError, match="Invalid audio configuration"):
            audio_engine.start_processing(incomplete_config)

    def test_stop_audio_processing_contract(self):
        """Test audio processing stop contract"""
        audio_engine = AudioEngine()

        # Start processing first
        audio_config = {
            "input_device": "Scarlett 2i2 USB",
            "output_device": "BlackHole 2ch",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            audio_engine.start_processing(audio_config)

            # Stop processing
            with patch.object(audio_engine, '_cleanup_audio_stream'):
                result = audio_engine.stop_processing()

                assert result is True
                status = audio_engine.get_status()
                assert status["active"] is False

    def test_process_audio_frame_contract(self):
        """Test audio frame processing contract"""
        audio_engine = AudioEngine()

        # Valid audio frame
        audio_frame = {
            "samples": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],  # 2 channels, 3 samples each
            "channels": 2,
            "sample_rate": 48000,
            "timestamp": 1234567890.123
        }

        with patch.object(audio_engine, '_process_frame') as mock_process:
            mock_process.return_value = {
                "samples": [[0.15, 0.25, 0.35], [0.45, 0.55, 0.65]],  # Processed samples
                "channels": 2,
                "sample_rate": 48000,
                "timestamp": 1234567890.123
            }

            result = audio_engine.process_frame(audio_frame)

            assert result["channels"] == 2
            assert result["sample_rate"] == 48000
            assert len(result["samples"]) == 2  # 2 channels
            assert len(result["samples"][0]) == 3  # 3 samples per channel
            assert result["timestamp"] == audio_frame["timestamp"]

    def test_process_audio_frame_invalid_data(self):
        """Test audio frame processing with invalid data"""
        audio_engine = AudioEngine()

        # Invalid audio frame - mismatched channels
        invalid_frame = {
            "samples": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],  # 3 channels
            "channels": 2,  # Claims 2 channels
            "sample_rate": 48000
        }

        with pytest.raises(ValueError, match="Invalid audio frame data"):
            audio_engine.process_frame(invalid_frame)

        # Missing required fields
        incomplete_frame = {
            "samples": [[0.1, 0.2]]
            # Missing channels, sample_rate
        }

        with pytest.raises(ValueError, match="Invalid audio frame data"):
            audio_engine.process_frame(incomplete_frame)

    def test_get_audio_status_contract(self):
        """Test audio status retrieval contract"""
        audio_engine = AudioEngine()

        status = audio_engine.get_status()

        # Required status fields
        assert "active" in status
        assert "latency_ms" in status
        assert "cpu_usage" in status
        assert "buffer_underruns" in status
        assert "buffer_overruns" in status
        assert "sample_rate" in status
        assert "buffer_size" in status
        assert "input_device" in status
        assert "output_device" in status

        # Field types
        assert isinstance(status["active"], bool)
        assert isinstance(status["latency_ms"], (int, float))
        assert isinstance(status["cpu_usage"], (int, float))
        assert isinstance(status["buffer_underruns"], int)
        assert isinstance(status["buffer_overruns"], int)

    def test_audio_device_error_handling(self):
        """Test audio processing error handling"""
        audio_engine = AudioEngine()

        # Simulate audio hardware error
        audio_config = {
            "input_device": "Non-existent Device",
            "output_device": "Another Non-existent Device",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        with pytest.raises(RuntimeError, match="Audio hardware error"):
            audio_engine.start_processing(audio_config)

    def test_concurrent_audio_processing_prevention(self):
        """Test that multiple concurrent audio processing is prevented"""
        audio_engine = AudioEngine()

        audio_config = {
            "input_device": "Scarlett 2i2 USB",
            "output_device": "BlackHole 2ch",
            "sample_rate": 48000,
            "buffer_size": 256,
            "input_channels": [0],
            "output_channels": [0, 1]
        }

        with patch.object(audio_engine, '_initialize_audio_stream'):
            # Start first processing
            audio_engine.start_processing(audio_config)

            # Attempt to start second processing should fail
            with pytest.raises(RuntimeError, match="Audio processing already active"):
                audio_engine.start_processing(audio_config)