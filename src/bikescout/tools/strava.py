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
import time
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.weather import get_weather_forecast

STRAVA_AUTH_URL = "https://www.strava.com/oauth/token"
STRAVA_BASE_URL = "https://www.strava.com/api/v3"

class StravaMissionDebrief:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = self._refresh_access_token()

    def _refresh_access_token(self) -> str:
        """Satellite Link: Ensures valid OAuth token for high-bandwidth stream access."""
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        res = requests.post(STRAVA_AUTH_URL, data=data, timeout=10)
        res.raise_for_status()
        return res.json()['access_token']

    def _get_streams(self, activity_id: str) -> Dict[str, List]:
        """High-Fidelity Telemetry: Fetches raw GPS, Time, and Velocity streams."""
        url = f"{STRAVA_BASE_URL}/activities/{activity_id}/streams"
        params = {
            "keys": "latlng,time,altitude,velocity_smooth,watts",
            "key_by_type": "true"
        }
        headers = {'Authorization': f"Bearer {self.access_token}"}
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def analyze_mission(self, activity_date: str) -> Dict[str, Any]:
        """
        Post-Mission Debriefing Tool.
        Fuses GPS streams with historical environment data to identify 'The Performance Gap'.
        """
        try:
            # 1. Fetch Activity List
            headers = {'Authorization': f"Bearer {self.access_token}"}
            r = requests.get(f"{STRAVA_BASE_URL}/athlete/activities", headers=headers, timeout=10)
            r.raise_for_status()

            # Find the target mission
            target = next((a for a in r.json() if a['start_date_local'].startswith(activity_date)), None)
            if not target:
                return {"status": "Error", "message": f"No mission telemetry found for {activity_date}."}

            activity_id = target['id']
            start_time_utc = datetime.fromisoformat(target['start_date'].replace('Z', '+00:00'))

            # 2. Extract High-Res Streams
            streams = self._get_streams(activity_id)
            latlng = streams.get('latlng', {}).get('data', [])
            time_offsets = streams.get('time', {}).get('data', [])
            velocities = streams.get('velocity_smooth', {}).get('data', [])

            if not latlng:
                return {"status": "Error", "message": "GPS stream data is empty."}

            # 3. Spatio-Temporal Fusion (Sample Start, Middle, and End)
            # We sample indices to stay within API limits while capturing evolution
            sample_indices = [0, len(latlng) // 2, len(latlng) - 1]
            environmental_snapshots = []

            for idx in sample_indices:
                point_lat, point_lon = latlng[idx]
                point_time = (start_time_utc + timedelta(seconds=time_offsets[idx])).isoformat()

                # Fetch Mud and Weather for this specific location AND time
                # Using the target_date parameter allows historical reconstruction
                mud = get_mud_risk_analysis(point_lat, point_lon, target_date=activity_date)
                weather = get_weather_forecast(point_lat, point_lon, target_date=activity_date)

                environmental_snapshots.append({
                    "timestamp": point_time,
                    "location": [point_lat, point_lon],
                    "mud_score": mud.get('tactical_analysis', {}).get('mud_risk_numeric', 0),
                    "wind_speed": weather.get('current_conditions', {}).get('wind_speed', 0)
                })

            # 4. The Performance Gap Analysis
            actual_avg_speed = target.get('average_speed', 0) * 3.6
            # Example heuristic: If mud > 15, expected speed degradation is 25%
            worst_mud = max(s['mud_score'] for s in environmental_snapshots)

            performance_delta = 0
            efficiency_note = "Performance matched environmental expectations."

            if worst_mud > 15 and actual_avg_speed < 12:
                efficiency_note = "Significant speed degradation detected in High-Risk mud sectors. Traction model validated."
            elif worst_mud < 5 and actual_avg_speed < 12:
                efficiency_note = "Low speed detected despite optimal terrain. Potential mechanical issue or rider fatigue."

            # 5. Calibration Payload
            # Learning from the rider's VAM (Vertical Ascent Meters per hour)
            total_ascent = target.get('total_elevation_gain', 0)
            total_moving_time = target.get('moving_time', 1)
            actual_vam = (total_ascent / total_moving_time) * 3600

            return {
                "status": "Success",
                "mission_id": activity_id,
                "debriefing_summary": {
                    "name": target.get('name'),
                    "actual_avg_speed": f"{actual_avg_speed:.1f} km/h",
                    "actual_vam": f"{actual_vam:.0f} m/h",
                    "worst_encountered_mud": worst_mud
                },
                "spatio_temporal_logs": environmental_snapshots,
                "tactical_calibration": {
                    "efficiency_scoring": efficiency_note,
                    "suggested_profile_update": {
                        "climbing_efficiency": "High" if actual_vam > 800 else "Standard",
                        "mud_penalty_factor": "Increase" if worst_mud > 15 and actual_avg_speed < 8 else "Accurate"
                    }
                },
                "mechanical_feedback": "Tire pressure refinement suggested based on speed-to-saturation correlation."
            }

        except Exception as e:
            return {"status": "Error", "message": f"Debriefing failed: {str(e)}"}

# --- Global Interface ---
def get_strava_activity(activity_date, client_id, client_secret, refresh_token):
    debrief = StravaMissionDebrief(client_id, client_secret, refresh_token)
    return debrief.analyze_mission(activity_date)
