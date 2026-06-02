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
from typing import Any


@dataclass(frozen=True)
class BikeSetupConfig:
    road_default_bike_type: str = "road"
    unmapped_surface_label: str = "Unmapped/Mixed"


class BikeSetupService:
    def __init__(self, config: BikeSetupConfig | None = None) -> None:
        self.config = config or BikeSetupConfig()

    def analyze_compatibility(
            self,
            bike_type: str,
            tire_mm: int,
            extras: dict,
            surface_map: dict,
    ):
        normalized_bike_type = self._normalize_bike_type(bike_type)
        normalized_tire_mm = self._coerce_tire_mm(tire_mm)
        aggregated = self._aggregate_surface_summary(extras, surface_map)

        breakdown = []
        warnings = []
        is_compatible = True

        for name, percentage in aggregated.items():
            percentage = round(percentage, 1)

            if name in ["Gravel", "Unpaved"]:
                if normalized_tire_mm < 28 and percentage > 10.0:
                    is_compatible = False
                    warnings.append(
                        f"CRITICAL: {normalized_tire_mm}mm tires are unsafe for {percentage}% {name} (min 28mm)."
                    )
                elif normalized_tire_mm < 32:
                    warnings.append(
                        f"Caution: {normalized_tire_mm}mm tires may lack stability on {percentage}% {name}."
                    )

            elif name in ["Pebbles", "Stony", "Cobblestone"]:
                if normalized_tire_mm < 32:
                    warnings.append(
                        f"Safety Alert: Loose stones ({name}) detected. {normalized_tire_mm}mm is below recommended safety margin."
                    )

            elif name in ["Grass", "Muddy", "Earth"]:
                if normalized_tire_mm < 42:
                    warnings.append(
                        f"Traction Alert: {percentage}% is {name}. {normalized_tire_mm}mm tires may slip in wet/loose conditions."
                    )

            if normalized_bike_type == "road":
                if name in ["Gravel", "Unpaved", "Pebbles", "Grass", self.config.unmapped_surface_label] and percentage > 15.0:
                    warnings.append(
                        f"Geometry Warning: {percentage}% {name} exceeds standard road bike handling design."
                    )

            breakdown.append({"type": name, "percentage": f"{percentage}%"})

        breakdown.sort(key=lambda x: float(x["percentage"].replace("%", "")), reverse=True)
        return breakdown, warnings, is_compatible

    def get_tire_setup(
            self,
            bike_type: str,
            tire_size_option: str,
            mud_index: float = 0.0,
            surface_type: str = "mixed",
            rider_weight_kg: float = 80.0,
    ):
        normalized_bike_type = self._normalize_bike_type(bike_type)
        normalized_surface_type = self._normalize_surface_type(surface_type)
        normalized_weight = self._coerce_rider_weight(rider_weight_kg, fallback=80.0)
        normalized_mud_index = self._clamp_mud_index(mud_index)
        normalized_tire_size_option = self._normalize_tire_size_option(tire_size_option)

        base_psi, width_mm, wheel_label = self._base_setup_for_bike_type(normalized_bike_type)

        if normalized_bike_type in ["mtb", "e-mtb", "enduro"]:
            wheel_label = '29"' if normalized_tire_size_option in ["700c", "650b", "25", "28"] else normalized_tire_size_option
        elif normalized_bike_type == "gravel":
            wheel_label = normalized_tire_size_option if normalized_tire_size_option in ["700c", "650b"] else "700c"

        weight_adjustment = (normalized_weight - 85.0) / 5.0
        adjusted_psi = base_psi + weight_adjustment

        strategy = "Standard"

        if normalized_mud_index > 0.6:
            adjusted_psi *= 0.85
            strategy = "Mud Flotation"
        elif any(keyword in normalized_surface_type for keyword in ["rock", "root", "technical"]):
            adjusted_psi -= 2.0
            strategy = "Compliance"
        elif any(keyword in normalized_surface_type for keyword in ["smooth", "asphalt", "paved"]):
            adjusted_psi += 3.0
            strategy = "Efficiency"

        final_psi = round(adjusted_psi, 1)
        final_bar = round(final_psi * 0.0689476, 2)

        tactical_display = (
            f"{wheel_label} wheels | {final_psi} PSI ({final_bar} Bar) "
            f"[{strategy} Setup]"
        )

        return width_mm, tactical_display

    def _aggregate_surface_summary(self, extras: Any, surface_map: Any) -> dict[str, float]:
        if not isinstance(extras, dict):
            return {}
        if not isinstance(surface_map, dict):
            return {}

        surface = extras.get("surface", {})
        if not isinstance(surface, dict):
            return {}

        summary = surface.get("summary", [])
        if not isinstance(summary, list):
            return {}

        temp_map: dict[str, float] = {}

        for item in summary:
            if not isinstance(item, dict):
                continue

            raw_name = surface_map.get(item.get("value"), "Other")

            if raw_name in ["Unknown", "Other", "None", "Null"]:
                name = self.config.unmapped_surface_label
            else:
                name = raw_name

            try:
                amount = float(item.get("amount", 0.0))
            except (TypeError, ValueError):
                continue

            temp_map[name] = temp_map.get(name, 0.0) + amount

        return temp_map

    def _normalize_bike_type(self, bike_type: Any) -> str:
        if not isinstance(bike_type, str) or not bike_type.strip():
            return self.config.road_default_bike_type
        return bike_type.strip().lower()

    @staticmethod
    def _coerce_tire_mm(tire_mm: Any) -> int:
        try:
            value = int(tire_mm)
        except (TypeError, ValueError):
            return 25
        return value

    @staticmethod
    def _normalize_surface_type(surface_type: Any) -> str:
        if not isinstance(surface_type, str):
            return "mixed"
        value = surface_type.strip().lower()
        return value or "mixed"

    @staticmethod
    def _normalize_tire_size_option(tire_size_option: Any) -> str:
        if not isinstance(tire_size_option, str):
            return ""
        return tire_size_option.strip()

    @staticmethod
    def _coerce_rider_weight(rider_weight_kg: Any, fallback: float = 80.0) -> float:
        try:
            value = float(rider_weight_kg)
        except (TypeError, ValueError):
            return fallback
        return value if value > 0 else fallback

    @staticmethod
    def _clamp_mud_index(mud_index: Any) -> float:
        try:
            value = float(mud_index)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(value, 1.0))

    @staticmethod
    def _base_setup_for_bike_type(bike_type: str) -> tuple[float, int, str]:
        configs = {
            "mtb": (24.0, 58, '29"'),
            "e-mtb": (26.0, 60, '29"'),
            "enduro": (23.0, 60, '29"'),
            "gravel": (35.0, 40, "700c"),
            "road": (85.0, 25, "700c"),
        }
        return configs.get(bike_type, configs["road"])


service = BikeSetupService()


def analyze_compatibility(bike_type: str, tire_mm: int, extras: dict, surface_map: dict):
    return service.analyze_compatibility(bike_type, tire_mm, extras, surface_map)


def get_tire_setup(
        bike_type: str,
        tire_size_option: str,
        mud_index: float = 0.0,
        surface_type: str = "mixed",
        rider_weight_kg: float = 80.0,
):
    return service.get_tire_setup(
        bike_type=bike_type,
        tire_size_option=tire_size_option,
        mud_index=mud_index,
        surface_type=surface_type,
        rider_weight_kg=rider_weight_kg,
    )
