import os
import time
import threading

from typing import Dict, Any, Tuple
from dotenv import load_dotenv

from edison.models.Car import Car
from edison.helpers.data_communication import DataPacketBuilder
from edison.helpers.packet_communication import PacketCommuncation
from edison._lib.device_location import DeviceLocationReader
from edison._lib.get_video import GetWebcam

load_dotenv()  # Load environment variables from .env file

class CarController:
    """Base controller class for managing car state and communication."""
    
    def __init__(self):
        load_dotenv()
        self.car = self._initialize_car()
        self.builder = DataPacketBuilder()
        self.sender = self._initialize_serial_communicatior()
    
        self._lock = threading.Lock()
        self.device_location = DeviceLocationReader()

        self.web_cam = GetWebcam()
        self.web_cam.get_webcam()
        
        # Start the logcat reader in a separate thread
        self.location_thread = threading.Thread(target=self.device_location.read_logcat, daemon=True)
        self.location_thread.start()  # Run in the background
        
        while True:
            if self.device_location.location != (None, None): 
                break
            print("Make sure to connect usb, Waiting for the signal..")
            time.sleep(1)

        self.arduino_code_reader = threading.Thread(target=self.sender.init_recieving_packet_process, daemon=True)
        self.arduino_code_reader.start()

    def _initialize_car(self) -> Car:
        """Initialize and return a Car instance with configuration from environment variables."""
        car_states = {
            "current_speed": 0,
            "current_direction": int(os.getenv("FRONT_ANGLE", 90))
        }

        return Car(
            car_states=car_states,
            MIN_SPEED=int(os.getenv("CAR_MIN_SPEED", 100)),
            MAX_SPEED=int(os.getenv("CAR_MAX_SPEED", 200)),
            ACCELERATION_DELAY=float(os.getenv("ACCELERATION_DELAY", 0.1)),
            DECELERATION_DELAY=float(os.getenv("DECELERATION_DELAY", 0.1)),
            ACCELERATION_INCREMENT=int(os.getenv("ACCELERATION_INCREMENT", 5)),
            DECELERATION_INCREMENT=int(os.getenv("DECELERATION_INCREMENT", 5)),
            LEFT_ANGLE=int(os.getenv("LEFT_ANGLE", 120)),
            RIGHT_ANGLE=int(os.getenv("RIGHT_ANGLE", 60)),
            FRONT_ANGLE=int(os.getenv("FRONT_ANGLE", 90))
        )

    def _initialize_serial_communicatior(self) -> PacketCommuncation :
        """Initialize and return a SerialPacketSender instance with configuration from environment variables."""
        print(os.getenv("SERIAL_PORT", "COM12"))
        return PacketCommuncation(
            port=os.getenv("SERIAL_PORT", "COM12"),
            baud_rate=int(os.getenv("BAUD_RATE", 9600))
        )
    
    def update_car_state(self) -> None:
        """Update the car's state and send the corresponding data packet."""
        with self._lock:
            current_state = self.car.car_states.copy()

        try:
            packet = self.builder.construct_data_packet(
                direction=current_state['current_direction'],
                speed=current_state['current_speed']
            )
            print(packet)
            print(f"Constructed packet: {packet.hex(':')}")
            self._send_packet(packet)

        except (EnvironmentError, ValueError) as e:
            print(f"Packet construction failed: {e}")

    def _send_packet(self, packet: bytes) -> None:
        """Send the constructed packet using the serial sender."""
        try:
            self.sender.send_packet(packet)
        except Exception as e:
            print(f"Error sending the packet: {e}")

    def _reset_states(self) -> None:
        """Reset all control states to default values."""
        with self._lock:
            self.car.car_states['current_speed'] = 0
            self.car.car_states['current_direction'] = self.car.FRONT_ANGLE

    def _get_location(self) -> Tuple[Any, Any, Any]:
        """Get the current location, direction, and general direction of the car."""
        with self._lock:
            return (self.device_location.location, self.device_location.direction, self.device_location.general_direction)

    def get_current_state(self) -> Dict[str, Any]:
        """Get the current state of the car."""
        with self._lock:
            return self.car.car_states.copy()

    def is_moving(self) -> bool:
        """Check if the car is currently moving."""
        with self._lock:
            return self.car.car_states['current_speed'] > 0

class EdisonCar(CarController):
    """Enhanced car controller with movement and speed management capabilities."""
    
    def __init__(self):
        super().__init__()
        self.accelerating = False
        self.decelerating = False

    def turn_left(self) -> None:
        """Turn the car to the maximum left direction."""
        self.set_direction(self.car.LEFT_ANGLE)

    def turn_right(self) -> None:
        """Turn the car to the maximum right direction."""
        self.set_direction(self.car.RIGHT_ANGLE)

    def turn_front(self) -> None:
        """Reset steering to the front-facing direction."""
        self.set_direction(self.car.FRONT_ANGLE)

    def set_direction(self, angle: int) -> None:
        """
        Set the car's steering direction to a specific angle.
        
        Args:
            angle: The desired steering angle (clamped between RIGHT_ANGLE and LEFT_ANGLE)
        """
        clamped_angle = max(self.car.RIGHT_ANGLE, min(angle, self.car.LEFT_ANGLE))
        with self._lock:
            self.car.car_states['current_direction'] = clamped_angle
        self.update_car_state()

    def accelerate(self) -> None:
        """Increase speed by the configured acceleration increment."""
        with self._lock:
            current_speed = self.car.car_states['current_speed']
            
            if current_speed == 0:
                new_speed = self.car.MIN_SPEED
            else:
                new_speed = current_speed + self.car.ACCELERATION_INCREMENT
            
            new_speed = min(new_speed, self.car.MAX_SPEED)
            self.car.car_states['current_speed'] = new_speed
        
        self.update_car_state()

    def decelerate(self) -> None:
        """Decrease speed by the configured deceleration increment."""
        with self._lock:
            current_speed = self.car.car_states['current_speed']
            
            if current_speed == 0:
                return
            
            new_speed = current_speed - self.car.DECELERATION_INCREMENT
            if new_speed < self.car.MIN_SPEED:
                new_speed = 0
            
            self.car.car_states['current_speed'] = new_speed
        
        self.update_car_state()

    def set_speed(self, speed: int) -> None:
        """
        Set the car to a specific speed.
        
        Args:
            speed: Desired speed (0 for stop, clamped between MIN_SPEED and MAX_SPEED when moving)
        """
        if speed < 0:
            new_speed = 0
        elif speed == 0:
            new_speed = 0
        else:
            new_speed = max(self.car.MIN_SPEED, min(speed, self.car.MAX_SPEED))
        
        with self._lock:
            self.car.car_states['current_speed'] = new_speed
        self.update_car_state()

    def stop(self) -> None:
        """Immediately stop the car."""
        self.set_speed(0)

    def start_gradual_acceleration(self) -> None:
        """Start continuous acceleration until MAX_SPEED is reached."""
        if not self.accelerating:
            self.accelerating = True
            threading.Thread(target=self._acceleration_loop, daemon=True).start()

    def stop_gradual_acceleration(self) -> None:
        """Stop continuous acceleration."""
        self.accelerating = False

    def start_gradual_deceleration(self) -> None:
        """Start continuous deceleration until stopped."""
        if not self.decelerating:
            self.decelerating = True
            threading.Thread(target=self._deceleration_loop, daemon=True).start()

    def stop_gradual_deceleration(self) -> None:
        """Stop continuous deceleration."""
        self.decelerating = False

    def _acceleration_loop(self) -> None:
        """Continuous acceleration loop with delay."""
        self.stop_gradual_deceleration()
        while self.accelerating:
            with self._lock:
                current_speed = self.car.car_states['current_speed']
                if current_speed >= self.car.MAX_SPEED:
                    self.accelerating = False
                    break
            self.accelerate()
            time.sleep(self.car.ACCELERATION_DELAY)

    def _deceleration_loop(self) -> None:
        """Continuous deceleration loop with delay."""
        self.stop_gradual_acceleration()
        while self.decelerating:
            with self._lock:
                current_speed = self.car.car_states['current_speed']
                if current_speed == 0:
                    self.decelerating = False
                    break
            self.decelerate()
            time.sleep(self.car.DECELERATION_DELAY)