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

from datetime import datetime, date
from typing import Literal
from datetime import date, datetime
from astral import LocationInfo
from astral.sun import sun
from timezonefinder import TimezoneFinder
import zoneinfo
from bikescout.tools.weather import get_weather_forecast
from bikescout.tools.mud import get_mud_risk_analysis

def get_solar_visibility(lat: float, lon: float, target_date: date) -> tuple:
    """
    Calculates Sunrise and Sunset based strictly on GPS coordinates.
    Automatically detects the correct local timezone.
    """
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"

        location = LocationInfo("Tactical Point", "Region", tz_name, lat, lon)

        s = sun(location.observer, date=target_date, tzinfo=zoneinfo.ZoneInfo(tz_name))

        sunrise_hour = s["sunrise"].hour + (s["sunrise"].minute / 60.0)
        sunset_hour = s["sunset"].hour + (s["sunset"].minute / 60.0)

        return (sunrise_hour, sunset_hour)

    except Exception:
        return (7.0, 18.0)

def calculate_ride_windows(
        lat: float,
        lon: float,
        ride_duration_hours: float = 2.0,
        surface_type: Literal["dirt", "gravel", "asphalt", "sand", "clay"] = "dirt",
        target_date: str = None):
    """
    Tactical Ride Planner v1.1: Optimized for physical safety and solar precision.
    Integrates astral-based visibility and thermal stress scoring.
    """
    try:
        # 1. TEMPORAL & SOLAR SETUP (Astral Precision)
        t_date = date.fromisoformat(target_date) if target_date else date.today()
        sunrise_h, sunset_h = get_solar_visibility(lat, lon, t_date)

        START_ALLOWED = sunrise_h
        END_ALLOWED = sunset_h

        # 2. DATA ACQUISITION
        weather_data = get_weather_forecast(lat, lon, target_date)
        mud_risk_data = get_mud_risk_analysis(lat, lon, surface_type)

        raw_forecasts = weather_data.get("tactical_forecast", [])
        current_mud_score = mud_risk_data.get("mud_risk_score", 0)

        # 3. DATA NORMALIZATION
        normalized_forecasts = []
        for h in raw_forecasts:
            try:
                def clean_val(v):
                    if isinstance(v, str):
                        return float(v.replace('°C', '').replace('C', '').replace('%', '').replace(' km/h', '').strip())
                    return float(v or 0)

                hour_int = int(h.get("time", "00:00").split(":")[0])

                normalized_forecasts.append({
                    "time": h.get("time", "N/A"),
                    "hour": hour_int,
                    "precip_prob": clean_val(h.get("rain_prob", 0)),
                    "wind_speed": clean_val(h.get("wind", 0)),
                    "temp": clean_val(h.get("temp", 15))
                })
            except Exception:
                continue

        # 4. SLIDING WINDOW ENGINE
        duration_int = int(max(1, ride_duration_hours))
        best_slot = None
        highest_score = -500.0

        for i in range(len(normalized_forecasts) - duration_int + 1):
            window = normalized_forecasts[i : i + duration_int]

            if window[0]["hour"] < START_ALLOWED or window[-1]["hour"] > END_ALLOWED:
                continue

            avg_rain = sum(h["precip_prob"] for h in window) / duration_int
            max_wind = max(h["wind_speed"] for h in window)
            avg_temp = sum(h["temp"] for h in window) / duration_int

            # SCORING LOGIC (Tactical Intelligence)
            current_score = 100.0

            if avg_rain > 30: current_score -= (avg_rain - 30) * 3
            else: current_score -= (avg_rain * 0.5)

            if max_wind > 25: current_score -= (max_wind - 25) * 2

            if avg_temp <= 0:
                current_score -= 20

            if avg_temp < 10:
                current_score -= (10 - avg_temp) * 4

            if avg_temp > 30:
                current_score -= (avg_temp - 30) * 5

            if surface_type != "asphalt":
                current_score -= (current_mud_score * 0.6)

            # Update Best Slot
            if current_score > highest_score:
                highest_score = current_score
                best_slot = {
                    "start": window[0]["time"],
                    "end": window[-1]["time"],
                    "score": round(max(0, current_score), 1),
                    "details": {
                        "rain_avg": f"{round(avg_rain)}%",
                        "wind_max": f"{round(max_wind)} km/h",
                        "temp_avg": f"{round(avg_temp)}°C"
                    }
                }

        # 5. VERDICT & RESPONSE
        if not best_slot:
            return {
                "status": "Success",
                "planner_report": {
                    "verdict": "NO-GO",
                    "tactical_color": "RED",
                    "confidence_score": "0/100",
                    "best_window": "N/A",
                    "environmental_briefing": {"message": "No safe daylight visibility for the requested duration"},
                    "mud_risk_impact": f"{current_mud_score}%"
                }
            }

        if highest_score > 75: verdict, color = "GO", "GREEN"
        elif highest_score > 40: verdict, color = "CAUTION", "YELLOW"
        else: verdict, color = "NO-GO", "RED"

        return {
            "payload_version": "1.1",
            "status": "Success",
            "metadata": {
                "analyzed_date": t_date.isoformat(),
                "surface_type": surface_type,
                "solar_window": f"{int(sunrise_h)}:00 - {int(sunset_h)}:00"
            },
            "planner_report": {
                "verdict": verdict,
                "tactical_color": color,
                "confidence_score": f"{best_slot['score']}/100",
                "best_window": f"{best_slot['start']} - {best_slot['end']}",
                "environmental_briefing": best_slot["details"],
                "mud_risk_impact": f"{current_mud_score}%"
            }
        }

    except Exception as e:
        return {"status": "Error", "message": f"Tactical Planner failed: {str(e)}"}