import requests

def get_surface_analyzer(api_key: str, lat: float, lon: float, radius_km: int = 10, profile: str = "cycling-mountain"):
    """
    Analyzes the route surface composition (asphalt, gravel, dirt, etc.)
    using OpenRouteService 'extra_info' metadata.
    """
    url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"

    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }

    body = {
        "coordinates": [[lon, lat]],
        "options": {"round_trip": {"length": radius_km * 1000, "points": 3}},
        "extra_info": ["surface", "waytype"]
    }

    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()

        surface_info = data['features'][0]['properties']['extras']['surface']
        summary = surface_info['summary']

        surface_map = {
            0: "Unknown", 1: "Asphalt", 2: "Unpaved", 3: "Paved",
            4: "Cobblestone", 5: "Gravel", 6: "Fine Gravel",
            7: "Atv", 8: "Pebbles", 9: "Wood", 10: "Stepping Stones",
            11: "Grass", 12: "Compact", 13: "Sett", 14: "Concrete"
        }

        breakdown = []
        for item in summary:
            name = surface_map.get(item['value'], "Other")
            percentage = round(item['amount'], 1)
            breakdown.append({"type": name, "percentage": f"{percentage}%"})

        return {
            "status": "Success",
            "surface_breakdown": breakdown,
            "total_distance_m": data['features'][0]['properties']['summary']['distance']
        }
    except Exception as e:
        return {"status": "Error", "message": str(e)}