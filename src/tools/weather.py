import requests
from datetime import datetime

def get_weather_forecast(lat: float, lon: float):
    """
    Fetches a 24-hour weather forecast for the given coordinates.
    Uses Open-Meteo API (Free, no-key required).
    """
    url = "https://api.open-meteo.com/v1/forecast"
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
            "advice": "Perfect for riding!" if int(hourly['precipitation_probability'][current_hour]) < 20 else "Careful, rain expected."
        }
    except Exception as e:
        return {"status": "Error", "message": str(e)}