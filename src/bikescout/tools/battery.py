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

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BatteryConfig:
    usable_capacity_factor: float = 0.93
    cold_temp_threshold_c: float = 15.0
    cold_temp_penalty_per_degree: float = 0.01
    min_usable_capacity_factor: float = 0.10
    gravity: float = 9.81
    air_density: float = 1.225
    cda: float = 0.45
    default_speed_kmh: float = 18.0
    default_ambient_temp_c: float = 20.0
    default_rider_ftp_w: int = 200
    default_intensity_score: int = 3
    base_efficiency: float = 0.85
    steep_grade_threshold: float = 0.08
    steep_grade_efficiency_penalty: float = 0.10
    hot_temp_threshold_c: float = 30.0
    hot_temp_efficiency_penalty: float = 0.05
    default_surface_crr: float = 0.015
    unknown_surface_crr: float = 0.020
    mud_crr_penalty_factor: float = 0.05
    mud_normalization_max_mm: float = 20.0
    # Heuristic fallback when no hardware motor limit is provided.
    default_motor_power_limit_w: float = 250.0


class BatteryService:
    def __init__(self, config: BatteryConfig | None = None) -> None:
        self.config = config or BatteryConfig()

    def calculate_battery_drain(
        self,
        battery_wh: float,
        assist_level: str,
        weight_kg: float,
        ascent_m: float,
        distance_km: float,
        surface_breakdown: dict[str, Any] | list[dict[str, Any]] | None,
        mud_index: float,
        avg_speed_kmh: float = 18.0,
        ambient_temp_c: float = 20.0,
        rider_ftp_w: float = 200,
        intensity_score: int = 3,
        motor_power_limit_w: float | None = None,
    ):
        battery_wh = self._coerce_positive_float(battery_wh, fallback=500.0)
        assist_level = self._normalize_assist_level(assist_level)
        weight_kg = self._coerce_positive_float(weight_kg, fallback=85.0)
        ascent_m = self._coerce_float(ascent_m, fallback=0.0)
        distance_km = self._coerce_non_negative_float(distance_km, fallback=0.0)
        mud_index = self._normalize_mud_index(mud_index)
        avg_speed_kmh = self._coerce_positive_float(
            avg_speed_kmh, fallback=self.config.default_speed_kmh
        )
        ambient_temp_c = self._coerce_float(
            ambient_temp_c, fallback=self.config.default_ambient_temp_c
        )
        rider_ftp_w = self._coerce_positive_float(
            rider_ftp_w, fallback=float(self.config.default_rider_ftp_w)
        )
        intensity_score = int(
            self._clamp_float(
                intensity_score,
                minimum=1.0,
                maximum=5.0,
                fallback=float(self.config.default_intensity_score),
            )
        )
        motor_limit_w = self._resolve_motor_limit(motor_power_limit_w)

        usable_wh = self._usable_capacity_at_temperature(battery_wh, ambient_temp_c)

        velocity_ms = avg_speed_kmh / 3.6
        grade = ascent_m / (distance_km * 1000) if distance_km > 0 else 0.0
        theta = math.atan(grade)

        p_gravity = weight_kg * self.config.gravity * velocity_ms * math.sin(theta)
        p_aero = 0.5 * self.config.air_density * self.config.cda * (velocity_ms**3)

        avg_crr = self._weighted_crr(surface_breakdown)
        avg_crr += mud_index * self.config.mud_crr_penalty_factor

        p_rolling = avg_crr * weight_kg * self.config.gravity * velocity_ms * math.cos(theta)
        p_required = p_gravity + p_aero + p_rolling

        intensity_mult = 0.25 + (intensity_score * 0.15)
        p_rider = rider_ftp_w * intensity_mult

        assist_ratios = {"Eco": 0.6, "Trail": 2.0, "Boost": 3.4}
        max_assist_ratio = assist_ratios.get(assist_level, 2.0)

        p_motor_raw = max(0.0, p_required - p_rider)
        assist_cap_w = p_rider * max_assist_ratio
        p_motor_capped = min(p_motor_raw, assist_cap_w, motor_limit_w)

        efficiency = self._motor_efficiency(grade, ambient_temp_c)
        p_motor_final = p_motor_capped / efficiency if efficiency > 0 else p_motor_capped

        total_time_hours = distance_km / avg_speed_kmh if avg_speed_kmh > 0 else 0.0
        total_wh_spent = p_motor_final * total_time_hours

        remaining_wh = max(0.0, usable_wh - total_wh_spent)
        remaining_pct = round((remaining_wh / battery_wh) * 100, 1) if battery_wh > 0 else 0.0

        status = self._battery_status(remaining_pct)
        cap_reached = p_motor_raw > p_motor_capped + 0.1

        return {
            "status": "Success",
            "battery_metrics": {
                "estimated_drain_wh": round(total_wh_spent, 1),
                "remaining_battery_pct": remaining_pct,
                "safety_buffer_status": status,
                "usable_wh_at_temp": round(usable_wh, 1),
            },
            "power_breakdown_w": {
                "gravity_resistance": round(p_gravity, 1),
                "rolling_resistance": round(p_rolling, 1),
                "aerodynamic_drag": round(p_aero, 1),
                "rider_contribution": round(p_rider, 1),
                "motor_net_output": round(p_motor_capped, 1),
            },
            "assumptions": {
                "avg_speed_kmh": round(avg_speed_kmh, 2),
                "ambient_temp_c": round(ambient_temp_c, 1),
                "rider_ftp_w": round(rider_ftp_w, 1),
                "intensity_score": intensity_score,
                "assist_level": assist_level,
                "motor_power_limit_w": round(motor_limit_w, 1),
                "mud_index_0_1": round(mud_index, 3),
                "model_basis": (
                    "Heuristic power-balance estimate; not a certified range prediction. "
                    "Uses simplified physics, average speed/grade, and assumed rider/motor limits."
                ),
                "confidence": "low",
            },
            "tactical_advice": self._tactical_advice(status, cap_reached, assist_level),
        }

    def _usable_capacity_at_temperature(self, battery_wh: float, ambient_temp_c: float) -> float:
        usable_wh = battery_wh * self.config.usable_capacity_factor
        if ambient_temp_c < self.config.cold_temp_threshold_c:
            temp_penalty = (
                self.config.cold_temp_threshold_c - ambient_temp_c
            ) * self.config.cold_temp_penalty_per_degree
            usable_wh *= max(self.config.min_usable_capacity_factor, 1.0 - temp_penalty)
        return max(0.0, usable_wh)

    def _normalize_mud_index(self, mud_index: Any) -> float:
        value = self._coerce_float(mud_index, fallback=0.0)
        if value > 1.0:
            value = value / self.config.mud_normalization_max_mm
        return self._clamp_float(value, minimum=0.0, maximum=1.0, fallback=0.0)

    def _resolve_motor_limit(self, motor_power_limit_w: float | None) -> float:
        if motor_power_limit_w is None:
            return self.config.default_motor_power_limit_w
        return self._coerce_positive_float(
            motor_power_limit_w, fallback=self.config.default_motor_power_limit_w
        )

    def _weighted_crr(self, surface_breakdown: Any) -> float:
        surface_crr_map = {
            "asphalt": 0.004,
            "paved": 0.004,
            "concrete": 0.005,
            "paving_stones": 0.006,
            "compacted": 0.009,
            "fine_gravel": 0.012,
            "gravel": 0.015,
            "ground": 0.018,
            "dirt": 0.020,
            "unpaved": 0.020,
            "earth": 0.022,
            "grass": 0.030,
            "sand": 0.060,
            "mud": 0.070,
            "deep_mud": 0.080,
            "unknown": self.config.unknown_surface_crr,
        }

        items = self._surface_items(surface_breakdown)
        if not items:
            return self.config.default_surface_crr

        total_pct = 0.0
        weighted_crr = 0.0
        for surf, pct in items:
            key = self._normalize_surface_key(surf)
            crr_val = surface_crr_map.get(key, self.config.unknown_surface_crr)
            try:
                pct_val = max(0.0, float(pct))
            except (TypeError, ValueError):
                pct_val = 0.0
            weighted_crr += crr_val * pct_val
            total_pct += pct_val

        if total_pct <= 0:
            return self.config.default_surface_crr
        return weighted_crr / total_pct

    @staticmethod
    def _surface_items(surface_breakdown: Any) -> list[tuple[Any, Any]]:
        if isinstance(surface_breakdown, dict):
            return list(surface_breakdown.items())
        if isinstance(surface_breakdown, list):
            items: list[tuple[Any, Any]] = []
            for entry in surface_breakdown:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("type", entry.get("surface", entry.get("name")))
                pct = entry.get("percentage", entry.get("pct", entry.get("value", 0)))
                if isinstance(pct, str):
                    pct = pct.replace("%", "").strip()
                items.append((name, pct))
            return items
        return []

    @staticmethod
    def _normalize_surface_key(surface: Any) -> str:
        key = str(surface or "").strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "finegravel": "fine_gravel",
            "deepmud": "deep_mud",
            "unmapped_mixed": "unknown",
            "mixed": "unknown",
        }
        return aliases.get(key, key)

    def _motor_efficiency(self, grade: float, ambient_temp_c: float) -> float:
        efficiency = self.config.base_efficiency
        if grade > self.config.steep_grade_threshold:
            efficiency -= self.config.steep_grade_efficiency_penalty
        if ambient_temp_c > self.config.hot_temp_threshold_c:
            efficiency -= self.config.hot_temp_efficiency_penalty
        return efficiency

    @staticmethod
    def _battery_status(remaining_pct: float) -> str:
        if remaining_pct < 15:
            return "CRITICAL"
        if remaining_pct < 25:
            return "WARNING"
        return "SAFE"

    @staticmethod
    def _tactical_advice(status: str, cap_reached: bool, assist_level: str) -> str:
        if status == "CRITICAL":
            return "Battery critical: switch to Eco, reduce assist on climbs, and plan a shorter/charge stop."
        if cap_reached and assist_level == "Boost":
            return (
                "Motor/assist cap reached on demand: Boost may not sustain target pace on climbs; "
                "use lower assist on flats to preserve range."
            )
        if status == "WARNING":
            return "Switch to lower assist on flats and climbs where possible to save range."
        return "Pace maintained; monitor assist on sustained climbs."

    @staticmethod
    def _normalize_assist_level(assist_level: Any) -> str:
        if not isinstance(assist_level, str) or not assist_level.strip():
            return "Trail"
        cleaned = assist_level.strip().lower()
        mapping = {
            "eco": "Eco",
            "trail": "Trail",
            "boost": "Boost",
        }
        return mapping.get(cleaned, "Trail")

    @staticmethod
    def _coerce_float(value: Any, fallback: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _coerce_positive_float(self, value: Any, fallback: float) -> float:
        result = self._coerce_float(value, fallback=fallback)
        return result if result > 0 else fallback

    def _coerce_non_negative_float(self, value: Any, fallback: float = 0.0) -> float:
        result = self._coerce_float(value, fallback=fallback)
        return result if result >= 0 else fallback

    @staticmethod
    def _clamp_float(value: Any, minimum: float, maximum: float, fallback: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return fallback
        return max(minimum, min(parsed, maximum))


service = BatteryService()


def calculate_battery_drain(
    battery_wh: float,
    assist_level: str,
    weight_kg: float,
    ascent_m: float,
    distance_km: float,
    surface_breakdown: dict[str, Any] | list[dict[str, Any]] | None,
    mud_index: float,
    avg_speed_kmh: float = 18.0,
    ambient_temp_c: float = 20.0,
    rider_ftp_w: float = 200,
    intensity_score: int = 3,
    motor_power_limit_w: float | None = None,
):
    return service.calculate_battery_drain(
        battery_wh=battery_wh,
        assist_level=assist_level,
        weight_kg=weight_kg,
        ascent_m=ascent_m,
        distance_km=distance_km,
        surface_breakdown=surface_breakdown,
        mud_index=mud_index,
        avg_speed_kmh=avg_speed_kmh,
        ambient_temp_c=ambient_temp_c,
        rider_ftp_w=rider_ftp_w,
        intensity_score=intensity_score,
        motor_power_limit_w=motor_power_limit_w,
    )
