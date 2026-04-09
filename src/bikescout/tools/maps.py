import json

FLY_DEV_URL="https://static-maps.fly.dev/staticmap"

def get_static_map_url(geojson_data: dict) -> str:
    """
    Generates a static map image URL using OpenStreetMap data.
    It samples the route coordinates to stay within URL length limits.

    Args:
        geojson_data (dict): The GeoJSON response from OpenRouteService containing the route.

    Returns:
        str: A URL pointing to a static PNG image of the route.
    """
    try:
        # Check if features exist in the provided GeoJSON
        if not geojson_data or 'features' not in geojson_data:
            return None

        # Extract coordinates from the GeoJSON feature
        # ORS format for coordinates is [longitude, latitude, (optional) elevation]
        all_coords = geojson_data['features'][0]['geometry']['coordinates']

        # URL length management: limit path to ~45 points to avoid '414 Request-URI Too Large'
        # We calculate the sampling step to evenly distribute points along the route
        max_points = 45
        total_points = len(all_coords)

        if total_points == 0:
            return None

        step = max(1, total_points // max_points)
        sampled_coords = all_coords[::step]

        # Ensure the last coordinate is always included for a complete path
        if sampled_coords[-1] != all_coords[-1]:
            sampled_coords.append(all_coords[-1])

        # Format coordinates for the static map provider (Format: latitude,longitude)
        path_segments = [f"{p[1]},{p[0]}" for p in sampled_coords]
        path_str = "|".join(path_segments)

        # Construct the URL using a public OpenStreetMap static map service (fly.dev instance)
        # Parameters:
        # - size: dimensions of the image
        # - path: weight, color, and coordinates of the polyline
        # - maptype: mapnik (standard OSM style)
        base_url = FLY_DEV_URL
        map_url = (
            f"{base_url}?size=600x400&path=weight:3|color:red|{path_str}"
            f"&maptype=mapnik"
        )

        return map_url

    except Exception as e:
        # Log the error for debugging (stdout will be visible in MCP logs)
        print(f"Error generating static map: {e}")
        return None