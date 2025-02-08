# geoutils.py
import math

def haversine(lat1: float, lon1: float, lat2: float, lon2: float, radius: float = 6371.0) -> float:
    """
    Calculate the great-circle distance between two points on a sphere using the Haversine formula.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        radius: Earth radius in kilometers (default: 6371 km)
    
    Returns:
        Distance between points in kilometers (unless radius is changed)
    
    Example:
        >>> haversine(48.8566, 2.3522, 40.7128, -74.0060)  # Paris to NYC
        5836.48  # approximate
    """
    # Convert degrees to radians
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)

    # Haversine formula components
    a = (math.sin(Δφ/2)**2 
         + math.cos(φ1) * math.cos(φ2) 
         * math.sin(Δλ/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return radius * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the initial bearing (forward azimuth) between two geographic points.
    
    Args:
        lat1: Latitude of starting point in degrees
        lon1: Longitude of starting point in degrees
        lat2: Latitude of destination point in degrees
        lon2: Longitude of destination point in degrees
    
    Returns:
        Bearing angle in degrees from North (0-360)
    
    Example:
        >>> calculate_bearing(51.5074, 0.1278, 40.7128, -74.0060)  # London to NYC
        288.31  # approximate
    """
    if (lat1 == lat2) and (lon1 == lon2):
        return 0.0  # Same point
    
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    λ1 = math.radians(lon1)
    λ2 = math.radians(lon2)
    
    y = math.sin(λ2 - λ1) * math.cos(φ2)
    x = (math.cos(φ1) * math.sin(φ2) 
         - math.sin(φ1) * math.cos(φ2) * math.cos(λ2 - λ1))
    
    θ = math.atan2(y, x)
    bearing = math.degrees(θ)
    
    # Normalize to 0-360 compass bearing
    return (bearing + 360) % 360

# Optional test cases
if __name__ == "__main__":
    # Test Haversine (Paris to NYC)
    dist = haversine(48.8566, 2.3522, 40.7128, -74.0060)
    print(f"Distance: {dist:.2f} km")  # Should be ~5836 km
    
    # Test Bearing (London to NYC)
    bearing = calculate_bearing(51.5074, 0.1278, 40.7128, -74.0060)
    print(f"Initial bearing: {bearing:.2f}°")  # Should be ~288°