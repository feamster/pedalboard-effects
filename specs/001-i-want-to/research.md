# Research Findings: Guitar Pedalboard Effects Chain

## Audio Latency Requirements

**Decision**: Target 6ms latency (256 samples at 44.1kHz) for stable real-time guitar processing
**Rationale**:
- Spotify pedalboard can achieve 1.5-3ms ultra-low latency but may cause dropouts
- 6ms provides excellent responsiveness while maintaining stability
- Python's garbage collection requires soft real-time approach with buffer management
**Alternatives considered**:
- 1-3ms ultra-low latency (rejected: stability issues with Python GC)
- 12ms conservative approach (rejected: noticeable delay for guitar players)

## Primary Audio Library Selection

**Decision**: Use Spotify pedalboard's built-in AudioStream for core audio processing
**Rationale**:
- Built on JUCE framework with 300x performance advantage
- Native real-time support via AudioStream class (v0.7.0+)
- Direct support for VST3/AU plugins and professional effects
- Releases GIL for multi-threaded parameter control
**Alternatives considered**:
- sounddevice + manual effect implementation (rejected: inferior performance and effect quality)
- PyO with JACK (rejected: additional complexity, JACK not standard on macOS)

## Effects Chain Architecture

**Decision**: Boost → Distortion → Delay → Reverb signal chain using pedalboard effects
**Rationale**:
- Standard guitar pedal ordering for musical coherence
- Pedalboard provides all required effects: Gain, Distortion, Delay, Reverb
- Real-time parameter updates support smooth control
- Effect bypassing without removal maintains audio continuity
**Alternatives considered**:
- Custom DSP implementation (rejected: development time vs quality tradeoff)
- Plugin-based architecture (considered for future expansion)

## Audio Routing Strategy

**Decision**: Scarlett input → pedalboard processing → BlackHole → external monitoring
**Rationale**:
- BlackHole provides zero-latency virtual audio routing
- Maintains existing audio setup compatibility
- Enables recording and DAW integration
- Supports multi-output device configuration
**Alternatives considered**:
- Direct hardware monitoring (rejected: defeats purpose of digital effects)
- JACK audio server (rejected: not standard macOS audio solution)

## User Interface Framework

**Decision**: PyQt6 for professional audio application UI
**Rationale**:
- Professional appearance suitable for audio applications
- Efficient real-time widget updates for parameter controls
- Cross-platform compatibility for future expansion
- Good integration with audio processing threads
**Alternatives considered**:
- tkinter (rejected: limited styling and professional appearance)
- web-based UI (rejected: unnecessary complexity for desktop audio app)

## Performance Optimization Strategy

**Decision**: Multi-threaded architecture with separate audio, control, and UI threads
**Rationale**:
- Pedalboard releases GIL enabling true multi-threading
- Audio thread isolation prevents UI blocking
- Lock-free queues for inter-thread communication
- Adaptive buffer management based on system performance
**Alternatives considered**:
- Single-threaded approach (rejected: UI updates would block audio)
- Async/await pattern (rejected: not suitable for hard real-time audio)

## Development and Testing Approach

**Decision**: Test-driven development with audio mocking and real device integration tests
**Rationale**:
- Contract-first approach ensures interface stability
- Mock audio devices for unit testing
- Real device tests for integration and latency validation
- Performance profiling integrated into test suite
**Alternatives considered**:
- Manual testing only (rejected: insufficient for audio latency validation)
- Simulation-only testing (rejected: real audio hardware behavior essential)

## Key Technical Specifications

- **Target Latency**: 6ms (256 samples at 44.1kHz)
- **Sample Rate**: 48kHz (optimal for Scarlett interfaces)
- **Buffer Management**: Adaptive sizing with dropout monitoring
- **Threading**: Audio (high priority) + Control + UI threads
- **Audio Format**: 32-bit float for processing, 24-bit for I/O
- **Parameter Update Rate**: 100Hz for smooth real-time control

## Implementation Dependencies

- **Core**: pedalboard >= 0.7.0, numpy, PyQt6
- **Audio**: sounddevice (fallback), pyaudio (device enumeration)
- **Serialization**: JSON for presets (human-readable)
- **Testing**: pytest, pytest-mock, audio-testing-utils

This research provides the foundation for a professional-quality real-time guitar effects processor optimized for the specified audio hardware configuration.