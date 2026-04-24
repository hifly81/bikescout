import math
from geopy.distance import geodesic

def calculate_geodetic_segment(lat1: float, lon1: float, lat2: float, lon2: float, wind_direction: float = None):
    """
    Orchestrates the calculation of geodetic data for a single track segment.

    This method replaces the legacy 'haversine' approach. It calculates the
    precise distance (WGS-84) and the forward bearing. If a wind direction
    is provided, it also calculates the wind alignment score.

    Args:
        lat1, lon1: Starting point coordinates (Decimal Degrees).
        lat2, lon2: Destination point coordinates (Decimal Degrees).
        wind_direction: The direction the wind is coming FROM (0-359°). Optional.

    Returns:
        dict: A tactical packet containing:
            - 'distance': meters (float)
            - 'bearing': degrees (float)
            - 'wind_alignment': score between -1.0 and 1.0 (float or None)
    """

    # 1. Calculate High-Precision Distance (WGS-84 Ellipsoid)
    try:
        distance = geodesic((lat1, lon1), (lat2, lon2)).meters
    except Exception:
        # Fallback to Spherical Earth model
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        distance = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 2. Calculate Forward Bearing
    # This is called internally to establish the direction of travel
    bearing = calculate_bearing(lat1, lon1, lat2, lon2)

    # 3. Calculate Wind Alignment Score
    # Only triggered if wind_direction telemetry is provided
    alignment = None
    if wind_direction is not None:
        alignment = get_wind_alignment_score(bearing, wind_direction)

    return {
        "distance": distance,
        "bearing": bearing,
        "wind_alignment": alignment
    }

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the Forward Bearing (heading) between two GPS points.
    Essential for Crosswind Analysis and Aero Drag Modeling.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - \
        math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    initial_bearing = math.degrees(math.atan2(y, x))
    return (initial_bearing + 360) % 360

def get_wind_alignment_score(segment_bearing: float, wind_direction: float) -> float:
    """
    Calculates the vector alignment between travel direction and wind direction.
    +1.0 = Tailwind | 0.0 = Crosswind | -1.0 = Headwind
    """
    # Wind direction is where it comes FROM, so we shift by 180 to get where it's GOING
    angle_diff = math.radians(segment_bearing - (wind_direction - 180))
    return math.cos(angle_diff)