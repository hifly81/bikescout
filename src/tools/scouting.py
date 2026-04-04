import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions"


def generate_gpx(geojson_data):
    """Converts GeoJSON coordinates into a standard GPX XML string."""
    try:
        # ORS returns [lon, lat, elevation]
        coords = geojson_data['features'][0]['geometry']['coordinates']
        gpx = '<?xml version="1.0" encoding="UTF-8"?>\n'
        gpx += '<gpx version="1.1" creator="BikeScout" xmlns="http://www.topografix.com/GPX/1/1">\n'
        gpx += '  <trk><name>BikeScout Route</name><trkseg>\n'
        for p in coords:
            # lat=p[1], lon=p[0], ele=p[2]
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

    # Round Trip structure for ORS V2
    payload = {
        "coordinates": [[lon, lat]],
        "options": {
            "round_trip": {
                "length": radius_km * 1000,
                "seed": 42
            }
        },
        "elevation": "true", # ORS prefers string "true" in some versions
        "instructions": "false",
        "units": "m"
    }

    try:
        # The correct V2 endpoint for GeoJSON output is usually:
        # https://api.openrouteservice.org/v2/directions/{profile}/geojson
        endpoint = f"{ORS_BASE_URL}/{profile}/geojson"

        response = requests.post(endpoint, json=payload, headers=headers, timeout=15)

        # If 404, try the non-geojson endpoint
        if response.status_code == 404:
            endpoint = f"{ORS_BASE_URL}/{profile}"
            response = requests.post(endpoint, json=payload, headers=headers, timeout=15)

        response.raise_for_status()
        data = response.json()

        if 'features' not in data:
            return {"status": "Error", "message": "API returned success but no route features found."}

        props = data['features'][0]['properties']
        summary = props.get('summary', {})

        dist = round(summary.get('distance', 0) / 1000, 2)
        # Ascent is often in 'ascent' or inside 'summary'
        ascent = round(props.get('ascent', summary.get('ascent', 0)), 0)

        return {
            "status": "Success",
            "info": {
                "trails": trail_names[:5],
                "distance_km": dist,
                "ascent_m": ascent,
                "difficulty": "Expert" if ascent > 500 else "Easy"
            },
            "map_url": f"https://www.google.com/maps?q={lat},{lon}",
            "gpx_content": generate_gpx(data)
        }

    except requests.exceptions.HTTPError as e:
        return {"status": "Error", "code": e.response.status_code, "message": e.response.text}
    except Exception as e:
        return {"status": "Error", "message": str(e)}