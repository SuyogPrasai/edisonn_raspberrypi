from serial import Serial
from typing import ByteString, Optional
from edison.helpers.data_communication import DataPacketBuilder

class PacketCommuncation:
    def __init__(self, port: str, baud_rate: int = 9600, timeout: Optional[float] = 1.0):
        """
        Initializes the SerialPacketSender with a serial port and baud rate.
        
        :param port: Serial port to use (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux).
        :param baud_rate: Baud rate for the serial communication.
        :param timeout: Timeout for serial communication in seconds.
        """
        self.serial_port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.ser: Serial = None

        try: 
            self.open_connection()
        except Exception as e:
            print(f"Failed communicating with the arduino, Exitting..., {e}")
            exit(1)
        
    def open_connection(self):
        """Opens the serial connection."""
        if self.ser is None or not self.ser.is_open:
            self.ser = Serial(self.serial_port, self.baud_rate, timeout=self.timeout)
        
    def close_connection(self):
        """Closes the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_packet(self, data_packet: ByteString):
        """Sends a data packet over the serial connection."""
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial connection is not open. Call open_connection() first.")
        
        self.ser.write(data_packet)

    def recieve_packet(self) -> str:
        # must initialize as a separate process to completely for it to work maybe run it in a different thread
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("Serial port is not established, Error recieving the packegt")   

        try:
            data = self.ser.readline()
            return data if data else None
        except Exception as e:
            print(f"Error recieving the packet")


    def init_recieving_packet_process(self):
        while True:
            try:
                data = self.recieve_packet()
                if data is not None:
                    print(f"[+] Arduino: {data}")
            except Exception as e:
                raise RuntimeError(f"Error initializing the packet recieving process: {e}")
                break

    def __enter__(self):
        """Allows usage of the class in a context manager."""
        self.open_connection()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Ensures the connection is closed when exiting the context."""
        self.close_connection()

# Example usage:
# with SerialPacketSender('/dev/ttyUSB0', 115200) as sender:
#     packet = DataPacketBuilder().build()
#     sender.send_packet(packet)
