import unittest
import time
from unittest.mock import patch, MagicMock
from edison.models.Car import Car
from edison.helpers.DataPacket import DataPacketBuilder
from edison.helpers.SendPacket import SerialPacketSender
from edison.components.arduino_control.Control import EdisonCar  # Replace 'your_module' with the actual module name

class TestEdisonCar(unittest.TestCase):
    """Test suite for the EdisonCar class."""

    def setUp(self):
        """Set up the test environment."""
        # Mock environment variables
        self.env_vars = {
            "FRONT_ANGLE": "90",
            "MIN_SPEED": "100",
            "MAX_SPEED": "255",
            "ACCELERATION_DELAY": "0.1",
            "DECELERATION_DELAY": "0.1",
            "ACCELERATION_INCREMENT": "5",
            "DECELERATION_INCREMENT": "5",
            "LEFT_ANGLE": "120",
            "RIGHT_ANGLE": "60",
            "SERIAL_PORT": "COM11",
            "BAUD_RATE": "9600",
        }
        self.patcher = patch.dict("os.environ", self.env_vars)
        self.patcher.start()

        # Mock the SerialPacketSender to avoid actual serial communication
        self.mock_sender = MagicMock(spec=SerialPacketSender)
        self.mock_sender.send_packet.return_value = None

        # Patch the SerialPacketSender in the EdisonCar class
        self.sender_patcher = patch("edison.helpers.SendPacket.SerialPacketSender", return_value=self.mock_sender)
        self.sender_patcher.start()

        # Initialize the EdisonCar instance
        self.car = EdisonCar()

    def tearDown(self):
        """Clean up after each test."""
        self.patcher.stop()
        self.sender_patcher.stop()

    def test_initial_state(self):
        """Test if the car initializes with the correct default state."""
        self.assertEqual(self.car.car.car_states["current_speed"], 0)
        self.assertEqual(self.car.car.car_states["current_direction"], 90)

    def test_turn_left(self):
        """Test turning the car to the left."""
        self.car.turn_left()
        self.assertEqual(self.car.car.car_states["current_direction"], 120)
        self.mock_sender.send_packet.assert_called_once()

    def test_turn_right(self):
        """Test turning the car to the right."""
        self.car.turn_right()
        self.assertEqual(self.car.car.car_states["current_direction"], 60)
        self.mock_sender.send_packet.assert_called_once()

    def test_turn_front(self):
        """Test resetting the car's direction to front."""
        self.car.turn_left()  # Turn left first
        self.car.turn_front()  # Reset to front
        self.assertEqual(self.car.car.car_states["current_direction"], 90)
        self.assertEqual(self.mock_sender.send_packet.call_count, 2)

    def test_set_direction(self):
        """Test setting the car's direction to a specific angle."""
        self.car.set_direction(100)
        self.assertEqual(self.car.car.car_states["current_direction"], 100)
        self.mock_sender.send_packet.assert_called_once()

    def test_set_direction_clamping(self):
        """Test that setting an invalid direction clamps to the nearest valid angle."""
        self.car.set_direction(200)  # Above LEFT_ANGLE
        self.assertEqual(self.car.car.car_states["current_direction"], 120)

        self.car.set_direction(50)  # Below RIGHT_ANGLE
        self.assertEqual(self.car.car.car_states["current_direction"], 60)

    def test_accelerate(self):
        """Test accelerating the car."""
        self.car.accelerate()
        self.assertEqual(self.car.car.car_states["current_speed"], 100)  # MIN_SPEED
        self.mock_sender.send_packet.assert_called_once()

        # Accelerate again
        self.car.accelerate()
        self.assertEqual(self.car.car.car_states["current_speed"], 105)  # MIN_SPEED + ACCELERATION_INCREMENT

    def test_decelerate(self):
        """Test decelerating the car."""
        self.car.set_speed(200)  # Set initial speed
        self.car.decelerate()
        self.assertEqual(self.car.car.car_states["current_speed"], 195)  # 200 - DECELERATION_INCREMENT

    def test_decelerate_below_min_speed(self):
        """Test decelerating below MIN_SPEED stops the car."""
        self.car.set_speed(102)  # Set speed just above MIN_SPEED
        self.car.decelerate()
        self.assertEqual(self.car.car.car_states["current_speed"], 0)  # Should stop

    def test_set_speed(self):
        """Test setting the car's speed directly."""
        self.car.set_speed(150)
        self.assertEqual(self.car.car.car_states["current_speed"], 150)
        self.mock_sender.send_packet.assert_called_once()

    def test_set_speed_clamping(self):
        """Test that setting an invalid speed clamps to the nearest valid value."""
        self.car.set_speed(300)  # Above MAX_SPEED
        self.assertEqual(self.car.car.car_states["current_speed"], 255)

        self.car.set_speed(50)  # Below MIN_SPEED but above 0
        self.assertEqual(self.car.car.car_states["current_speed"], 100)  # MIN_SPEED

        self.car.set_speed(-10)  # Below 0
        self.assertEqual(self.car.car.car_states["current_speed"], 0)

    def test_stop(self):
        """Test stopping the car."""
        self.car.set_speed(200)
        self.car.stop()
        self.assertEqual(self.car.car.car_states["current_speed"], 0)
        self.mock_sender.send_packet.assert_called()

    def test_gradual_acceleration(self):
        """Test gradual acceleration."""
        self.car.start_gradual_acceleration()
        time.sleep(0.5)  # Allow time for acceleration
        self.car.stop_gradual_acceleration()
        self.assertGreater(self.car.car.car_states["current_speed"], 100)  # Should have accelerated
        self.mock_sender.send_packet.assert_called()

    def test_gradual_deceleration(self):
        """Test gradual deceleration."""
        self.car.set_speed(200)  # Set initial speed
        self.car.start_gradual_deceleration()
        time.sleep(0.5)  # Allow time for deceleration
        self.car.stop_gradual_deceleration()
        self.assertLess(self.car.car.car_states["current_speed"], 200)  # Should have decelerated
        self.mock_sender.send_packet.assert_called()

    def test_reset_states(self):
        """Test resetting the car's states."""
        self.car.set_speed(200)
        self.car.turn_left()
        self.car._reset_states()
        self.assertEqual(self.car.car.car_states["current_speed"], 0)
        self.assertEqual(self.car.car.car_states["current_direction"], 90)

if __name__ == "__main__":
    unittest.main()