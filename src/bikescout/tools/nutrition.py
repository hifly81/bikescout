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

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class NutritionConfig:
    default_weight_kg: float = 70.0
    default_gender: str = "male"
    default_sweat_profile: str = "standard"
    default_intensity_score: int = 2
    default_duration_hours: float = 1.0
    default_temp_c: float = 20.0
    male_gender_factor: float = 1.0
    non_male_gender_factor: float = 0.85
    sweat_rate_multiplier: float = 1.0


class NutritionService:
    def __init__(self, config: NutritionConfig | None = None) -> None:
        self.config = config or NutritionConfig()

    def get_nutrition_plan(
            self,
            duration_hours: float,
            temp_c: float,
            intensity_score: int,
            weight_kg: float = 70.0,
            gender: str = "male",
            sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
    ):
        duration_hours = self._coerce_positive_float(duration_hours, self.config.default_duration_hours)
        temp_c = self._coerce_float(temp_c, self.config.default_temp_c)
        intensity_score = self._normalize_intensity_score(intensity_score)
        weight_kg = self._coerce_positive_float(weight_kg, self.config.default_weight_kg)
        gender = self._normalize_gender(gender)
        sweat_profile = self._normalize_sweat_profile(sweat_profile)

        gender_factor = self.config.male_gender_factor if gender == "male" else self.config.non_male_gender_factor
        intensity_factor = self._intensity_factor(intensity_score)

        avg_hourly_fluid = self._avg_hourly_fluid_ml(
            duration_hours=duration_hours,
            temp_c=temp_c,
            intensity_factor=intensity_factor,
            weight_kg=weight_kg,
            gender_factor=gender_factor,
        )
        total_fluid_l = (avg_hourly_fluid * duration_hours) / 1000.0

        carb_rate, intensity_label = self._carb_rate_and_label(duration_hours, intensity_factor)
        total_carbs = carb_rate * duration_hours
        ratios = "2:1 Glucose-to-Fructose (or 1:0.8 ratio)" if carb_rate > 60 else "Standard isotonic or whole foods"

        sodium_concentration = self._sodium_concentration(sweat_profile)
        hourly_sodium_mg = (avg_hourly_fluid / 1000.0) * sodium_concentration
        total_sodium_mg = hourly_sodium_mg * duration_hours

        alerts = self._build_alerts(
            carb_rate=carb_rate,
            ratios=ratios,
            temp_c=temp_c,
            duration_hours=duration_hours,
            intensity_factor=intensity_factor,
            hourly_sodium_mg=hourly_sodium_mg,
            total_fluid_l=total_fluid_l,
            weight_kg=weight_kg,
        )

        return {
            "status": "Success",
            "mission_nutrition_briefing": {
                "fluids": {
                    "total_liters": round(total_fluid_l, 1),
                    "hourly_average_ml": int(avg_hourly_fluid),
                },
                "carbohydrates": {
                    "total_grams": int(total_carbs),
                    "hourly_target_g": carb_rate,
                    "recommended_ratio": ratios,
                    "intensity_context": intensity_label,
                },
                "electrolytes": {
                    "total_sodium_mg": int(total_sodium_mg),
                    "hourly_sodium_mg": int(hourly_sodium_mg),
                },
                "tactical_advice": alerts,
            },
        }

    def _avg_hourly_fluid_ml(
            self,
            duration_hours: float,
            temp_c: float,
            intensity_factor: float,
            weight_kg: float,
            gender_factor: float,
    ) -> float:
        base_rate_mass = weight_kg * 10
        temp_delta_coeff = max(0.0, temp_c - 15.0) * (weight_kg * 0.4)
        intensity_heat_coeff = intensity_factor * (weight_kg * 4)

        steady_state_hourly_ml = (
                                         base_rate_mass + temp_delta_coeff + intensity_heat_coeff
                                 ) * gender_factor * self.config.sweat_rate_multiplier

        if duration_hours <= 1.0:
            return steady_state_hourly_ml * 0.75

        total_vol = (steady_state_hourly_ml * 0.75 * 1.0) + (
                steady_state_hourly_ml * (duration_hours - 1.0)
        )
        return total_vol / duration_hours

    @staticmethod
    def _intensity_factor(intensity_score: int) -> float:
        intensity_map = {
            1: 0.60,
            2: 0.75,
            3: 0.85,
            4: 0.95,
            5: 1.05,
        }
        return intensity_map.get(intensity_score, 0.75)

    @staticmethod
    def _carb_rate_and_label(duration_hours: float, intensity_factor: float) -> tuple[int, str]:
        if intensity_factor >= 0.95:
            carb_rate = 90
            intensity_label = "Race / Threshold"
        elif intensity_factor >= 0.85:
            carb_rate = 60
            intensity_label = "Tempo"
        else:
            carb_rate = 40
            intensity_label = "Endurance / Recovery"

        if duration_hours > 3.0 and intensity_factor >= 0.85:
            carb_rate += 30

        carb_rate = min(120, carb_rate)
        return carb_rate, intensity_label

    @staticmethod
    def _sodium_concentration(sweat_profile: str) -> int:
        sodium_profile_map = {
            "low": 400,
            "standard": 800,
            "high": 1200,
            "extreme": 1800,
        }
        return sodium_profile_map.get(sweat_profile.lower(), 800)

    @staticmethod
    def _build_alerts(
            carb_rate: int,
            ratios: str,
            temp_c: float,
            duration_hours: float,
            intensity_factor: float,
            hourly_sodium_mg: float,
            total_fluid_l: float,
            weight_kg: float,
    ) -> list[str]:
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

        return alerts

    def _normalize_gender(self, gender: Any) -> str:
        if not isinstance(gender, str) or not gender.strip():
            return self.config.default_gender
        return gender.strip().lower()

    def _normalize_sweat_profile(self, sweat_profile: Any) -> str:
        if not isinstance(sweat_profile, str) or not sweat_profile.strip():
            return self.config.default_sweat_profile
        return sweat_profile.strip().lower()

    def _normalize_intensity_score(self, intensity_score: Any) -> int:
        try:
            value = int(intensity_score)
        except (TypeError, ValueError):
            return self.config.default_intensity_score
        return max(1, min(value, 5))

    @staticmethod
    def _coerce_float(value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _coerce_positive_float(self, value: Any, fallback: float) -> float:
        parsed = self._coerce_float(value, fallback)
        return parsed if parsed > 0 else fallback


service = NutritionService()


def get_nutrition_plan(
        duration_hours: float,
        temp_c: float,
        intensity_score: int,
        weight_kg: float = 70.0,
        gender: str = "male",
        sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
):
    return service.get_nutrition_plan(
        duration_hours=duration_hours,
        temp_c=temp_c,
        intensity_score=intensity_score,
        weight_kg=weight_kg,
        gender=gender,
        sweat_profile=sweat_profile,
    )
