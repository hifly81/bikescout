import requests
from bikescout.tools.maps import get_static_map_url

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

def generate_gpx(geojson_data):
    """Converts GeoJSON coordinates into a standard GPX XML string."""
    try:
        coords = geojson_data['features'][0]['geometry']['coordinates']
        gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
        gpx += '<gpx version="1.1" creator="BikeScout" xmlns="http://www.topografix.com/GPX/1/1">\n'
        gpx += '  <trk><name>BikeScout Route</name><trkseg>\n'
        for p in coords:
            ele = f"<ele>{p[2]}</ele>" if len(p) > 2 else ""
            gpx += f'    <trkpt lat="{p[1]}" lon="{p[0]}">{ele}</trkpt>\n'
        gpx += '  </trkseg></trk></gpx>'
        return gpx
    except:
        return "GPX conversion failed."

def get_complete_trail_scout(api_key, lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    Finds trails using OSM and ORS. Returns technical data, map link, and GPX content.
    """
    # 1. OSM NAMES (Overpass)
    trail_names = []
    try:
        query = f'[out:json];way["highway"~"path|track"]["name"](around:2000,{lat},{lon});out tags;'
        r_osm = requests.post(OVERPASS_URL, data={'data': query}, timeout=10)
        if r_osm.status_code == 200:
            trail_names = list(set([e['tags']['name'] for e in r_osm.json().get('elements', []) if 'name' in e['tags']]))
    except:
        pass

    # 2. ROUTING (OpenRouteService)
    headers = {
        'Accept': 'application/json, application/geo+json',
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }

    payload = {
        "coordinates": [[lon, lat]],
        "options": {
            "round_trip": {
                "length": radius_km * 1000,
                "seed": 42
            }
        },
        "elevation": "true",
        "instructions": "false",
        "units": "m"
    }

    try:
        endpoint = f"{ORS_BASE_URL}/{profile}/geojson"
        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)

        if response.status_code == 404:
            endpoint = f"{ORS_BASE_URL}/{profile}"
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)

        response.raise_for_status()
        data = response.json()

        if 'features' not in data:
            return {"status": "Error", "message": "No route features found."}

        props = data['features'][0]['properties']
        summary = props.get('summary', {})

        dist = round(summary.get('distance', 0) / 1000, 2)
        ascent = round(props.get('ascent', summary.get('ascent', 0)), 0)

        # Apply new difficulty logic
        difficulty_rating = calculate_detailed_difficulty(dist, ascent)

        # Get Static map
        static_map = get_static_map_url(data)

        return {
            "status": "Success",
            "info": {
                "trails": trail_names[:5],
                "distance_km": dist,
                "ascent_m": ascent,
                "difficulty": difficulty_rating
            },
            "map_image_url": static_map,
            "map_url": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}",
            "gpx_content": generate_gpx(data)
        }

    except requests.exceptions.HTTPError as e:
        return {"status": "Error", "code": e.response.status_code, "message": e.response.text}
    except Exception as e:
        return {"status": "Error", "message": str(e)}