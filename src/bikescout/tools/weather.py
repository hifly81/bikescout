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
from datetime import date, datetime, time
from typing import Any, Dict

import requests
from timezonefinder import TimezoneFinder

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

REQUIRED_HOURLY_FIELDS = (
    "time",
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "windspeed_10m",
    "windgusts_10m",
    "winddirection_10m",
)

# WMO weather interpretation codes used by Open-Meteo.
WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherDataError(ValueError):
    """Raised when provider data is missing, inconsistent or out of range."""


def describe_weather_code(code: Any) -> tuple[int | None, str | None]:
    """Map a WMO code to a numeric code and its plain-language description.

    Args:
        code: Raw weather code returned by the provider.

    Returns:
        A ``(code, description)`` pair. Both values are ``None`` when the
        provider omitted the code, so clients never see an invented condition.
    """
    if code is None:
        return None, None
    try:
        numeric = int(code)
    except (TypeError, ValueError) as exc:
        raise WeatherDataError(f"Invalid weather code: {code!r}") from exc
    description = WEATHER_CODE_DESCRIPTIONS.get(numeric, "Unclassified weather code")
    return numeric, description


def get_safety_advice(
    app_temp: float,
    rain_prob: int,
    rain_mm: float,
    wind_speed: float,
    wind_gusts: float,
    condition: str | None = None,
) -> dict[str, Any]:
    """Build a cycling safety briefing from the verified worst-case values.

    ``condition`` is descriptive context only; it never weakens or replaces a
    threshold crossing. Callers that cannot supply verified data must use
    ``unavailable_safety_advice`` instead of this function.
    """
    wind_risk_score = (wind_speed * 0.4) + (wind_gusts * 0.6)

    if rain_mm > 10.0 or wind_risk_score > 55:
        status_label = "[NOT RECOMMENDED]"
        status_msg = "Critical risk: Heavy rain volume or dangerous wind gusts. Riding is unsafe."
    elif rain_mm > 2.0 or wind_risk_score > 35:
        status_label = "[CAUTION]"
        status_msg = (
            "Significant hazards: Moderate rain or strong crosswinds expected. Use extreme care."
        )
    elif rain_prob > 30 or wind_speed > 25:
        status_label = "[WATCH]"
        status_msg = (
            "Sub-optimal: Light rain possible or stiff breeze. Manageable for experienced riders."
        )
    else:
        status_label = "[GO]"
        status_msg = "No threshold exceedance in the available forecast; verify conditions locally."

    if app_temp < 5:
        gear = "Deep Winter (Heavy thermal layers, insulated gloves, overshoes, skull cap)"
    elif app_temp <= 12:
        gear = "Spring/Fall (Knee/arm warmers, windproof gilet, medium base layer)"
    elif app_temp <= 25:
        gear = "Standard (Short sleeves, summer bibs, light base layer)"
    else:
        gear = "High Summer (Ultra-light kit, double hydration priority, sunscreen)"

    return {
        "status": status_label,
        "message": status_msg,
        "wind_risk_score": round(wind_risk_score, 1),
        "gear_advice": gear,
        "condition_at_peak_risk": condition,
    }


def unavailable_safety_advice(reason: str) -> dict[str, Any]:
    """Return an explicit no-data verdict; never imply that conditions are safe."""
    return {
        "status": "[UNAVAILABLE]",
        "message": f"Safety assessment unavailable: {reason}",
        "wind_risk_score": None,
        "gear_advice": None,
        "condition_at_peak_risk": None,
    }


@dataclass(frozen=True)
class WeatherConfig:
    open_meteo_url: str = OPEN_METEO_URL
    request_timeout_seconds: float = 10.0


class WeatherService:
    def __init__(
        self,
        config: WeatherConfig | None = None,
        requests_session: Any | None = None,
        timezone_finder: Any | None = None,
        now_func=None,
    ) -> None:
        self.config = config or WeatherConfig()
        self.requests_session = requests_session or requests
        self.timezone_finder = timezone_finder or TimezoneFinder()
        self.now_func = now_func or (lambda tz: datetime.now(tz))

    def get_weather_forecast(
        self, lat: float, lon: float, target_date: str | None = None, target_hour: int = 9
    ) -> Dict[str, Any]:
        """Fetch the full requested day and derive a worst-case cycling briefing.

        ``target_hour`` anchors the reference conditions; the safety verdict
        always scans every hourly slot returned for the day.
        """
        try:
            latitude = self._require_coordinate(lat, -90.0, 90.0, "latitude")
            longitude = self._require_coordinate(lon, -180.0, 180.0, "longitude")
            reference_hour = self._normalize_target_hour(target_hour)

            tz_name = self._resolve_timezone_name(latitude, longitude)
            local_tz = zoneinfo.ZoneInfo(tz_name)
            target_dt_local = self._target_datetime(local_tz, target_date, reference_hour)

            params = self._build_forecast_params(latitude, longitude, tz_name, target_dt_local)

            response = self.requests_session.get(
                self.config.open_meteo_url,
                params=params,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()

            hourly = self._normalize_hourly(data.get("hourly"))
            ref_idx = self._reference_index(hourly, target_dt_local)
            forecast_summary = self._forecast_summary(hourly)

            weather_code, condition = describe_weather_code(
                hourly["weathercode"][ref_idx] if hourly["weathercode"] else None
            )

            return {
                "status": "Success",
                "metadata": {
                    "date_analyzed": target_dt_local.date().isoformat(),
                    "local_timezone": tz_name,
                    "target_time_local": target_dt_local.strftime("%H:%M"),
                    "location": {"lat": latitude, "lon": longitude},
                    "analysis_scope": "full_day",
                    "forecast_window": {
                        "start": hourly["time"][0],
                        "end": hourly["time"][-1],
                    },
                    "forecast_source": "Open-Meteo",
                },
                "tactical_forecast": forecast_summary,
                "reference_conditions": {
                    "temp_actual": hourly["temperature_2m"][ref_idx],
                    "temp_apparent": hourly["apparent_temperature"][ref_idx],
                    "rain_probability": hourly["precipitation_probability"][ref_idx],
                    "precipitation_mm": hourly["precipitation"][ref_idx],
                    "wind_speed": hourly["windspeed_10m"][ref_idx],
                    "wind_gusts": hourly["windgusts_10m"][ref_idx],
                    "wind_direction": hourly["winddirection_10m"][ref_idx],
                    "reference_hour_local": f"{reference_hour:02d}:00",
                    "temp_max": max(hourly["temperature_2m"]),
                    "weather_code": weather_code,
                    "condition": condition,
                },
                "safety_advice": self._worst_case_safety_advice(forecast_summary),
            }

        except requests.exceptions.RequestException as e:
            return {"status": "Error", "message": f"Weather API Connection Error: {str(e)}"}
        except WeatherDataError as e:
            return {"status": "Error", "message": f"Weather data validation error: {e}"}
        except Exception as e:
            return {"status": "Error", "message": f"Unexpected Weather Engine Error: {str(e)}"}

    def _resolve_timezone_name(self, lat: float, lon: float) -> str:
        tz_name = self.timezone_finder.timezone_at(lng=lon, lat=lat)
        return tz_name or "UTC"

    def _target_datetime(
        self, local_tz: zoneinfo.ZoneInfo, target_date: str | None, target_hour: int
    ) -> datetime:
        if target_date:
            return datetime.combine(
                date.fromisoformat(target_date),
                time(hour=target_hour),
            ).replace(tzinfo=local_tz)

        now_local = self.now_func(local_tz)
        return now_local.replace(hour=target_hour, minute=0, second=0, microsecond=0)

    @staticmethod
    def _build_forecast_params(
        lat: float, lon: float, tz_name: str, target_dt_local: datetime
    ) -> dict[str, Any]:
        return {
            "latitude": lat,
            "longitude": lon,
            "hourly": [
                "temperature_2m",
                "apparent_temperature",
                "precipitation_probability",
                "precipitation",
                "windspeed_10m",
                "windgusts_10m",
                "winddirection_10m",
                "weathercode",
            ],
            "timezone": tz_name,
            "start_date": target_dt_local.date().isoformat(),
            "end_date": target_dt_local.date().isoformat(),
        }

    @staticmethod
    def _require_coordinate(value: Any, minimum: float, maximum: float, name: str) -> float:
        try:
            coordinate = float(value)
        except (TypeError, ValueError) as exc:
            raise WeatherDataError(
                f"{name} must be a number between {minimum} and {maximum}"
            ) from exc
        if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
            raise WeatherDataError(f"{name} must be between {minimum} and {maximum}")
        return coordinate

    @staticmethod
    def _require_float(value: Any, field: str, index: int) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise WeatherDataError(f"{field}[{index}] must be numeric") from exc
        if not math.isfinite(number):
            raise WeatherDataError(f"{field}[{index}] must be finite")
        return number

    @classmethod
    def _normalize_hourly(cls, hourly: Any) -> dict[str, list[Any]]:
        """Validate provider arrays and return numeric, length-aligned series."""
        if not isinstance(hourly, dict):
            raise WeatherDataError("No hourly data returned from provider.")

        for field in REQUIRED_HOURLY_FIELDS:
            values = hourly.get(field)
            if not isinstance(values, list) or not values:
                raise WeatherDataError(f"Hourly field {field} is missing or empty.")

        times = hourly["time"]
        expected_length = len(times)
        normalized: dict[str, list[Any]] = {"time": [str(value) for value in times]}

        for field in REQUIRED_HOURLY_FIELDS[1:]:
            values = hourly[field]
            if len(values) != expected_length:
                raise WeatherDataError(
                    f"Hourly field {field} has {len(values)} values; expected {expected_length}."
                )
            normalized[field] = [
                cls._require_float(value, field, index) for index, value in enumerate(values)
            ]

        for index, direction in enumerate(normalized["winddirection_10m"]):
            if not 0 <= direction <= 360:
                raise WeatherDataError(
                    f"winddirection_10m[{index}] must be between 0 and 360 degrees."
                )

        raw_codes = hourly.get("weathercode") or [None] * expected_length
        if len(raw_codes) != expected_length:
            raise WeatherDataError(
                f"Hourly field weathercode has {len(raw_codes)} values; expected {expected_length}."
            )
        normalized["weathercode"] = [describe_weather_code(value)[0] for value in raw_codes]
        return normalized

    @staticmethod
    def _reference_index(hourly: dict[str, list[Any]], target_dt_local: datetime) -> int:
        target_local_str = target_dt_local.strftime("%Y-%m-%dT%H:00")
        try:
            return hourly["time"].index(target_local_str)
        except ValueError as exc:
            raise WeatherDataError(
                f"Target hour {target_dt_local.strftime('%H:%M')} is not present in provider data."
            ) from exc

    @staticmethod
    def _forecast_summary(hourly: dict[str, Any]) -> list[dict[str, Any]]:
        """Build numeric hourly snapshots from validated provider series."""
        normalized = WeatherService._normalize_hourly(hourly)
        times = normalized["time"]
        codes = normalized["weathercode"]

        forecast_summary: list[dict[str, Any]] = []
        for index, raw_time in enumerate(times):
            dt_naive = datetime.fromisoformat(raw_time)
            code, condition = describe_weather_code(codes[index])
            forecast_summary.append(
                {
                    "time": dt_naive.strftime("%H:%M"),
                    "temp": normalized["temperature_2m"][index],
                    "app_temp": normalized["apparent_temperature"][index],
                    "rain_prob": int(round(normalized["precipitation_probability"][index])),
                    "rain_mm": normalized["precipitation"][index],
                    "wind": normalized["windspeed_10m"][index],
                    "gusts": normalized["windgusts_10m"][index],
                    "wind_direction": int(round(normalized["winddirection_10m"][index])),
                    "weather_code": code,
                    "condition": condition,
                }
            )

        return forecast_summary

    @staticmethod
    def _worst_case_safety_advice(forecast: list[dict[str, Any]]) -> dict[str, Any]:
        """Build the safety briefing from the worst point of the forecast window.

        Peak wind and gusts are taken from the same hour to avoid combining
        unrelated readings. Rain is the maximum of the window, clothing
        advice uses the coldest apparent temperature, and the WMO condition of
        the peak-risk hour is reported as context.

        Args:
            forecast: Hourly snapshots produced by _forecast_summary.
        Returns:
            A SafetyAdvice dictionary for the whole mission window.
        """
        if not forecast:
            return unavailable_safety_advice("the forecast window contains no hourly data")

        peak_risk = -1.0
        peak_wind = 0.0
        peak_gusts = 0.0
        peak_condition: str | None = None
        coldest_app_temp: float | None = None
        max_rain_prob = 0.0
        max_rain_mm = 0.0

        for entry in forecast:
            wind = WeatherService._coerce_float(entry.get("wind"), 0.0)
            gusts = WeatherService._coerce_float(entry.get("gusts"), 0.0)
            rain_prob = WeatherService._coerce_float(entry.get("rain_prob"), 0.0)
            rain_mm = WeatherService._coerce_float(entry.get("rain_mm"), 0.0)
            app_temp = WeatherService._coerce_float(entry.get("app_temp"), 20.0)

            risk = (wind * 0.4) + (gusts * 0.6)
            if risk > peak_risk:
                peak_risk = risk
                peak_wind = wind
                peak_gusts = gusts
                peak_condition = entry.get("condition")

            coldest_app_temp = (
                app_temp if coldest_app_temp is None else min(coldest_app_temp, app_temp)
            )
            max_rain_prob = max(max_rain_prob, rain_prob)
            max_rain_mm = max(max_rain_mm, rain_mm)

        return get_safety_advice(
            app_temp=coldest_app_temp if coldest_app_temp is not None else 20.0,
            rain_prob=int(max_rain_prob),
            rain_mm=max_rain_mm,
            wind_speed=peak_wind,
            wind_gusts=peak_gusts,
            condition=peak_condition,
        )

    @staticmethod
    def _coerce_float(value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _normalize_target_hour(target_hour: Any) -> int:
        try:
            hour = int(target_hour)
        except (TypeError, ValueError) as exc:
            raise WeatherDataError("target_hour must be an integer between 0 and 23") from exc
        if not 0 <= hour <= 23:
            raise WeatherDataError("target_hour must be between 0 and 23")
        return hour

    @staticmethod
    def _circular_mean_degrees(
        directions: list[float],
    ) -> tuple[int | None, bool]:
        """Return the circular mean bearing and whether it is undefined.

        Opposing directions produce a zero-length resultant; in that case no
        bearing is reported instead of inventing an arithmetic midpoint.
        """
        if not directions:
            return None, False
        x_component = sum(math.cos(math.radians(value)) for value in directions)
        y_component = sum(math.sin(math.radians(value)) for value in directions)
        if math.hypot(x_component, y_component) < 1e-9:
            return None, True
        mean = math.degrees(math.atan2(y_component, x_component)) % 360
        return int(round(mean)) % 360, False


service = WeatherService()


def get_weather_forecast(
    lat: float, lon: float, target_date: str | None = None, target_hour: int = 9
) -> Dict[str, Any]:
    return service.get_weather_forecast(
        lat=lat,
        lon=lon,
        target_date=target_date,
        target_hour=target_hour,
    )


def apply_weather_windowing(weather_data: Dict, start: int, end: int) -> Dict:
    """Restrict the forecast to a ride window and recompute its safety verdict."""
    filtered_forecast = []
    window_temps, window_winds, window_dirs = [], [], []

    if "reference_conditions" not in weather_data:
        weather_data["reference_conditions"] = {}

    for hour_info in weather_data.get("tactical_forecast", []):
        try:
            h_int = int(hour_info["time"].split(":")[0])
            if start <= h_int <= end:
                filtered_forecast.append(hour_info)

                t_val = float(str(hour_info["temp"]).strip())
                w_val = float(str(hour_info["wind"]).strip())
                w_dir_str = str(hour_info.get("wind_direction", "0")).strip()
                w_dir = float(w_dir_str)

                window_temps.append(t_val)
                window_winds.append(w_val)
                window_dirs.append(w_dir)
        except (ValueError, KeyError):
            continue

    if window_temps:
        mean_direction, ambiguous = WeatherService._circular_mean_degrees(window_dirs)
        weather_data["reference_conditions"].update(
            {
                "temp": round(sum(window_temps) / len(window_temps), 1),
                "wind_speed": round(sum(window_winds) / len(window_winds), 1),
                "wind_dir_degrees": mean_direction,
                "wind_direction_ambiguous": ambiguous,
                "reference_hour": f"Calculated window {start:02d}-{end:02d}",
            }
        )

    weather_data["tactical_forecast"] = filtered_forecast
    weather_data["safety_advice"] = WeatherService._worst_case_safety_advice(filtered_forecast)
    return weather_data
