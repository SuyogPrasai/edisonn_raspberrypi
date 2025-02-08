import requests
import json
from typing import Dict, Any, Tuple

def validate_coordinate(coord: float, coord_type: str):
    """
    Validates latitude and longitude values.

    Args:
        coord (float): The coordinate value to validate.
        coord_type (str): Either "latitude" or "longitude".

    Raises:
        ValueError: If the coordinate is invalid.
    """
    if coord_type == "latitude" and not (-90 <= coord <= 90):
        raise ValueError(f"Invalid latitude: {coord}")
    if coord_type == "longitude" and not (-180 <= coord <= 180):
        raise ValueError(f"Invalid longitude: {coord}")


def get_route(
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
    server_url: str = "http://router.project-osrm.org",
) -> Dict[str, Any]:
    """
    Queries OSRM for a route between the start and end coordinates.

    Args:
        start_lon (float): Longitude of the start point.
        start_lat (float): Latitude of the start point.
        end_lon (float): Longitude of the end point.
        end_lat (float): Latitude of the end point.
        server_url (str): Base URL of the OSRM server.

    Returns:
        Dict[str, Any]: JSON response from OSRM containing the route information.

    Raises:
        Exception: If the OSRM request fails.
    """
    # Validate coordinates
    validate_coordinate(start_lat, "latitude")
    validate_coordinate(start_lon, "longitude")
    validate_coordinate(end_lat, "latitude")
    validate_coordinate(end_lon, "longitude")

    coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = f"{server_url}/route/v1/driving/{coordinates}"

    params = {
        "overview": "full",  # "full" returns the full geometry
        "geometries": "geojson",  # Return GeoJSON format
        "steps": "true",  # Include step-by-step instructions
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            save_route_as_geojson(response.json())
        except:
            raise Exception(f"Failed to save path data to file")
        return response.json()
    else:
        raise Exception(f"OSRM request failed with status code {response.status_code}: {response.text}")


def save_route_as_geojson(route_data: Dict[str, Any], filename: str = "data/route.geojson"):
    """
    Saves OSRM route data as a GeoJSON file.

    Args:
        route_data (Dict[str, Any]): JSON response from OSRM.
        filename (str): Output filename for the GeoJSON file.
    """
    if "routes" in route_data and len(route_data["routes"]) > 0:
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": route_data["routes"][0]["geometry"],
                    "properties": {
                        "name": "Route 1",
                    },
                }
            ],
        }
        with open(filename, "w") as f:
            json.dump(geojson_data, f, indent=4)
        print(f"Route saved as {filename}")
    else:
        print("No route found in the response.")