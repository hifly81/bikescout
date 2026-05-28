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

from typing import Literal

def get_nutrition_plan(
        duration_hours: float,
        temp_c: float,
        intensity_score: int,
        weight_kg: float = 70.0,
        gender: str = "male",
        sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard"
):
    """
    Tactical Nutrition & Hydration Engine

    Correlates Glycogen Depletion with Thermoregulatory Strain using weight-scaled
    sweat modeling, dynamic sodium profiling, and non-linear thermal ramp-up.

    Key Features:
        - Body Mass Scaling: Adjusts fluid and thermal load based on rider weight.
        - Thermal Drift Logic: Simulates the physiological ramp-up of sweat rates over time.
        - Genetic Sodium Profiling: Supports variance from 400mg to 1800mg/L of sweat.
        - Individual Tuning: Customizable via sweat_rate_multiplier for personal baseline adjustments.
    """

    # --- 1. Physiological Factors & Intensity Normalization ---
    # Gender factor accounts for variance in plasma volume and sweat gland density
    gender_factor = 1.0 if gender.lower() == "male" else 0.85
    sweat_rate_multiplier = 1.0

    # Intensity Factor (IF) mapping from 1-5 tactical scale
    intensity_map = {
        1: 0.60,  # Z1 / Active Recovery
        2: 0.75,  # Z2 / Endurance
        3: 0.85,  # Z3 / Tempo / Sweet Spot
        4: 0.95,  # Z4 / Threshold
        5: 1.05   # Z5 / VO2 Max / Race Day
    }
    intensity_factor = intensity_map.get(intensity_score, 0.75)

    # --- 2. Dynamic Hydration & Sweat Rate Modeling ---
    # Steady-state sweat rate based on body mass (ml/kg/hr)
    # Base metabolism + Temperature delta + Intensity kinetic heat
    base_rate_mass = weight_kg * 10
    temp_delta_coeff = max(0, temp_c - 15) * (weight_kg * 0.4)
    intensity_heat_coeff = intensity_factor * (weight_kg * 4)

    steady_state_hourly_ml = (base_rate_mass + temp_delta_coeff + intensity_heat_coeff) * \
                             gender_factor * sweat_rate_multiplier

    # Thermal Ramp-up Logic:
    # Sweat rate is not constant; it increases as core temp rises (thermal drift).
    # We estimate 75% of steady state for the first hour, 100% thereafter.
    if duration_hours <= 1.0:
        avg_hourly_fluid = steady_state_hourly_ml * 0.75
    else:
        total_vol = (steady_state_hourly_ml * 0.75 * 1.0) + \
                    (steady_state_hourly_ml * (duration_hours - 1.0))
        avg_hourly_fluid = total_vol / duration_hours

    total_fluid_l = (avg_hourly_fluid * duration_hours) / 1000

    # --- 3. Advanced Carbohydrate Optimization ---
    # Base fueling rates scaled by metabolic demand
    if intensity_factor >= 0.95:
        carb_rate = 90
        intensity_label = "Race / Threshold"
    elif intensity_factor >= 0.85:
        carb_rate = 60
        intensity_label = "Tempo"
    else:
        carb_rate = 40
        intensity_label = "Endurance / Recovery"

    # Duration Attrition: Extreme rides increase dependence on exogenous glucose
    if duration_hours > 3.0 and intensity_factor >= 0.85:
        carb_rate += 30

    # Human physiological absorption ceiling (Gut limit)
    carb_rate = min(120, carb_rate)
    total_carbs = carb_rate * duration_hours

    # Dual-Source Gut Logic for high-carb oxidation
    ratios = "Standard isotonic or whole foods"
    if carb_rate > 60:
        ratios = "2:1 Glucose-to-Fructose (or 1:0.8 ratio)"

    # --- 4. Individualized Electrolyte (Sodium) Profiling ---
    # Mapping genetic variance in sweat sodium concentration
    sodium_profile_map = {
        "low": 400,      # Diluted sweat
        "standard": 800, # Population mean
        "high": 1200,    # Salty sweater (noticeable salt crusts)
        "extreme": 1800  # Genetic outlier / Heavy loser
    }
    sodium_concentration = sodium_profile_map.get(sweat_profile.lower(), 800)

    # Sodium loss is tied to total fluid volume lost
    hourly_sodium_mg = (avg_hourly_fluid / 1000) * sodium_concentration
    total_sodium_mg = hourly_sodium_mg * duration_hours

    # --- 5. Tactical Intelligence & Safety Alerts ---
    alerts = []

    if carb_rate > 60:
        alerts.append(f"FUELING ALERT: High target ({carb_rate}g/hr). Use {ratios} to prevent GI distress.")

    if temp_c > 28:
        alerts.append("HEAT STRESS: Prioritize liquid carbs and increase electrolyte vigilance.")

    if duration_hours > 2.5 and intensity_factor >= 0.85:
        alerts.append("BONK RISK: Prolonged high intensity. Maintain feeding window to avoid glycogen crash.")

    if hourly_sodium_mg >= 1000:
        alerts.append(f"ELECTROLYTE CRITICAL: High loss ({int(hourly_sodium_mg)}mg/hr). Supplement bottles with salt.")

    if total_fluid_l > (weight_kg * 0.02 * duration_hours):
        alerts.append("HYPER-HYDRATION RISK: Fluid targets are high relative to mass. Ensure sodium balance.")

    return {
        "status": "Success",
        "mission_nutrition_briefing": {
            "fluids": {
                "total_liters": round(total_fluid_l, 1),
                "hourly_average_ml": int(avg_hourly_fluid)
            },
            "carbohydrates": {
                "total_grams": int(total_carbs),
                "hourly_target_g": carb_rate,
                "recommended_ratio": ratios,
                "intensity_context": intensity_label
            },
            "electrolytes": {
                "total_sodium_mg": int(total_sodium_mg),
                "hourly_sodium_mg": int(hourly_sodium_mg)
            },
            "tactical_advice": alerts
        }
    }
