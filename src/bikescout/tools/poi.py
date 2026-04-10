import requests
import json

def get_poi_scout(api_key: str, lat: float, lon: float, radius_km: float):
    """
    Finds cycling POIs by category.
    If some categories are missing, it returns what's available.
    """
    url = "https://api.openrouteservice.org/pois"
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }

    # API Limit: 2000m
    safe_buffer = min(int(radius_km * 1000), 2000)

    # Expanded category list to be more inclusive
    # 162: Water
    # 372: Bicycle Shop
    # 342: Shelter
    # 331: Picnic Site (often has water/shelter)
    categories = {
        162: "Water Fountain 💧",
        372: "Bike Shop/Repair 🔧",
        342: "Shelter/Rest Area 🏠",
        331: "Picnic Area 🧺"
    }

    all_pois = []

    for cat_id, label in categories.items():
        body = {
            "request": "pois",
            "geometry": {
                "buffer": safe_buffer,
                "geojson": {
                    "type": "Point",
                    "coordinates": [float(lon), float(lat)]
                }
            },
            "filters": {
                "category_ids": [cat_id]
            },
            "limit": 5
        }

        try:
            response = requests.post(url, data=json.dumps(body), headers=headers)
            if response.ok:
                data = response.json()
                features = data.get('features', [])

                for feature in features:
                    p = feature.get('properties', {})
                    g = feature.get('geometry', {}).get('coordinates', [])
                    tags = p.get('osm_tags', {})

                    all_pois.append({
                        "name": tags.get('name') or tags.get('operator') or f"{label}",
                        "type": label,
                        "distance_m": round(p.get('distance', 0)),
                        "location": {"lat": g[1], "lon": g[0]}
                    })
        except Exception:
            continue

    # De-duplicate results
    unique_pois = {f"{p['location']['lat']}{p['location']['lon']}": p for p in all_pois}.values()
    results = sorted(list(unique_pois), key=lambda x: x['distance_m'])

    if not results:
        return {
            "status": "Success",
            "message": f"No specific cycling amenities found within {safe_buffer}m. Try a different coordinate or a larger radius.",
            "amenities": []
        }

    return {
        "status": "Success",
        "search_radius": f"{safe_buffer}m",
        "total_found": len(results),
        "amenities": results[:15]
    }