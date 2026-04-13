from datetime import datetime, timedelta, timezone
from pysolar.solar import get_altitude
import requests


OPEN_METEO_ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive'


def get_shadow_penalty(lat, lon):
    """
    Calculates the Solar Evaporation Penalty based on sun altitude.
    Low sun angles (winter or late afternoon) significantly reduce trail drying speed.
    """
    try:
        now = datetime.now(timezone.utc)
        altitude = get_altitude(lat, lon, now)

        # Heuristic: Sun below 20° provides minimal drying energy (Shadow Lock)
        if altitude < 20:
            return 0.4  # 60% reduction in drying efficiency
        elif altitude < 40:
            return 0.7  # 30% reduction in drying efficiency
        return 1.0      # Full solar potential
    except Exception:
        return 1.0      # Neutral fallback

def get_mud_risk_analysis(lat, lon, surface_type):
    """
    Tactical Mud Risk Analysis v2.1: TAEL (Terrain-Aware Evaporation Lag) Model.
    Accounts for cumulative rainfall, atmospheric drying efficiency, and solar persistence.
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=3)

    # Open-Meteo Archive API - Fetching historical weather for ground saturation analysis
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ["precipitation_sum", "temperature_2m_max", "wind_speed_10m_max"],
        "timezone": "auto"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get('daily', {})

        # 1. Environmental Data Extraction (72h window)
        precip_list = data.get('precipitation_sum', [0, 0, 0])
        temp_list = data.get('temperature_2m_max', [15, 15, 15])
        wind_list = data.get('wind_speed_10m_max', [10, 10, 10])

        total_raw_rain = sum(precip_list)
        avg_temp = sum(temp_list) / len(temp_list)
        avg_wind = sum(wind_list) / len(wind_list)

        # 2. Advanced Drying Efficiency Heuristic
        # Merges Thermal (Temp), Kinetic (Wind), and Photonic (Solar Angle) factors
        temp_factor = max(0.5, (avg_temp / 20))  # Baseline drying at 20°C
        wind_factor = max(0.5, (avg_wind / 15))  # Baseline drying at 15km/h

        # Integration of the Killer Feature: Shadow Persistence
        shadow_penalty = get_shadow_penalty(lat, lon)

        # Final Drying Efficiency Coefficient
        drying_efficiency = min(2.0, temp_factor * wind_factor * shadow_penalty)

        # 3. Adjusted Precipitation Index (API)
        # Calculates 'effective' moisture remaining on the surface
        adjusted_rain = total_raw_rain / drying_efficiency

        # 4. Terrain Sensitivity Coefficients
        # Non-linear drainage behavior based on soil texture
        soil_sensitivity = {
            "clay": 1.2,    # High saturation, extreme persistence
            "dirt": 0.9,
            "earth": 0.9,
            "grass": 0.7,
            "gravel": 0.3,  # High permeability
            "sand": 0.1,    # Fast drainage
            "asphalt": 0.05 # Negligible mud risk
        }
        sensitivity = soil_sensitivity.get(surface_type.lower(), 0.7)

        # 5. Mud Risk Score Matrix
        mud_score = adjusted_rain * sensitivity

        # Tactical Categorization & Advice
        if mud_score < 3:
            risk, advice = "Low", "Optimal grip. Surface is stable and fast."
        elif mud_score < 10:
            risk, advice = "Medium", "Damp sections. Expect reduced traction on off-camber roots."
        elif mud_score < 20:
            risk, advice = "High", "Significant saturation. High risk of sliding in technical sectors."
        else:
            risk, advice = "Extreme", "Total saturation. Trail damage likely. Recommend Go/No-Go re-evaluation."

        # 6. Tactical Intel Output
        now = datetime.now(timezone.utc)
        return {
            "status": "Success",
            "environmental_context": {
                "raw_rain_72h": f"{total_raw_rain:.1f}mm",
                "avg_temp": f"{avg_temp:.1f}°C",
                "drying_efficiency": f"{drying_efficiency:.2f}x",
                "shadow_penalty_active": "Yes" if shadow_penalty < 1.0 else "No",
                "solar_altitude": f"{get_altitude(lat, lon, now):.1f}°"
            },
            "tactical_analysis": {
                "adjusted_moisture_index": round(adjusted_rain, 2),
                "mud_risk_score": risk,
                "surface_detected": surface_type,
                "safety_advice": advice
            }
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": f"Telemetry failure: {str(e)}",
            "mud_risk_score": "Unknown"
        }