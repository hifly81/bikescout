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

"""Deterministic, evidence-labelled fueling and hydration estimates.

The published ranges below set the bounds of the planning heuristics; they are
not a clinical prescription. An individual sweat-rate measurement always
replaces the population fluid estimate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

NUTRITION_REFERENCES: tuple[str, ...] = (
    "ACSM Position Stand: Nutrition and Athletic Performance (2009), MSSE 41(3):709-731: "
    "30-60 g carbohydrate/h, up to 90 g/h in prolonged events with multiple "
    "transportable carbohydrates.",
    "ACSM Position Stand: Exercise and Fluid Replacement (2007), MSSE 39(2):377-390: "
    "initial fluid plan 400-800 ml/h, adjusted to the individual sweat rate.",
    "Maughan & Shirreffs (2008) and Baker et al. (2019) sweat-composition data: "
    "sweat sodium concentration spans roughly 460-1840 mg/L.",
)


@dataclass(frozen=True)
class NutritionConfig:
    default_weight_kg: float = 70.0
    default_gender: str = "male"
    default_sweat_profile: str = "standard"
    default_intensity_score: int = 2
    default_duration_hours: float = 1.0
    default_temp_c: float = 20.0
    # Gender alone is not a supported basis for sweat-rate differences; the
    # rider can supply a measured rate instead. The factor is kept at 1.0.
    male_gender_factor: float = 1.0
    non_male_gender_factor: float = 1.0
    sweat_rate_multiplier: float = 1.0
    estimated_fluid_min_ml_per_hour: float = 400.0
    estimated_fluid_max_ml_per_hour: float = 800.0


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
        sweat_rate_ml_per_hour: float | None = None,
        relative_humidity_pct: float | None = None,
        temperature_basis: Literal[
            "ride_window", "daily_max", "manual", "reference_fallback", "default"
        ] = "ride_window",
    ) -> dict[str, Any]:
        """Build a fueling plan, or report invalid inputs as an Error payload."""
        try:
            duration_hours = self._require_number("duration_hours", duration_hours, 0.1, 24.0)
            temp_c = self._require_number("temp_c", temp_c, -40.0, 60.0)
            intensity_score = self._require_int("intensity_score", intensity_score, 1, 5)
            weight_kg = self._require_number("weight_kg", weight_kg, 20.0, 250.0)
            gender = self._require_choice(
                "gender", gender, ("male", "female"), self.config.default_gender
            )
            normalized_profile = self._require_choice(
                "sweat_profile",
                sweat_profile,
                ("low", "standard", "high", "extreme"),
                self.config.default_sweat_profile,
            )
            normalized_basis = self._require_choice(
                "temperature_basis",
                temperature_basis,
                ("ride_window", "daily_max", "manual", "reference_fallback", "default"),
                "ride_window",
            )
            sweat_rate = (
                self._require_number(
                    "sweat_rate_ml_per_hour", sweat_rate_ml_per_hour, 100.0, 5000.0
                )
                if sweat_rate_ml_per_hour is not None
                else None
            )
            humidity = (
                self._require_number("relative_humidity_pct", relative_humidity_pct, 0.0, 100.0)
                if relative_humidity_pct is not None
                else None
            )
        except ValueError as exc:
            return {"status": "Error", "error_message": str(exc)}

        gender_factor = (
            self.config.male_gender_factor
            if gender == "male"
            else self.config.non_male_gender_factor
        )
        intensity_factor = self._intensity_factor(intensity_score)

        estimated_fluid_ml = self._avg_hourly_fluid_ml(
            duration_hours=duration_hours,
            temp_c=temp_c,
            intensity_factor=intensity_factor,
            weight_kg=weight_kg,
            gender_factor=gender_factor,
        )
        sweat_rate_source = "measured" if sweat_rate is not None else "estimated"
        if sweat_rate is None:
            avg_hourly_fluid = min(
                max(estimated_fluid_ml, self.config.estimated_fluid_min_ml_per_hour),
                self.config.estimated_fluid_max_ml_per_hour,
            )
        else:
            avg_hourly_fluid = sweat_rate
        total_fluid_l = (avg_hourly_fluid * duration_hours) / 1000.0

        carb_rate, intensity_label = self._carb_rate_and_label(duration_hours, intensity_factor)
        total_carbs = carb_rate * duration_hours
        ratios = (
            "2:1 Glucose-to-Fructose (or 1:0.8 ratio)"
            if carb_rate > 60
            else "Standard isotonic or whole foods"
        )

        sodium_concentration = self._sodium_concentration(normalized_profile)
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
            estimated_fluid_ml=estimated_fluid_ml,
            humidity_pct=humidity,
            sweat_rate_ml_per_hour=sweat_rate,
            temperature_basis=normalized_basis,
        )

        if sweat_rate is not None:
            basis = (
                "Fluid target from a rider-provided measured sweat rate. Carbohydrate tiers "
                "follow published 30-90 g/h ranges; sodium uses the self-reported sweat profile."
            )
            confidence = "moderate"
            uncertainty = (
                "Fluid target reflects the measured sweat rate; sodium concentration remains "
                "self-reported and is not a clinical prescription."
            )
        else:
            basis = (
                "Fluid target is a population estimate from rider mass, air temperature and "
                "intensity, bounded to the published "
                f"{self.config.estimated_fluid_min_ml_per_hour:g}-"
                f"{self.config.estimated_fluid_max_ml_per_hour:g} ml/h planning range. "
                "Carbohydrate tiers follow published 30-90 g/h ranges; sodium uses the "
                "self-reported sweat profile."
            )
            confidence = "low"
            uncertainty = (
                "No measured sweat rate: fluid target is a population estimate; sodium profile "
                "is self-reported. Validate with a timed weigh-in before an event."
            )
        if normalized_basis != "ride_window":
            uncertainty += (
                f" Temperature basis is '{normalized_basis}', not the ride window; "
                "heat exposure may be overstated."
            )
        if humidity is not None:
            uncertainty += (
                f" Relative humidity ({humidity:g}%) is reported but does not change the "
                "fluid target."
            )

        inputs_used: dict[str, Any] = {
            "duration_hours": duration_hours,
            "temp_c": temp_c,
            "temperature_basis": normalized_basis,
            "intensity_score": intensity_score,
            "weight_kg": weight_kg,
            "gender": gender,
            "sweat_profile": normalized_profile,
            "sweat_rate_ml_per_hour": sweat_rate,
            "sweat_rate_source": sweat_rate_source,
            "relative_humidity_pct": humidity,
        }

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
                "data_basis": basis,
                "estimate_confidence": confidence,
                "uncertainty_note": uncertainty,
                "inputs_used": inputs_used,
                "references": list(NUTRITION_REFERENCES),
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
            (base_rate_mass + temp_delta_coeff + intensity_heat_coeff)
            * gender_factor
            * self.config.sweat_rate_multiplier
        )

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
        return intensity_map[intensity_score]

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
        return sodium_profile_map[sweat_profile]

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
        estimated_fluid_ml: float,
        humidity_pct: float | None = None,
        sweat_rate_ml_per_hour: float | None = None,
        temperature_basis: str = "ride_window",
    ) -> list[str]:
        alerts: list[str] = []

        if carb_rate > 60:
            alerts.append(
                f"FUELING ALERT: High target ({carb_rate}g/hr). Use {ratios} to prevent GI distress."
            )

        if temp_c > 28:
            alerts.append(
                "HEAT STRESS: Prioritize liquid carbs and increase electrolyte vigilance."
            )

        if duration_hours > 2.5 and intensity_factor >= 0.85:
            alerts.append(
                "BONK RISK: Prolonged high intensity. Maintain feeding window to avoid glycogen crash."
            )

        if hourly_sodium_mg >= 1000:
            alerts.append(
                f"ELECTROLYTE CRITICAL: High loss ({int(hourly_sodium_mg)}mg/hr). Supplement bottles with salt."
            )

        if total_fluid_l > (weight_kg * 0.02 * duration_hours):
            alerts.append(
                "HYPER-HYDRATION RISK: Fluid targets are high relative to mass. Ensure sodium balance."
            )

        if sweat_rate_ml_per_hour is None and estimated_fluid_ml > 800:
            alerts.append(
                "FLUID CEILING: Population estimate exceeds 800 ml/h. Confirm with a timed "
                "weigh-in before raising the target."
            )
        if sweat_rate_ml_per_hour is not None and sweat_rate_ml_per_hour > 2500:
            alerts.append(
                "SWEAT CHECK: Measured rate above 2.5 L/h. Verify the weigh-in and seek "
                "medical advice if confirmed."
            )
        if humidity_pct is not None and temp_c >= 24 and humidity_pct >= 60:
            alerts.append(
                "HUMIDITY LOAD: Hot and humid conditions raise heat strain. No humidity-specific "
                "volume adjustment is applied; calibrate with thirst and a post-ride weigh-in."
            )
        if temperature_basis == "daily_max":
            alerts.append(
                "TEMPERATURE CONTEXT: Daily peak temperature used; ride-window heat may be lower."
            )

        return alerts

    @staticmethod
    def _require_number(name: str, value: Any, minimum: float, maximum: float) -> float:
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a number between {minimum:g} and {maximum:g}.")
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{name} must be a number between {minimum:g} and {maximum:g}."
            ) from None
        if not math.isfinite(parsed) or not minimum <= parsed <= maximum:
            raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}; got {value!r}.")
        return parsed

    @staticmethod
    def _require_int(name: str, value: Any, minimum: int, maximum: int) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{name} must be an integer between {minimum} and {maximum}.")
        try:
            parsed_float = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{name} must be an integer between {minimum} and {maximum}."
            ) from None
        if not math.isfinite(parsed_float) or not parsed_float.is_integer():
            raise ValueError(f"{name} must be an integer between {minimum} and {maximum}.")
        parsed = int(parsed_float)
        if not minimum <= parsed <= maximum:
            raise ValueError(f"{name} must be between {minimum} and {maximum}; got {value!r}.")
        return parsed

    @staticmethod
    def _require_choice(name: str, value: Any, allowed: tuple[str, ...], default: str) -> str:
        if value is None or (isinstance(value, str) and not value.strip()):
            return default
        normalized = str(value).strip().lower()
        if normalized not in allowed:
            choices = ", ".join(allowed)
            raise ValueError(f"{name} must be one of {choices}; got {value!r}.")
        return normalized


service = NutritionService()


def get_nutrition_plan(
    duration_hours: float,
    temp_c: float,
    intensity_score: int,
    weight_kg: float = 70.0,
    gender: str = "male",
    sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
    sweat_rate_ml_per_hour: float | None = None,
    relative_humidity_pct: float | None = None,
    temperature_basis: Literal[
        "ride_window", "daily_max", "manual", "reference_fallback", "default"
    ] = "ride_window",
) -> dict[str, Any]:
    return service.get_nutrition_plan(
        duration_hours=duration_hours,
        temp_c=temp_c,
        intensity_score=intensity_score,
        weight_kg=weight_kg,
        gender=gender,
        sweat_profile=sweat_profile,
        sweat_rate_ml_per_hour=sweat_rate_ml_per_hour,
        relative_humidity_pct=relative_humidity_pct,
        temperature_basis=temperature_basis,
    )
