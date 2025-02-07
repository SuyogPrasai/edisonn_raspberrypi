from edison.models.Car import Car
from edison.helpers.DataPacket import DataPacketBuilder
from edison.helpers.SendPacket import SerialPacketSender
from edison.components.arduino_control.Control import EdisonCar  # Replace 'your_module' with the actual module name


gadi = EdisonCar()
print(gadi.get_current_state())
print(gadi._get_location())
print(gadi.is_moving())
gadi.turn_left()
print(gadi.get_current_state())
gadi.set_direction(-122)
gadi.set_speed(2)
print(gadi.get_current_state())
while True:
    try:
        gadi.start_gradual_acceleration()
        print(gadi.get_current_state())
    except KeyboardInterrupt:
        break