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

import math
import requests
import zoneinfo
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta, timezone
from astral import Observer
from astral.sun import elevation
from typing import Literal, Dict, Any

# Open-Meteo API Endpoints
ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive'
FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'

def get_solar_altitude(lat: float, lon: float, current_dt: datetime) -> float:
    try:
        observer = Observer(latitude=lat, longitude=lon)
        solar_angle = elevation(observer, current_dt)
        return round(solar_angle, 2)
    except Exception:
        return 0.0

def get_mud_risk_analysis(
        lat: float,
        lon: float,
        surface_type: Literal["asphalt", "sand", "gravel", "grass", "dirt", "earth", "clay"] = "dirt",
        target_date: str = None) -> Dict[str, Any]:
    """
    Tactical Mud Risk Analysis v3.3: Time-Step Reservoir Model TAEL©.

    This engine simulates ground saturation by tracking moisture via an hourly recursive formula:
    Mt = Mt-1 * e^(-k * Dt) + Rt

    It accounts for local timezones, solar-driven evaporation (via Astral),
    and non-linear soil sensitivities.
    """
    try:
        # --- 1. Temporal & Timezone Localization ---
        # Detect local timezone based on coordinates to ensure solar precision
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        local_tz = zoneinfo.ZoneInfo(tz_name)

        # Establish the tactical reference point (localized)
        if target_date:
            # Parse target date and treat it as the start of the day in local time
            reference_date = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=local_tz)
        else:
            reference_date = datetime.now(local_tz)

        # Set a 72-hour look-back window for deep soil saturation context
        end_date = reference_date
        start_date = end_date - timedelta(hours=72)

        # Determine if we need Forecast or Historical data
        is_predictive = reference_date > datetime.now(local_tz)
        # Note: Ensure FORECAST_URL and ARCHIVE_URL are defined in your scope
        url = FORECAST_URL if is_predictive else ARCHIVE_URL

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": ["precipitation", "temperature_2m", "wind_speed_10m", "cloudcover"],
            "timezone": tz_name  # Request API data aligned with local time
        }

        # --- 2. Data Acquisition ---
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get('hourly', {})

        times = data.get('time', [])
        precips = data.get('precipitation', [])
        temps = data.get('temperature_2m', [])
        winds = data.get('wind_speed_10m', [])
        clouds = data.get('cloudcover', [])

        if not times:
            raise ValueError("No hourly weather data returned from API.")

        # --- 3. Reservoir State Machine Setup ---
        # Drainage coefficients (k): higher values represent superior permeability
        soil_k_matrix = {
            "asphalt": 0.50,
            "sand": 0.30,
            "gravel": 0.15,
            "grass": 0.10,
            "dirt": 0.08,
            "earth": 0.08,
            "clay": 0.04  # Prone to saturation and "clumping"
        }
        base_k = soil_k_matrix.get(surface_type.lower(), 0.08)

        # Initialize the reservoir with seasonal memory before processing hourly rain
        M = _get_seasonal_saturation_bias(reference_date, lat)
        pet_hours = 0         # Hours with significant solar drying potential
        total_raw_rain = 0.0  # Cumulative 72h precipitation
        recent_rain_12h = 0.0 # Recent rain impacting top-layer traction
        recent_dt_sum = 0.0   # Rolling sum of drying potential for ETA projection

        # --- 4. Hourly Integration Loop ---
        for i in range(len(times)):
            # Convert API time string to a timezone-aware datetime object
            current_dt = datetime.fromisoformat(times[i]).replace(tzinfo=local_tz)

            # Strict window adherence
            if current_dt < start_date or current_dt > end_date:
                continue

            rain = float(precips[i] or 0.0)
            temp = float(temps[i] or 0.0)
            wind = float(winds[i] or 0.0)
            cloud = float(clouds[i] or 0.0)

            total_raw_rain += rain
            time_diff = (end_date - current_dt).total_seconds()

            if time_diff <= (12 * 3600):
                recent_rain_12h += rain

            # A. Solar Engine (Astral Precision)
            # Calculate solar altitude for UV-based evaporation assessment
            solar_alt = get_solar_altitude(lat, lon, current_dt)

            # B. Drying Potential (Dt) Calculation
            temp_factor = max(0.01, (temp / 20.0))
            wind_factor = max(0.5, (wind / 15.0))

            # Solar drying is active when Sun > 20°, attenuated by cloud cover
            solar_factor = 1.0
            if solar_alt > 20:
                solar_factor += ((solar_alt / 90.0) * (1.0 - (cloud / 100.0)))
                pet_hours += 1

            Dt = temp_factor * wind_factor * solar_factor

            # Track recent drying trend for ETA simulation
            if time_diff <= (24 * 3600):
                recent_dt_sum += Dt

            # C. Non-Linear Soil Sensitivity
            current_k = base_k
            if surface_type.lower() == "clay" and M > 12.0:
                # Saturated clay seals up, losing drainage efficiency
                current_k *= 0.3

            # D. Recursive Moisture Update
            # Moisture = (Previous Moisture * Decay) + New Rainfall
            M = (M * math.exp(-current_k * Dt)) + rain

        # --- 5. Dry-Time ETA Simulation ---
        # Project hours needed to reach 'Optimal' status (< 2.0mm moisture)
        dry_threshold = 2.0
        eta_hours = 0
        avg_recent_Dt = max(0.1, (recent_dt_sum / 24.0))

        sim_M = M
        while sim_M > dry_threshold and eta_hours < 96:
            iter_k = base_k * 0.3 if (surface_type.lower() == "clay" and sim_M > 12.0) else base_k
            sim_M = sim_M * math.exp(-iter_k * avg_recent_Dt)
            eta_hours += 1

        # --- 6. Risk Categorization ---
        # Traction Risk (Surface "Greasiness")
        traction_index = (recent_rain_12h * 1.5) + (M * 0.5)
        if traction_index < 2.0:
            traction_risk, traction_advice = "Low", "Maximum grip. Surface is hardpack."
        elif traction_index < 6.0:
            traction_risk, traction_advice = "Medium", "Greasy top layer. Watch off-cambers."
        else:
            traction_risk, traction_advice = "High", "Zero traction. Tires will pack instantly."

        # Trail Damage Risk (Structural Integrity)
        if M < 4.0:
            damage_risk, damage_advice = "Low", "Trail structure is solid."
        elif M < 15.0:
            damage_risk, damage_advice = "Medium", "Sub-surface is soft. Rutting possible."
        else:
            damage_risk, damage_advice = "Extreme", "DO NOT RIDE. Structural damage likely."

        if M < 4.0:
            global_label = "Low"
        elif M < 12.0:
            global_label = "Medium"
        elif M < 20.0:
            global_label = "High"
        else:
            global_label = "Extreme"

        # --- 7. Final Payload Assembly ---
        return {
            "status": "Success",
            "metadata": {
                "target_date": reference_date.isoformat(),
                "timezone": tz_name,
                "is_predictive": is_predictive,
                "model": "TAEL© v3.2"
            },
            "environmental_context": {
                "total_rain_72h_mm": round(total_raw_rain, 1),
                "integrated_pet_hours": pet_hours,
                "reservoir_moisture_mm": round(M, 2)
            },
            "tactical_analysis": {
                "surface_type": surface_type,
                "mud_risk_numeric": round(M, 2),
                "mud_risk_score": global_label,
                "traction_risk": {"level": traction_risk, "advice": traction_advice},
                "trail_damage_risk": {"level": damage_risk, "advice": damage_advice},
                "dry_time_eta": f"{eta_hours} hours" if eta_hours > 0 else "Ready Now"
            }
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": f"Tactical Planner failure: {str(e)}",
            "tactical_analysis": None
        }
def _get_seasonal_saturation_bias(reference_date: datetime, lat: float) -> float:
    """
    Calculates the initial soil moisture baseline (M_initial) based on
    seasonal cycles and hemispheric location.

    This prevents the 'amnesia effect' where the model assumes perfectly
    dry soil (M=0.0) at the start of a 72h window, even in wet seasons.
    """
    month = reference_date.month
    is_northern_hemisphere = lat >= 0

    # Baseline saturation values in mm (Reservoir Moisture)
    # High values (15-20) represent saturated/winter soils.
    # Low values (0-2) represent dry/summer soils.
    if is_northern_hemisphere:
        seasonal_map = {
            12: 18.0, 1: 20.0, 2: 18.0,  # Winter: High saturation/Frozen potential
            3: 12.0, 4: 8.0, 5: 4.0,     # Spring: Thaw and progressive drying
            6: 1.0, 7: 0.0, 8: 0.0,      # Summer: Arid/Baked soil
            9: 2.0, 10: 6.0, 11: 14.0    # Autumn: Cumulative rainfall and low evapotranspiration
        }
    else:
        # Southern Hemisphere (Inverted seasons)
        seasonal_map = {
            6: 18.0, 7: 20.0, 8: 18.0,
            9: 12.0, 10: 8.0, 11: 4.0,
            12: 1.0, 1: 0.0, 2: 0.0,
            3: 2.0, 4: 6.0, 5: 14.0
        }

    return float(seasonal_map.get(month, 0.0))