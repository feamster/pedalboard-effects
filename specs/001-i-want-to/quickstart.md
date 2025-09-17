# Quickstart Guide: Guitar Pedalboard Effects Chain

## Prerequisites

### Hardware Setup
1. **Scarlett Audio Interface**: Connected via USB with latest Focusrite drivers
2. **Guitar**: Connected to Input 2 of Scarlett
3. **Vocal Microphone**: Connected to Input 1 of Scarlett (optional)
4. **External Headphones**: Connected to monitor output

### Software Requirements
```bash
# Python 3.11 or higher
python --version

# Install core dependencies
pip install pedalboard>=0.7.0 PyQt6 numpy sounddevice

# Install development dependencies
pip install pytest pytest-mock pytest-asyncio
```

### Audio System Configuration
1. Open **Audio MIDI Setup** (Applications > Utilities)
2. Create **Multi-Output Device**:
   - Check both "Built-in Output" and "BlackHole 2ch"
   - Set Built-in Output as master device
3. Set **System Audio Output** to the Multi-Output Device
4. Configure **Scarlett** input gain and phantom power as needed

## Quick Start

### 1. Basic Audio Test
```python
# Test audio setup
python -c "
import sounddevice as sd
print('Available audio devices:')
print(sd.query_devices())
"
```

### 2. Launch Application
```bash
# From project root
python src/main.py

# Or with specific audio devices
python src/main.py --input='Scarlett 2i2 USB' --output='BlackHole 2ch'
```

### 3. Initial Configuration
1. **Audio Settings**:
   - Input: Select your Scarlett device (automatically detects dual inputs)
   - Output: Select Scarlett device or preferred output
   - Buffer Size: Start with 256 samples
   - Sample Rate: 48000 Hz

2. **Input Setup**:
   - **Input 1**: Vocal microphone (if connected)
   - **Input 2**: Guitar input
   - Both inputs are processed simultaneously and mixed to stereo output

3. **Effects Chain Setup**:
   - Add "Boost" effect (set Gain to +6 dB for clean boost)
   - Add "Distortion" with moderate drive
   - Add "Delay" for spatial effect
   - Add "Reverb" for ambience

## User Scenarios Walkthrough

### Scenario 1: Real-Time Audio Processing
**Given**: Guitar connected to Scarlett interface
**When**: Application starts
**Then**: Audio input should be detected and processed

**Test Steps**:
1. Connect guitar to Scarlett input 2
2. Optionally connect vocal mic to Scarlett input 1
3. Set input gains on Scarlett to appropriate levels (green LEDs)
4. Launch application
5. Verify audio meters show input signals from both channels
6. Play guitar and/or sing, confirm processed output in headphones

**Expected Result**: Clear, real-time audio processing with <10ms latency

### Scenario 2: Effect Parameter Adjustment
**Given**: Active audio processing
**When**: Adjusting effect parameters
**Then**: Audio output reflects changes immediately

**Test Steps**:
1. Add Distortion effect to chain
2. Move "Drive" slider from 0 to 15 dB
3. Adjust "Tone" knob while playing
4. Click "Bypass: OFF" button to toggle to "Bypass: ON"
5. Verify effect is bypassed but controls remain functional
6. Adjust parameters while bypassed
7. Toggle back to "Bypass: OFF" to re-enable effect

**Expected Result**: Smooth, real-time parameter changes without audio dropouts or UI freezing

### Scenario 3: Effects Chain Reordering
**Given**: Multiple effects in chain
**When**: Dragging effects to reorder
**Then**: Audio processing order updates immediately

**Test Steps**:
1. Add Boost, Distortion, Delay, Reverb effects
2. Play sustained chord
3. Drag Delay before Distortion
4. Listen to tonal difference
5. Reorder effects in different combinations

**Expected Result**: Immediate audio processing order changes

### Scenario 4: Preset Management
**Given**: Configured effects chain
**When**: Saving and loading presets
**Then**: Complete configuration restored

**Test Steps**:
1. Configure desired effects chain
2. Click "Save Preset" button
3. Name preset "My Rock Tone"
4. Add tags: "rock", "distortion"
5. Load different preset
6. Reload "My Rock Tone" preset

**Expected Result**: Exact effect configuration and parameters restored

## Testing Integration Scenarios

### Audio Routing Test
```python
# Verify audio routing through BlackHole
def test_audio_routing():
    # Start recording from BlackHole
    # Generate test tone through effects
    # Verify signal reaches BlackHole output
    pass
```

### Effect Chain Test
```python
# Verify effects processing order
def test_effects_chain():
    # Create chain: Boost -> Distortion -> Delay -> Reverb
    # Send test signal through chain
    # Verify each effect processes correctly
    # Verify order affects output characteristics
    pass
```

### Real-Time Parameter Test
```python
# Verify real-time parameter updates
def test_realtime_parameters():
    # Start audio processing
    # Modify distortion drive parameter
    # Verify audio output changes immediately
    # Measure update latency (<100ms)
    pass
```

### Preset Persistence Test
```python
# Verify preset save/load functionality
def test_preset_persistence():
    # Configure specific effects chain
    # Save as preset
    # Clear current chain
    # Load preset
    # Verify exact configuration restored
    pass
```

## Performance Validation

### Latency Measurement
```bash
# Measure round-trip latency
python scripts/measure_latency.py --input='Scarlett' --output='BlackHole'

# Expected: <10ms total latency
```

### CPU Usage Monitoring
```bash
# Monitor CPU usage during processing
python scripts/monitor_performance.py --duration=60

# Expected: <50% CPU usage on modern hardware
```

### Buffer Stability Test
```bash
# Test for audio dropouts over extended period
python scripts/stability_test.py --duration=3600

# Expected: Zero dropouts over 1 hour
```

## Troubleshooting

### Common Issues

**No Audio Input**:
- Check Scarlett device selection
- Verify input gain settings
- Confirm guitar cable connection

**High Latency**:
- Reduce buffer size to 128 or 64 samples
- Update Scarlett drivers
- Check system audio settings

**Audio Dropouts**:
- Increase buffer size to 512 samples
- Close unnecessary applications
- Check CPU usage

**Effect Not Working**:
- Verify effect is not bypassed
- Check parameter ranges
- Restart audio processing

### Debug Commands
```bash
# Check audio device status
python -c "import sounddevice; print(sounddevice.query_devices())"

# Verify pedalboard installation
python -c "import pedalboard; print(pedalboard.__version__)"

# Test basic audio processing
python scripts/audio_test.py --verbose
```

## Success Criteria

✅ **Audio Processing**: Real-time guitar processing with <10ms latency
✅ **Effect Control**: Smooth parameter adjustment without dropouts
✅ **Chain Management**: Instant effect reordering and bypass functionality
✅ **Preset System**: Reliable save/load with complete state restoration
✅ **Hardware Integration**: Seamless Scarlett + BlackHole audio routing
✅ **Performance**: Stable operation with <50% CPU usage

This quickstart guide validates all core functionality and provides confidence in the system's real-time audio processing capabilities.