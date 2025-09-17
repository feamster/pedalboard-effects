# Guitar Pedalboard Effects Chain

A real-time guitar effects processor built with Python, featuring dual input support and a responsive PyQt6 interface.

## Features

🎸 **Real-time Audio Processing**
- Sub-10ms latency guitar effects processing
- Spotify's pedalboard library integration
- Dual input support (guitar + vocal microphone)

🎛️ **Interactive Effects Chain**
- Boost, Distortion, Delay, Reverb effects
- Real-time parameter adjustment
- Drag-and-drop effect reordering
- Smart bypass functionality (controls remain active)

🔧 **Hardware Integration**
- Optimized for Focusrite Scarlett audio interfaces
- Input 1: Vocal microphone
- Input 2: Guitar
- Stereo output mixing

## Quick Start

### Prerequisites
```bash
# Python 3.11+
pip install pedalboard>=0.7.0 PyQt6 numpy sounddevice
```

### Hardware Setup
1. Connect guitar to Scarlett Input 2
2. Connect vocal mic to Scarlett Input 1 (optional)
3. Connect headphones to monitor output

### Run Application
```bash
python src/main.py
```

### Basic Usage
1. **Audio → Start Audio** to begin processing
2. Add effects using the "Add Effect" dropdown
3. Adjust parameters with real-time sliders
4. Use "Bypass: OFF/ON" to toggle effects
5. Save/load presets for different sounds

## Effects Available

- **Boost**: Clean gain boost with tone control
- **Distortion**: Overdrive/distortion with drive and tone
- **Delay**: Echo effect with feedback and mix controls
- **Reverb**: Spatial reverb with room size and damping

## Architecture

- **Audio Engine**: Real-time processing with sounddevice + pedalboard
- **Effects Chain**: Ordered sequence of configurable effects
- **UI Layer**: PyQt6 interface with responsive controls
- **Preset System**: Save/load complete effect configurations

## Development

### Project Structure
```
src/
├── main.py              # Application entry point
├── services/            # Core audio and effects services
├── ui/                  # PyQt6 interface components
├── models/              # Data models for effects and chains
└── cli/                 # Command-line utilities

tests/                   # Unit and integration tests
specs/                   # Feature specifications and documentation
```

### Running Tests
```bash
cd src && pytest && ruff check .
```

## Performance

- **Latency**: <10ms round-trip
- **CPU Usage**: <50% on modern hardware
- **Buffer Sizes**: 64-512 samples supported
- **Sample Rates**: 44.1kHz, 48kHz, 96kHz

## Hardware Tested

- ✅ Focusrite Scarlett 18i8 USB
- ✅ Focusrite Scarlett 2i2 USB
- ✅ BlackHole virtual audio driver
- ✅ Built-in Mac audio (limited performance)

## Contributing

This project uses feature branch development with specification-driven design. See `specs/` directory for detailed requirements and implementation plans.

## License

MIT License - see LICENSE file for details.

---

Built with ❤️ for guitarists who code (and coders who play guitar) 🎸⚡