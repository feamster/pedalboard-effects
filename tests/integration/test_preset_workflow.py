import pytest
import json
from unittest.mock import Mock, patch, mock_open
from src.services.preset_manager import PresetManager
from src.services.effects_manager import EffectsManager
from src.services.audio_engine import AudioEngine


class TestPresetWorkflowIntegration:
    """Integration tests for complete preset save/load workflow"""

    def test_complete_preset_save_load_workflow(self):
        """Test complete workflow: create effects → save preset → load preset"""
        effects_manager = EffectsManager()
        preset_manager = PresetManager()

        # Step 1: Create complex effects chain
        chain_config = {
            "name": "Rock Lead Tone",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 8.0, "tone": 0.7}
                },
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 18.0, "tone": 0.4, "level": 0.8}
                },
                {
                    "type": "DELAY",
                    "parameters": {"delay_seconds": 0.35, "feedback": 0.45, "mix": 0.4}
                },
                {
                    "type": "REVERB",
                    "parameters": {"room_size": 0.6, "damping": 0.3, "wet_level": 0.35}
                }
            ]
        }

        original_chain = effects_manager.create_chain(chain_config)

        # Step 2: Save as preset
        preset_config = {
            "name": "My Rock Lead",
            "description": "Heavy lead tone with delay and reverb",
            "effects_chain_config": {
                "name": original_chain.name,
                "effects": [
                    {
                        "type": "BOOST",
                        "parameters": {"gain_db": 8.0, "tone": 0.7},
                        "bypassed": False
                    },
                    {
                        "type": "DISTORTION",
                        "parameters": {"drive_db": 18.0, "tone": 0.4, "level": 0.8},
                        "bypassed": False
                    },
                    {
                        "type": "DELAY",
                        "parameters": {"delay_seconds": 0.35, "feedback": 0.45, "mix": 0.4},
                        "bypassed": False
                    },
                    {
                        "type": "REVERB",
                        "parameters": {"room_size": 0.6, "damping": 0.3, "wet_level": 0.35},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["rock", "lead", "distortion", "delay"],
            "author": "Test User"
        }

        with patch.object(preset_manager, '_save_to_file'):
            saved_preset = preset_manager.save_preset(preset_config)

        # Verify preset was saved correctly
        assert saved_preset.name == "My Rock Lead"
        assert saved_preset.description == "Heavy lead tone with delay and reverb"
        assert saved_preset.tags == ["rock", "lead", "distortion", "delay"]
        assert len(saved_preset.effects_chain_config["effects"]) == 4

        # Step 3: Clear current effects chain
        clean_chain = effects_manager.create_chain({"name": "Empty", "effects": []})
        assert len(clean_chain.effects) == 0

        # Step 4: Load preset back
        with patch.object(preset_manager, '_load_from_file'):
            with patch.object(preset_manager, '_get_preset_by_id', return_value=saved_preset):
                loaded_chain = preset_manager.load_preset(saved_preset.id)

        # Step 5: Verify loaded chain matches original
        assert loaded_chain.name == "My Rock Lead"  # Uses preset name
        assert len(loaded_chain.effects) == 4

        # Verify each effect was restored correctly
        boost = loaded_chain.effects[0]
        assert boost.type.value == "BOOST"
        assert boost.parameters["gain_db"] == 8.0
        assert boost.parameters["tone"] == 0.7

        distortion = loaded_chain.effects[1]
        assert distortion.type.value == "DISTORTION"
        assert distortion.parameters["drive_db"] == 18.0
        assert distortion.parameters["tone"] == 0.4
        assert distortion.parameters["level"] == 0.8

        delay = loaded_chain.effects[2]
        assert delay.type.value == "DELAY"
        assert delay.parameters["delay_seconds"] == 0.35
        assert delay.parameters["feedback"] == 0.45
        assert delay.parameters["mix"] == 0.4

        reverb = loaded_chain.effects[3]
        assert reverb.type.value == "REVERB"
        assert reverb.parameters["room_size"] == 0.6
        assert reverb.parameters["damping"] == 0.3
        assert reverb.parameters["wet_level"] == 0.35

    def test_preset_workflow_with_audio_processing(self):
        """Test preset workflow integration with audio processing"""
        audio_engine = AudioEngine()
        effects_manager = EffectsManager()
        preset_manager = PresetManager()

        # Create and save a preset
        chain_config = {
            "name": "Audio Test Chain",
            "effects": [
                {
                    "type": "BOOST",
                    "parameters": {"gain_db": 6.0, "tone": 0.5}
                },
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 12.0, "tone": 0.6, "level": 0.7}
                }
            ]
        }

        original_chain = effects_manager.create_chain(chain_config)

        preset_config = {
            "name": "Audio Test Preset",
            "effects_chain_config": {
                "name": original_chain.name,
                "effects": [
                    {
                        "type": "BOOST",
                        "parameters": {"gain_db": 6.0, "tone": 0.5},
                        "bypassed": False
                    },
                    {
                        "type": "DISTORTION",
                        "parameters": {"drive_db": 12.0, "tone": 0.6, "level": 0.7},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["audio_test"]
        }

        with patch.object(preset_manager, '_save_to_file'):
            saved_preset = preset_manager.save_preset(preset_config)

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

            # Load preset while audio is running
            with patch.object(preset_manager, '_get_preset_by_id', return_value=saved_preset):
                loaded_chain = preset_manager.load_preset(saved_preset.id)

            # Apply loaded chain to audio engine
            audio_engine.set_effects_chain(loaded_chain)

            # Verify audio processing works with loaded preset
            import numpy as np
            test_signal = np.sin(2 * np.pi * 440 * np.linspace(0, 0.01, 256))
            audio_frame = {
                "samples": [test_signal.tolist()],
                "channels": 1,
                "sample_rate": 48000
            }

            with patch.object(audio_engine, '_apply_effects_chain') as mock_effects:
                mock_effects.return_value = test_signal * 2.0  # Mock processing
                processed_frame = audio_engine.process_frame(audio_frame)
                assert processed_frame is not None

    def test_preset_file_persistence(self):
        """Test preset file system persistence"""
        preset_manager = PresetManager()

        # Create preset data
        preset_config = {
            "name": "File Persistence Test",
            "description": "Testing file save/load",
            "effects_chain_config": {
                "name": "Test Chain",
                "effects": [
                    {
                        "type": "REVERB",
                        "parameters": {"room_size": 0.8, "damping": 0.2},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["file_test", "persistence"]
        }

        # Mock file operations
        saved_data = None

        def mock_save_to_file(preset):
            nonlocal saved_data
            saved_data = preset.to_json()
            return True

        def mock_load_from_file(preset_id):
            if saved_data:
                from src.models.preset import Preset
                return Preset.from_json(saved_data)
            return None

        with patch.object(preset_manager, '_save_to_file', side_effect=mock_save_to_file):
            with patch.object(preset_manager, '_load_from_file', side_effect=mock_load_from_file):
                # Save preset
                saved_preset = preset_manager.save_preset(preset_config)

                # Verify data was "saved" to mock file
                assert saved_data is not None
                saved_json = json.loads(saved_data)
                assert saved_json["name"] == "File Persistence Test"

                # Load preset back
                with patch.object(preset_manager, '_get_preset_by_id', return_value=saved_preset):
                    loaded_preset = preset_manager.get_preset(saved_preset.id)

                # Verify loaded preset matches saved
                assert loaded_preset.name == saved_preset.name
                assert loaded_preset.description == saved_preset.description
                assert loaded_preset.tags == saved_preset.tags

    def test_preset_export_import_workflow(self):
        """Test preset export/import workflow"""
        preset_manager = PresetManager()

        # Create multiple presets
        preset1_config = {
            "name": "Export Test 1",
            "description": "First preset for export",
            "effects_chain_config": {
                "name": "Export Chain 1",
                "effects": [
                    {"type": "BOOST", "parameters": {"gain_db": 5.0}, "bypassed": False}
                ]
            },
            "tags": ["export", "test1"]
        }

        preset2_config = {
            "name": "Export Test 2",
            "description": "Second preset for export",
            "effects_chain_config": {
                "name": "Export Chain 2",
                "effects": [
                    {"type": "DISTORTION", "parameters": {"drive_db": 15.0}, "bypassed": False}
                ]
            },
            "tags": ["export", "test2"]
        }

        with patch.object(preset_manager, '_save_to_file'):
            preset1 = preset_manager.save_preset(preset1_config)
            preset2 = preset_manager.save_preset(preset2_config)

        # Export presets
        export_config = {
            "preset_ids": [preset1.id, preset2.id],
            "format": "json"
        }

        with patch.object(preset_manager, '_get_preset_by_id') as mock_get:
            mock_get.side_effect = lambda pid: preset1 if pid == preset1.id else preset2

            export_data = preset_manager.export_presets(export_config)

        # Verify export data
        assert isinstance(export_data, bytes)
        exported_json = json.loads(export_data.decode('utf-8'))
        assert len(exported_json) == 2

        # Import presets back (simulating fresh installation)
        import_config = {
            "file": export_data,
            "overwrite_existing": False
        }

        with patch.object(preset_manager, '_save_to_file'):
            with patch.object(preset_manager, '_preset_name_exists', return_value=False):
                import_result = preset_manager.import_presets(import_config)

        # Verify import results
        assert import_result["imported_count"] == 2
        assert import_result["skipped_count"] == 0
        assert len(import_result["errors"]) == 0

    def test_preset_workflow_error_handling(self):
        """Test preset workflow error handling and recovery"""
        preset_manager = PresetManager()
        effects_manager = EffectsManager()

        # Test save error handling
        preset_config = {
            "name": "Error Test Preset",
            "effects_chain_config": {"name": "Test", "effects": []},
            "tags": []
        }

        # Simulate file save error
        with patch.object(preset_manager, '_save_to_file', side_effect=IOError("Disk full")):
            with pytest.raises(RuntimeError, match="Failed to save preset"):
                preset_manager.save_preset(preset_config)

        # Test load error handling
        from uuid import uuid4
        test_preset_id = uuid4()

        # Simulate file load error
        with patch.object(preset_manager, '_load_from_file', side_effect=IOError("File not found")):
            with pytest.raises(RuntimeError, match="Failed to load preset"):
                preset_manager.load_preset(test_preset_id)

        # Test corrupted preset data handling
        corrupted_data = b"not valid json data"

        with patch.object(preset_manager, '_load_from_file', return_value=corrupted_data):
            with pytest.raises(ValueError, match="Invalid preset file format"):
                preset_manager.load_preset(test_preset_id)

    def test_preset_workflow_with_effect_modifications(self):
        """Test preset workflow when effects are modified after loading"""
        effects_manager = EffectsManager()
        preset_manager = PresetManager()

        # Create and save original preset
        original_config = {
            "name": "Modification Test",
            "effects_chain_config": {
                "name": "Original Chain",
                "effects": [
                    {
                        "type": "BOOST",
                        "parameters": {"gain_db": 5.0, "tone": 0.5},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["modification_test"]
        }

        with patch.object(preset_manager, '_save_to_file'):
            original_preset = preset_manager.save_preset(original_config)

        # Load preset
        with patch.object(preset_manager, '_get_preset_by_id', return_value=original_preset):
            loaded_chain = preset_manager.load_preset(original_preset.id)

        # Modify the loaded effects chain
        boost_effect = loaded_chain.effects[0]
        effects_manager.update_effect_parameters(boost_effect.id, {"gain_db": 12.0})

        # Add another effect
        distortion_config = {
            "type": "DISTORTION",
            "parameters": {"drive_db": 15.0, "tone": 0.6, "level": 0.8}
        }
        effects_manager.add_effect_to_chain(loaded_chain.id, distortion_config)

        # Save as new preset with modifications
        modified_config = {
            "name": "Modified Version",
            "description": "Modified version of original preset",
            "effects_chain_config": {
                "name": loaded_chain.name,
                "effects": [
                    {
                        "type": "BOOST",
                        "parameters": {"gain_db": 12.0, "tone": 0.5},  # Modified
                        "bypassed": False
                    },
                    {
                        "type": "DISTORTION",
                        "parameters": {"drive_db": 15.0, "tone": 0.6, "level": 0.8},  # Added
                        "bypassed": False
                    }
                ]
            },
            "tags": ["modification_test", "modified"]
        }

        with patch.object(preset_manager, '_save_to_file'):
            modified_preset = preset_manager.save_preset(modified_config)

        # Verify both presets exist and are different
        assert original_preset.id != modified_preset.id
        assert len(original_preset.effects_chain_config["effects"]) == 1
        assert len(modified_preset.effects_chain_config["effects"]) == 2

        # Load original preset again to verify it wasn't affected
        with patch.object(preset_manager, '_get_preset_by_id', return_value=original_preset):
            reloaded_original = preset_manager.load_preset(original_preset.id)

        assert len(reloaded_original.effects) == 1
        assert reloaded_original.effects[0].parameters["gain_db"] == 5.0  # Original value

    def test_preset_workflow_performance(self):
        """Test preset workflow performance for responsive UI"""
        import time
        preset_manager = PresetManager()

        # Create preset data
        preset_config = {
            "name": "Performance Test",
            "effects_chain_config": {
                "name": "Performance Chain",
                "effects": [
                    {"type": "BOOST", "parameters": {"gain_db": 6.0}, "bypassed": False},
                    {"type": "DISTORTION", "parameters": {"drive_db": 12.0}, "bypassed": False},
                    {"type": "DELAY", "parameters": {"delay_seconds": 0.3}, "bypassed": False},
                    {"type": "REVERB", "parameters": {"room_size": 0.5}, "bypassed": False}
                ]
            },
            "tags": ["performance"]
        }

        # Measure save time
        with patch.object(preset_manager, '_save_to_file'):
            start_time = time.time()
            saved_preset = preset_manager.save_preset(preset_config)
            save_time = (time.time() - start_time) * 1000  # ms

        # Measure load time
        with patch.object(preset_manager, '_get_preset_by_id', return_value=saved_preset):
            start_time = time.time()
            loaded_chain = preset_manager.load_preset(saved_preset.id)
            load_time = (time.time() - start_time) * 1000  # ms

        # Verify performance requirements (< 100ms for UI responsiveness)
        assert save_time < 100, f"Preset save took {save_time:.2f}ms, exceeds 100ms requirement"
        assert load_time < 100, f"Preset load took {load_time:.2f}ms, exceeds 100ms requirement"

        # Verify functionality wasn't compromised for performance
        assert loaded_chain.name == "Performance Test"
        assert len(loaded_chain.effects) == 4