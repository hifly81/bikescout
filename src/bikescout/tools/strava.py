import requests
import polyline
from datetime import datetime
# Import your existing tactical modules
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.weather import get_weather_forecast

def get_strava_activity(activity_date, client_id, client_secret, refresh_token):
    """
    Tactical Post-Ride Analysis Engine.
    Fuses Strava GPS data with Mud Risk and Weather Intelligence.
    """

    # 1. OAuth Satellite Link (Refresh Token)
    auth_url = "https://www.strava.com/oauth/token"
    auth_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    try:
        # Auth Request
        auth_res = requests.post(auth_url, data=auth_data, timeout=10)
        auth_res.raise_for_status()
        access_token = auth_res.json()['access_token']

        # 2. Fetch Intelligence (Activities)
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {'Authorization': f"Bearer {access_token}"}
        r = requests.get(activities_url, headers=headers, timeout=10)
        r.raise_for_status()
        activities = r.json()

        # 3. Target Acquisition (Filter by Date)
        target_activity = next(
            (a for a in activities if a['start_date_local'].startswith(activity_date)),
            None
        )

        if not target_activity:
            return {"status": "Error", "message": f"No mission found on {activity_date}."}

        # 4. Decode Terrain Geometry
        map_data = target_activity.get('map', {})
        encoded_polyline = map_data.get('summary_polyline')
        if not encoded_polyline:
            return {"status": "Error", "message": "No GPS telemetry found."}

        path_points = polyline.decode(encoded_polyline)
        lat, lon = path_points[0] # Get start coordinates

        # --- TACTICAL FUSION SECTION ---

        # Determine surface based on activity type (simplified logic)
        surface_type = "dirt" if target_activity.get('type') in ['MountainBikeRide', 'GravelRide'] else "asphalt"

        # Pull Mud Intelligence
        mud_report = get_mud_risk_analysis(lat, lon, surface_type)

        # Pull Weather Context
        weather_report = get_weather_forecast(lat, lon)

        # 5. Final Report Construction
        return {
            "status": "Success",
            "mission_briefing": {
                "name": target_activity.get('name'),
                "distance_km": round(target_activity.get('distance', 0) / 1000, 2),
                "elevation_gain_m": target_activity.get('total_elevation_gain', 0),
                "avg_speed_kmh": round(target_activity.get('average_speed', 0) * 3.6, 1)
            },
            "environmental_validation": {
                "mud_risk": mud_report.get('tactical_analysis', {}).get('mud_risk_score'),
                "moisture_index": mud_report.get('tactical_analysis', {}).get('adjusted_moisture_index'),
                "weather_advice": weather_report.get('safety_advice'),
                "conditions_at_start": weather_report.get('current_conditions')
            },
            "tactical_notes": f"Analysis based on {surface_type} surface coefficients. GPS data validated."
        }

    except Exception as e:
        return {"status": "Error", "message": f"Fusion failed: {str(e)}"}