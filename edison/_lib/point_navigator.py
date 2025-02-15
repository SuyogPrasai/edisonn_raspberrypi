import time
import threading
from typing import Tuple, List, Dict, Any

from edison.components.control.Control import EdisonCar
from edison._lib.path_generator import get_route


class PointNavigator:
    def __init__(self, car: EdisonCar):
        """
        Initialize the PointNavigator with a car instance.

        Args:
            car (EdisonCar): An instance of the EdisonCar class for location and control.
        """
        self.car = car
        # self.routes = self.get_route_coordinates()
        # self.next_point = self.routes[0]

    def current_location(self) -> Tuple[Tuple[float, float], float, str]:
        """
        Returns the current coordinates (latitude, longitude), direction angle, and general direction.

        Returns:
            Tuple[Tuple[float, float], float, str]: ((latitude, longitude), direction angle, general direction)
        """
        return self.car._get_location()

    def prompt_final_destination(self) -> Tuple[float, float]:
        """
        Prompts the user for the final destination coordinates in the format "latitude, longitude".

        Returns:
            Tuple[float, float]: (latitude, longitude) of the destination.
        """
        while True:
            try:
                user_input = input("Enter the latitude and longitude of the final destination (format: latitude, longitude): ")
                latitude, longitude = map(float, user_input.split(','))
                return (latitude, longitude)
            except ValueError:
                print("Invalid input. Please enter numeric values in the format 'latitude, longitude'.")

    def generate_route_data(self) -> Dict[str, Any]:
        """
        Generates routing data between the current location and the destination.

        Returns:
            Dict[str, Any]: Route data from OSRM.
        """
        # Wait for valid GPS coordinates
        while True:
            coordinates, _, _ = self.current_location()
            if coordinates and coordinates[0] is not None and coordinates[1] is not None:
                break
            print("No gps signal, waiting for GPS signal...")
            time.sleep(1)

        src_lat, src_lon = coordinates
        
        dest_lat, dest_lon = self.prompt_final_destination()

        try:
            return get_route(src_lon, src_lat, dest_lon, dest_lat)
        except Exception as e:
            raise RuntimeError(f"Failed to generate route: {str(e)}")

    def get_route_coordinates(self) -> List[Tuple[float, float]]:
        """
        Extracts coordinate points from the generated route.

        Returns:
            List[Tuple[float, float]]: List of (longitude, latitude) coordinates along the route.
        """
        try:
            route_data = self.generate_route_data()
            return route_data["routes"][0]["geometry"]["coordinates"]
        except KeyError:
            raise ValueError("Invalid route data format from OSRM")
        except IndexError:
            raise ValueError("No route features found in response")