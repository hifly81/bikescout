import math
import os
import polyline
from urllib.parse import urlencode, quote
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration: Get your key from stadiamaps.com
STADIA_API_KEY = os.getenv("STADIA_API_KEY", "")

def get_static_map_url(geojson_data: dict) -> str:
    """
    Generates a professional static map URL using Stadia Maps.
    Uses Encoded Polylines and strict character formatting to ensure path visibility.
    """

    # 1. API Key Guard
    if not STADIA_API_KEY:
        return "Can't generate static map. Add Stadia API Key to the configuration"

    try:
        # 2. Data Validation
        if not geojson_data or 'features' not in geojson_data:
            return None

        # Extract [lon, lat] coordinates
        all_coords = geojson_data['features'][0]['geometry']['coordinates']
        if not all_coords:
            return None

        # 3. Dynamic Bounding Box & Center Calculation
        lons = [p[0] for p in all_coords]
        lats = [p[1] for p in all_coords]
        min_lon, max_lon = min(lons), max(lons)
        min_lat, max_lat = min(lats), max(lats)

        center_lon = (min_lon + max_lon) / 2
        center_lat = (min_lat + max_lat) / 2

        # 4. Dynamic Zoom Calculation
        delta = max(max_lon - min_lon, max_lat - min_lat)
        if delta > 0:
            # -1 padding ensures the route doesn't touch the image edges
            zoom = max(1, min(14, round(math.log2(360 / delta) - 1)))
        else:
            zoom = 14

        # 5. Path Compression using Polyline
        # Sampling points to keep the string short and clean
        step = max(1, len(all_coords) // 40)
        sampled_points = [(p[1], p[0]) for p in all_coords[::step]]

        # Ensure the path is closed/complete
        if sampled_points[-1] != (all_coords[-1][1], all_coords[-1][0]):
            sampled_points.append((all_coords[-1][1], all_coords[-1][0]))

        encoded_polyline = polyline.encode(sampled_points)

        # 6. Final URL Construction (Manual string building for the path)
        # We MUST keep | and : unencoded for the server to draw the line
        base_url = "https://tiles.stadiamaps.com/static/outdoors"

        # Standard parameters
        params = {
            "center": f"{center_lat},{center_lon}",
            "zoom": zoom,
            "size": "600x400@2x",
            "api_key": STADIA_API_KEY
        }

        query_string = urlencode(params)

        # We manually append the path.
        # The polyline string itself IS encoded, but the delimiters | and : ARE NOT.
        path_string = f"path=color:0xff0000ff|weight:4|enc:{encoded_polyline}"

        return f"{base_url}?{query_string}&{path_string}"

    except Exception as e:
        print(f"Stadia Generation Error: {e}")
        return f"Stadia Generation Error: {str(e)}"