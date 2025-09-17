# Data Model: Guitar Pedalboard Effects Chain

## Core Entities

### EffectsChain
**Purpose**: Manages ordered sequence of audio effects and their processing flow
**Fields**:
- `id`: Unique identifier (UUID)
- `name`: Human-readable name for the chain
- `effects`: Ordered list of AudioEffect instances
- `active`: Boolean indicating if chain is currently processing
- `created_at`: Timestamp of creation
- `modified_at`: Timestamp of last modification

**Validation Rules**:
- Effects list must maintain order integrity
- Maximum 8 effects per chain (performance constraint)
- Chain name must be 1-50 characters
- Cannot have duplicate effect instances

**State Transitions**:
- `inactive` → `active`: Initialize audio processing
- `active` → `inactive`: Stop processing and release resources
- `active` → `active`: Modify effects (hot-swapping)

### AudioEffect
**Purpose**: Individual processing unit with configurable parameters
**Fields**:
- `id`: Unique identifier (UUID)
- `type`: Effect type enum (BOOST, DISTORTION, DELAY, REVERB)
- `parameters`: Dictionary of effect-specific parameters
- `bypassed`: Boolean indicating if effect is bypassed
- `position`: Integer indicating order in chain (0-based)
- `preset_name`: Optional saved parameter configuration name

**Validation Rules**:
- Parameter values must be within effect-specific ranges
- Type cannot be changed after instantiation
- Position must be unique within chain
- Preset name must be valid filename characters only

**Effect-Specific Parameters**:

#### BOOST
- `gain_db`: Float (-20.0 to +30.0, default: 0.0)
- `tone`: Float (0.0 to 1.0, default: 0.5)

#### DISTORTION
- `drive_db`: Float (0.0 to +30.0, default: 10.0)
- `tone`: Float (0.0 to 1.0, default: 0.5)
- `level`: Float (0.0 to 1.0, default: 0.7)

#### DELAY
- `delay_seconds`: Float (0.0 to 2.0, default: 0.25)
- `feedback`: Float (0.0 to 0.95, default: 0.3)
- `mix`: Float (0.0 to 1.0, default: 0.3)
- `tempo_sync`: Boolean (default: False)

#### REVERB
- `room_size`: Float (0.0 to 1.0, default: 0.5)
- `damping`: Float (0.0 to 1.0, default: 0.5)
- `wet_level`: Float (0.0 to 1.0, default: 0.3)
- `dry_level`: Float (0.0 to 1.0, default: 0.7)

### Preset
**Purpose**: Saved configuration of complete effects chain
**Fields**:
- `id`: Unique identifier (UUID)
- `name`: Human-readable preset name
- `description`: Optional description text
- `effects_chain_config`: Serialized EffectsChain configuration
- `created_at`: Timestamp of creation
- `tags`: List of searchable tags
- `author`: Creator identification

**Validation Rules**:
- Preset name must be unique and 1-100 characters
- Description maximum 500 characters
- Effects chain config must be valid JSON
- Tags must be alphanumeric with hyphens/underscores only

### AudioInterface
**Purpose**: Represents audio hardware connection and configuration
**Fields**:
- `input_device_name`: String name of input device
- `output_device_name`: String name of output device
- `sample_rate`: Integer sample rate (44100, 48000, 96000)
- `buffer_size`: Integer buffer size in samples
- `input_channels`: List of active input channel indices
- `output_channels`: List of active output channel indices
- `latency_ms`: Measured actual latency

**Validation Rules**:
- Device names must match available system devices
- Sample rate must be supported by devices
- Buffer size must be power of 2 between 32-2048
- Channel indices must be valid for selected devices

### EffectParameter
**Purpose**: Individual configurable parameter with metadata
**Fields**:
- `name`: Parameter name (matches effect parameter keys)
- `value`: Current parameter value
- `min_value`: Minimum allowed value
- `max_value`: Maximum allowed value
- `default_value`: Factory default value
- `units`: Display units (db, ms, %, etc.)
- `curve_type`: Parameter scaling (linear, log, exponential)

**Validation Rules**:
- Value must be within min/max range
- Curve type affects UI control mapping
- Units used for display formatting only

## Relationships

### EffectsChain → AudioEffect
- **Type**: One-to-Many (composition)
- **Constraint**: Ordered list with position integrity
- **Cascade**: Delete chain deletes all contained effects

### Preset → EffectsChain
- **Type**: One-to-One (serialization)
- **Constraint**: Preset contains complete chain configuration
- **Behavior**: Loading preset recreates entire chain

### AudioEffect → EffectParameter
- **Type**: One-to-Many (composition)
- **Constraint**: Parameters specific to effect type
- **Cascade**: Effect deletion removes all parameters

### AudioInterface → EffectsChain
- **Type**: One-to-One (processing context)
- **Constraint**: Single active chain per interface
- **Behavior**: Interface provides processing context for chain

## Data Flow

### Audio Processing Flow
```
AudioInterface → EffectsChain → [AudioEffect...] → AudioInterface
```

### Configuration Flow
```
Preset → EffectsChain → AudioEffect → EffectParameter
```

### UI Control Flow
```
UI Controls → EffectParameter → AudioEffect → Real-time Audio Update
```

## Persistence Strategy

### JSON Format for Presets
```json
{
  "id": "uuid",
  "name": "My Guitar Tone",
  "description": "Crunchy distortion with spatial delay",
  "effects_chain": {
    "effects": [
      {
        "type": "BOOST",
        "parameters": {"gain_db": 6.0, "tone": 0.6},
        "bypassed": false
      },
      {
        "type": "DISTORTION",
        "parameters": {"drive_db": 15.0, "tone": 0.4, "level": 0.8},
        "bypassed": false
      }
    ]
  },
  "created_at": "2025-09-15T10:30:00Z",
  "tags": ["rock", "crunch", "lead"]
}
```

### Configuration Files
- **Presets**: `~/.pedalboard/presets/*.json`
- **Audio Settings**: `~/.pedalboard/audio_config.json`
- **UI Settings**: `~/.pedalboard/ui_config.json`

This data model provides a robust foundation for real-time audio effects processing while maintaining simplicity and performance optimization.