import requests
from bikescout.tools.maps import get_static_map_url
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.surface import get_surface_analyzer
from bikescout.tools.poi import get_poi_scout
from bikescout.tools.mud import get_mud_risk_analysis

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions"

def calculate_detailed_difficulty(dist_km: float, ascent_m: float) -> str:
    """
    Categorizes the route difficulty based on distance, ascent, and average gradient.
    """
    if dist_km == 0:
        return "Unknown"

    # Calculate average gradient
    # Formula: (ascent / (distance * 1000)) * 100
    avg_gradient = (ascent_m / (dist_km * 1000)) * 100

    # 1. EXPERT: High distance, high climbing, or very steep
    if dist_km > 50 or ascent_m > 1000 or avg_gradient > 7:
        return "🔴 Expert (Challenging distance or very steep climbs)"

    # 2. ADVANCED: Significant climbing or moderate distance
    if dist_km > 30 or ascent_m > 600 or avg_gradient > 4:
        return "🟠 Advanced (Requires good fitness and stamina)"

    # 3. MODERATE: Accessible but with some effort
    if dist_km > 15 or ascent_m > 300:
        return "🟡 Moderate (Accessible for regular cyclists)"

    # 4. BEGINNER: Short and flat
    return "🟢 Beginner (Short and relatively flat, ideal for everyone)"

def generate_tactical_gpx(geojson_data, amenities=[]):
    """
    Generates a GPX with embedded tactical waypoints for navigation units.
    Includes Summits, Steep Climbs (>10%), and Cycling Amenities.
    """
    feature = geojson_data['features'][0]
    coords = feature['geometry']['coordinates']  # [lon, lat, ele]

    gpx_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    gpx_xml += '<gpx version="1.1" creator="BikeScout" xmlns="http://www.topografix.com/GPX/1/1">\n'

    waypoints = ""

    # --- A. WAYPOINT: CYCLING AMENITIES (Water & Repair) ---
    for poi in amenities:
        name = poi.get('name', 'Cycling POI')
        # Accessing nested 'location' to prevent KeyError
        loc = poi.get('location', {})
        p_lat, p_lon = loc.get('lat'), loc.get('lon')

        if p_lat and p_lon:
            waypoints += f'  <wpt lat="{p_lat}" lon="{p_lon}">\n'
            waypoints += f'    <name>{name}</name>\n'
            waypoints += f'    <sym>Watering Hole</sym>\n'
            waypoints += f'  </wpt>\n'

    # --- B. WAYPOINT: SUMMIT ---
    if coords and len(coords[0]) > 2:
        peak = max(coords, key=lambda x: x[2])
        waypoints += f'  <wpt lat="{peak[1]}" lon="{peak[0]}">\n'
        waypoints += f'    <name>SUMMIT: {int(peak[2])}m</name>\n'
        waypoints += f'    <sym>Summit</sym>\n'
        waypoints += f'  </wpt>\n'

    # --- C. WAYPOINT: STEEP CLIMBS (>10%) ---
    # We iterate with a step to smooth elevation noise
    for i in range(5, len(coords) - 10, 10):
        p1, p2 = coords[i], coords[i+10]
        # Distance calculation (meters)
        d_lat = (p2[1] - p1[1]) * 111139
        d_lon = (p2[0] - p1[0]) * 111139 * 0.7
        dist = (d_lat**2 + d_lon**2)**0.5

        if dist > 60:
            grade = ((p2[2] - p1[2]) / dist) * 100
            if grade > 10:
                waypoints += f'  <wpt lat="{p1[1]}" lon="{p1[0]}">\n'
                waypoints += f'    <name>WALL: {int(grade)}%</name>\n'
                waypoints += f'    <sym>Danger Area</sym>\n'
                waypoints += f'  </wpt>\n'
                i += 30 # Avoid waypoint clutter on the same hill

    # --- D. TRACK ---
    track = '  <trk>\n    <name>BikeScout Tactical Route</name>\n    <trkseg>\n'
    for lon, lat, ele in coords:
        track += f'      <trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele></trkpt>\n'
    track += '    </trkseg>\n  </trk>\n'

    return gpx_xml + waypoints + track + '</gpx>'

def get_complete_trail_scout(api_key, lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    The Master Orchestrator: Finds a specific trail and enriches it with
    Surface Analysis, Weather, Cycling POIs, and Mud Risk.
    """
    # --- 1. CONFIGURATION & HEADERS ---
    headers = {
        'Accept': 'application/json, application/geo+json',
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }

    # Payload for the primary route discovery (Round Trip)
    routing_payload = {
        "coordinates": [[lon, lat]],
        "options": {"round_trip": {"length": radius_km * 1000, "seed": 42}},
        "elevation": "true",
        "extra_info": ["surface", "steepness"]
    }

    try:
        # --- 2. EXECUTE PRIMARY ROUTING ---
        # We fetch the actual geometry and basic metrics first
        endpoint = f"{ORS_BASE_URL}/{profile}/geojson"
        response = requests.post(endpoint, json=routing_payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        feature = data['features'][0]
        props = feature['properties']
        summary = props.get('summary', {})

        # Core metrics
        dist_km = round(summary.get('distance', 0) / 1000, 2)
        ascent_m = round(props.get('ascent', 0), 0)

        # Extract dominant surface ID directly from primary route for accurate Mud Analysis
        # This acts as a fallback if the specialized analyzer fails
        raw_surface_extras = props.get('extras', {}).get('surface', {}).get('summary', [])
        dominant_id = raw_surface_extras[0]['value'] if raw_surface_extras else 10 # Default to dirt
        dominant_surface_name = _map_surface_id(dominant_id)

        # --- 3. CALL: SURFACE ANALYZER (Advanced Setup Check) ---
        # Note: We pass points=3 (integer) instead of a list of coordinates.
        # This prevents the 'Parameter options has incorrect format' error in the ORS API.
        try:
            surface_report = get_surface_analyzer(
                api_key=api_key,
                lat=lat,
                lon=lon,
                radius_km=radius_km,
                profile=profile,
                bike_type="mountain" if "mountain" in profile else "gravel",
                tire_size_option="wide",
                points=3,                 # Integer representing the number of waypoints
                seed=42,
                surface_preference="neutral"
            )
        except Exception as e:
            surface_report = {"status": "Error", "message": f"Surface Analysis skipped: {str(e)}"}

        # --- 4. CALL: WEATHER FORECAST ---
        # Retrieves real-time conditions for the starting coordinates
        weather_report = get_weather_forecast(lat, lon)

        # --- 5. CALL: POI SCOUT (Logistics) ---
        # Finds water, repair stations, and shelters within 2km
        try:
            poi_res = get_poi_scout(api_key, lat, lon, radius_km=2.0)
            amenities = poi_res.get('amenities', []) if poi_res.get('status') == "Success" else []
        except:
            amenities = []

        # --- 6. CALL: MUD RISK ANALYSIS ---
        # Uses 72h rain history + the dominant surface found in Step 2
        mud_analysis = get_mud_risk_analysis(lat, lon, dominant_surface_name)

        # --- 7. FINAL CONSOLIDATED RESPONSE ---
        return {
            "status": "Success",
            "info": {
                "distance_km": dist_km,
                "ascent_m": ascent_m,
                "difficulty": calculate_detailed_difficulty(dist_km, ascent_m),
                "surface_analysis": surface_report
            },
            "conditions": {
                "weather": weather_report.get('next_4_hours', []) if isinstance(weather_report, dict) else [],
                "mud_risk": mud_analysis,
                "safety_advice": weather_report.get('safety_advice', "") if isinstance(weather_report, dict) else ""
            },
            "logistics": {
                "nearby_amenities": amenities[:5] # Return top 5 cycling POIs
            },
            "map_image_url": get_static_map_url(data), # Static preview map
            "gpx_content": generate_tactical_gpx(data, amenities)
        }

    except Exception as e:
        # Catch-all for routing failures or API timeouts
        return {"status": "Error", "message": f"Master Orchestrator failed: {str(e)}"}

def _map_surface_id(s_id):
    """Internal helper to convert ORS surface IDs to strings for Mud Analysis."""
    mapping = {1: "asphalt", 2: "unpaved", 5: "gravel", 10: "dirt", 11: "grass", 12: "compact"}
    return mapping.get(s_id, "dirt")