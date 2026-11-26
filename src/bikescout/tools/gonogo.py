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
from datetime import date
from typing import Any, Literal

from astral import LocationInfo
from astral.sun import sun
from timezonefinder import TimezoneFinder

from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.weather import get_weather_forecast


@dataclass(frozen=True)
class GoNoGoConfig:
    rain_penalty_start_pct: float = 30.0
    rain_penalty_high_factor: float = 3.0
    rain_penalty_low_factor: float = 0.5
    wind_penalty_start_kmh: float = 25.0
    wind_penalty_factor: float = 2.0
    cold_threshold_c: float = 10.0
    cold_penalty_factor: float = 4.0
    freeze_penalty: float = 20.0
    heat_threshold_c: float = 30.0
    heat_penalty_factor: float = 5.0
    mud_penalty_factor: float = 0.6
    verdict_go: float = 75.0
    verdict_caution: float = 40.0


def get_solar_visibility(lat: float, lon: float, target_date: date) -> tuple[float, float]:
    """Calculates sunrise/sunset hours from GPS coordinates and local timezone."""
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=lon, lat=lat) or "UTC"
        location = LocationInfo("Tactical Point", "Region", tz_name, lat, lon)
        s = sun(location.observer, date=target_date, tzinfo=zoneinfo.ZoneInfo(tz_name))
        sunrise_hour = s["sunrise"].hour + (s["sunrise"].minute / 60.0)
        sunset_hour = s["sunset"].hour + (s["sunset"].minute / 60.0)
        return (sunrise_hour, sunset_hour)
    except Exception:
        return (7.0, 18.0)


def calculate_ride_windows(
    lat: float,
    lon: float,
    ride_duration_hours: float = 2.0,
    surface_type: Literal["dirt", "gravel", "asphalt", "sand", "clay"] = "dirt",
    target_date: str | None = None,
    config: GoNoGoConfig | None = None,
) -> dict[str, Any]:
    """Tactical Go/No-Go planner with solar-bounded moving windows."""
    cfg = config or GoNoGoConfig()
    try:
        t_date = date.fromisoformat(target_date) if target_date else date.today()
        sunrise_h, sunset_h = get_solar_visibility(lat, lon, t_date)

        weather_data = get_weather_forecast(lat, lon, target_date)
        if weather_data.get("status") == "Error":
            reason = weather_data.get("message") or "unknown weather provider error"
            return _error_result(
                f"Weather forecast unavailable: {reason}",
                next_step="Retry later or verify coordinates/date for weather forecast.",
                metadata=_metadata(t_date, surface_type, sunrise_h, sunset_h, ride_duration_hours),
            )

        mud_risk_data = get_mud_risk_analysis(lat, lon, surface_type, target_date=target_date)
        mud_status = str(mud_risk_data.get("status", "Error"))
        mud_score = _mud_score(mud_risk_data)
        mud_available = mud_status == "Success" and mud_score is not None

        raw_forecasts = weather_data.get("tactical_forecast", [])
        normalized_forecasts = _normalize_forecasts(raw_forecasts)
        if not normalized_forecasts:
            return _error_result(
                "Weather forecast has no usable hourly data for Go/No-Go planning.",
                next_step="Retry later or provide a date with available hourly weather data.",
                metadata=_metadata(t_date, surface_type, sunrise_h, sunset_h, ride_duration_hours),
            )

        duration_slots = _duration_slots(ride_duration_hours, len(normalized_forecasts))
        best_slot: dict[str, Any] | None = None
        highest_score = -math.inf

        for i in range(len(normalized_forecasts) - duration_slots + 1):
            window = normalized_forecasts[i : i + duration_slots]
            if window[0]["hour"] < sunrise_h or window[-1]["hour"] + 1 > sunset_h:
                continue

            avg_rain = sum(h["precip_prob"] for h in window) / duration_slots
            max_wind = max(h["wind_speed"] for h in window)
            avg_temp = sum(h["temp"] for h in window) / duration_slots
            score = _score_window(avg_rain, max_wind, avg_temp, surface_type, mud_score, cfg)

            if score > highest_score:
                highest_score = score
                best_slot = {
                    "start": window[0]["time"],
                    "end": window[-1]["time"],
                    "score": round(max(0.0, score), 1),
                    "details": {
                        "rain_avg": f"{round(avg_rain)}%",
                        "wind_max": f"{round(max_wind)} km/h",
                        "temp_avg": f"{round(avg_temp)}°C",
                        "mud_score_mm": round(mud_score, 2) if mud_score is not None else None,
                        "mud_available": mud_available,
                    },
                }

        metadata = _metadata(t_date, surface_type, sunrise_h, sunset_h, ride_duration_hours)
        metadata["mud_status"] = mud_status
        metadata["mud_available"] = mud_available
        metadata["mud_model_confidence"] = (mud_risk_data.get("metadata") or {}).get(
            "model_confidence"
        )

        if not best_slot:
            message = "No safe daylight visibility for the requested duration."
            if not mud_available:
                message = (
                    "No safe daylight window and mud analysis unavailable; "
                    "cannot fully assess rideability."
                )
            return {
                "status": "Success",
                "metadata": metadata,
                "planner_report": {
                    "verdict": "NO-GO",
                    "tactical_color": "RED",
                    "confidence_score": "0/100",
                    "best_window": "N/A",
                    "environmental_briefing": {"message": message},
                    "mud_risk_impact": _mud_impact(mud_score, mud_available),
                },
            }

        if highest_score > cfg.verdict_go:
            verdict, color = "GO", "GREEN"
        elif highest_score > cfg.verdict_caution:
            verdict, color = "CAUTION", "YELLOW"
        else:
            verdict, color = "NO-GO", "RED"

        if not mud_available and verdict == "GO":
            verdict, color = "CAUTION", "YELLOW"
            best_slot["details"]["message"] = (
                "Mud analysis unavailable; verdict downgraded to CAUTION."
            )

        return {
            "status": "Success",
            "metadata": metadata,
            "planner_report": {
                "verdict": verdict,
                "tactical_color": color,
                "confidence_score": f"{best_slot['score']}/100",
                "best_window": f"{best_slot['start']} - {best_slot['end']}",
                "environmental_briefing": best_slot["details"],
                "mud_risk_impact": _mud_impact(mud_score, mud_available),
            },
        }

    except Exception as e:
        return _error_result(
            f"Tactical Planner failed: {str(e)}",
            next_step="Verify coordinates/date and retry; inspect logs if the error persists.",
        )


def _clean_weather_value(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        cleaned = v.replace("°C", "").replace("km/h", "").replace("%", "").replace("C", "")
        try:
            return float(cleaned.strip())
        except ValueError:
            return 0.0
    return 0.0


def _normalize_forecasts(raw_forecasts: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_forecasts, list):
        return []
    normalized: list[dict[str, Any]] = []
    for h in raw_forecasts:
        if not isinstance(h, dict):
            continue
        time_str = str(h.get("time", "00:00"))
        try:
            hour_int = int(time_str.split(":")[0])
        except Exception:
            continue
        if not (0 <= hour_int <= 23):
            continue
        normalized.append(
            {
                "time": time_str,
                "hour": hour_int,
                "precip_prob": _clean_weather_value(h.get("rain_prob", 0)),
                "wind_speed": _clean_weather_value(h.get("wind", 0)),
                "temp": _clean_weather_value(h.get("temp", 15)),
            }
        )
    return normalized


def _duration_slots(ride_duration_hours: float, available: int) -> int:
    try:
        hours = float(ride_duration_hours)
    except (TypeError, ValueError):
        hours = 2.0
    if not math.isfinite(hours) or hours <= 0:
        hours = 1.0
    slots = int(math.ceil(hours))
    return max(1, min(slots, max(1, available)))


def _mud_score(mud_risk_data: dict[str, Any]) -> float | None:
    tactical = mud_risk_data.get("tactical_analysis") or {}
    raw = tactical.get("mud_risk_numeric")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return max(0.0, value)


def _mud_impact(mud_score: float | None, mud_available: bool) -> str:
    if not mud_available or mud_score is None:
        return "Unavailable"
    return f"{round(mud_score, 2)}mm"


def _score_window(
    avg_rain: float,
    max_wind: float,
    avg_temp: float,
    surface_type: str,
    mud_score: float | None,
    cfg: GoNoGoConfig,
) -> float:
    score = 100.0
    if avg_rain > cfg.rain_penalty_start_pct:
        score -= (avg_rain - cfg.rain_penalty_start_pct) * cfg.rain_penalty_high_factor
    else:
        score -= avg_rain * cfg.rain_penalty_low_factor

    if max_wind > cfg.wind_penalty_start_kmh:
        score -= (max_wind - cfg.wind_penalty_start_kmh) * cfg.wind_penalty_factor

    if avg_temp <= 0:
        score -= cfg.freeze_penalty
    if avg_temp < cfg.cold_threshold_c:
        score -= (cfg.cold_threshold_c - avg_temp) * cfg.cold_penalty_factor
    if avg_temp > cfg.heat_threshold_c:
        score -= (avg_temp - cfg.heat_threshold_c) * cfg.heat_penalty_factor

    if surface_type != "asphalt" and mud_score is not None:
        score -= mud_score * cfg.mud_penalty_factor
    return score


def _metadata(
    t_date: date, surface_type: str, sunrise_h: float, sunset_h: float, duration_hours: float
) -> dict[str, Any]:
    return {
        "analyzed_date": t_date.isoformat(),
        "surface_type": surface_type,
        "solar_window": f"{int(sunrise_h)}:00 - {int(sunset_h)}:00",
        "requested_duration_hours": duration_hours,
        "model_basis": "Heuristic Go/No-Go scoring over solar-bounded weather windows; not safety-certified.",
    }


def _error_result(
    message: str, next_step: str | None = None, metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "Error", "message": message}
    if next_step:
        result["next_step"] = next_step
    if metadata is not None:
        result["metadata"] = metadata
    return result
