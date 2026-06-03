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
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Literal

import requests
from astral import Observer
from astral.sun import elevation
from timezonefinder import TimezoneFinder


ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


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

    def get_mud_risk_analysis(
            self,
            lat: float,
            lon: float,
            surface_type: Literal["asphalt", "sand", "gravel", "grass", "dirt", "earth", "clay"] = "dirt",
            target_date: str = None,
    ) -> Dict[str, Any]:
        try:
            lat = self._coerce_float(lat, 0.0)
            lon = self._coerce_float(lon, 0.0)
            normalized_surface_type = self._normalize_surface_type(surface_type)

            tz_name = self._resolve_timezone_name(lat, lon)
            local_tz = zoneinfo.ZoneInfo(tz_name)

            reference_date = self._reference_date(local_tz, target_date)
            end_date = reference_date
            start_date = end_date - timedelta(hours=72)

            is_predictive = reference_date > self.now_func(local_tz)
            url = self.config.forecast_url if is_predictive else self.config.archive_url
            params = self._build_weather_params(lat, lon, start_date, end_date, tz_name)

            response = self.requests_session.get(url, params=params, timeout=self.config.request_timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            data = payload.get("hourly", {}) if isinstance(payload, dict) else {}

            times = data.get("time", [])
            precips = data.get("precipitation", [])
            temps = data.get("temperature_2m", [])
            winds = data.get("wind_speed_10m", [])
            clouds = data.get("cloudcover", [])

            if not times:
                raise ValueError("No hourly weather data returned from API.")

            base_k = self._base_drainage_coefficient(normalized_surface_type)

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

                total_raw_rain += rain
                time_diff = (end_date - current_dt).total_seconds()

                if time_diff <= (12 * 3600):
                    recent_rain_12h += rain

                solar_alt = self.solar_altitude_func(lat, lon, current_dt)

                temp_factor = max(0.01, (temp / 20.0))
                wind_factor = max(0.5, (wind / 15.0))

                solar_factor = 1.0
                if solar_alt > 20:
                    solar_factor += ((solar_alt / 90.0) * (1.0 - (cloud / 100.0)))
                    pet_hours += 1

                Dt = temp_factor * wind_factor * solar_factor

                if time_diff <= (24 * 3600):
                    recent_dt_sum += Dt

                current_k = base_k
                if normalized_surface_type == "clay" and M > 12.0:
                    current_k *= 0.3

                M = (M * math.exp(-current_k * Dt)) + rain

            eta_hours = self._dry_time_eta(
                moisture=M,
                base_k=base_k,
                avg_recent_dt=max(0.1, (recent_dt_sum / 24.0)),
                surface_type=normalized_surface_type,
            )

            traction_risk, traction_advice = self._traction_risk((recent_rain_12h * 1.5) + (M * 0.5))
            damage_risk, damage_advice = self._damage_risk(M)
            global_label = self._global_mud_label(M)

            return {
                "status": "Success",
                "metadata": {
                    "target_date": reference_date.isoformat(),
                    "timezone": tz_name,
                    "is_predictive": is_predictive,
                    "model": self.config.model_name,
                },
                "environmental_context": {
                    "total_rain_72h_mm": round(total_raw_rain, 1),
                    "integrated_pet_hours": pet_hours,
                    "reservoir_moisture_mm": round(M, 2),
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

        except Exception as e:
            return {
                "status": "Error",
                "message": f"Tactical Planner failure: {str(e)}",
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
    def _build_weather_params(lat: float, lon: float, start_date: datetime, end_date: datetime, tz_name: str) -> dict[str, Any]:
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
        return surface_type.strip().lower()

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
            rain = float(precips[i] or 0.0)
            temp = float(temps[i] or 0.0)
            wind = float(winds[i] or 0.0)
            cloud = float(clouds[i] or 0.0)
            yield current_dt, rain, temp, wind, cloud

    @staticmethod
    def _dry_time_eta(moisture: float, base_k: float, avg_recent_dt: float, surface_type: str) -> int:
        dry_threshold = 2.0
        eta_hours = 0
        sim_M = moisture

        while sim_M > dry_threshold and eta_hours < 96:
            iter_k = base_k * 0.3 if (surface_type == "clay" and sim_M > 12.0) else base_k
            sim_M = sim_M * math.exp(-iter_k * avg_recent_dt)
            eta_hours += 1

        return eta_hours

    @staticmethod
    def _traction_risk(traction_index: float) -> tuple[str, str]:
        if traction_index < 2.0:
            return "Low", "Maximum grip. Surface is hardpack."
        if traction_index < 6.0:
            return "Medium", "Greasy top layer. Watch off-cambers."
        return "High", "Zero traction. Tires will pack instantly."

    @staticmethod
    def _damage_risk(moisture: float) -> tuple[str, str]:
        if moisture < 4.0:
            return "Low", "Trail structure is solid."
        if moisture < 15.0:
            return "Medium", "Sub-surface is soft. Rutting possible."
        return "Extreme", "DO NOT RIDE. Structural damage likely."

    @staticmethod
    def _global_mud_label(moisture: float) -> str:
        if moisture < 4.0:
            return "Low"
        if moisture < 12.0:
            return "Medium"
        if moisture < 20.0:
            return "High"
        return "Extreme"


def _get_seasonal_saturation_bias(reference_date: datetime, lat: float) -> float:
    month = reference_date.month
    is_northern_hemisphere = lat >= 0

    if is_northern_hemisphere:
        seasonal_map = {
            12: 18.0, 1: 20.0, 2: 18.0,
            3: 12.0, 4: 8.0, 5: 4.0,
            6: 1.0, 7: 0.0, 8: 0.0,
            9: 2.0, 10: 6.0, 11: 14.0,
        }
    else:
        seasonal_map = {
            6: 18.0, 7: 20.0, 8: 18.0,
            9: 12.0, 10: 8.0, 11: 4.0,
            12: 1.0, 1: 0.0, 2: 0.0,
            3: 2.0, 4: 6.0, 5: 14.0,
        }

    return float(seasonal_map.get(month, 0.0))


service = MudAnalysisService()


def get_mud_risk_analysis(
        lat: float,
        lon: float,
        surface_type: Literal["asphalt", "sand", "gravel", "grass", "dirt", "earth", "clay"] = "dirt",
        target_date: str = None,
) -> Dict[str, Any]:
    return service.get_mud_risk_analysis(
        lat=lat,
        lon=lon,
        surface_type=surface_type,
        target_date=target_date,
    )