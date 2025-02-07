import os
import time
from typing import Dict, Any

from dotenv import load_dotenv

from edison.models.Car import Car
from edison.helpers.DataPacket import DataPacketBuilder
from edison.helpers.SendPacket import SerialPacketSender

class CarController:

    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

        self.car = self._initialize_car()
        self.builder = DataPacketBuilder()
        self.sender = self._initialize_serial_sender()

    def _initialize_car(self) -> Car:
        """Initialize and return a Car instance with configuration from environment variables."""
        car_states = {
            "current_speed": 0,
            "current_direction": int(os.getenv("FRONT_ANGLE", 90))
        }

        return Car(
            car_states=car_states,
            current_speed=0,
            current_direction=int(os.getenv("FRONT_ANGLE", 90)),
            MIN_SPEED=int(os.getenv("MIN_SPEED", 100)),
            MAX_SPEED=int(os.getenv("MAX_SPEED", 255)),
            ACCELERATION_DELAY=float(os.getenv("ACCELERATION_DELAY", 0.1)),
            DECELERATION_DELAY=float(os.getenv("DECELERATION_DELAY", 0.1)),
            ACCELERATION_INCREMENT=int(os.getenv("ACCELERATION_INCREMENT", 5)),
            DECELERATION_INCREMENT=int(os.getenv("DECELERATION_INCREMENT", 5)),
            LEFT_ANGLE=int(os.getenv("LEFT_ANGLE", 120)),
            RIGHT_ANGLE=int(os.getenv("RIGHT_ANGLE", 60)),
            FRONT_ANGLE=int(os.getenv("FRONT_ANGLE", 90))
        )

    def _initialize_serial_sender(self) -> SerialPacketSender:
        """Initialize and return a SerialPacketSender instance with configuration from environment variables."""
        return SerialPacketSender(
            port=os.getenv("SERIAL_PORT", "COM11"),
            baud_rate=int(os.getenv("BAUD_RATE", 9600))
        )

    def update_car_state(self) -> None:
        """Update the car's state and send the corresponding data packet."""
        current_state = self.car.control_state

        try:
            packet = self.builder.construct_data_packet(
                direction=current_state['current_direction'],
                speed=current_state['current_speed']
            )

            self._send_packet(packet)

        except (EnvironmentError, ValueError) as e:
            print(f"Packet construction failed: {e}")

    def _send_packet(self, packet: bytes) -> None:
        """Send the constructed packet using the serial sender."""
        try:
            self.sender.send_packet(packet)
        except Exception as e:
            print(f"Error sending the packet: {e}")