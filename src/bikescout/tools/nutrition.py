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

def get_nutrition_plan(duration_hours: float, temp_c: float, intensity_score: int, weight_kg: float = 70.0, gender: str = "male"):
    """
    Nutrition & Hydration Logic
    Correlates Glycogen Depletion with Thermoregulatory Strain to provide pro-grade
    fueling intelligence based on Intensity Factor (IF), Heat Stress, and Duration.
    """

    gender_factor = 1.0 if gender.lower() == "male" else 0.85

    # --- 1. Intensity Normalization (The "Human Engine" Map) ---
    # Maps the orchestrator's 1-5 scale into a standardized Intensity Factor (IF)
    intensity_map = {
        1: 0.60,  # Z1 / Active Recovery
        2: 0.75,  # Z2 / Endurance
        3: 0.85,  # Z3 / Tempo / Sweet Spot
        4: 0.95,  # Z4 / Threshold
        5: 1.05   # Z5 / VO2 Max / Race Day
    }
    # Fallback to Z2 if out of bounds
    intensity_factor = intensity_map.get(intensity_score, 0.75)

    # --- 2. Continuous Hydration & Sweat Rate Modeling ---
    # Replaces the step-function with a continuous linear equation.
    # Base fluid + Temp coefficient (+30ml per degree > 15C) + Intensity kinetic heat.
    base_rate = weight_kg * 10
    temp_coeff = max(0, temp_c - 15) * (weight_kg * 0.4)
    intensity_coeff = intensity_factor * (weight_kg * 4)

    hourly_fluid = (base_rate + temp_coeff + intensity_coeff) * gender_factor
    total_fluid = (hourly_fluid * duration_hours) / 1000 # Convert to Liters

    # --- 3. Advanced Carbohydrate Optimization ---
    # Base carbohydrate demand scales dynamically with Intensity Factor
    if intensity_factor >= 0.95:      # High intensity
        carb_rate = 90
        intensity_label = "Race / Threshold"
    elif intensity_factor >= 0.85:    # Moderate/Tempo intensity
        carb_rate = 60
        intensity_label = "Tempo"
    else:                             # Low intensity
        carb_rate = 40
        intensity_label = "Endurance / Recovery"

    # Duration multiplier: Long, demanding rides drastically increase glycogen burn
    if duration_hours > 3.0 and intensity_factor >= 0.85:
        carb_rate += 30 # Push towards 90g or 120g/hr for extreme attrition

    # Cap at human absolute limit for gut absorption
    carb_rate = min(120, carb_rate)
    total_carbs = carb_rate * duration_hours

    # Dual-Source Gut Logic
    ratios = "Standard isotonic or whole foods"
    if carb_rate > 60:
        ratios = "2:1 Glucose-to-Fructose (or 1:0.8 ratio)"

    # --- 4. Electrolyte (Sodium) Estimation ---
    # Typical physiological loss is ~800mg per liter of sweat.
    # We estimate sweat loss tightly matches the calculated fluid demand.
    sodium_mg_per_liter = 800
    hourly_sodium = (hourly_fluid / 1000) * sodium_mg_per_liter
    total_sodium = hourly_sodium * duration_hours

    # --- 5. Tactical "Low-Tank" Warnings ---
    alerts = []

    if carb_rate > 60:
        alerts.append(f"FUELING ALERT: High target ({carb_rate}g/hr). Use a {ratios} mix to prevent GI distress. Gut training required.")

    if temp_c > 28:
        alerts.append("HEAT STRESS RISK: High core temp expected. Prioritize liquid carbs over solids and consider active pre-cooling.")

    if duration_hours > 2.5 and intensity_factor >= 0.85:
        alerts.append("BONK RISK: High intensity over prolonged duration. Missing a single feeding window will cause catastrophic glycogen depletion.")

    if hourly_sodium >= 800:
        alerts.append(f"ELECTROLYTE CRITICAL: High sodium output detected. Add {round(hourly_sodium)}mg/hr directly to your bottles to prevent cramping.")

    if total_fluid > (weight_kg * 0.03 * duration_hours):
        alerts.append(f"HYPER-HYDRATION RISK: Fluid targets are high relative to body mass. Sip steadily and ensure sodium intake matches targets to avoid hyponatremia.")

    return {
        "status": "Success",
        "mission_nutrition_briefing": {
            "fluids": {
                "total_liters": round(total_fluid, 1),
                "hourly_rate_ml": int(hourly_fluid)
            },
            "carbohydrates": {
                "total_grams": int(total_carbs),
                "hourly_target_g": carb_rate,
                "recommended_ratio": ratios,
                "intensity_context": intensity_label
            },
            "electrolytes": {
                "total_sodium_mg": int(total_sodium),
                "hourly_sodium_mg": int(hourly_sodium)
            },
            "tactical_advice": alerts
        }
    }
