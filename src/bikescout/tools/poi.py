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

# OpenRouteService POIs API endpoint
ORS_POIS_URL = "https://api.openrouteservice.org/pois"

def get_poi_scout(api_key: str, lat: float, lon: float, radius_km: float):
    """
    Finds cycling-specific POIs (Water, Repair, Rest Areas).
    Strictly follows ORS server constraints: Max 2000m buffer and 5 specific categories.
    """
    # 1. Standardized headers for ORS API
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json, application/geo+json'
    }

    # 2. Parameter Normalization
    # Buffer MUST be an integer between 1 and 2000 meters.
    safe_buffer = int(min(max(radius_km * 1000, 1), 2000))

    # 3. Category Selection (STRICT LIMIT: 5 categories per request)
    # These IDs are verified from your server's whitelist:
    # 162: Drinking Water
    # 372: Bicycle Shop
    # 371: Bicycle Rental / Repair Station
    # 331: Picnic Site
    # 332: Playground (Reliable source of benches/water)
    target_categories = [162, 372, 371, 331, 332]

    # 4. Request Body Construction
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
        # 5. API Execution
        # Use json=body to ensure clean serialization and correct Content-Type
        response = requests.post(ORS_POIS_URL, json=body, headers=headers)

        # 6. Detailed Error Handling for MCP Stability
        if not response.ok:
            # We log the specific API error message to stderr
            # This prevents breaking the MCP JSON-RPC protocol on stdout
            print(f"ORS API Error: {response.status_code} - {response.text}", file=sys.stderr)
            return {
                "status": "Error",
                "message": f"ORS API error {response.status_code}"
            }

        # 7. Response Processing
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

        # 8. Success Response
        # Return the clean payload sorted by proximity
        return {
            "status": "Success",
            "search_radius": f"{safe_buffer}m",
            "total_found": len(all_amenities),
            "amenities": sorted(all_amenities, key=lambda x: x['distance_m'])
        }

    except Exception as e:
        # Catch-all for network or serialization errors, logged to stderr
        print(f"POI Engine Critical Exception: {str(e)}", file=sys.stderr)
        return {
            "status": "Error",
            "message": f"Internal Engine failure: {str(e)}"
        }
