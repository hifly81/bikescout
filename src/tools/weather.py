import requests
from datetime import datetime

OPEN_METEO_URL = 'https://api.open-meteo.com/v1/forecast'

def get_safety_advice(temp: float, rain_prob: int, wind_speed: float) -> str:
    """
    Evaluates cycling safety based on multi-factor weather thresholds.
    """
    # 1. Critical Danger (Severe weather)
    if rain_prob > 50 or wind_speed > 45:
        return "❌ NOT RECOMMENDED: High risk of heavy rain or dangerous wind gusts."

    # 2. Significant Hazards
    if rain_prob > 25:
        return "⚠️ CAUTION: High rain probability. Bring a waterproof jacket."

    if wind_speed > 25:
        return "💨 WINDY: Strong winds. Use caution on descents and open ridges."

    # 3. Temperature/Gear Advice
    if temp < 7:
        return "❄️ COLD: Near freezing. Wear thermal layers and winter gloves."

    if temp > 30:
        return "☀️ HOT: Heat exhaustion risk. Bring extra water and electrolytes."

    if temp < 15:
        return "🌥️ CHILLY: Light jacket or arm warmers recommended."

    # 4. Optimal Conditions
    return "✅ IDEAL: Perfect conditions for a great ride!"

def get_weather_forecast(lat: float, lon: float):
    """
    Fetches a 24-hour weather forecast and provides cycling-specific safety advice.
    Uses Open-Meteo API.
    """
    url = OPEN_METEO_URL
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "precipitation_probability", "windspeed_10m", "weathercode"],
        "timezone": "auto",
        "forecast_days": 1
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current_hour = datetime.now().hour
        hourly = data["hourly"]

        # Current conditions for the safety advisor
        # We use the current hour's data to generate the main advice
        curr_temp = hourly['temperature_2m'][current_hour]
        curr_rain = hourly['precipitation_probability'][current_hour]
        curr_wind = hourly['windspeed_10m'][current_hour]

        forecast_summary = []
        for i in range(current_hour, current_hour + 4):
            if i < len(hourly["time"]):
                forecast_summary.append({
                    "time": hourly["time"][i].split("T")[1],
                    "temp": f"{hourly['temperature_2m'][i]}°C",
                    "rain_prob": f"{hourly['precipitation_probability'][i]}%",
                    "wind": f"{hourly['windspeed_10m'][i]} km/h"
                })

        return {
            "status": "Success",
            "location": {"lat": lat, "lon": lon},
            "next_4_hours": forecast_summary,
            "current_conditions": {
                "temp": curr_temp,
                "rain_prob": curr_rain,
                "wind_speed": curr_wind
            },
            "safety_advice": get_safety_advice(curr_temp, curr_rain, curr_wind)
        }
    except Exception as e:
        return {"status": "Error", "message": str(e)}