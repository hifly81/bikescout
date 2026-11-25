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

import re
from dataclasses import dataclass
from typing import Any

from bikescout.schemas import TireSetupRecommendation

BAR_PER_PSI = 0.0689476
REFERENCE_RIDER_WEIGHT_KG = 85.0

# Approximate bike mass used to convert rider mass into total system load.
BIKE_MASS_KG: dict[str, float] = {
    "road": 9.0,
    "gravel": 11.0,
    "mtb": 14.0,
    "e-mtb": 24.0,
    "enduro": 16.0,
}
FRONT_LOAD_SHARE: dict[str, float] = {
    "road": 0.45,
    "gravel": 0.45,
    "mtb": 0.40,
    "e-mtb": 0.40,
    "enduro": 0.40,
}
REFERENCE_TIRE_WIDTH_MM: dict[str, int] = {
    "road": 25,
    "gravel": 40,
    "mtb": 58,
    "e-mtb": 60,
    "enduro": 60,
}
REFERENCE_RIM_INTERNAL_MM: dict[str, int] = {
    "road": 19,
    "gravel": 21,
    "mtb": 25,
    "e-mtb": 27,
    "enduro": 28,
}
DEFAULT_CASING_TYPE: dict[str, str] = {
    "road": "xc",
    "gravel": "xc",
    "mtb": "trail",
    "e-mtb": "trail",
    "enduro": "enduro",
}
CASING_STIFFNESS_FACTOR: dict[str, float] = {
    "xc": 1.0,
    "trail": 0.95,
    "enduro": 0.88,
    "dh": 0.83,
}
RIM_WIDTH_RATIO_RANGE: dict[str, tuple[float, float]] = {
    "road": (0.60, 0.75),
    "gravel": (0.50, 0.65),
    "mtb": (0.40, 0.60),
    "e-mtb": (0.40, 0.60),
    "enduro": (0.40, 0.60),
}

# Exponents of the pneumatic volume/load model.
WEIGHT_EXPONENT = 1.25
LOAD_DISTRIBUTION_EXPONENT = 0.6
VOLUME_EXPONENT = 2.0
RIM_SUPPORT_EXPONENT = 0.5

TUBE_PRESSURE_FACTOR = 1.18
MUD_FLOTATION_THRESHOLD = 0.6
MUD_FLOTATION_FACTOR = 0.85
COMPLIANCE_FACTOR = 0.92
TECHNICAL_COMPLIANCE_FACTOR = 0.96
SMOOTH_SURFACE_FACTOR = 1.08
TECHNICAL_ADVICE_MIN_LEVEL = 3
PINCH_FLAT_ASCENT_THRESHOLD_M = 800.0
PINCH_FLAT_FLOOR_FACTOR = 0.93
ROCKY_SURFACE_KEYWORDS = (
    "rock",
    "root",
    "technical",
    "stone",
    "stony",
    "pebble",
    "cobble",
)
SMOOTH_SURFACE_KEYWORDS = ("asphalt", "paved", "smooth", "concrete")


def _bike_key(bike_type: Any) -> str:
    """Normalize a bike type to the lowercase keys used by the lookup tables."""
    if not isinstance(bike_type, str) or not bike_type.strip():
        return "road"
    return bike_type.strip().lower()


def default_tire_width_mm(bike_type: str) -> int:
    """Return the reference tire width for a bike category."""
    return REFERENCE_TIRE_WIDTH_MM.get(
        _bike_key(bike_type), REFERENCE_TIRE_WIDTH_MM["road"]
    )


def default_rim_internal_width_mm(bike_type: str) -> int:
    """Return the reference rim internal width for a bike category."""
    return REFERENCE_RIM_INTERNAL_MM.get(
        _bike_key(bike_type), REFERENCE_RIM_INTERNAL_MM["road"]
    )


def default_casing_type(bike_type: str) -> str:
    """Return the reference casing class for a bike category."""
    return DEFAULT_CASING_TYPE.get(_bike_key(bike_type), DEFAULT_CASING_TYPE["road"])


@dataclass(frozen=True)
class BikeSetupConfig:
    road_default_bike_type: str = "road"
    unmapped_surface_label: str = "Unmapped/Mixed"


class BikeSetupService:
    """Surface compatibility and tire pressure optimization service."""

    def __init__(self, config: BikeSetupConfig | None = None) -> None:
        self.config = config or BikeSetupConfig()

    def analyze_compatibility(
        self,
        bike_type: str,
        tire_mm: int,
        extras: dict,
        surface_map: dict,
        rim_internal_width_mm: int | None = None,
    ) -> tuple[list[dict[str, str]], list[str], bool]:
        """
        Check tire/surface suitability and flag tire-to-rim width mismatches.

        Args:
            bike_type: Bike category used for road-geometry and rim-range rules.
            tire_mm: Actual tire width in millimeters.
            extras: ORS extras payload containing the surface summary.
            surface_map: Mapping from ORS surface values to readable labels.
            rim_internal_width_mm: Optional rim internal width in millimeters.

        Returns:
            A tuple of (surface breakdown, warnings, compatible flag). A rim-width
            mismatch is reported as a warning and does not mark the bike incompatible.
        """
        normalized_bike_type = self._normalize_bike_type(bike_type)
        normalized_tire_mm = self._coerce_tire_mm(tire_mm)
        aggregated = self._aggregate_surface_summary(extras, surface_map)

        breakdown: list[dict[str, str]] = []
        warnings: list[str] = []
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

            elif name in ["Grass", "Muddy", "Earth"] and normalized_tire_mm < 42:
                warnings.append(
                    f"Traction Alert: {percentage}% is {name}. {normalized_tire_mm}mm tires may slip in wet/loose conditions."
                )

            if (
                normalized_bike_type == "road"
                and name
                in [
                    "Gravel",
                    "Unpaved",
                    "Pebbles",
                    "Grass",
                    self.config.unmapped_surface_label,
                ]
                and percentage > 15.0
            ):
                warnings.append(
                    f"Geometry Warning: {percentage}% {name} exceeds standard road bike handling design."
                )

            breakdown.append({"type": name, "percentage": f"{percentage}%"})

        breakdown.sort(
            key=lambda x: float(x["percentage"].replace("%", "")), reverse=True
        )

        rim_mm = self._coerce_optional_int(rim_internal_width_mm)
        if rim_mm is not None:
            min_rim_mm, max_rim_mm = self._rim_width_recommendation(
                normalized_bike_type, normalized_tire_mm
            )
            if rim_mm < min_rim_mm or rim_mm > max_rim_mm:
                warnings.append(
                    f"Rim-Width Mismatch: {normalized_tire_mm}mm tire on a {rim_mm}mm internal rim "
                    f"(recommended {min_rim_mm}-{max_rim_mm}mm). Check sidewall support and pinch-flat risk."
                )

        return breakdown, warnings, is_compatible

    def get_tire_setup(
        self,
        bike_type: str,
        tire_size_option: str,
        mud_index: float = 0.0,
        surface_type: str = "mixed",
        rider_weight_kg: float = 80.0,
        *,
        tire_width_mm: int | None = None,
        rim_internal_width_mm: int | None = None,
        casing_type: str | None = None,
        tubeless: bool = True,
        technical_difficulty: Any = None,
        ascent_m: float = 0.0,
        surface_analysis: Any = None,
    ) -> TireSetupRecommendation:
        """
        Compute differential front/rear pressures with a volume and load model.

        The model scales reference pressures by total system mass (non-linear),
        tire air volume (width squared), rim support, casing stiffness and tube
        setup, then splits the load between the wheels before applying grip and
        rim-impact optimization.

        Args:
            bike_type: Bike category driving load split and reference geometry.
            tire_size_option: Wheel diameter label (e.g. 29, 700c, 650b).
            mud_index: Normalized mud severity from 0.0 to 1.0.
            surface_type: Dominant surface label used for grip optimization.
            rider_weight_kg: Rider mass in kilograms.
            tire_width_mm: Actual tire width; falls back to the bike reference.
            rim_internal_width_mm: Rim internal width; falls back to the bike reference.
            casing_type: One of xc, trail, enduro or dh.
            tubeless: True for tubeless, False for inner tubes.
            technical_difficulty: Technical grade (string, S-label or dict with label).
            ascent_m: Total climbing meters used for pinch-flat risk assessment.
            surface_analysis: Surface breakdown from the surface analyzer; rocky,
                stony or cobblestone entries also trigger compliance logic.

        Returns:
            A TireSetupRecommendation with front/rear PSI and bar, strategy,
            equipment advice, warnings and a tactical display string.
        """
        normalized_bike_type = self._normalize_bike_type(bike_type)
        normalized_surface_type = self._normalize_surface_type(surface_type)
        normalized_weight = self._coerce_rider_weight(rider_weight_kg, fallback=80.0)
        normalized_mud_index = self._clamp_mud_index(mud_index)
        normalized_tire_size_option = self._normalize_tire_size_option(tire_size_option)

        base_psi, fallback_width_mm, wheel_label = self._base_setup_for_bike_type(
            normalized_bike_type
        )

        if normalized_bike_type in ["mtb", "e-mtb", "enduro"]:
            wheel_label = (
                '29"'
                if normalized_tire_size_option in ["700c", "650b", "25", "28"]
                else normalized_tire_size_option
            )
        elif normalized_bike_type == "gravel":
            wheel_label = (
                normalized_tire_size_option
                if normalized_tire_size_option in ["700c", "650b"]
                else "700c"
            )

        effective_width_mm = self._coerce_optional_int(tire_width_mm)
        if effective_width_mm is None:
            effective_width_mm = (
                default_tire_width_mm(normalized_bike_type) or fallback_width_mm
            )

        rim_mm = self._coerce_optional_int(rim_internal_width_mm)
        if rim_mm is None:
            rim_mm = default_rim_internal_width_mm(normalized_bike_type)

        casing = self._normalize_casing_type(casing_type, normalized_bike_type)
        is_tubeless = self._coerce_bool(tubeless)
        technical_level = self._technical_difficulty_level(technical_difficulty)
        clean_ascent_m = self._coerce_nonnegative_float(ascent_m)

        reference_width_mm = REFERENCE_TIRE_WIDTH_MM.get(
            normalized_bike_type, fallback_width_mm
        )
        reference_rim_mm = REFERENCE_RIM_INTERNAL_MM.get(
            normalized_bike_type, default_rim_internal_width_mm(normalized_bike_type)
        )
        bike_mass_kg = BIKE_MASS_KG.get(normalized_bike_type, BIKE_MASS_KG["road"])
        total_mass_kg = normalized_weight + bike_mass_kg
        reference_mass_kg = REFERENCE_RIDER_WEIGHT_KG + bike_mass_kg

        mass_factor = (total_mass_kg / reference_mass_kg) ** WEIGHT_EXPONENT
        volume_factor = (reference_width_mm / effective_width_mm) ** VOLUME_EXPONENT
        rim_factor = (reference_rim_mm / rim_mm) ** RIM_SUPPORT_EXPONENT
        casing_factor = CASING_STIFFNESS_FACTOR.get(
            casing, CASING_STIFFNESS_FACTOR[default_casing_type(normalized_bike_type)]
        )
        tube_factor = 1.0 if is_tubeless else TUBE_PRESSURE_FACTOR

        # Pressure required to support the load before grip/compliance tuning.
        support_psi = (
            base_psi
            * mass_factor
            * volume_factor
            * rim_factor
            * casing_factor
            * tube_factor
        )

        rocky_surface = (
            any(
                keyword in normalized_surface_type for keyword in ROCKY_SURFACE_KEYWORDS
            )
            or technical_level >= TECHNICAL_ADVICE_MIN_LEVEL
            or self._rocky_surface_from_analysis(surface_analysis)
        )
        smooth_surface = any(
            keyword in normalized_surface_type for keyword in SMOOTH_SURFACE_KEYWORDS
        )

        strategy = "Standard"
        grip_factor = 1.0
        if normalized_mud_index > MUD_FLOTATION_THRESHOLD:
            grip_factor = MUD_FLOTATION_FACTOR
            strategy = "Mud Flotation"
        elif rocky_surface:
            grip_factor = COMPLIANCE_FACTOR
            if technical_level >= TECHNICAL_ADVICE_MIN_LEVEL:
                grip_factor *= TECHNICAL_COMPLIANCE_FACTOR
            strategy = "Compliance"
        elif smooth_surface:
            grip_factor = SMOOTH_SURFACE_FACTOR
            strategy = "Efficiency"

        front_share = FRONT_LOAD_SHARE.get(
            normalized_bike_type, FRONT_LOAD_SHARE["road"]
        )
        rear_share = 1.0 - front_share
        front_load_factor = (front_share / 0.5) ** LOAD_DISTRIBUTION_EXPONENT
        rear_load_factor = (rear_share / 0.5) ** LOAD_DISTRIBUTION_EXPONENT

        target_front_psi = support_psi * grip_factor * front_load_factor
        target_rear_psi = support_psi * grip_factor * rear_load_factor

        warnings: list[str] = []
        pinch_flat_risk = rocky_surface and (
            technical_level >= TECHNICAL_ADVICE_MIN_LEVEL
            or clean_ascent_m >= PINCH_FLAT_ASCENT_THRESHOLD_M
        )
        if pinch_flat_risk:
            floor_front_psi = support_psi * front_load_factor * PINCH_FLAT_FLOOR_FACTOR
            floor_rear_psi = support_psi * rear_load_factor * PINCH_FLAT_FLOOR_FACTOR
            if target_front_psi < floor_front_psi or target_rear_psi < floor_rear_psi:
                target_front_psi = max(target_front_psi, floor_front_psi)
                target_rear_psi = max(target_rear_psi, floor_rear_psi)
                if strategy == "Compliance":
                    strategy = "Pinch-Flat Protection"
                risk_reason = []
                if technical_level >= TECHNICAL_ADVICE_MIN_LEVEL:
                    risk_reason.append(f"S{technical_level}+ technical grade")
                if clean_ascent_m >= PINCH_FLAT_ASCENT_THRESHOLD_M:
                    risk_reason.append(f"{clean_ascent_m:.0f}m ascent")
                warnings.append(
                    "Pinch-Flat Warning: rocky/root terrain with "
                    f"{' and '.join(risk_reason) or 'high impact risk'} needs more support "
                    f"than the grip-optimized pressure; raised to {target_front_psi:.1f}/{target_rear_psi:.1f} PSI (F/R)."
                )

        min_rim_mm, max_rim_mm = self._rim_width_recommendation(
            normalized_bike_type, effective_width_mm
        )
        if rim_mm < min_rim_mm or rim_mm > max_rim_mm:
            warnings.append(
                f"Rim-Width Mismatch: {effective_width_mm}mm tire on a {rim_mm}mm internal rim "
                f"(recommended {min_rim_mm}-{max_rim_mm}mm)."
            )

        advice: list[str] = []
        if technical_level >= TECHNICAL_ADVICE_MIN_LEVEL:
            advice.append("Tire Inserts Recommended (rear wheel first) for S3+ terrain")
            if is_tubeless:
                advice.append(
                    "Verify sealant and tubeless setup before technical riding"
                )
            else:
                advice.append("Tubeless Conversion Recommended for S3+ terrain")
        if normalized_mud_index > MUD_FLOTATION_THRESHOLD:
            advice.append("Sealant Check Required for muddy conditions")
        if rocky_surface and effective_width_mm < reference_width_mm:
            advice.append("High-Volume Casing Suggested for rocky impact absorption")

        if normalized_mud_index > MUD_FLOTATION_THRESHOLD:
            knob_choice = "Mud Spikes"
        elif smooth_surface and normalized_mud_index < 0.15:
            knob_choice = "Semi-Slick"
        else:
            knob_choice = "All-Terrain / Trail"

        psi_front = round(target_front_psi, 1)
        psi_rear = round(target_rear_psi, 1)
        bar_front = round(psi_front * BAR_PER_PSI, 2)
        bar_rear = round(psi_rear * BAR_PER_PSI, 2)

        tactical_display = (
            f"{wheel_label} wheels | {effective_width_mm}mm | "
            f"F: {psi_front} PSI | R: {psi_rear} PSI "
            f"({bar_front}/{bar_rear} Bar) [{strategy} Setup]"
        )

        return TireSetupRecommendation(
            wheel_label=str(wheel_label),
            tire_width_mm=effective_width_mm,
            rim_internal_width_mm=rim_mm,
            casing_type=casing,
            tubeless=is_tubeless,
            psi_front=psi_front,
            psi_rear=psi_rear,
            bar_front=bar_front,
            bar_rear=bar_rear,
            strategy=strategy,
            load_split={"front": front_share, "rear": rear_share},
            knob_choice=knob_choice,
            advice=advice,
            warnings=warnings,
            tactical_display=tactical_display,
        )

    def _aggregate_surface_summary(
        self, extras: Any, surface_map: Any
    ) -> dict[str, float]:
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
    def _coerce_optional_int(value: Any) -> int | None:
        try:
            coerced = int(value)
        except (TypeError, ValueError):
            return None
        return coerced if coerced > 0 else None

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "tubeless"}
        return bool(value)

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
    def _coerce_nonnegative_float(value: Any) -> float:
        try:
            coerced = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, coerced)

    @staticmethod
    def _clamp_mud_index(mud_index: Any) -> float:
        try:
            value = float(mud_index)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(value, 1.0))

    @staticmethod
    def _normalize_casing_type(casing_type: Any, bike_type: str) -> str:
        value = casing_type.strip().lower() if isinstance(casing_type, str) else ""
        if value in CASING_STIFFNESS_FACTOR:
            return value
        return default_casing_type(bike_type)

    @staticmethod
    def _rocky_surface_from_analysis(surface_analysis: Any) -> bool:
        """Detect rocky/stony entries in a surface analyzer breakdown."""
        if surface_analysis is None:
            return False

        entries: Any = surface_analysis
        if isinstance(surface_analysis, dict):
            entries = (
                surface_analysis.get("surface_breakdown")
                or surface_analysis.get("breakdown")
                or surface_analysis.get("entries")
                or []
            )
        if isinstance(entries, dict):
            entries = list(entries.values())
        if not isinstance(entries, (list, tuple, set)):
            return False

        for entry in entries:
            label: Any = entry
            if isinstance(entry, dict):
                label = (
                    entry.get("type")
                    or entry.get("surface")
                    or entry.get("name")
                    or entry.get("label")
                )
            if isinstance(label, str) and any(
                keyword in label.lower() for keyword in ROCKY_SURFACE_KEYWORDS
            ):
                return True
        return False

    @staticmethod
    def _technical_difficulty_level(value: Any) -> int:
        label = value.get("label") if isinstance(value, dict) else value
        if not isinstance(label, str):
            return 0
        match = re.search(r"\bS([0-5])\b", label.upper())
        if not match:
            match = re.search(r"\b([0-5])\b", label)
        return int(match.group(1)) if match else 0

    def _rim_width_recommendation(
        self, bike_type: str, tire_mm: int
    ) -> tuple[int, int]:
        normalized = self._normalize_bike_type(bike_type)
        min_ratio, max_ratio = RIM_WIDTH_RATIO_RANGE.get(
            normalized, RIM_WIDTH_RATIO_RANGE["road"]
        )
        return round(tire_mm * min_ratio), round(tire_mm * max_ratio)

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


def analyze_compatibility(
    bike_type: str,
    tire_mm: int,
    extras: dict,
    surface_map: dict,
    rim_internal_width_mm: int | None = None,
) -> tuple[list[dict[str, str]], list[str], bool]:
    """Delegate compatibility analysis to the module-level service."""
    return service.analyze_compatibility(
        bike_type=bike_type,
        tire_mm=tire_mm,
        extras=extras,
        surface_map=surface_map,
        rim_internal_width_mm=rim_internal_width_mm,
    )


def get_tire_setup(
    bike_type: str,
    tire_size_option: str,
    mud_index: float = 0.0,
    surface_type: str = "mixed",
    rider_weight_kg: float = 80.0,
    *,
    tire_width_mm: int | None = None,
    rim_internal_width_mm: int | None = None,
    casing_type: str | None = None,
    tubeless: bool = True,
    technical_difficulty: Any = None,
    ascent_m: float = 0.0,
    surface_analysis: Any = None,
) -> TireSetupRecommendation:
    """Delegate tire setup optimization to the module-level service."""
    return service.get_tire_setup(
        bike_type=bike_type,
        tire_size_option=tire_size_option,
        mud_index=mud_index,
        surface_type=surface_type,
        rider_weight_kg=rider_weight_kg,
        tire_width_mm=tire_width_mm,
        rim_internal_width_mm=rim_internal_width_mm,
        casing_type=casing_type,
        tubeless=tubeless,
        technical_difficulty=technical_difficulty,
        ascent_m=ascent_m,
        surface_analysis=surface_analysis,
    )
