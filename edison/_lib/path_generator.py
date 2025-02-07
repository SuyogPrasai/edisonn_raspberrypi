import requests
import json

def get_route(start_lat, start_lon, end_lat, end_lon, server_url="http://router.project-osrm.org"):
    """
    Queries OSRM for a route between the start and end coordinates.
    
    Parameters:
        start_lat (float): Latitude of the start point.
        start_lon (float): Longitude of the start point.
        end_lat (float): Latitude of the end point.
        end_lon (float): Longitude of the end point.
        server_url (str): Base URL of the OSRM server.
    
    Returns:
        dict: JSON response from OSRM containing the route information.
    """
    coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = f"{server_url}/route/v1/driving/{coordinates}"
    
    params = {
        "overview": "full",     # "full" returns the full geometry
        "geometries": "geojson",  # Return GeoJSON format
        "steps": "true"         # Include step-by-step instructions
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"OSRM request failed with status code {response.status_code}: {response.text}")

def save_route_as_geojson(route_data, filename="data/route.geojson"):
    """
    Saves OSRM route data as a GeoJSON file.
    
    Parameters:
        route_data (dict): JSON response from OSRM.
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
                        "name": "Route 1"
                    }
                }
            ]
        }
        with open(filename, "w") as f:
            json.dump(geojson_data, f, indent=4)
        print(f"Route saved as {filename}")
    else:
        print("No route found in the response.")

if __name__ == "__main__":
    start_lat, start_lon = 27.70333, 85.31239
    end_lat, end_lon = 27.78209, 85.35950
    
    try:
        route_data = get_route(start_lat, start_lon, end_lat, end_lon)
        save_route_as_geojson(route_data)
    except Exception as e:
        print("An error occurred:", e)