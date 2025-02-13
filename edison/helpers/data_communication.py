from typing import List, ByteString
import os
from dotenv import load_dotenv

load_dotenv()

class DataPacketBuilder:
    """Constructs binary data packets with sequence tracking and checksum validation."""
    
    _MAX_SEQUENCE_NUMBER: int = 256 
    _BYTE_MASK: int = 0xFF           # Mask for 8-bit values
    
    def __init__(self) -> None:
        """
        Initialize the DataPacketBuilder with configuration from environment variables.
        
        Raises:
            EnvironmentError: If required environment variables are missing or invalid
        """
        self._sequence_number: int = 0
        self._packet_start_byte = self._validate_start_byte()
        
    def _validate_start_byte(self) -> int:
        """Validate and convert PACKET_START_BYTE environment variable to integer."""
        start_byte = os.getenv("PACKET_START_BYTE")
        if not start_byte:
            raise EnvironmentError("PACKET_START_BYTE environment variable not set")
        
        try:
            # Handle hex format (0xXX) or decimal format
            return int(start_byte, 0) & self._BYTE_MASK
        except ValueError:
            raise ValueError(
                f"Invalid PACKET_START_BYTE format: {start_byte}. "
                "Use decimal (255) or hex (0xff) format."
            ) from None

    def calculate_checksum(self, data: List[int]) -> int:
        """
        Calculate 8-bit checksum for the given data bytes.
        
        Args:
            data: List of integer values (0-255) to calculate checksum for
            
        Returns:
            8-bit checksum as integer
            
        Raises:
            ValueError: If any value is out of 0-255 range
        """
        if any(not (0 <= byte <= self._BYTE_MASK) for byte in data):
            raise ValueError("All data bytes must be in 0-255 range")
            
        return sum(data) & self._BYTE_MASK

    def construct_data_packet(
        self, 
        direction: int, 
        speed: int
    ) -> ByteString:
        """
        Construct a complete data packet with header, payload, and checksum.
        
        Packet Structure:
        [Start Byte][Direction][Speed][Sequence Number][Checksum]
        
        Args:
            direction: Movement direction (0-255)
            speed: Movement speed (0-255)
            
        Returns:
            Bytes object containing the complete packet
            
        Raises:
            ValueError: If direction or speed are out of 0-255 range
        """
        self._validate_byte_range(direction, "Direction")
        self._validate_byte_range(speed, "Speed")
        
        self._sequence_number = (self._sequence_number + 1) % self._MAX_SEQUENCE_NUMBER
        payload = [
            self._packet_start_byte,
            direction,
            speed,
            self._sequence_number
        ]
        
        checksum = self.calculate_checksum(payload)
        packet_bytes = bytes(payload + [checksum])
        
        return packet_bytes

    def _validate_byte_range(self, value: int, field_name: str) -> None:
        """Validate that a value is within 0-255 range."""
        if not (0 <= value <= self._BYTE_MASK):
            raise ValueError(
                f"{field_name} must be between 0-255. Got: {value}"
            )

if __name__ == "__main__":
    try:
        builder = DataPacketBuilder()
        packet = builder.construct_data_packet(
            direction=0x10,
            speed=0x20
        )
        print(f"Constructed packet: {packet.hex(':')}")
    except (EnvironmentError, ValueError) as e:
        print(f"Packet construction failed: {e}")