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

import requests
import sys
from math import radians, cos, sin, asin, sqrt

# OpenRouteService POIs API endpoint
ORS_POIS_URL = "https://api.openrouteservice.org/pois"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def get_poi_scout_free(lat: float, lon: float, total_length_km: float):
    """
    Finds cycling POIs using Overpass API (No API Key required).
    Features: Water, Bike Repair, Shelters, and Picnic areas.
    """

    # Overpass handles large radii better than ORS
    total_length_m = total_length_km * 1000

    # We search for specific OSM tags:
    # - drinking_water / water_point
    # - bicycle_repair_station / bicycle_shop
    # - shelter / picnic_site
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="drinking_water"](around:{total_length_m},{lat},{lon});
      node["amenity"="bicycle_repair_station"](around:{total_length_m},{lat},{lon});
      node["shop"="bicycle"](around:{total_length_m},{lat},{lon});
      node["amenity"="shelter"](around:{total_length_m},{lat},{lon});
      node["leisure"="picnic_table"](around:{total_length_m},{lat},{lon});
    );
    out body;
    """

    try:
        response = requests.post(OVERPASS_URL, data={'data': query})

        if response.status_code != 200:
            print(f"Overpass Error: {response.status_code}", file=sys.stderr)
            return {"status": "Error", "message": "Overpass server busy"}

        data = response.json()
        elements = data.get('elements', [])

        all_amenities = []
        for el in elements:
            tags = el.get('tags', {})

            label = "Point of Interest"
            if tags.get('amenity') == 'drinking_water':
                label = "Water Fountain 💧"
            elif 'bicycle' in tags.get('amenity', '') or 'bicycle' in tags.get('shop', ''):
                label = "Bike Support 🔧"
            elif tags.get('amenity') == 'shelter' or tags.get('leisure') == 'picnic_table':
                label = "Rest Area 🧺"

            current_lat = el.get('lat')
            current_lon = el.get('lon')
            distance_m = 0
            if current_lat and current_lon and lat and lon:
                distance_m = round(haversine_distance(lat, lon, current_lat, current_lon))

            all_amenities.append({
                "name": tags.get('name') or tags.get('amenity') or tags.get('operator') or label,
                "type": label,
                "distance_m": distance_m,
                "location": {"lat": current_lat, "lon": current_lon},
                "osm_id": el.get('id')  # Optional
            })

        return {
            "status": "Success",
            "search_km": f"{total_length_m}m",
            "total_found": len(all_amenities),
            "amenities": all_amenities
        }

    except Exception as e:
        print(f"Overpass Critical Exception: {str(e)}", file=sys.stderr)
        return {"status": "Error", "message": str(e)}

def get_poi_scout(api_key: str, lat: float, lon: float, total_length_km: float):
    """
    Finds cycling-specific POIs (Water, Repair, Rest Areas).
    Strictly follows ORS server constraints: Max 2000m buffer and 5 specific categories.
    """

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json, application/geo+json'
    }

    # Buffer MUST be an integer between 1 and 2000 meters.
    safe_buffer = int(min(max(total_length_km * 1000, 1), 2000))

    # Category Selection (STRICT LIMIT: 5 categories per request)
    # These IDs are verified from your server's whitelist:
    # 162: Drinking Water
    # 372: Bicycle Shop
    # 371: Bicycle Rental / Repair Station
    # 331: Picnic Site
    # 332: Playground (Reliable source of benches/water)
    target_categories = [162, 372, 371, 331, 332]

    body = {
        "request": "pois",
        "geometry": {
            "geojson": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)] # GeoJSON is [Longitude, Latitude]
            },
            "buffer": safe_buffer
        },
        "filters": {
            "category_ids": target_categories
        },
        "limit": 20,
        "sortby": "distance"
    }

    try:
        # Use json=body to ensure clean serialization and correct Content-Type
        response = requests.post(ORS_POIS_URL, json=body, headers=headers)

        if not response.ok:
            # We log the specific API error message to stderr
            # This prevents breaking the MCP JSON-RPC protocol on stdout
            print(f"ORS API Error: {response.status_code} - {response.text}", file=sys.stderr)
            return {
                "status": "Error",
                "message": f"ORS API error {response.status_code}"
            }

        data = response.json()
        features = data.get('features', [])

        all_amenities = []
        for feature in features:
            props = feature.get('properties', {})
            geom = feature.get('geometry', {}).get('coordinates', [])
            tags = props.get('osm_tags', {})

            # Map category IDs back to readable labels
            # Keys in props['category_ids'] are returned as strings by ORS
            found_cats = props.get('category_ids', {}).keys()

            label = "Point of Interest"
            if '162' in found_cats:
                label = "Water Fountain 💧"
            elif '372' in found_cats or '371' in found_cats:
                label = "Bike Support 🚲"
            elif '331' in found_cats or '332' in found_cats:
                label = "Rest Area 🧺"

            all_amenities.append({
                "name": tags.get('name') or tags.get('amenity') or tags.get('operator') or label,
                "type": label,
                "distance_m": round(props.get('distance', 0)),
                "location": {"lat": geom[1], "lon": geom[0]}
            })

        return {
            "status": "Success",
            "search_km": f"{safe_buffer}m",
            "total_found": len(all_amenities),
            "amenities": sorted(all_amenities, key=lambda x: x['distance_m'])
        }

    except Exception as e:
        print(f"POI Engine Critical Exception: {str(e)}", file=sys.stderr)
        return {
            "status": "Error",
            "message": f"Internal Engine failure: {str(e)}"
        }

def haversine_distance(lat1, lon1, lat2, lon2):
    r = 6371000
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))