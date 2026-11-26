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
import zoneinfo
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import requests
from astral import Observer
from astral.sun import elevation
from timezonefinder import TimezoneFinder

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

MODEL_BASIS = (
    "TAEL heuristic reservoir model (exponential decay, seasonal bias, PET-like "
    "drying). Coefficients are not empirically calibrated; no soil/DEM ground-truth data."
)
MODEL_CONFIDENCE = "low"
MODEL_LIMITATIONS = [
    "Coefficients are heuristic and not calibrated against field measurements.",
    "No real soil composition, DEM, drainage, or vegetation dataset is used.",
    "Drainage/slope signals can be inferred heuristically from route/surface; they are proxies, not ground truth.",
    "Output is a moisture index in mm, not a 1-100 score and not ground truth.",
]

# Display categories from the surface analyzer are mapped to TAEL soil keys.
MUD_SURFACE_ALIASES = {
    "asphalt": "asphalt",
    "paved": "asphalt",
    "road": "asphalt",
    "concrete": "asphalt",
    "unpaved": "dirt",
    "sand": "sand",
    "gravel": "gravel",
    "grass": "grass",
    "dirt": "dirt",
    "earth": "earth",
    "clay": "clay",
    "mixed": "dirt",
    "unmapped": "dirt",
    "unmapped/mixed": "dirt",
}


def get_solar_altitude(lat: float, lon: float, current_dt: datetime) -> float:
    try:
        observer = Observer(latitude=lat, longitude=lon)
        solar_angle = elevation(observer, current_dt)
        return round(solar_angle, 2)
    except Exception:
        return 0.0


@dataclass(frozen=True)
class MudAnalysisConfig:
    archive_url: str = ARCHIVE_URL
    forecast_url: str = FORECAST_URL
    default_surface_type: str = "dirt"
    request_timeout_seconds: float = 10.0
    model_name: str = "TAEL® v3.2"
    # Heuristic moisture-label thresholds (mm). Not calibrated ground truth.
    threshold_low_max_mm: float = 4.0
    threshold_medium_max_mm: float = 12.0
    threshold_high_max_mm: float = 20.0


class MudAnalysisError(ValueError):
    """Raised when mud analysis cannot produce a safe assessment."""


class MudAnalysisService:
    def __init__(
        self,
        config: MudAnalysisConfig | None = None,
        requests_session: Any | None = None,
        timezone_finder: Any | None = None,
        solar_altitude_func: Callable[[float, float, datetime], float] | None = None,
        now_func: Callable[[zoneinfo.ZoneInfo], datetime] | None = None,
    ) -> None:
        self.config = config or MudAnalysisConfig()
        self.requests_session = requests_session or requests
        self.timezone_finder = timezone_finder or TimezoneFinder()
        self.solar_altitude_func = solar_altitude_func or get_solar_altitude
        self.now_func = now_func or (lambda tz: datetime.now(tz))

    @staticmethod
    def _validate_coords(lat: Any, lon: Any) -> tuple[float, float]:
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError) as exc:
            raise MudAnalysisError("lat and lon must be valid numbers.") from exc
        if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
            raise MudAnalysisError("lat must be between -90 and 90 and lon between -180 and 180.")
        return lat_f, lon_f

    def get_mud_risk_analysis(
        self,
        lat: float,
        lon: float,
        surface_type: str = "dirt",
        target_date: str | None = None,
        avg_slope_pct: float | None = None,
        soil_drainage_class: str | None = None,
        max_gradient_pct: float | None = None,
    ) -> dict[str, Any]:
        try:
            lat, lon = self._validate_coords(lat, lon)
            normalized_surface_type = self._normalize_surface_type(surface_type)

            tz_name = self._resolve_timezone_name(lat, lon)
            local_tz = zoneinfo.ZoneInfo(tz_name)

            reference_date = self._reference_date(local_tz, target_date)
            end_date = reference_date
            start_date = end_date - timedelta(hours=72)

            is_predictive = reference_date > self.now_func(local_tz)
            url = self.config.forecast_url if is_predictive else self.config.archive_url
            params = self._build_weather_params(lat, lon, start_date, end_date, tz_name)

            response = self.requests_session.get(
                url, params=params, timeout=self.config.request_timeout_seconds
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("hourly", {}) if isinstance(payload, dict) else {}

            times = data.get("time", [])
            precips = data.get("precipitation", [])
            temps = data.get("temperature_2m", [])
            winds = data.get("wind_speed_10m", [])
            clouds = data.get("cloudcover", [])

            required = [times, precips, temps, winds, clouds]
            if not times or any(len(series) == 0 for series in required):
                raise MudAnalysisError(
                    "No hourly weather data returned from provider for mud assessment. "
                    "Cannot assess mud risk safely (missing data is not treated as dry)."
                )
            lengths = {len(series) for series in required}
            if len(lengths) != 1:
                raise MudAnalysisError(
                    "Inconsistent hourly weather arrays returned from provider; cannot assess mud risk safely."
                )

            base_k = self._base_drainage_coefficient(normalized_surface_type)
            slope_pct = self._sanitize_slope_pct(avg_slope_pct)
            max_slope_pct = self._sanitize_slope_pct(max_gradient_pct)
            drainage_input = self._normalize_drainage_class(soil_drainage_class)
            inferred_drainage, drainage_source = self._resolve_drainage_class(
                normalized_surface_type, slope_pct, max_slope_pct, drainage_input
            )
            terrain_drainage_factor = self._terrain_drainage_factor(slope_pct, max_slope_pct)
            soil_drainage_factor = self._soil_drainage_factor(inferred_drainage)
            effective_k = base_k * terrain_drainage_factor * soil_drainage_factor

            M = _get_seasonal_saturation_bias(reference_date, lat)
            pet_hours = 0
            total_raw_rain = 0.0
            recent_rain_12h = 0.0
            recent_dt_sum = 0.0

            for current_dt, rain, temp, wind, cloud in self._iter_hourly_points(
                times, precips, temps, winds, clouds, local_tz
            ):
                if current_dt < start_date or current_dt > end_date:
                    continue
                if rain is None or temp is None or wind is None or cloud is None:
                    raise MudAnalysisError(
                        "Missing weather value in provider data; cannot assess mud risk safely."
                    )

                total_raw_rain += rain
                time_diff = (end_date - current_dt).total_seconds()

                if time_diff <= (12 * 3600):
                    recent_rain_12h += rain

                solar_alt = self.solar_altitude_func(lat, lon, current_dt)

                temp_factor = max(0.01, (temp / 20.0))
                wind_factor = max(0.5, (wind / 15.0))

                solar_factor = 1.0
                if solar_alt > 20:
                    solar_factor += (solar_alt / 90.0) * (1.0 - (cloud / 100.0))
                    pet_hours += 1

                Dt = temp_factor * wind_factor * solar_factor

                if time_diff <= (24 * 3600):
                    recent_dt_sum += Dt

                current_k = effective_k
                if normalized_surface_type == "clay" and M > 12.0:
                    current_k *= 0.3

                M = (M * math.exp(-current_k * Dt)) + rain

            eta_hours = self._dry_time_eta(
                moisture=M,
                base_k=effective_k,
                avg_recent_dt=max(0.1, (recent_dt_sum / 24.0)),
                surface_type=normalized_surface_type,
            )

            traction_risk, traction_advice = self._traction_risk(
                (recent_rain_12h * 1.5) + (M * 0.5),
                normalized_surface_type,
            )
            damage_risk, damage_advice = self._damage_risk(M)
            global_label = self._global_mud_label(M)
            confidence, confidence_reason = self._model_confidence(
                slope_pct=slope_pct,
                max_slope_pct=max_slope_pct,
                drainage_class=inferred_drainage,
                drainage_source=drainage_source,
            )

            return {
                "status": "Success",
                "metadata": {
                    "target_date": reference_date.isoformat(),
                    "timezone": tz_name,
                    "is_predictive": is_predictive,
                    "model": self.config.model_name,
                    "model_confidence": confidence,
                    "model_confidence_reason": confidence_reason,
                    "model_basis": MODEL_BASIS,
                    "model_limitations": list(MODEL_LIMITATIONS),
                    "thresholds_mm": {
                        "low_max": self.config.threshold_low_max_mm,
                        "medium_max": self.config.threshold_medium_max_mm,
                        "high_max": self.config.threshold_high_max_mm,
                    },
                },
                "environmental_context": {
                    "total_rain_72h_mm": round(total_raw_rain, 1),
                    "integrated_pet_hours": pet_hours,
                    "reservoir_moisture_mm": round(M, 2),
                    "avg_slope_pct": slope_pct,
                    "max_slope_pct": max_slope_pct,
                    "soil_drainage_class": inferred_drainage,
                    "drainage_proxy": {
                        "value": inferred_drainage,
                        "source": drainage_source,
                        "is_inferred": drainage_source != "provided",
                        "basis": "Heuristic proxy from surface type and route slope; not soil ground truth.",
                    },
                    "drainage_factor": round(effective_k / base_k, 3) if base_k else 1.0,
                },
                "tactical_analysis": {
                    "surface_type": normalized_surface_type,
                    "mud_risk_numeric": round(M, 2),
                    "mud_risk_score": global_label,
                    "traction_risk": {"level": traction_risk, "advice": traction_advice},
                    "trail_damage_risk": {"level": damage_risk, "advice": damage_advice},
                    "dry_time_eta": f"{eta_hours} hours" if eta_hours > 0 else "Ready Now",
                },
            }

        except MudAnalysisError as e:
            return {
                "status": "Error",
                "message": str(e),
                "next_step": "Provide valid coordinates/date and retry when hourly weather data is available.",
                "tactical_analysis": None,
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "Error",
                "message": f"Mud weather provider error: {e}.",
                "next_step": "Retry later or verify coordinates/date and network connectivity.",
                "tactical_analysis": None,
            }
        except Exception as e:
            return {
                "status": "Error",
                "message": f"Unexpected mud analysis error: {e}",
                "next_step": "Retry with valid inputs; if it persists, inspect logs/provider availability.",
                "tactical_analysis": None,
            }

    def _resolve_timezone_name(self, lat: float, lon: float) -> str:
        tz_name = self.timezone_finder.timezone_at(lng=lon, lat=lat)
        return tz_name or "UTC"

    def _reference_date(self, local_tz: zoneinfo.ZoneInfo, target_date: str | None) -> datetime:
        if target_date:
            return datetime.strptime(target_date, "%Y-%m-%d").replace(tzinfo=local_tz)
        return self.now_func(local_tz)

    @staticmethod
    def _build_weather_params(
        lat: float, lon: float, start_date: datetime, end_date: datetime, tz_name: str
    ) -> dict[str, Any]:
        return {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "hourly": ["precipitation", "temperature_2m", "wind_speed_10m", "cloudcover"],
            "timezone": tz_name,
        }

    @staticmethod
    def _base_drainage_coefficient(surface_type: str) -> float:
        soil_k_matrix = {
            "asphalt": 0.50,
            "sand": 0.30,
            "gravel": 0.15,
            "grass": 0.10,
            "dirt": 0.08,
            "earth": 0.08,
            "clay": 0.04,
        }
        return soil_k_matrix.get(surface_type.lower(), 0.08)

    @staticmethod
    def _normalize_surface_type(surface_type: Any) -> str:
        if not isinstance(surface_type, str) or not surface_type.strip():
            return "dirt"
        return MUD_SURFACE_ALIASES.get(surface_type.strip().lower(), "dirt")

    @staticmethod
    def _sanitize_slope_pct(value: Any) -> float | None:
        try:
            slope = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(slope):
            return None
        return max(0.0, min(60.0, abs(slope)))

    @staticmethod
    def _normalize_drainage_class(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        mapping = {
            "poor": "poor",
            "slow": "poor",
            "moderate": "moderate",
            "medium": "moderate",
            "good": "good",
            "fast": "good",
            "very_good": "very_good",
            "excellent": "very_good",
        }
        return mapping.get(normalized)

    @staticmethod
    def _terrain_drainage_factor(
        slope_pct: float | None, max_slope_pct: float | None = None
    ) -> float:
        """Heuristic slope adjustment: steeper slopes shed water faster."""
        if slope_pct is None and max_slope_pct is None:
            return 1.0
        avg = slope_pct if slope_pct is not None else 0.0
        peak = max_slope_pct if max_slope_pct is not None else avg
        composite = (avg * 0.7) + (peak * 0.3)
        return max(0.7, min(1.8, 1.0 + (composite / 40.0)))

    @staticmethod
    def _soil_drainage_factor(drainage_class: str | None) -> float:
        """Heuristic soil-drainage adjustment; unknown keeps neutral factor."""
        factors = {
            "poor": 0.75,
            "moderate": 1.0,
            "good": 1.25,
            "very_good": 1.45,
        }
        if drainage_class is None:
            return 1.0
        return factors.get(drainage_class, 1.0)

    @classmethod
    def _infer_drainage_class(
        cls, surface_type: str, slope_pct: float | None, max_slope_pct: float | None
    ) -> str:
        """Infer drainage proxy from surface and route slope; not soil data."""
        surface = (surface_type or "dirt").lower()
        avg = slope_pct if slope_pct is not None else 0.0
        peak = max_slope_pct if max_slope_pct is not None else avg
        steep = avg >= 8.0 or peak >= 15.0
        flat = avg <= 2.0 and peak <= 5.0

        base = {
            "asphalt": "very_good",
            "gravel": "good",
            "sand": "good",
            "grass": "moderate",
            "dirt": "moderate",
            "earth": "moderate",
            "clay": "poor",
        }.get(surface, "moderate")

        order = ["poor", "moderate", "good", "very_good"]
        idx = order.index(base)
        if steep and idx < len(order) - 1:
            idx += 1
        if flat and idx > 0 and surface in {"clay", "earth", "dirt", "grass"}:
            idx -= 1
        return order[idx]

    @classmethod
    def _resolve_drainage_class(
        cls,
        surface_type: str,
        slope_pct: float | None,
        max_slope_pct: float | None,
        drainage_input: str | None,
    ) -> tuple[str, str]:
        if drainage_input is not None:
            return drainage_input, "provided"
        inferred = cls._infer_drainage_class(surface_type, slope_pct, max_slope_pct)
        if slope_pct is None and max_slope_pct is None:
            return inferred, "inferred_from_surface"
        return inferred, "inferred_from_surface_and_slope"

    @staticmethod
    def _model_confidence(
        slope_pct: float | None,
        max_slope_pct: float | None,
        drainage_class: str | None,
        drainage_source: str,
    ) -> tuple[str, str]:
        has_slope = slope_pct is not None or max_slope_pct is not None
        if drainage_source == "provided" and has_slope:
            return (
                "low-medium",
                "Heuristic model with route slope and provided drainage hint; no field calibration.",
            )
        if drainage_source.startswith("inferred") and has_slope:
            return (
                "low",
                "Heuristic model with inferred drainage proxy from surface+slope; not soil ground truth.",
            )
        if drainage_source.startswith("inferred"):
            return (
                "low",
                "Heuristic model with drainage proxy inferred from surface only; no soil/DEM calibration.",
            )
        return (
            "low",
            "Heuristic model using weather+surface only; no soil/DEM/slope calibration.",
        )

    @staticmethod
    def _coerce_float(value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _iter_hourly_points(times, precips, temps, winds, clouds, local_tz):
        max_len = min(len(times), len(precips), len(temps), len(winds), len(clouds))
        for i in range(max_len):
            current_dt = datetime.fromisoformat(times[i]).replace(tzinfo=local_tz)
            rain = None if precips[i] is None else float(precips[i])
            temp = None if temps[i] is None else float(temps[i])
            wind = None if winds[i] is None else float(winds[i])
            cloud = None if clouds[i] is None else float(clouds[i])
            yield current_dt, rain, temp, wind, cloud

    @staticmethod
    def _dry_time_eta(
        moisture: float, base_k: float, avg_recent_dt: float, surface_type: str
    ) -> int:
        dry_threshold = 2.0
        eta_hours = 0
        sim_M = moisture

        while sim_M > dry_threshold and eta_hours < 96:
            iter_k = base_k * 0.3 if (surface_type == "clay" and sim_M > 12.0) else base_k
            sim_M = sim_M * math.exp(-iter_k * avg_recent_dt)
            eta_hours += 1

        return eta_hours

    @staticmethod
    def _traction_risk(
        traction_index: float,
        surface_type: str = "dirt",
    ) -> tuple[str, str]:
        """Translate the raw slip index into a surface-aware grip briefing.

        Args:
            traction_index: Combined rain/moisture slip index.
            surface_type: Normalized TAEL surface key.
        Returns:
            A ``(level, advice)`` pair. Hard surfaces never report mud packing.
        """
        normalized_surface = surface_type.strip().lower()
        if normalized_surface in {"asphalt", "concrete", "paved", "road"}:
            if traction_index < 2.0:
                return "Low", "Firm tarmac grip. Minimal slip risk."
            if traction_index < 6.0:
                return "Medium", "Wet tarmac: reduced grip, watch manhole covers and paint."
            return "Medium", "Standing water on pavement: aquaplaning risk in the wetter sections."

        if traction_index < 2.0:
            return "Low", "Maximum grip. Surface is hardpack."
        if traction_index < 6.0:
            return "Medium", "Greasy top layer. Watch off-cambers."
        return "High", "Zero traction. Tires will pack instantly."

    def _damage_risk(self, moisture: float) -> tuple[str, str]:
        if moisture < self.config.threshold_low_max_mm:
            return "Low", "Trail structure is solid."
        if moisture < self.config.threshold_high_max_mm - 5.0:
            return "Medium", "Sub-surface is soft. Rutting possible."
        return "Extreme", "DO NOT RIDE. Structural damage likely."

    def _global_mud_label(self, moisture: float) -> str:
        if moisture < self.config.threshold_low_max_mm:
            return "Low"
        if moisture < self.config.threshold_medium_max_mm:
            return "Medium"
        if moisture < self.config.threshold_high_max_mm:
            return "High"
        return "Extreme"


def _get_seasonal_saturation_bias(reference_date: datetime, lat: float) -> float:
    month = reference_date.month
    is_northern_hemisphere = lat >= 0

    if is_northern_hemisphere:
        seasonal_map = {
            12: 18.0,
            1: 20.0,
            2: 18.0,
            3: 12.0,
            4: 8.0,
            5: 4.0,
            6: 1.0,
            7: 0.0,
            8: 0.0,
            9: 2.0,
            10: 6.0,
            11: 14.0,
        }
    else:
        seasonal_map = {
            6: 18.0,
            7: 20.0,
            8: 18.0,
            9: 12.0,
            10: 8.0,
            11: 4.0,
            12: 1.0,
            1: 0.0,
            2: 0.0,
            3: 2.0,
            4: 6.0,
            5: 14.0,
        }

    return float(seasonal_map.get(month, 0.0))


service = MudAnalysisService()


def get_mud_risk_analysis(
    lat: float,
    lon: float,
    surface_type: str = "dirt",
    target_date: str | None = None,
    avg_slope_pct: float | None = None,
    soil_drainage_class: str | None = None,
    max_gradient_pct: float | None = None,
) -> dict[str, Any]:
    return service.get_mud_risk_analysis(
        lat=lat,
        lon=lon,
        surface_type=surface_type,
        target_date=target_date,
        avg_slope_pct=avg_slope_pct,
        soil_drainage_class=soil_drainage_class,
        max_gradient_pct=max_gradient_pct,
    )
