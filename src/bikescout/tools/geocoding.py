import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def get_coordinates(location_name: str):
    """
    Converts a place name into lat/lon coordinates using Nominatim (OSM).
    """
    url = NOMINATIM_URL
    headers = {
        'User-Agent': 'BikeScout_MCP_Server/1.0'
    }
    params = {
        'q': location_name,
        'format': 'json',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            return {"status": "Error", "message": f"Location '{location_name}' not found."}

        return {
            "status": "Success",
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"]
        }
    except Exception as e:
        return {"status": "Error", "message": str(e)}