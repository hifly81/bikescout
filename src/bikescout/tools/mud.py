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

from datetime import datetime, timedelta, timezone
from pysolar.solar import get_altitude
from typing import Literal, Dict, Any
import requests
import math

# Open-Meteo API Endpoints
ARCHIVE_URL = 'https://archive-api.open-meteo.com/v1/archive'
FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'

def get_mud_risk_analysis(
        lat: float,
        lon: float,
        surface_type: Literal["asphalt", "sand", "gravel", "grass", "dirt", "earth", "clay"] = "dirt",
        target_date: str = None) -> Dict[str, Any]:
    """
    Tactical Mud Risk Analysis v3.0: Time-Step Reservoir Model (TAEL).

    This engine simulates ground saturation by tracking moisture via an hourly recursive formula:
    Mt = Mt-1 * e^(-k * Dt) + Rt

    It accounts for Temporal Aliasing, Time-Integrated Solar Energy (PET hours),
    and non-linear soil sensitivities (e.g., clay clumping).
    """
    try:
        # --- 1. Temporal Window Logic ---
        if target_date:
            reference_date = datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            reference_date = datetime.now(timezone.utc)

        # 72-hour look-back window for building the "Reservoir"
        end_date = reference_date
        start_date = end_date - timedelta(hours=72)

        # Determine API to use (Forecast for future, Archive for past)
        # Open-Meteo standardizes on YYYY-MM-DD strings for hourly bounds
        is_predictive = reference_date > datetime.now(timezone.utc)
        url = FORECAST_URL if is_predictive else ARCHIVE_URL

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": ["precipitation", "temperature_2m", "wind_speed_10m", "cloudcover"],
            "timezone": "UTC"
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

        # --- 3. The Reservoir State Machine Setup ---
        # Base drainage constants (k) - higher means faster drainage/drying
        soil_k_matrix = {
            "asphalt": 0.50,
            "sand": 0.30,
            "gravel": 0.15,
            "grass": 0.10,
            "dirt": 0.08,
            "earth": 0.08,
            "clay": 0.04
        }
        base_k = soil_k_matrix.get(surface_type.lower(), 0.08)

        # State variables
        M = 0.0  # Ground reservoir moisture (mm equivalent)
        pet_hours = 0  # Potential Evapotranspiration hours (Sun > 20°)
        total_raw_rain = 0.0
        recent_rain_12h = 0.0
        recent_dt_sum = 0.0 # Used for forward-simulating the Dry-Time ETA

        # --- 4. Hourly Integration Loop ---
        for i in range(len(times)):
            # Parse current hour string to datetime
            current_dt = datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc)

            # Skip dates outside our exact 72h window if API returned extra days
            if current_dt < start_date or current_dt > end_date:
                continue

            rain = precips[i] if precips[i] else 0.0
            temp = temps[i] if temps[i] else 0.0
            wind = winds[i] if winds[i] else 0.0
            cloud = clouds[i] if clouds[i] else 0.0

            total_raw_rain += rain
            if (end_date - current_dt).total_seconds() <= (12 * 3600):
                recent_rain_12h += rain

            # A. Time-Integrated Solar Engine
            # Calculate exact sun altitude for this specific hour
            solar_alt = get_altitude(lat, lon, current_dt)

            # B. Calculate Drying Potential (Dt)
            # Temp factor: Approaches 0 below freezing, scales up with heat
            temp_factor = max(0.01, (temp / 20.0))
            # Wind factor: Base drying + wind kinetic energy
            wind_factor = max(0.5, (wind / 15.0))

            # Solar factor: Active only when sun is > 20°, mitigated by cloud cover
            solar_factor = 1.0
            if solar_alt > 20:
                solar_factor += ((solar_alt / 90.0) * (1.0 - (cloud / 100.0)))
                pet_hours += 1

            Dt = temp_factor * wind_factor * solar_factor

            # Store recent Dt to project future drying ETA
            if (end_date - current_dt).total_seconds() <= (24 * 3600):
                recent_dt_sum += Dt

            # C. Non-Linear Soil Sensitivity (Clay Clumping)
            current_k = base_k
            if surface_type.lower() == "clay" and M > 12.0:
                # Clay loses 70% of its drainage efficiency once heavily saturated
                current_k *= 0.3

                # D. The Recursive Reservoir Formula
            # Mt = Mt-1 * e^(-k * Dt) + Rt
            M = (M * math.exp(-current_k * Dt)) + rain

        # --- 5. Dry-Time ETA Simulation ---
        # Simulate how many hours it will take for the reservoir to drop below 'Optimal'
        dry_threshold = 2.0
        eta_hours = 0
        avg_recent_Dt = max(0.1, (recent_dt_sum / 24.0)) # Average drying potential of the last 24h

        sim_M = M
        sim_k = base_k
        while sim_M > dry_threshold and eta_hours < 96: # Cap simulation at 4 days
            # Apply same clay clumping logic to simulation
            iter_k = sim_k * 0.3 if (surface_type.lower() == "clay" and sim_M > 12.0) else sim_k
            sim_M = sim_M * math.exp(-iter_k * avg_recent_Dt)
            eta_hours += 1

        # --- 6. Dual-Risk Categorization ---
        # Traction Risk: heavily biased by immediate surface conditions (recent rain + total moisture)
        traction_index = (recent_rain_12h * 1.5) + (M * 0.5)
        if traction_index < 2.0:
            traction_risk = "Low"
            traction_advice = "Maximum grip. Surface is hardpack and fast."
        elif traction_index < 6.0:
            traction_risk = "Medium"
            traction_advice = "Greasy top layer. Watch front wheel washout on off-cambers."
        else:
            traction_risk = "High"
            traction_advice = "Zero traction. Surface is slick; tires will pack with mud instantly."

        # Trail Damage Risk: purely based on deep reservoir saturation
        if M < 4.0:
            damage_risk = "Low"
            damage_advice = "Trail structure is solid. No rutting expected."
        elif M < 15.0:
            damage_risk = "Medium"
            damage_advice = "Sub-surface is soft. Heavy braking will cause braking bumps and shallow ruts."
        else:
            damage_risk = "Extreme"
            damage_advice = "DO NOT RIDE. Trail is structurally compromised. Riding will cause deep, permanent trenching."

        # --- 7. Payload Assembly ---
        return {
            "status": "Success",
            "metadata": {
                "target_date": reference_date.isoformat(),
                "is_predictive": is_predictive,
                "model_version": "TAEL v3.0"
            },
            "environmental_context": {
                "total_rain_72h_mm": round(total_raw_rain, 1),
                "integrated_pet_hours": pet_hours,
                "reservoir_moisture_mm": round(M, 2)
            },
            "tactical_analysis": {
                "surface_type": surface_type,
                "traction_risk": {
                    "level": traction_risk,
                    "advice": traction_advice
                },
                "trail_damage_risk": {
                    "level": damage_risk,
                    "advice": damage_advice
                },
                "dry_time_eta": f"{eta_hours} hours" if eta_hours > 0 else "Ready Now"
            }
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": f"Telemetry failure: {str(e)}",
            "tactical_analysis": None
        }
