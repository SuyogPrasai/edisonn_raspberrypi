import math

from edison.helpers.Vector2D import Vector2D
from edison.components.arduino_control.Control import EdisonCar
from edison.components.point_navigation.PointNavigator import PointNavigator

class Traverser:
    def __init__(self, car: EdisonCar, point_navigator: PointNavigator):
        self.car = car
        self.point_navigator = point_navigator
        self.counter = 0
        self.next_point = self.point_navigator.routes[self.counter]

    def get_coordinates(self):
        coordinates, _, _ = self.car._get_location()
        return coordinates

    def get_direction(self):
        _, direction, _ = self.car._get_location()
        return direction

    def get_general_direction(self):
        _, _, direction = self.car._get_location()
        return direction
    
    def get_magnitude(self):
        """
        Calculate the distance in meters between the current position
        and the next point using the Haversine formula.
        """
        # Unpack coordinates
        dest_lon, dest_lat = self.next_point
        start_lat, start_lon = self.get_coordinates()

        # Convert latitude and longitude from degrees to radians
        start_lat_rad = math.radians(start_lat)
        start_lon_rad = math.radians(start_lon)
        dest_lat_rad = math.radians(dest_lat)
        dest_lon_rad = math.radians(dest_lon)

        # Compute differences in coordinates
        dlat = dest_lat_rad - start_lat_rad
        dlon = dest_lon_rad - start_lon_rad

        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 +
            math.cos(start_lat_rad) * math.cos(dest_lat_rad) *
            math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Earth's radius in meters (mean radius)
        R = 6371000
        distance = R * c
        return distance

    def get_angle(self):
        """
        Calculate the angle (in degrees) from the current position to the next point,
        with north defined as 0° and angles increasing clockwise.
        """
        # Unpack coordinates
        dest_lon, dest_lat = self.next_point
        start_lat, start_lon = self.get_coordinates()
        
        # Calculate differences:
        # dx corresponds to the change in longitude,
        # dy corresponds to the change in latitude.
        dx = dest_lon - start_lon
        dy = dest_lat - start_lat

        # Compute the angle using atan2.
        # Normally, atan2(dy, dx) gives the angle relative to the positive x-axis.
        # By swapping the arguments (atan2(dx, dy)), we obtain an angle measured from north.
        angle = math.degrees(math.atan2(dx, dy))
        
        # Normalize the angle to be in the range [0, 360)
        angle = (angle + 360) % 360

        return angle
    
    def turn_angle(self):
        f_angle = self.get_angle()
        c_angle = self.get_direction()

        return ( f_angle - c_angle )

    def set_direction_next_point(self):
        angle = self.turn_angle()
        while True:
            if self.get_direction() == self.get_angle():
                break
            if angle < 0:
                self.car.turn_left()
                self.car.set_speed(20)
            elif angle > 0:
                self.car.turn_right()
                self.car.set_speed(20)
            else: 
                break

    def move_to_point(self):
        self.car.set_speed(40)
        while True:
            if self.get_magnitude < 5:
                self.counter += 1
                self.next_point = self.point_navigator.routes[self.counter]
                break