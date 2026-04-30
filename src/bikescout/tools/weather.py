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
import zoneinfo
from datetime import datetime, date, timezone, time
from timezonefinder import TimezoneFinder
from typing import Dict, Any, Optional

OPEN_METEO_URL = 'https://api.open-meteo.com/v1/forecast'

def get_safety_advice(app_temp: float, rain_prob: int, rain_mm: float, wind_speed: float, wind_gusts: float) -> dict:
    """
    Evaluates cycling safety based on multi-factor weather thresholds,
    including wind gusts, precipitation volume, and apparent temperature.
    """
    # 1. Multi-Factor Risk Calculations
    # Wind risk heavily weighs gusts as they cause loss of bike control
    wind_risk_score = (wind_speed * 0.4) + (wind_gusts * 0.6)

    # 2. Safety Status Engine
    if rain_mm > 10.0 or wind_risk_score > 55:
        status_label = "🔴 [NOT RECOMMENDED]"
        status_msg = "Critical risk: Heavy rain volume or dangerous wind gusts. Riding is unsafe."
    elif rain_mm > 2.0 or wind_risk_score > 35:
        status_label = "🟡 [CAUTION]"
        status_msg = "Significant hazards: Moderate rain or strong crosswinds expected. Use extreme care."
    elif rain_prob > 30 or wind_speed > 25:
        status_label = "🔵 [WATCH]"
        status_msg = "Sub-optimal: Light rain possible or stiff breeze. Manageable for experienced riders."
    else:
        status_label = "🟢 [GO]"
        status_msg = "Ideal conditions: Low wind, dry, and safe."

    # 3. Adaptive Gear Recommendations based on Thermal Stress
    if app_temp < 5:
        gear = "Deep Winter (Heavy thermal layers, insulated gloves, overshoes, skull cap)"
    elif app_temp <= 12:
        gear = "Spring/Fall (Knee/arm warmers, windproof gilet, medium base layer)"
    elif app_temp <= 25:
        gear = "Standard (Short sleeves, summer bibs, light base layer)"
    else:
        gear = "High Summer (Ultra-light kit, double hydration priority, sunscreen)"

    return {
        "status": status_label,
        "message": status_msg,
        "wind_risk_score": round(wind_risk_score, 1),
        "gear_advice": gear
    }

def get_weather_forecast(lat: float, lon: float, target_date: str = None, target_hour: int = 9) -> Dict[str, Any]:
    """
    Advanced cycling-specific weather engine for BikeScout.
    Synchronizes local user time with Open-Meteo UTC timeline using GPS coordinates.

    Args:
        lat: Latitude of the target location.
        lon: Longitude of the target location.
        target_date: Optional 'YYYY-MM-DD' string. Defaults to today.
        target_hour: The specific local hour to evaluate for safety (0-23).
    """
    try:
        # 1. Temporal & Timezone Localization
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = zoneinfo.ZoneInfo(tz_name)

        # Establish Local Reference Point
        if target_date:
            target_dt_local = datetime.combine(
                date.fromisoformat(target_date),
                time(hour=target_hour)
            ).replace(tzinfo=local_tz)
        else:
            now_local = datetime.now(local_tz)
            # If target_hour is provided, we adjust today's reference
            target_dt_local = now_local.replace(hour=target_hour, minute=0, second=0, microsecond=0)

        # 2. API Parameters
        # Fetching full day data to allow sliding window analysis
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "windspeed_10m",
                "windgusts_10m",
                "weathercode"
            ],
            "timezone": "UTC", # Kept UTC for raw data consistency
            "start_date": target_dt_local.date().isoformat(),
            "end_date": target_dt_local.date().isoformat()
        }

        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "hourly" not in data:
            return {"status": "Error", "message": "No hourly data returned from provider."}

        hourly = data["hourly"]

        # 3. UTC Temporal Mapping (Localized Matching)
        # Convert our local target time to UTC to find the exact index in the API response
        target_dt_utc = target_dt_local.astimezone(timezone.utc)
        target_utc_str = target_dt_utc.strftime('%Y-%m-%dT%H:00')

        try:
            ref_idx = hourly["time"].index(target_utc_str)
        except (ValueError, KeyError):
            # Fallback if the timezone offset pushes the index out of the requested day array
            ref_idx = 0

        # 4. Tactical Forecast Generation (Localized Display)
        forecast_summary = []
        for i in range(len(hourly["time"])):
            # Convert UTC response time back to local time for user-friendly display
            utc_dt = datetime.fromisoformat(hourly["time"][i]).replace(tzinfo=timezone.utc)
            local_time_str = utc_dt.astimezone(local_tz).strftime('%H:%M')

            forecast_summary.append({
                "time": local_time_str,
                "temp": f"{hourly['temperature_2m'][i]}°C",
                "app_temp": f"{hourly['apparent_temperature'][i]}°C",
                "rain_prob": f"{hourly['precipitation_probability'][i]}%",
                "rain_mm": f"{hourly['precipitation'][i]} mm",
                "wind": f"{hourly['windspeed_10m'][i]} km/h",
                "gusts": f"{hourly['windgusts_10m'][i]} km/h"
            })

        # 5. Extract Baseline Reference Conditions (Target Hour)
        curr_app_temp = hourly['apparent_temperature'][ref_idx]
        curr_rain_prob = hourly['precipitation_probability'][ref_idx]
        curr_rain_mm = hourly['precipitation'][ref_idx]
        curr_wind = hourly['windspeed_10m'][ref_idx]
        curr_gusts = hourly['windgusts_10m'][ref_idx]

        # 6. Return Structured Multi-Temporal Payload
        return {
            "status": "Success",
            "metadata": {
                "date_analyzed": target_dt_local.date().isoformat(),
                "local_timezone": tz_name,
                "target_time_local": target_dt_local.strftime('%H:%M'),
                "location": {"lat": lat, "lon": lon}
            },
            "tactical_forecast": forecast_summary,
            "reference_conditions": {
                "temp_actual": hourly['temperature_2m'][ref_idx],
                "temp_apparent": curr_app_temp,
                "rain_probability": curr_rain_prob,
                "precipitation_mm": curr_rain_mm,
                "wind_speed": curr_wind,
                "wind_gusts": curr_gusts,
                "reference_hour_local": f"{target_hour}:00"
            },
            "safety_advice": get_safety_advice(
                app_temp=curr_app_temp,
                rain_prob=curr_rain_prob,
                rain_mm=curr_rain_mm,
                wind_speed=curr_wind,
                wind_gusts=curr_gusts
            )
        }

    except requests.exceptions.RequestException as e:
        return {"status": "Error", "message": f"Weather API Connection Error: {str(e)}"}
    except Exception as e:
        return {"status": "Error", "message": f"Unexpected Weather Engine Error: {str(e)}"}