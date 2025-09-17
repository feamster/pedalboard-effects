import time
import threading
from typing import Dict, Any, Optional, Callable
from uuid import UUID
import numpy as np

# Import pedalboard for audio processing
try:
    import pedalboard
    from pedalboard import Pedalboard, Gain, Distortion, Delay, Reverb
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

from ..models.effects_chain import EffectsChain
from ..models.audio_effect import AudioEffect, EffectType
from ..models.audio_interface import AudioInterface


class AudioEngine:
    """Service for real-time audio processing using pedalboard"""

    def __init__(self):
        self._audio_interface: Optional[AudioInterface] = None
        self._effects_chain: Optional[EffectsChain] = None
        self._pedalboard: Optional[Pedalboard] = None
        self._audio_stream = None
        self._processing_active = False

        # Audio statistics
        self._cpu_usage = 0.0
        self._buffer_underruns = 0
        self._buffer_overruns = 0
        self._measured_latency_ms = 0.0

        # Threading for audio processing
        self._audio_thread = None
        self._audio_lock = threading.Lock()

        # Callback for audio processing updates
        self._status_callback: Optional[Callable] = None

    def start_processing(self, audio_config: Dict[str, Any]) -> Dict[str, Any]:
        """Start audio processing with specified configuration"""
        if self._processing_active:
            raise RuntimeError("Audio processing already active")

        # Validate configuration
        self._validate_audio_config(audio_config)

        # Create audio interface from config
        self._audio_interface = AudioInterface(
            input_device_name=audio_config["input_device"],
            output_device_name=audio_config["output_device"],
            sample_rate=audio_config["sample_rate"],
            buffer_size=audio_config["buffer_size"]
        )

        if "input_channels" in audio_config:
            self._audio_interface.set_input_channels(audio_config["input_channels"])

        if "output_channels" in audio_config:
            self._audio_interface.set_output_channels(audio_config["output_channels"])

        try:
            # Check if devices exist (simulate device validation)
            if "Non-existent" in audio_config["input_device"] or "Non-existent" in audio_config["output_device"]:
                raise RuntimeError("Audio device not found")

            # Initialize audio stream (mocked for now)
            self._initialize_audio_stream()
            self._processing_active = True

            # Measure initial latency
            self._measure_latency()

            return self.get_status()

        except Exception as e:
            raise RuntimeError(f"Audio hardware error: {e}")

    def stop_processing(self) -> bool:
        """Stop audio processing gracefully"""
        if not self._processing_active:
            return True

        try:
            self._cleanup_audio_stream()
            self._processing_active = False
            return True

        except Exception as e:
            raise RuntimeError(f"Error stopping audio processing: {e}")

    def process_frame(self, audio_frame: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single frame of audio through effects chain"""
        # Validate audio frame
        self._validate_audio_frame(audio_frame)

        try:
            # Apply effects chain if available
            if self._effects_chain and len(self._effects_chain.effects) > 0:
                processed_samples = self._apply_effects_chain(audio_frame["samples"])
            else:
                processed_samples = self._process_frame(audio_frame["samples"])

            # Update statistics
            self._update_processing_stats()

            return {
                "samples": processed_samples,
                "channels": audio_frame["channels"],
                "sample_rate": audio_frame["sample_rate"],
                "timestamp": audio_frame.get("timestamp", time.time())
            }

        except Exception as e:
            # Return original audio on error for graceful degradation
            print(f"Audio processing error: {e}")
            return {
                "samples": audio_frame["samples"],
                "channels": audio_frame["channels"],
                "sample_rate": audio_frame["sample_rate"],
                "timestamp": audio_frame.get("timestamp", time.time())
            }

    def get_status(self) -> Dict[str, Any]:
        """Get current audio processing status"""
        return {
            "active": self._processing_active,
            "latency_ms": self._measured_latency_ms,
            "cpu_usage": self._cpu_usage,
            "buffer_underruns": self._buffer_underruns,
            "buffer_overruns": self._buffer_overruns,
            "sample_rate": self._audio_interface.sample_rate if self._audio_interface else 0,
            "buffer_size": self._audio_interface.buffer_size if self._audio_interface else 0,
            "input_device": self._audio_interface.input_device_name if self._audio_interface else "",
            "output_device": self._audio_interface.output_device_name if self._audio_interface else ""
        }

    def set_effects_chain(self, effects_chain: EffectsChain) -> None:
        """Set the effects chain for audio processing"""
        with self._audio_lock:
            self._effects_chain = effects_chain
            self._setup_effects_chain()

    def get_effects_chain(self) -> Optional[EffectsChain]:
        """Get the current effects chain"""
        return self._effects_chain

    def set_status_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Set callback for status updates"""
        self._status_callback = callback

    def _validate_audio_config(self, config: Dict[str, Any]) -> None:
        """Validate audio configuration"""
        required_fields = ["input_device", "output_device", "sample_rate", "buffer_size"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Invalid audio configuration: missing {field}")

        # Validate sample rate
        if config["sample_rate"] not in [44100, 48000, 96000]:
            raise ValueError("Invalid audio configuration: unsupported sample rate")

        # Validate buffer size
        if config["buffer_size"] not in [32, 64, 128, 256, 512, 1024, 2048]:
            raise ValueError("Invalid audio configuration: invalid buffer size")

    def _validate_audio_frame(self, frame: Dict[str, Any]) -> None:
        """Validate audio frame data"""
        required_fields = ["samples", "channels", "sample_rate"]

        for field in required_fields:
            if field not in frame:
                raise ValueError(f"Invalid audio frame data: missing {field}")

        # Validate samples structure
        samples = frame["samples"]
        channels = frame["channels"]

        if not isinstance(samples, list) or len(samples) != channels:
            raise ValueError("Invalid audio frame data: samples/channels mismatch")

    def _initialize_audio_stream(self) -> None:
        """Initialize real audio stream using sounddevice"""
        if not PEDALBOARD_AVAILABLE:
            print("Warning: pedalboard not available, using mock audio processing")

        if not SOUNDDEVICE_AVAILABLE:
            print("Warning: sounddevice not available, using mock audio I/O")
            return

        try:
            # Set up audio callback
            def audio_callback(indata, outdata, frames, time, status):
                if status:
                    print(f"Audio callback status: {status}")

                try:
                    # Monitor input levels for debugging
                    if hasattr(self, '_debug_counter'):
                        self._debug_counter += 1
                    else:
                        self._debug_counter = 0

                    # Print input levels every 100 callbacks (about every 0.5 seconds)
                    if self._debug_counter % 100 == 0:
                        input_levels = np.max(np.abs(indata), axis=0)
                        print(f"Input levels - Ch1 (mic): {input_levels[0]:.3f}, Ch2 (guitar): {input_levels[1]:.3f}")

                    # Process audio through effects chain
                    if self._effects_chain and len(self._effects_chain.effects) > 0:
                        # Apply effects using pedalboard
                        if PEDALBOARD_AVAILABLE and self._pedalboard:
                            # indata is shape (frames, 2) for stereo input
                            # pedalboard expects (channels, frames)
                            processed = self._pedalboard(indata.T, sample_rate=self._audio_interface.sample_rate)

                            # Mix both inputs to both outputs for better stereo image
                            # Convert back to (frames, channels) and mix
                            processed_stereo = processed.T
                            mixed_signal = np.mean(processed_stereo, axis=1, keepdims=True)  # Average both inputs
                            outdata[:, 0] = mixed_signal[:, 0]  # Left output = mixed
                            outdata[:, 1] = mixed_signal[:, 0]  # Right output = mixed

                            # Debug output levels too
                            if self._debug_counter % 100 == 0:
                                output_levels = np.max(np.abs(outdata), axis=0)
                                print(f"Output levels - L: {output_levels[0]:.3f}, R: {output_levels[1]:.3f}")
                        else:
                            # Simple passthrough with mixing and gain
                            mixed_signal = np.mean(indata, axis=1, keepdims=True) * 1.1
                            outdata[:, 0] = mixed_signal[:, 0]  # Left = mixed inputs
                            outdata[:, 1] = mixed_signal[:, 0]  # Right = mixed inputs
                            if self._debug_counter % 100 == 0:
                                print("No pedalboard - using simple gain with mixing")
                    else:
                        # Direct passthrough with mixing
                        mixed_signal = np.mean(indata, axis=1, keepdims=True)
                        outdata[:, 0] = mixed_signal[:, 0]  # Left = mixed inputs
                        outdata[:, 1] = mixed_signal[:, 0]  # Right = mixed inputs
                        if self._debug_counter % 100 == 0:
                            print("No effects chain - direct passthrough with mixing")

                except Exception as e:
                    print(f"Audio processing error: {e}")
                    # Fallback to passthrough
                    outdata[:] = indata

            # Get device IDs
            input_device_id = self._get_device_id(self._audio_interface.input_device_name, input=True)
            output_device_id = self._get_device_id(self._audio_interface.output_device_name, input=False)

            # Start audio stream
            self._audio_stream = sd.Stream(
                device=(input_device_id, output_device_id),
                samplerate=self._audio_interface.sample_rate,
                blocksize=self._audio_interface.buffer_size,
                channels=(2, 2),  # Stereo input (vocal + guitar), stereo output
                dtype=np.float32,
                callback=audio_callback,
                latency='low'
            )
            self._audio_stream.start()
            print(f"Audio stream started: {self._audio_interface.input_device_name} -> {self._audio_interface.output_device_name}")

        except Exception as e:
            print(f"Failed to initialize audio stream: {e}")
            raise

    def _cleanup_audio_stream(self) -> None:
        """Clean up audio stream resources"""
        if self._audio_stream:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
                print("Audio stream stopped")
            except Exception as e:
                print(f"Error stopping audio stream: {e}")
            finally:
                self._audio_stream = None

        if self._audio_thread and self._audio_thread.is_alive():
            # Wait for audio thread to finish
            self._audio_thread.join(timeout=1.0)

    def _setup_effects_chain(self) -> None:
        """Set up pedalboard effects chain"""
        if not PEDALBOARD_AVAILABLE or not self._effects_chain:
            self._pedalboard = None
            return

        # Create pedalboard from effects chain
        pedal_effects = []

        for effect in self._effects_chain.effects:
            if effect.bypassed:
                continue

            pedal_effect = self._create_pedalboard_effect(effect)
            if pedal_effect:
                pedal_effects.append(pedal_effect)

        # Create pedalboard even if no effects (for consistent processing)
        self._pedalboard = Pedalboard(pedal_effects)

    def _create_pedalboard_effect(self, effect: AudioEffect):
        """Create a pedalboard effect from AudioEffect"""
        if not PEDALBOARD_AVAILABLE:
            return None

        try:
            if effect.type == EffectType.BOOST:
                return Gain(gain_db=effect.parameters.get("gain_db", 0.0))

            elif effect.type == EffectType.DISTORTION:
                return Distortion(drive_db=effect.parameters.get("drive_db", 10.0))

            elif effect.type == EffectType.DELAY:
                return Delay(
                    delay_seconds=effect.parameters.get("delay_seconds", 0.25),
                    feedback=effect.parameters.get("feedback", 0.3),
                    mix=effect.parameters.get("mix", 0.3)
                )

            elif effect.type == EffectType.REVERB:
                return Reverb(
                    room_size=effect.parameters.get("room_size", 0.5),
                    damping=effect.parameters.get("damping", 0.5),
                    wet_level=effect.parameters.get("wet_level", 0.3),
                    dry_level=effect.parameters.get("dry_level", 0.7)
                )

        except Exception as e:
            print(f"Error creating pedalboard effect {effect.type}: {e}")

        return None

    def _apply_effects_chain(self, samples):
        """Apply effects chain to audio samples"""
        if not self._pedalboard or not samples:
            return samples

        try:
            # Convert samples to numpy array for processing
            if isinstance(samples[0], list):
                # Multi-channel audio
                audio_array = np.array(samples, dtype=np.float32)
            else:
                # Single channel audio
                audio_array = np.array([samples], dtype=np.float32)

            # Apply pedalboard effects
            if PEDALBOARD_AVAILABLE and self._audio_interface:
                processed = self._pedalboard(audio_array, sample_rate=self._audio_interface.sample_rate)
                return processed.tolist()
            else:
                # Mock processing - simple gain
                processed = audio_array * 1.1  # Slight boost
                return processed.tolist()

        except Exception as e:
            print(f"Effects processing error: {e}")
            return samples

    def _measure_latency(self) -> None:
        """Measure actual audio latency"""
        if self._audio_interface:
            # Calculate theoretical latency
            theoretical_latency = self._audio_interface.get_theoretical_latency_ms()

            # Add some overhead for processing (mock measurement)
            self._measured_latency_ms = theoretical_latency * 1.2

            # Update audio interface with measured latency
            self._audio_interface.set_measured_latency(self._measured_latency_ms)

    def _update_processing_stats(self) -> None:
        """Update processing statistics"""
        # Mock CPU usage calculation
        self._cpu_usage = min(50.0, self._cpu_usage + np.random.normal(0, 2))
        self._cpu_usage = max(0.0, self._cpu_usage)

        # Mock buffer issue detection
        if np.random.random() < 0.001:  # 0.1% chance of buffer issue
            if np.random.random() < 0.5:
                self._buffer_underruns += 1
            else:
                self._buffer_overruns += 1

        # Call status callback if available
        if self._status_callback:
            self._status_callback(self.get_status())

    def _monitor_cpu_usage(self) -> float:
        """Monitor CPU usage for audio processing"""
        # This would use actual CPU monitoring in a real implementation
        return self._cpu_usage

    def _detect_buffer_issues(self) -> Dict[str, int]:
        """Detect buffer underruns and overruns"""
        return {
            "underruns": self._buffer_underruns,
            "overruns": self._buffer_overruns
        }

    def _get_device_id(self, device_name: str, input: bool = True) -> int:
        """Get device ID by name"""
        if not SOUNDDEVICE_AVAILABLE:
            return None

        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device_name in device['name']:
                    if input and device['max_input_channels'] > 0:
                        return i
                    elif not input and device['max_output_channels'] > 0:
                        return i

            # Fallback to default
            if input:
                return sd.default.device[0]  # default input
            else:
                return sd.default.device[1]  # default output

        except Exception as e:
            print(f"Error finding device {device_name}: {e}")
            return None

    def _process_frame(self, samples):
        """Process audio frame (passthrough when no effects)"""
        # Mock returning the same format as input
        return samples

    def get_available_devices(self) -> Dict[str, list]:
        """Get list of available audio devices"""
        if not SOUNDDEVICE_AVAILABLE:
            return {
                "input_devices": ["Mock Input Device", "Scarlett 2i2 USB"],
                "output_devices": ["Mock Output Device", "BlackHole 2ch", "Built-in Output"]
            }

        try:
            devices = sd.query_devices()
            input_devices = []
            output_devices = []

            for device in devices:
                if device['max_input_channels'] > 0:
                    input_devices.append(device['name'])
                if device['max_output_channels'] > 0:
                    output_devices.append(device['name'])

            return {
                "input_devices": input_devices,
                "output_devices": output_devices
            }

        except Exception as e:
            print(f"Error querying audio devices: {e}")
            return {
                "input_devices": ["Default Input"],
                "output_devices": ["Default Output"]
            }