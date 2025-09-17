import pytest
from uuid import UUID
from src.services.effects_manager import EffectsManager
from src.models.effects_chain import EffectsChain
from src.models.audio_effect import AudioEffect, EffectType


class TestEffectsManagementContract:
    """Contract tests for effects management interface"""

    def test_get_current_effects_chain_contract(self):
        """Test getting current effects chain contract"""
        effects_manager = EffectsManager()

        chain = effects_manager.get_current_chain()

        # Should return EffectsChain with required fields
        assert hasattr(chain, 'id')
        assert hasattr(chain, 'name')
        assert hasattr(chain, 'effects')
        assert hasattr(chain, 'active')
        assert hasattr(chain, 'created_at')
        assert hasattr(chain, 'modified_at')

        assert isinstance(chain.id, UUID)
        assert isinstance(chain.name, str)
        assert isinstance(chain.effects, list)
        assert isinstance(chain.active, bool)

    def test_create_new_effects_chain_contract(self):
        """Test creating new effects chain contract"""
        effects_manager = EffectsManager()

        chain_config = {
            "name": "New Test Chain",
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

        created_chain = effects_manager.create_chain(chain_config)

        # Verify chain creation
        assert created_chain.name == "New Test Chain"
        assert len(created_chain.effects) == 2
        assert isinstance(created_chain.id, UUID)

        # Verify first effect
        boost_effect = created_chain.effects[0]
        assert boost_effect.type == EffectType.BOOST
        assert boost_effect.parameters["gain_db"] == 6.0
        assert boost_effect.parameters["tone"] == 0.6

        # Verify second effect
        distortion_effect = created_chain.effects[1]
        assert distortion_effect.type == EffectType.DISTORTION
        assert distortion_effect.parameters["drive_db"] == 15.0

    def test_create_chain_invalid_config(self):
        """Test creating chain with invalid configuration"""
        effects_manager = EffectsManager()

        # Missing name
        invalid_config = {
            "effects": []
        }

        with pytest.raises(ValueError, match="Invalid effects chain configuration"):
            effects_manager.create_chain(invalid_config)

        # Invalid effect type
        invalid_effect_config = {
            "name": "Invalid Chain",
            "effects": [
                {
                    "type": "INVALID_TYPE",
                    "parameters": {}
                }
            ]
        }

        with pytest.raises(ValueError, match="Invalid effects chain configuration"):
            effects_manager.create_chain(invalid_effect_config)

    def test_update_effects_chain_contract(self):
        """Test updating effects chain contract"""
        effects_manager = EffectsManager()

        # Create initial chain
        chain_config = {
            "name": "Initial Chain",
            "effects": []
        }
        chain = effects_manager.create_chain(chain_config)
        chain_id = chain.id

        # Update chain
        update_config = {
            "name": "Updated Chain",
            "active": True
        }

        updated_chain = effects_manager.update_chain(chain_id, update_config)

        assert updated_chain.id == chain_id
        assert updated_chain.name == "Updated Chain"
        assert updated_chain.active is True

    def test_update_nonexistent_chain(self):
        """Test updating non-existent chain"""
        effects_manager = EffectsManager()

        from uuid import uuid4
        nonexistent_id = uuid4()

        update_config = {"name": "Updated Name"}

        with pytest.raises(ValueError, match="Effects chain not found"):
            effects_manager.update_chain(nonexistent_id, update_config)

    def test_add_effect_to_chain_contract(self):
        """Test adding effect to chain contract"""
        effects_manager = EffectsManager()

        # Create chain
        chain_config = {"name": "Test Chain", "effects": []}
        chain = effects_manager.create_chain(chain_config)

        # Add effect
        effect_config = {
            "type": "REVERB",
            "parameters": {"room_size": 0.7, "damping": 0.3},
            "position": 0
        }

        added_effect = effects_manager.add_effect_to_chain(chain.id, effect_config)

        # Verify effect was added
        assert added_effect.type == EffectType.REVERB
        assert added_effect.parameters["room_size"] == 0.7
        assert added_effect.parameters["damping"] == 0.3
        assert added_effect.position == 0
        assert isinstance(added_effect.id, UUID)

        # Verify chain was updated
        updated_chain = effects_manager.get_current_chain()
        assert len(updated_chain.effects) == 1
        assert updated_chain.effects[0].id == added_effect.id

    def test_add_effect_invalid_config(self):
        """Test adding effect with invalid configuration"""
        effects_manager = EffectsManager()

        chain_config = {"name": "Test Chain", "effects": []}
        chain = effects_manager.create_chain(chain_config)

        # Missing effect type
        invalid_config = {
            "parameters": {"gain_db": 6.0}
        }

        with pytest.raises(ValueError, match="Invalid effect configuration"):
            effects_manager.add_effect_to_chain(chain.id, invalid_config)

    def test_remove_effect_from_chain_contract(self):
        """Test removing effect from chain contract"""
        effects_manager = EffectsManager()

        # Create chain with effect
        chain_config = {
            "name": "Test Chain",
            "effects": [
                {
                    "type": "DELAY",
                    "parameters": {"delay_seconds": 0.5, "feedback": 0.4}
                }
            ]
        }
        chain = effects_manager.create_chain(chain_config)
        effect_id = chain.effects[0].id

        # Remove effect
        effects_manager.remove_effect_from_chain(chain.id, effect_id)

        # Verify effect was removed
        updated_chain = effects_manager.get_current_chain()
        assert len(updated_chain.effects) == 0

    def test_remove_nonexistent_effect(self):
        """Test removing non-existent effect"""
        effects_manager = EffectsManager()

        chain_config = {"name": "Test Chain", "effects": []}
        chain = effects_manager.create_chain(chain_config)

        from uuid import uuid4
        nonexistent_effect_id = uuid4()

        with pytest.raises(ValueError, match="Effect or chain not found"):
            effects_manager.remove_effect_from_chain(chain.id, nonexistent_effect_id)

    def test_reorder_effects_contract(self):
        """Test reordering effects in chain contract"""
        effects_manager = EffectsManager()

        # Create chain with multiple effects
        chain_config = {
            "name": "Test Chain",
            "effects": [
                {"type": "BOOST", "parameters": {"gain_db": 6.0}},
                {"type": "DISTORTION", "parameters": {"drive_db": 10.0}},
                {"type": "DELAY", "parameters": {"delay_seconds": 0.3}}
            ]
        }
        chain = effects_manager.create_chain(chain_config)

        # Get effect IDs in original order
        boost_id = chain.effects[0].id
        distortion_id = chain.effects[1].id
        delay_id = chain.effects[2].id

        # Reorder: delay -> boost -> distortion
        new_order = [delay_id, boost_id, distortion_id]
        reorder_config = {"effect_ids": new_order}

        reordered_chain = effects_manager.reorder_effects(chain.id, reorder_config)

        # Verify new order
        assert reordered_chain.effects[0].id == delay_id
        assert reordered_chain.effects[1].id == boost_id
        assert reordered_chain.effects[2].id == distortion_id

        # Verify positions were updated
        assert reordered_chain.effects[0].position == 0
        assert reordered_chain.effects[1].position == 1
        assert reordered_chain.effects[2].position == 2

    def test_reorder_effects_invalid_config(self):
        """Test reordering effects with invalid configuration"""
        effects_manager = EffectsManager()

        chain_config = {
            "name": "Test Chain",
            "effects": [{"type": "BOOST", "parameters": {}}]
        }
        chain = effects_manager.create_chain(chain_config)

        # Missing effect_ids
        invalid_config = {}

        with pytest.raises(ValueError, match="Invalid reorder configuration"):
            effects_manager.reorder_effects(chain.id, invalid_config)

        # Invalid effect ID
        from uuid import uuid4
        invalid_config = {"effect_ids": [uuid4()]}

        with pytest.raises(ValueError, match="Invalid reorder configuration"):
            effects_manager.reorder_effects(chain.id, invalid_config)

    def test_get_effect_parameters_contract(self):
        """Test getting effect parameters contract"""
        effects_manager = EffectsManager()

        # Create chain with effect
        chain_config = {
            "name": "Test Chain",
            "effects": [
                {
                    "type": "DISTORTION",
                    "parameters": {"drive_db": 15.0, "tone": 0.6, "level": 0.8}
                }
            ]
        }
        chain = effects_manager.create_chain(chain_config)
        effect_id = chain.effects[0].id

        # Get parameters
        parameters = effects_manager.get_effect_parameters(effect_id)

        # Verify parameter structure
        assert "drive_db" in parameters
        assert "tone" in parameters
        assert "level" in parameters

        # Verify parameter metadata
        drive_param = parameters["drive_db"]
        assert "value" in drive_param
        assert "min_value" in drive_param
        assert "max_value" in drive_param
        assert "default_value" in drive_param
        assert "units" in drive_param
        assert "curve_type" in drive_param

        assert drive_param["value"] == 15.0
        assert drive_param["min_value"] == 0.0
        assert drive_param["max_value"] == 30.0
        assert drive_param["units"] == "dB"

    def test_update_effect_parameters_contract(self):
        """Test updating effect parameters contract"""
        effects_manager = EffectsManager()

        # Create chain with effect
        chain_config = {
            "name": "Test Chain",
            "effects": [{"type": "BOOST", "parameters": {"gain_db": 0.0, "tone": 0.5}}]
        }
        chain = effects_manager.create_chain(chain_config)
        effect_id = chain.effects[0].id

        # Update parameters
        parameter_updates = {"gain_db": 12.0, "tone": 0.8}
        updated_parameters = effects_manager.update_effect_parameters(effect_id, parameter_updates)

        # Verify updates
        assert updated_parameters["gain_db"]["value"] == 12.0
        assert updated_parameters["tone"]["value"] == 0.8

    def test_update_effect_parameters_invalid_values(self):
        """Test updating effect parameters with invalid values"""
        effects_manager = EffectsManager()

        chain_config = {
            "name": "Test Chain",
            "effects": [{"type": "BOOST", "parameters": {}}]
        }
        chain = effects_manager.create_chain(chain_config)
        effect_id = chain.effects[0].id

        # Invalid parameter value
        invalid_updates = {"gain_db": 100.0}  # Exceeds maximum

        with pytest.raises(ValueError, match="Invalid parameter values"):
            effects_manager.update_effect_parameters(effect_id, invalid_updates)

    def test_toggle_effect_bypass_contract(self):
        """Test toggling effect bypass contract"""
        effects_manager = EffectsManager()

        # Create chain with effect
        chain_config = {
            "name": "Test Chain",
            "effects": [{"type": "REVERB", "parameters": {}}]
        }
        chain = effects_manager.create_chain(chain_config)
        effect_id = chain.effects[0].id

        # Toggle bypass
        bypass_config = {"bypassed": True}
        updated_effect = effects_manager.toggle_effect_bypass(effect_id, bypass_config)

        assert updated_effect.bypassed is True

        # Toggle back
        bypass_config = {"bypassed": False}
        updated_effect = effects_manager.toggle_effect_bypass(effect_id, bypass_config)

        assert updated_effect.bypassed is False