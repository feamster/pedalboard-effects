import pytest
from uuid import UUID
from src.services.preset_manager import PresetManager
from src.models.preset import Preset
from src.models.effects_chain import EffectsChain


class TestPresetManagementContract:
    """Contract tests for preset management interface"""

    def test_list_all_presets_contract(self):
        """Test listing all presets contract"""
        preset_manager = PresetManager()

        presets = preset_manager.list_presets()

        # Should return list of preset summaries
        assert isinstance(presets, list)

        if len(presets) > 0:
            preset_summary = presets[0]
            # Required fields for preset summary
            assert "id" in preset_summary
            assert "name" in preset_summary
            assert "description" in preset_summary
            assert "created_at" in preset_summary
            assert "tags" in preset_summary
            assert "effect_count" in preset_summary

            assert isinstance(preset_summary["id"], str)
            assert isinstance(preset_summary["name"], str)
            assert isinstance(preset_summary["tags"], list)
            assert isinstance(preset_summary["effect_count"], int)

    def test_list_presets_with_tags_filter(self):
        """Test listing presets with tags filter"""
        preset_manager = PresetManager()

        # Filter by tags
        filtered_presets = preset_manager.list_presets(tags=["rock", "distortion"])

        assert isinstance(filtered_presets, list)
        # All returned presets should have at least one of the specified tags
        for preset in filtered_presets:
            preset_tags = preset["tags"]
            assert any(tag in ["rock", "distortion"] for tag in preset_tags)

    def test_list_presets_with_search_filter(self):
        """Test listing presets with search filter"""
        preset_manager = PresetManager()

        # Search by name or description
        search_results = preset_manager.list_presets(search="rock")

        assert isinstance(search_results, list)
        # All returned presets should contain "rock" in name or description
        for preset in search_results:
            name_match = "rock" in preset["name"].lower()
            desc_match = preset["description"] and "rock" in preset["description"].lower()
            assert name_match or desc_match

    def test_save_new_preset_contract(self):
        """Test saving new preset contract"""
        preset_manager = PresetManager()

        # Create effects chain for preset
        from src.models.effects_chain import EffectsChain
        from src.models.audio_effect import AudioEffect, EffectType

        chain = EffectsChain(name="Test Chain")
        boost = AudioEffect(effect_type=EffectType.BOOST)
        boost.update_parameters({"gain_db": 8.0, "tone": 0.7})
        chain.add_effect(boost)

        preset_config = {
            "name": "Test Rock Preset",
            "description": "A test preset for rock music",
            "effects_chain_config": {
                "name": "Test Chain",
                "effects": [
                    {
                        "type": "BOOST",
                        "parameters": {"gain_db": 8.0, "tone": 0.7},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["rock", "test"],
            "author": "Test User"
        }

        saved_preset = preset_manager.save_preset(preset_config)

        # Verify saved preset
        assert isinstance(saved_preset.id, UUID)
        assert saved_preset.name == "Test Rock Preset"
        assert saved_preset.description == "A test preset for rock music"
        assert saved_preset.tags == ["rock", "test"]
        assert saved_preset.author == "Test User"
        assert saved_preset.version == "1.0.0"
        assert saved_preset.created_at is not None

    def test_save_preset_invalid_data(self):
        """Test saving preset with invalid data"""
        preset_manager = PresetManager()

        # Missing name
        invalid_config = {
            "description": "Missing name",
            "effects_chain_config": {"effects": []}
        }

        with pytest.raises(ValueError, match="Invalid preset data"):
            preset_manager.save_preset(invalid_config)

        # Missing effects_chain_config
        invalid_config = {
            "name": "Missing Chain Config",
            "description": "Missing effects chain"
        }

        with pytest.raises(ValueError, match="Invalid preset data"):
            preset_manager.save_preset(invalid_config)

    def test_save_preset_duplicate_name(self):
        """Test saving preset with duplicate name"""
        preset_manager = PresetManager()

        preset_config = {
            "name": "Duplicate Name",
            "effects_chain_config": {"name": "Test", "effects": []},
            "tags": []
        }

        # Save first preset
        preset_manager.save_preset(preset_config)

        # Attempt to save second preset with same name should fail
        with pytest.raises(ValueError, match="Preset name already exists"):
            preset_manager.save_preset(preset_config)

    def test_get_preset_details_contract(self):
        """Test getting preset details contract"""
        preset_manager = PresetManager()

        # First save a preset
        preset_config = {
            "name": "Detail Test Preset",
            "description": "For testing preset details",
            "effects_chain_config": {
                "name": "Detail Chain",
                "effects": [
                    {
                        "type": "DISTORTION",
                        "parameters": {"drive_db": 15.0, "tone": 0.5, "level": 0.7},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["detail", "test"]
        }

        saved_preset = preset_manager.save_preset(preset_config)

        # Get preset details
        preset_details = preset_manager.get_preset(saved_preset.id)

        # Verify complete preset structure
        assert preset_details.id == saved_preset.id
        assert preset_details.name == "Detail Test Preset"
        assert preset_details.description == "For testing preset details"
        assert preset_details.tags == ["detail", "test"]
        assert preset_details.version == "1.0.0"

        # Verify effects chain configuration
        chain_config = preset_details.effects_chain_config
        assert chain_config["name"] == "Detail Chain"
        assert len(chain_config["effects"]) == 1

        effect_config = chain_config["effects"][0]
        assert effect_config["type"] == "DISTORTION"
        assert effect_config["parameters"]["drive_db"] == 15.0

    def test_get_nonexistent_preset(self):
        """Test getting non-existent preset"""
        preset_manager = PresetManager()

        from uuid import uuid4
        nonexistent_id = uuid4()

        with pytest.raises(ValueError, match="Preset not found"):
            preset_manager.get_preset(nonexistent_id)

    def test_update_preset_contract(self):
        """Test updating preset contract"""
        preset_manager = PresetManager()

        # Save initial preset
        initial_config = {
            "name": "Original Name",
            "description": "Original description",
            "effects_chain_config": {"name": "Test", "effects": []},
            "tags": ["original"]
        }

        saved_preset = preset_manager.save_preset(initial_config)

        # Update preset
        update_config = {
            "name": "Updated Name",
            "description": "Updated description",
            "tags": ["updated", "modified"]
        }

        updated_preset = preset_manager.update_preset(saved_preset.id, update_config)

        # Verify updates
        assert updated_preset.id == saved_preset.id  # ID unchanged
        assert updated_preset.name == "Updated Name"
        assert updated_preset.description == "Updated description"
        assert updated_preset.tags == ["updated", "modified"]
        assert updated_preset.created_at == saved_preset.created_at  # Created time unchanged
        assert updated_preset.modified_at != saved_preset.modified_at  # Modified time changed

    def test_update_nonexistent_preset(self):
        """Test updating non-existent preset"""
        preset_manager = PresetManager()

        from uuid import uuid4
        nonexistent_id = uuid4()

        update_config = {"name": "Updated Name"}

        with pytest.raises(ValueError, match="Preset not found"):
            preset_manager.update_preset(nonexistent_id, update_config)

    def test_delete_preset_contract(self):
        """Test deleting preset contract"""
        preset_manager = PresetManager()

        # Save preset to delete
        preset_config = {
            "name": "To Be Deleted",
            "effects_chain_config": {"name": "Test", "effects": []},
            "tags": []
        }

        saved_preset = preset_manager.save_preset(preset_config)

        # Delete preset
        result = preset_manager.delete_preset(saved_preset.id)
        assert result is True

        # Verify preset is deleted
        with pytest.raises(ValueError, match="Preset not found"):
            preset_manager.get_preset(saved_preset.id)

    def test_delete_nonexistent_preset(self):
        """Test deleting non-existent preset"""
        preset_manager = PresetManager()

        from uuid import uuid4
        nonexistent_id = uuid4()

        with pytest.raises(ValueError, match="Preset not found"):
            preset_manager.delete_preset(nonexistent_id)

    def test_load_preset_contract(self):
        """Test loading preset contract"""
        preset_manager = PresetManager()

        # Save preset with complex effects chain
        preset_config = {
            "name": "Complex Load Test",
            "effects_chain_config": {
                "name": "Load Test Chain",
                "effects": [
                    {
                        "type": "BOOST",
                        "parameters": {"gain_db": 6.0, "tone": 0.6},
                        "bypassed": False
                    },
                    {
                        "type": "DISTORTION",
                        "parameters": {"drive_db": 20.0, "tone": 0.4, "level": 0.8},
                        "bypassed": False
                    },
                    {
                        "type": "DELAY",
                        "parameters": {"delay_seconds": 0.3, "feedback": 0.4, "mix": 0.5},
                        "bypassed": False
                    }
                ]
            },
            "tags": ["complex", "load_test"]
        }

        saved_preset = preset_manager.save_preset(preset_config)

        # Load preset into effects chain
        loaded_chain = preset_manager.load_preset(saved_preset.id)

        # Verify loaded chain matches preset configuration
        assert loaded_chain.name == "Complex Load Test"  # Uses preset name
        assert len(loaded_chain.effects) == 3

        # Verify first effect (boost)
        boost_effect = loaded_chain.effects[0]
        assert boost_effect.type.value == "BOOST"
        assert boost_effect.parameters["gain_db"] == 6.0
        assert boost_effect.parameters["tone"] == 0.6
        assert not boost_effect.bypassed

        # Verify second effect (distortion)
        distortion_effect = loaded_chain.effects[1]
        assert distortion_effect.type.value == "DISTORTION"
        assert distortion_effect.parameters["drive_db"] == 20.0

        # Verify third effect (delay)
        delay_effect = loaded_chain.effects[2]
        assert delay_effect.type.value == "DELAY"
        assert delay_effect.parameters["delay_seconds"] == 0.3

    def test_load_nonexistent_preset(self):
        """Test loading non-existent preset"""
        preset_manager = PresetManager()

        from uuid import uuid4
        nonexistent_id = uuid4()

        with pytest.raises(ValueError, match="Preset not found"):
            preset_manager.load_preset(nonexistent_id)

    def test_export_presets_contract(self):
        """Test exporting presets contract"""
        preset_manager = PresetManager()

        # Save multiple presets
        preset1_config = {
            "name": "Export Test 1",
            "effects_chain_config": {"name": "Test", "effects": []},
            "tags": ["export"]
        }
        preset2_config = {
            "name": "Export Test 2",
            "effects_chain_config": {"name": "Test", "effects": []},
            "tags": ["export"]
        }

        preset1 = preset_manager.save_preset(preset1_config)
        preset2 = preset_manager.save_preset(preset2_config)

        # Export presets
        export_config = {
            "preset_ids": [preset1.id, preset2.id],
            "format": "json"
        }

        export_data = preset_manager.export_presets(export_config)

        # Verify export data
        assert isinstance(export_data, bytes)  # Binary data for download

        # Parse exported JSON
        import json
        exported_presets = json.loads(export_data.decode('utf-8'))
        assert len(exported_presets) == 2
        assert any(p["name"] == "Export Test 1" for p in exported_presets)
        assert any(p["name"] == "Export Test 2" for p in exported_presets)

    def test_export_presets_invalid_request(self):
        """Test exporting presets with invalid request"""
        preset_manager = PresetManager()

        # Missing preset_ids
        invalid_config = {
            "format": "json"
        }

        with pytest.raises(ValueError, match="Invalid export request"):
            preset_manager.export_presets(invalid_config)

        # Empty preset_ids
        invalid_config = {
            "preset_ids": [],
            "format": "json"
        }

        with pytest.raises(ValueError, match="Invalid export request"):
            preset_manager.export_presets(invalid_config)

    def test_import_presets_contract(self):
        """Test importing presets contract"""
        preset_manager = PresetManager()

        # Create export data to import
        import json
        import_data = json.dumps([
            {
                "name": "Imported Preset 1",
                "description": "First imported preset",
                "effects_chain_config": {"name": "Import Test", "effects": []},
                "tags": ["imported"],
                "version": "1.0.0"
            },
            {
                "name": "Imported Preset 2",
                "description": "Second imported preset",
                "effects_chain_config": {"name": "Import Test", "effects": []},
                "tags": ["imported"],
                "version": "1.0.0"
            }
        ]).encode('utf-8')

        # Import presets
        import_config = {
            "file": import_data,
            "overwrite_existing": False
        }

        import_result = preset_manager.import_presets(import_config)

        # Verify import result
        assert "imported_count" in import_result
        assert "skipped_count" in import_result
        assert "errors" in import_result

        assert import_result["imported_count"] == 2
        assert import_result["skipped_count"] == 0
        assert len(import_result["errors"]) == 0

        # Verify presets were imported
        all_presets = preset_manager.list_presets()
        imported_names = [p["name"] for p in all_presets if "imported" in p["tags"]]
        assert "Imported Preset 1" in imported_names
        assert "Imported Preset 2" in imported_names

    def test_import_presets_invalid_file(self):
        """Test importing presets with invalid file"""
        preset_manager = PresetManager()

        # Invalid JSON data
        invalid_data = b"not valid json"

        import_config = {
            "file": invalid_data,
            "overwrite_existing": False
        }

        with pytest.raises(ValueError, match="Invalid import file"):
            preset_manager.import_presets(import_config)