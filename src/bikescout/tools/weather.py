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
from datetime import date, datetime, time
from typing import Any, Dict

import requests
import zoneinfo
from timezonefinder import TimezoneFinder


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_safety_advice(app_temp: float, rain_prob: int, rain_mm: float, wind_speed: float, wind_gusts: float) -> dict:
    wind_risk_score = (wind_speed * 0.4) + (wind_gusts * 0.6)

    if rain_mm > 10.0 or wind_risk_score > 55:
        status_label = "? [NOT RECOMMENDED]"
        status_msg = "Critical risk: Heavy rain volume or dangerous wind gusts. Riding is unsafe."
    elif rain_mm > 2.0 or wind_risk_score > 35:
        status_label = "? [CAUTION]"
        status_msg = "Significant hazards: Moderate rain or strong crosswinds expected. Use extreme care."
    elif rain_prob > 30 or wind_speed > 25:
        status_label = "? [WATCH]"
        status_msg = "Sub-optimal: Light rain possible or stiff breeze. Manageable for experienced riders."
    else:
        status_label = "? [GO]"
        status_msg = "Ideal conditions: Low wind, dry, and safe."

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

    def get_weather_forecast(self, lat: float, lon: float, target_date: str = None, target_hour: int = 9) -> Dict[str, Any]:
        try:
            lat = self._coerce_float(lat, 0.0)
            lon = self._coerce_float(lon, 0.0)
            target_hour = self._normalize_target_hour(target_hour)

            tz_name = self._resolve_timezone_name(lat, lon)
            local_tz = zoneinfo.ZoneInfo(tz_name)
            target_dt_local = self._target_datetime(local_tz, target_date, target_hour)

            params = self._build_forecast_params(lat, lon, tz_name, target_dt_local)

            response = self.requests_session.get(
                self.config.open_meteo_url,
                params=params,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()

            if "hourly" not in data:
                return {"status": "Error", "message": "No hourly data returned from provider."}

            hourly = data["hourly"]
            ref_idx = self._reference_index(hourly, target_dt_local)

            forecast_summary = self._forecast_summary(hourly)

            curr_app_temp = hourly["apparent_temperature"][ref_idx]
            curr_rain_prob = hourly["precipitation_probability"][ref_idx]
            curr_rain_mm = hourly["precipitation"][ref_idx]
            curr_wind = hourly["windspeed_10m"][ref_idx]
            curr_gusts = hourly["windgusts_10m"][ref_idx]
            curr_wind_dir = hourly["winddirection_10m"][ref_idx]

            hourly_temps = hourly.get("temperature_2m", [])
            max_temp_value = max(hourly_temps) if hourly_temps else "N/A"

            return {
                "status": "Success",
                "metadata": {
                    "date_analyzed": target_dt_local.date().isoformat(),
                    "local_timezone": tz_name,
                    "target_time_local": target_dt_local.strftime("%H:%M"),
                    "location": {"lat": lat, "lon": lon},
                },
                "tactical_forecast": forecast_summary,
                "reference_conditions": {
                    "temp_actual": hourly["temperature_2m"][ref_idx],
                    "temp_apparent": curr_app_temp,
                    "rain_probability": curr_rain_prob,
                    "precipitation_mm": curr_rain_mm,
                    "wind_speed": curr_wind,
                    "wind_gusts": curr_gusts,
                    "wind_direction": curr_wind_dir,
                    "reference_hour_local": f"{target_hour}:00",
                    "temp_max": max_temp_value,
                },
                "safety_advice": get_safety_advice(
                    app_temp=curr_app_temp,
                    rain_prob=curr_rain_prob,
                    rain_mm=curr_rain_mm,
                    wind_speed=curr_wind,
                    wind_gusts=curr_gusts,
                ),
            }

        except requests.exceptions.RequestException as e:
            return {"status": "Error", "message": f"Weather API Connection Error: {str(e)}"}
        except Exception as e:
            return {"status": "Error", "message": f"Unexpected Weather Engine Error: {str(e)}"}

    def _resolve_timezone_name(self, lat: float, lon: float) -> str:
        tz_name = self.timezone_finder.timezone_at(lng=lon, lat=lat)
        return tz_name or "UTC"

    def _target_datetime(self, local_tz: zoneinfo.ZoneInfo, target_date: str | None, target_hour: int) -> datetime:
        if target_date:
            return datetime.combine(
                date.fromisoformat(target_date),
                time(hour=target_hour),
            ).replace(tzinfo=local_tz)

        now_local = self.now_func(local_tz)
        return now_local.replace(hour=target_hour, minute=0, second=0, microsecond=0)

    @staticmethod
    def _build_forecast_params(lat: float, lon: float, tz_name: str, target_dt_local: datetime) -> dict[str, Any]:
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
    def _reference_index(hourly: dict, target_dt_local: datetime) -> int:
        target_local_str = target_dt_local.strftime("%Y-%m-%dT%H:00")
        try:
            return hourly["time"].index(target_local_str)
        except (ValueError, KeyError):
            return 0

    @staticmethod
    def _forecast_summary(hourly: dict) -> list[dict[str, str]]:
        forecast_summary = []

        times = hourly.get("time", [])
        max_len = min(
            len(times),
            len(hourly.get("temperature_2m", [])),
            len(hourly.get("apparent_temperature", [])),
            len(hourly.get("precipitation_probability", [])),
            len(hourly.get("precipitation", [])),
            len(hourly.get("windspeed_10m", [])),
            len(hourly.get("windgusts_10m", [])),
            len(hourly.get("winddirection_10m", [])),
        )

        for i in range(max_len):
            dt_naive = datetime.fromisoformat(times[i])
            local_time_str = dt_naive.strftime("%H:%M")

            forecast_summary.append(
                {
                    "time": local_time_str,
                    "temp": f"{hourly['temperature_2m'][i]}",
                    "app_temp": f"{hourly['apparent_temperature'][i]}",
                    "rain_prob": f"{hourly['precipitation_probability'][i]}",
                    "rain_mm": f"{hourly['precipitation'][i]}",
                    "wind": f"{hourly['windspeed_10m'][i]}",
                    "gusts": f"{hourly['windgusts_10m'][i]}",
                    "wind_direction": f"{hourly['winddirection_10m'][i]}",
                }
            )

        return forecast_summary

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
        except (TypeError, ValueError):
            return 9
        return max(0, min(hour, 23))


service = WeatherService()


def get_weather_forecast(lat: float, lon: float, target_date: str = None, target_hour: int = 9) -> Dict[str, Any]:
    return service.get_weather_forecast(
        lat=lat,
        lon=lon,
        target_date=target_date,
        target_hour=target_hour,
    )


def apply_weather_windowing(weather_data: Dict, start: int, end: int) -> Dict:
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
        weather_data["reference_conditions"].update(
            {
                "temp": round(sum(window_temps) / len(window_temps), 1),
                "wind_speed": round(sum(window_winds) / len(window_winds), 1),
                "wind_dir_degrees": int(sum(window_dirs) / len(window_dirs)),
                "reference_hour": f"Calculated window {start:02d}-{end:02d}",
            }
        )

    weather_data["tactical_forecast"] = filtered_forecast
    return weather_data