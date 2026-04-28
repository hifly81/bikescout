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
from datetime import datetime, date, timezone

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
        status_label = "🟠 [CAUTION]"
        status_msg = "Significant hazards: Moderate rain or strong crosswinds expected. Use extreme care."
    elif rain_prob > 30 or wind_speed > 25:
        status_label = "🟡 [WATCH]"
        status_msg = "Sub-optimal conditions: Light rain possible or stiff breeze. Manageable for experienced riders."
    else:
        status_label = "🟢 [GO]"
        status_msg = "Ideal conditions: Low wind, dry, and safe."

    # 3. Adaptive Gear Recommendations based on Thermal Stress (Apparent Temp)
    if app_temp < 5:
        gear = "Deep Winter (Heavy thermal layers, insulated gloves, overshoes, skull cap)"
    elif app_temp <= 12:
        gear = "Spring/Fall (Knee/arm warmers, windproof gilet, medium base layer)"
    elif app_temp <= 25:
        gear = "Standard (Short sleeves, summer bibs, light base layer)"
    else:
        gear = "High Summer (Ultra-light ventilated kit, double hydration priority, sunscreen)"

    return {
        "status": status_label,
        "message": status_msg,
        "wind_risk_score": round(wind_risk_score, 1),
        "gear_advice": gear
    }

def get_weather_forecast(lat: float, lon: float, target_date: str = None):
    """
    Advanced cycling-specific weather engine for BikeScout.
    Fetches a full 24-hour hourly forecast from Open-Meteo with exact UTC temporal matching.

    Args:
        lat: Latitude of the target location.
        lon: Longitude of the target location.
        target_date: Optional 'YYYY-MM-DD' string. Defaults to today.
    """
    # 1. Date Handling
    if target_date is None:
        target_date = date.today().isoformat()

    is_today = target_date == date.today().isoformat()

    # 2. API Parameters:
    # Forced to 'UTC' to standardize time arrays globally.
    # Added apparent_temperature, precipitation (mm), and windgusts_10m.
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
        "timezone": "UTC",
        "start_date": target_date,
        "end_date": target_date
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "hourly" not in data:
            return {"status": "Error", "message": "No hourly data returned from weather provider."}

        hourly = data["hourly"]

        # 3. ISO-8601 Temporal Matching (Fixes the Time-Drift Bug)
        # We match the current server UTC time exactly to the UTC time array from the API.
        ref_idx = 8 # Default reference hour (08:00 UTC) for future/past dates

        if is_today:
            # Format current UTC time to match Open-Meteo's hourly string (e.g., "2023-10-25T14:00")
            now_utc_str = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:00')
            try:
                ref_idx = hourly["time"].index(now_utc_str)
            except ValueError:
                # Fallback to the first hour if exact match fails (e.g., at midnight transitions)
                ref_idx = 0

        # 4. Full-Day Tactical Forecast Generation
        # Standardized UTF-8 symbols and extended metrics payload
        forecast_summary = []
        for i in range(24):
            forecast_summary.append({
                "time": hourly["time"][i].split("T")[1], # HH:MM format
                "temp": f"{hourly['temperature_2m'][i]}°C",
                "app_temp": f"{hourly['apparent_temperature'][i]}°C",
                "rain_prob": f"{hourly['precipitation_probability'][i]}%",
                "rain_mm": f"{hourly['precipitation'][i]} mm",
                "wind": f"{hourly['windspeed_10m'][i]} km/h",
                "gusts": f"{hourly['windgusts_10m'][i]} km/h"
            })

        # 5. Extract Baseline Reference Conditions
        curr_temp = hourly['temperature_2m'][ref_idx]
        curr_app_temp = hourly['apparent_temperature'][ref_idx]
        curr_rain_prob = hourly['precipitation_probability'][ref_idx]
        curr_rain_mm = hourly['precipitation'][ref_idx]
        curr_wind = hourly['windspeed_10m'][ref_idx]
        curr_gusts = hourly['windgusts_10m'][ref_idx]

        # 6. Return Structured Multi-Temporal Payload
        return {
            "status": "Success",
            "metadata": {
                "date_analyzed": target_date,
                "is_future_planning": not is_today,
                "location": {"lat": lat, "lon": lon},
                "data_points": len(forecast_summary),
                "matched_utc_time": hourly["time"][ref_idx]
            },
            "tactical_forecast": forecast_summary,
            "reference_conditions": {
                "temp_actual": curr_temp,
                "temp_apparent": curr_app_temp,
                "rain_probability": curr_rain_prob,
                "precipitation_mm": curr_rain_mm,
                "wind_speed": curr_wind,
                "wind_gusts": curr_gusts,
                "reference_index_utc": f"{ref_idx}:00"
            },
            # Delegate to the upgraded Safety Engine
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
