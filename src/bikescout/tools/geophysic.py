# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import math
from geopy.distance import geodesic
from typing import Dict, Any
from bikescout.tools.weather import get_weather_forecast

# Internal cache to avoid redundant API calls during route geometry analysis
_WEATHER_CACHE: Dict[str, Any] = {}

def calculate_geodetic_segment(lat1: float, lon1: float, lat2: float, lon2: float, wind_direction: float = None, wind_speed: float = 0.0):
    """
    Orchestrates the calculation of geodetic data for a single track segment.

    This method replaces the legacy 'haversine' approach. It calculates the
    precise distance (WGS-84) and the forward bearing. If a wind direction
    is provided, it also calculates the wind alignment score.
    If wind data is missing, it attempts to fetch it using local weather intelligence.

    Args:
        lat1, lon1: Starting point coordinates (Decimal Degrees).
        lat2, lon2: Destination point coordinates (Decimal Degrees).
        wind_direction: The direction the wind is coming FROM (0-359°). Optional.
        wind_speed: The speed of the wind. Optional

    Returns:
        dict: A tactical packet containing:
            - 'distance': meters (float)
            - 'bearing': degrees (float)
            - 'wind_alignment': score between -1.0 and 1.0 (float or None)
            - 'crosswind_component': lateral force in wind_speed units (float or None)
    """

    # 1. Weather Auto-Discovery (Lazy Loading)
    # If wind data isn't passed, we try to retrieve it from the weather module
    global _WEATHER_CACHE
    eff_wind_dir = wind_direction
    eff_wind_speed = wind_speed

    if eff_wind_dir is None:

        # Create a coarse cache key (approx 1km precision) to reuse weather data for nearby segments
        cache_key = f"{round(lat1, 2)}_{round(lon1, 2)}"

        if cache_key not in _WEATHER_CACHE:
            weather = get_weather_forecast(lat1, lon1)
            if weather.get("status") == "Success":
                ref = weather.get("reference_conditions", {})
                _WEATHER_CACHE[cache_key] = {
                    "dir": ref.get("wind_direction", 0),
                    "speed": ref.get("wind_speed", 0.0)
                }

        cached = _WEATHER_CACHE.get(cache_key, {"dir": 0, "speed": 0.0})
        eff_wind_dir = cached["dir"]
        eff_wind_speed = cached["speed"]

    # 2. Calculate High-Precision Distance (WGS-84 Ellipsoid)
    try:
        distance = geodesic((lat1, lon1), (lat2, lon2)).meters
    except Exception:
        # Fallback to Spherical Earth (Haversine)
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        distance = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    bearing = _calculate_bearing(lat1, lon1, lat2, lon2)

    # 3. Aero-Tactical Telemetry
    # Calculate alignment (+1 tail, -1 head)
    alignment = get_wind_alignment_score(bearing, eff_wind_dir)
    # Calculate lateral force (Crosswind component)
    crosswind = calculate_crosswind_component(bearing, eff_wind_dir, eff_wind_speed)

    return {
        "distance": round(distance, 2),
        "bearing": round(bearing, 1),
        "wind_alignment": round(alignment, 3),
        "crosswind_component": round(crosswind, 2),
        "telemetry_source": "cached_api" if wind_direction is None else "manual_input"
    }

def _calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the Forward Bearing (heading) between two points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - \
        math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    return (math.degrees(math.atan2(y, x)) + 360) % 360

def get_wind_alignment_score(segment_bearing: float, wind_direction: float) -> float:
    """
    Normalized alignment: +1.0 (Tailwind) to -1.0 (Headwind).
    Explicitly normalizes wind vector to 'Direction TO' for clarity.
    """
    # Normalize 'Wind From' to 'Wind To' (0-359 range)
    wind_to = (wind_direction + 180) % 360

    # Calculate the angular difference
    angle_diff = math.radians(segment_bearing - wind_to)
    return math.cos(angle_diff)

def calculate_crosswind_component(segment_bearing: float, wind_direction: float, wind_speed: float) -> float:
    """
    Calculates the effective lateral wind force (Crosswind).
    Result is in the same units as wind_speed (e.g., km/h).
    """
    # Angle between travel and wind origin
    angle_diff = math.radians(segment_bearing - wind_direction)

    # Crosswind uses Sin(theta). Absolute value because lateral force
    # affects stability regardless of left/right side.
    return abs(wind_speed * math.sin(angle_diff))

def clear_geodetic_cache():
    """Utility to clear weather cache between different route analyses."""
    global _WEATHER_CACHE
    _WEATHER_CACHE.clear()