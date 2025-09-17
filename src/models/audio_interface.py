from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AudioDeviceInfo:
    """Information about an audio device"""
    name: str
    max_input_channels: int
    max_output_channels: int
    supported_sample_rates: List[int]
    default_sample_rate: int
    device_index: int


class AudioInterface:
    """Represents audio hardware connection and configuration"""

    SUPPORTED_SAMPLE_RATES = [44100, 48000, 96000]
    VALID_BUFFER_SIZES = [32, 64, 128, 256, 512, 1024, 2048]

    def __init__(
        self,
        input_device_name: str,
        output_device_name: str,
        sample_rate: int = 48000,
        buffer_size: int = 256
    ):
        self.id = uuid4()
        self.input_device_name = input_device_name
        self.output_device_name = output_device_name
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.input_channels: List[int] = [0]  # Default to first channel
        self.output_channels: List[int] = [0, 1]  # Default to stereo
        self.latency_ms: Optional[float] = None

        # Validate configuration
        self._validate_sample_rate()
        self._validate_buffer_size()

    def _validate_sample_rate(self) -> None:
        """Validate sample rate"""
        if self.sample_rate not in self.SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Sample rate must be one of {self.SUPPORTED_SAMPLE_RATES}")

    def _validate_buffer_size(self) -> None:
        """Validate buffer size"""
        if self.buffer_size not in self.VALID_BUFFER_SIZES:
            raise ValueError(f"Buffer size must be one of {self.VALID_BUFFER_SIZES}")

    def set_sample_rate(self, sample_rate: int) -> None:
        """Set audio sample rate"""
        if sample_rate not in self.SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"Sample rate must be one of {self.SUPPORTED_SAMPLE_RATES}")
        self.sample_rate = sample_rate

    def set_buffer_size(self, buffer_size: int) -> None:
        """Set audio buffer size"""
        if buffer_size not in self.VALID_BUFFER_SIZES:
            raise ValueError(f"Buffer size must be one of {self.VALID_BUFFER_SIZES}")
        self.buffer_size = buffer_size

    def set_input_channels(self, channels: List[int]) -> None:
        """Set active input channels"""
        if not channels:
            raise ValueError("At least one input channel must be specified")
        if any(ch < 0 for ch in channels):
            raise ValueError("Channel indices must be non-negative")
        self.input_channels = channels.copy()

    def set_output_channels(self, channels: List[int]) -> None:
        """Set active output channels"""
        if not channels:
            raise ValueError("At least one output channel must be specified")
        if any(ch < 0 for ch in channels):
            raise ValueError("Channel indices must be non-negative")
        self.output_channels = channels.copy()

    def set_measured_latency(self, latency_ms: float) -> None:
        """Set measured actual latency"""
        if latency_ms < 0:
            raise ValueError("Latency must be non-negative")
        self.latency_ms = latency_ms

    def get_theoretical_latency_ms(self) -> float:
        """Calculate theoretical minimum latency based on buffer size and sample rate"""
        return (self.buffer_size / self.sample_rate) * 1000

    def is_low_latency_config(self) -> bool:
        """Check if configuration is optimized for low latency"""
        theoretical_latency = self.get_theoretical_latency_ms()
        return theoretical_latency <= 10.0  # < 10ms for guitar processing

    def get_input_channel_count(self) -> int:
        """Get number of active input channels"""
        return len(self.input_channels)

    def get_output_channel_count(self) -> int:
        """Get number of active output channels"""
        return len(self.output_channels)

    def supports_real_time_processing(self) -> bool:
        """Check if configuration supports real-time audio processing"""
        # Check if buffer size is reasonable for real-time processing
        if self.buffer_size > 1024:
            return False

        # Check if sample rate is suitable
        if self.sample_rate < 44100:
            return False

        return True

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration"""
        return {
            "input_device": self.input_device_name,
            "output_device": self.output_device_name,
            "sample_rate": self.sample_rate,
            "buffer_size": self.buffer_size,
            "input_channels": self.input_channels.copy(),
            "output_channels": self.output_channels.copy(),
            "theoretical_latency_ms": self.get_theoretical_latency_ms(),
            "measured_latency_ms": self.latency_ms,
            "low_latency": self.is_low_latency_config(),
            "real_time_capable": self.supports_real_time_processing()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert audio interface to dictionary for serialization"""
        return {
            "id": str(self.id),
            "input_device_name": self.input_device_name,
            "output_device_name": self.output_device_name,
            "sample_rate": self.sample_rate,
            "buffer_size": self.buffer_size,
            "input_channels": self.input_channels.copy(),
            "output_channels": self.output_channels.copy(),
            "latency_ms": self.latency_ms
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AudioInterface':
        """Create audio interface from dictionary"""
        interface = cls(
            input_device_name=data["input_device_name"],
            output_device_name=data["output_device_name"],
            sample_rate=data.get("sample_rate", 48000),
            buffer_size=data.get("buffer_size", 256)
        )

        if "id" in data:
            interface.id = UUID(data["id"])

        if "input_channels" in data:
            interface.set_input_channels(data["input_channels"])

        if "output_channels" in data:
            interface.set_output_channels(data["output_channels"])

        if "latency_ms" in data and data["latency_ms"] is not None:
            interface.set_measured_latency(data["latency_ms"])

        return interface

    def copy(self) -> 'AudioInterface':
        """Create a copy of this audio interface with new ID"""
        interface_dict = self.to_dict()
        copy_interface = self.from_dict(interface_dict)
        copy_interface.id = uuid4()  # Generate new ID for copy
        return copy_interface

    def __eq__(self, other) -> bool:
        """Compare audio interfaces by configuration"""
        if not isinstance(other, AudioInterface):
            return False

        return (
            self.input_device_name == other.input_device_name and
            self.output_device_name == other.output_device_name and
            self.sample_rate == other.sample_rate and
            self.buffer_size == other.buffer_size and
            self.input_channels == other.input_channels and
            self.output_channels == other.output_channels
        )

    def __repr__(self) -> str:
        return (
            f"AudioInterface("
            f"input='{self.input_device_name}', "
            f"output='{self.output_device_name}', "
            f"sr={self.sample_rate}, "
            f"buffer={self.buffer_size})"
        )