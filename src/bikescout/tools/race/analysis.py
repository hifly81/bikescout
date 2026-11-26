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
import os
import sys
import traceback
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import gpxpy
import matplotlib
import numpy as np
import requests
from fpdf import FPDF
from geopy.distance import geodesic

from bikescout.tools.mud import get_mud_risk_analysis
from bikescout.tools.nutrition import get_nutrition_plan
from bikescout.tools.weather import apply_weather_windowing, get_weather_forecast

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


GRAVITY = 9.80665
AIR_DENSITY = 1.225
CRR_ROAD = 0.004
CDA_CLIMB = 0.35


@dataclass(frozen=True)
class RaceAnalysisConfig:
    gpx_http_timeout_seconds: float = 20.0
    min_points: int = 10
    max_points: int = 5000


def analyze_track(
    gpx_url: str,
    rider_weight_kg: float = 75,
    rider_gender: Literal["male", "female"] = "male",
    rider_fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
    sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
    bike_weight_kg: float = 8.5,
    pro_intensity: float = 1.3,
    activity_type: Literal["road", "mtb"] = "road",
    target_date: Optional[str] = None,
    start_hour: Optional[int] = None,
    end_hour: Optional[int] = None,
    report: bool = False,
) -> Dict[str, Any]:
    return service.analyze_track(
        gpx_url=gpx_url,
        rider_weight_kg=rider_weight_kg,
        rider_gender=rider_gender,
        rider_fitness_level=rider_fitness_level,
        sweat_profile=sweat_profile,
        bike_weight_kg=bike_weight_kg,
        pro_intensity=pro_intensity,
        activity_type=activity_type,
        target_date=target_date,
        start_hour=start_hour,
        end_hour=end_hour,
        report=report,
    )


class RaceAnalysisService:
    def __init__(
        self,
        config: RaceAnalysisConfig | None = None,
        requests_session: Any | None = None,
        weather_getter=None,
        weather_windowing=None,
        mud_analyzer=None,
        nutrition_getter=None,
        stderr_writer=None,
        date_provider=None,
        plot_generator=None,
        pdf_generator=None,
    ) -> None:
        self.config = config or RaceAnalysisConfig()
        self.requests_session = requests_session or requests
        self.weather_getter = weather_getter or get_weather_forecast
        self.weather_windowing = weather_windowing or apply_weather_windowing
        self.mud_analyzer = mud_analyzer or get_mud_risk_analysis
        self.nutrition_getter = nutrition_getter or get_nutrition_plan
        self.stderr_writer = stderr_writer or sys.stderr
        self.date_provider = date_provider or (lambda: date.today().isoformat())
        self.plot_generator = plot_generator or _generate_elevation_plot
        self.pdf_generator = pdf_generator or _generate_pdf_report

    def analyze_track(
        self,
        gpx_url: str,
        rider_weight_kg: float = 75,
        rider_gender: Literal["male", "female"] = "male",
        rider_fitness_level: Literal["beginner", "intermediate", "pro"] = "intermediate",
        sweat_profile: Literal["standard", "low", "high", "extreme"] = "standard",
        bike_weight_kg: float = 8.5,
        pro_intensity: float = 1.3,
        activity_type: Literal["road", "mtb"] = "road",
        target_date: Optional[str] = None,
        start_hour: Optional[int] = None,
        end_hour: Optional[int] = None,
        report: bool = False,
    ) -> Dict[str, Any]:
        try:
            content = self._load_gpx_content(gpx_url)
            gpx = gpxpy.parse(content)

            points = self._extract_points(gpx)
            if len(points) < self.config.min_points:
                return {"status": "Error", "message": "Insufficient data points in GPX."}
            if len(points) > self.config.max_points:
                points = self._downsample_points(points, self.config.max_points)

            start_lat, start_lon = points[0]["lat"], points[0]["lon"]
            distance_km = round(gpx.length_3d() / 1000, 2)

            if distance_km == 0:
                distance_meters = 0.0
                for i in range(len(points) - 1):
                    distance_meters += geodesic(
                        (points[i]["lat"], points[i]["lon"]),
                        (points[i + 1]["lat"], points[i + 1]["lon"]),
                    ).meters
                distance_km = round(distance_meters / 1000, 2)

            _ud = gpx.get_uphill_downhill()
            _native_uphill = getattr(_ud, "uphill", None) if _ud else None
            if _native_uphill is not None and _native_uphill > 0:
                total_ascent = round(float(_native_uphill), 1)
            else:
                total_ascent = round(self._manual_ascent(points), 1)

            analysis_segments = _process_segments(points, activity_type)
            uci_climbs = _detect_uci_climbs(analysis_segments)

            s_hour = start_hour if start_hour is not None else 9
            e_hour = end_hour if end_hour is not None else 19
            t_date = target_date if target_date else self.date_provider()

            weather_data = self.weather_getter(start_lat, start_lon, t_date)
            ref_temp, ref_wind_speed, ref_wind_dir = 20.0, 10.0, 90.0
            weather_basis = "default"

            if isinstance(weather_data, dict) and weather_data.get("status") == "Success":
                weather_data = self.weather_windowing(weather_data, s_hour, e_hour)
                ref_cond = weather_data.get("reference_conditions", {})
                ref_temp = self._safe_float(
                    ref_cond.get("temp", ref_cond.get("temp_actual")), ref_temp
                )
                ref_wind_speed = self._safe_float(ref_cond.get("wind_speed"), ref_wind_speed)
                ref_wind_dir = self._safe_float(
                    ref_cond.get("wind_dir_degrees", ref_cond.get("wind_direction")), ref_wind_dir
                )
                weather_basis = "weather_forecast"

            intensity_score = self._intensity_score(distance_km, total_ascent, pro_intensity)
            duration_hours, _ = _estimate_ride_duration(
                distance_km, total_ascent, rider_fitness_level, activity_type
            )

            tactical_alerts: list[dict[str, Any]] = []
            mud_risk = None
            if activity_type.lower() == "road":
                tactical_alerts = _calculate_aero_risks(
                    analysis_segments, ref_wind_dir, ref_wind_speed
                )
            else:
                mapped_surface = "gravel" if "gravel" in activity_type.lower() else "dirt"
                try:
                    mud_risk = self.mud_analyzer(start_lat, start_lon, mapped_surface, t_date)
                except Exception as exc:  # noqa: BLE001
                    mud_risk = {"status": "Unavailable", "message": str(exc)}

            nutrition_plan = self.nutrition_getter(
                duration_hours,
                ref_temp,
                intensity_score,
                rider_weight_kg,
                rider_gender,
                sweat_profile,
            )
            performance = _calculate_performance(
                uci_climbs,
                rider_weight_kg,
                bike_weight_kg,
                pro_intensity,
                ref_temp,
                ref_wind_speed,
            )

            tactical_output = _identify_tactical_zones(analysis_segments, uci_climbs, distance_km)
            max_altitude = self._max_altitude(points)

            final_json: dict[str, Any] = {
                "status": "Success",
                "mode": activity_type.upper(),
                "target_date": t_date,
                "track_metrics": {
                    "distance_km": distance_km,
                    "total_ascent": total_ascent,
                    "max_altitude": round(max_altitude, 1),
                },
                "planning_tools": {
                    "weather_forecast": weather_data,
                    "nutrition_plan": nutrition_plan,
                    "mud_risk": mud_risk,
                    "weather_basis": weather_basis,
                },
                "climb_analysis": uci_climbs,
                "performance_simulation": performance,
                "tactical_alerts": tactical_alerts,
                "pre_climb_positioning": tactical_output["pre_climb_positioning"],
                "tactical_action_zones": tactical_output["action_zones"],
            }

            if report:
                plot_path = self.plot_generator(analysis_segments, t_date)
                pdf_path = self.pdf_generator(final_json, plot_path)
                final_json["report_path"] = pdf_path
                final_json["mcp_resource_uri_report"] = self._report_resource_uri(pdf_path)

            return final_json

        except Exception as e:
            self.stderr_writer.write(f"ANALYSIS FAILURE: {traceback.format_exc()}\n")
            return {"status": "Error", "message": str(e)}

    def _load_gpx_content(self, gpx_path: str) -> str:
        if gpx_path.startswith("https://"):
            res = self.requests_session.get(gpx_path, timeout=self.config.gpx_http_timeout_seconds)
            res.raise_for_status()
            return res.text
        with open(gpx_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _extract_points(gpx) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        for track in gpx.tracks:
            for segment in track.segments:
                for p in segment.points:
                    points.append(RaceAnalysisService._point_dict(p))

        for route in gpx.routes:
            for p in route.points:
                points.append(RaceAnalysisService._point_dict(p))

        return RaceAnalysisService._normalize_points(points)

    @staticmethod
    def _point_dict(p: Any) -> dict[str, Any]:
        ele = p.elevation
        try:
            ele_val = float(ele) if ele is not None else None
        except (TypeError, ValueError):
            ele_val = None
        if ele_val is not None and not math.isfinite(ele_val):
            ele_val = None
        return {
            "lat": float(p.latitude),
            "lon": float(p.longitude),
            "ele": ele_val,
            "time": p.time,
        }

    @staticmethod
    def _normalize_points(points: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not points:
            return points
        # Forward/back fill missing elevation; if all missing, set 0.0 and mark assumption.
        first_ele = next((p["ele"] for p in points if p.get("ele") is not None), None)
        if first_ele is None:
            for p in points:
                p["ele"] = 0.0
                p["ele_missing"] = True
            return points
        last = float(first_ele)
        for p in points:
            if p.get("ele") is None:
                p["ele"] = last
                p["ele_interpolated"] = True
            else:
                last = float(p["ele"])
        # Back-fill leading None-equivalent already handled; ensure float
        for p in points:
            p["ele"] = float(p["ele"])
        return points

    @staticmethod
    def _downsample_points(points: list[dict[str, Any]], max_points: int) -> list[dict[str, Any]]:
        if len(points) <= max_points or max_points < 2:
            return points
        step = (len(points) - 1) / (max_points - 1)
        sampled = [points[int(round(i * step))] for i in range(max_points)]
        sampled[-1] = points[-1]
        return sampled

    @staticmethod
    def _manual_ascent(points: list[dict[str, Any]]) -> float:
        ascent = 0.0
        for i in range(len(points) - 1):
            e0 = points[i].get("ele")
            e1 = points[i + 1].get("ele")
            if e0 is None or e1 is None:
                continue
            delta = float(e1) - float(e0)
            if math.isfinite(delta) and delta > 0:
                ascent += delta
        return ascent

    @staticmethod
    def _max_altitude(points: list[dict[str, Any]]) -> float:
        vals = [
            float(p["ele"])
            for p in points
            if p.get("ele") is not None and math.isfinite(float(p["ele"]))
        ]
        return max(vals) if vals else 0.0

    @staticmethod
    def _safe_float(value: Any, default: float) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return default
        return v if math.isfinite(v) else default

    @staticmethod
    def _report_resource_uri(pdf_path: str | None) -> str | None:
        if not pdf_path:
            return None
        try:
            path = Path(pdf_path)
            race_root = Path.home() / ".bikescout" / "race"
            rel = path.resolve().relative_to(race_root.resolve())
            return f"bikescout://race/{rel.as_posix()}"
        except Exception:
            return None

    @staticmethod
    def _intensity_score(distance_km: float, total_ascent: float, pro_intensity: float) -> int:
        raw_intensity = min(100, int((total_ascent / max(distance_km, 1)) * 10 * pro_intensity))
        if raw_intensity <= 20:
            return 1
        if raw_intensity <= 45:
            return 2
        if raw_intensity <= 65:
            return 3
        if raw_intensity <= 85:
            return 4
        return 5


def _estimate_ride_duration(
    distance_km: float, total_ascent_m: float, rider_fitness_level: str, activity_type: str
):
    base_speeds = {
        "beginner": {"road": 20.0, "gravel": 15.0, "mtb": 12.0},
        "intermediate": {"road": 26.0, "gravel": 20.0, "mtb": 15.0},
        "pro": {"road": 34.0, "gravel": 27.0, "mtb": 22.0},
    }

    rider_speeds = base_speeds.get(rider_fitness_level, base_speeds["intermediate"])
    est_speed = rider_speeds.get(activity_type.lower(), rider_speeds["road"])

    climbing_density = total_ascent_m / (distance_km / 10)
    climbing_penalty = (climbing_density / 50.0) * 0.01
    final_est_speed = est_speed * (1.0 - climbing_penalty)
    final_est_speed = max(final_est_speed, 8.0)

    duration_hours = distance_km / final_est_speed
    return duration_hours, final_est_speed


def _load_gpx_content(gpx_path: str) -> str:
    return service._load_gpx_content(gpx_path)


def _smooth_elevations(elevations: list[float], window: int = 10) -> np.ndarray:
    """Moving average with edge padding to avoid zero-padding corruption."""
    arr = np.asarray(elevations, dtype=float)
    if arr.size == 0:
        return arr
    w = max(1, min(window, arr.size))
    kernel = np.ones(w, dtype=float) / w
    pad = w // 2
    padded = np.pad(arr, (pad, pad), mode="edge")
    smoothed = np.convolve(padded, kernel, mode="valid")
    # Convolve valid with symmetric edge padding can yield length n+1 for even windows; trim/fit.
    if smoothed.size > arr.size:
        smoothed = smoothed[: arr.size]
    elif smoothed.size < arr.size:
        smoothed = np.pad(smoothed, (0, arr.size - smoothed.size), mode="edge")
    return smoothed


def _process_segments(points: List[Dict], surface: str) -> List[Dict]:
    dist_filter = 25.0 if surface == "road" else 15.0
    grade_cap = 25.0 if surface == "road" else 35.0

    elevations = [float(p.get("ele", 0.0) or 0.0) for p in points]
    smoothed_ele = _smooth_elevations(elevations, window=10)

    segments = []
    accum_d, total_elapsed, start_idx = 0.0, 0.0, 0
    for i in range(len(points) - 1):
        d = geodesic(
            (points[i]["lat"], points[i]["lon"]), (points[i + 1]["lat"], points[i + 1]["lon"])
        ).meters
        accum_d += d
        total_elapsed += d

        if accum_d >= dist_filter:
            elev_delta = float(smoothed_ele[i + 1] - smoothed_ele[start_idx])
            grade = (elev_delta / accum_d) * 100 if accum_d > 0 else 0.0
            if not math.isfinite(grade):
                grade = 0.0

            if total_elapsed < 500:
                grade = max(min(grade, 8.0), -8.0)
            else:
                grade = max(min(grade, grade_cap), -grade_cap)

            lat1, lon1, lat2, lon2 = map(
                math.radians,
                [points[i]["lat"], points[i]["lon"], points[i + 1]["lat"], points[i + 1]["lon"]],
            )
            y = math.sin(lon2 - lon1) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
                lon2 - lon1
            )
            bearing = (math.degrees(math.atan2(y, x)) + 360) % 360

            segments.append(
                {
                    "dist": accum_d,
                    "grade": grade,
                    "bearing": bearing,
                    "ele_start": float(smoothed_ele[start_idx]),
                    "ele_end": float(smoothed_ele[i + 1]),
                }
            )
            start_idx, accum_d = i + 1, 0.0
    return segments


def _detect_uci_climbs(segments: List[Dict]) -> List[Dict]:
    climbs, current, flat_b = [], [], 0
    for s in segments:
        if s["grade"] >= 1.5:
            current.append(s)
            flat_b = 0
        elif current:
            flat_b += s["dist"]
            current.append(s)
            if flat_b > 1000:
                while current and current[-1]["grade"] < 1.0:
                    current.pop()
                _finalize_climb_data(current, segments, climbs)
                current, flat_b = [], 0
    if current:
        while current and current[-1]["grade"] < 1.0:
            current.pop()
        _finalize_climb_data(current, segments, climbs)
    return climbs


def _finalize_climb_data(current_climb, all_segments, climbs_list):
    if not current_climb:
        return

    total_dist = sum(x["dist"] for x in current_climb)
    total_gain = current_climb[-1]["ele_end"] - current_climb[0]["ele_start"]
    avg_grade = (total_gain / total_dist) * 100

    if avg_grade < 3.5 and total_gain < 250:
        return

    if total_dist > 1500 and total_gain > 100:
        score = (total_gain * avg_grade) / 10
        start_idx = all_segments.index(current_climb[0])
        km_start = sum(x["dist"] for x in all_segments[:start_idx]) / 1000

        category = (
            "HC"
            if score >= 800 or total_gain >= 1000
            else "Cat 1"
            if score >= 400 or total_gain >= 600
            else "Cat 2"
            if score >= 200 or total_gain >= 350
            else "Cat 3"
            if (score >= 100 or total_gain >= 150) and total_dist > 2500
            else "Cat 4"
        )

        climbs_list.append(
            {
                "km_start": round(km_start, 1),
                "dist_km": round(total_dist / 1000, 2),
                "gain_m": round(total_gain, 1),
                "avg_grade": round(avg_grade, 1),
                "category": category,
                "category_system": "bikescout_heuristic",
            }
        )


def _identify_tactical_zones(
    segments: List[Dict], uci_climbs: List[Dict], total_dist: float
) -> Dict:
    pre_climb = []

    for c in uci_climbs:
        if c["category"] in ["HC", "Cat 1"]:
            pre_climb.append(
                {
                    "km": round(c["km_start"] - 0.8, 2),
                    "type": f"CRITICAL POSITIONING: {c['category']} Entrance",
                    "detail": f"Climb {c['dist_km']}km @ {c['avg_grade']}%",
                }
            )

    raw_zones = []
    curr_d = 0.0
    for s in segments:
        curr_d += s["dist"]
        km = curr_d / 1000
        abs_grade = abs(s["grade"])

        if abs_grade > 10.0:
            dist_to_finish = total_dist - km
            weight = 1.0
            if 0 < dist_to_finish <= 60:
                weight = 1.0 + (1.5 * (60 - dist_to_finish) / 60)

            score = abs_grade * weight
            diff = "high" if abs_grade > 14 else "medium" if abs_grade > 11 else "low"
            z_type = (
                "Explosive Wall / Attack Point" if s["grade"] > 0 else "Steep Technical Descent"
            )

            raw_zones.append(
                {
                    "km": round(km, 2),
                    "grade": round(s["grade"], 1),
                    "score": score,
                    "type": z_type,
                    "difficulty": diff,
                }
            )

    raw_zones.sort(key=lambda x: x["score"], reverse=True)

    final_action = []
    targets = {"high": 3, "medium": 2, "low": 1}

    for z in raw_zones:
        if targets[z["difficulty"]] > 0:
            if all(abs(z["km"] - existing["km"]) > 1.0 for existing in final_action):
                final_action.append(
                    {
                        "km": z["km"],
                        "grade": z["grade"],
                        "type": z["type"],
                        "difficulty": z["difficulty"],
                    }
                )
                targets[z["difficulty"]] -= 1

    final_action.sort(key=lambda x: x["km"])

    return {
        "pre_climb_positioning": pre_climb,
        "action_zones": final_action,
    }


def _calculate_performance(climbs, rider_w, bike_w, intensity, temp, wind_speed) -> List[Dict]:
    results = []
    total_mass = rider_w + bike_w
    target_wkg = 3.8 * intensity
    target_power = target_wkg * rider_w

    for c in climbs:
        grade_decimal = c["avg_grade"] / 100
        theta = math.atan(grade_decimal)

        v_mps = 2.0
        for _ in range(10):
            f_grav = total_mass * GRAVITY * math.sin(theta)
            f_roll = total_mass * GRAVITY * math.cos(theta) * CRR_ROAD
            f_aero = 0.5 * AIR_DENSITY * CDA_CLIMB * (v_mps**2)
            p_total = v_mps * (f_grav + f_roll + f_aero)
            dp_dv = f_grav + f_roll + 1.5 * AIR_DENSITY * CDA_CLIMB * (v_mps**2)
            v_mps = v_mps - (p_total - target_power) / dp_dv

        speed_kmh = max(v_mps * 3.6, 5.0)
        time_hours = c["dist_km"] / speed_kmh
        vam = c["gain_m"] / time_hours

        penalty = (target_power * 0.03 if temp > 28 else 0) + (
            target_power * 0.02 if wind_speed > 15 else 0
        )
        adj_wkg = (target_power + penalty) / rider_w

        results.append(
            {
                "climb": f"Climb @ km {c['km_start']} ({c['category']})",
                "est_time_min": round(time_hours * 60, 1),
                "est_vam": round(vam),
                "target_wkg": round(target_wkg, 2),
                "weather_adjusted_wkg": round(adj_wkg, 2),
            }
        )
    return results


def _calculate_aero_risks(segments, wind_dir, wind_speed) -> List[Dict]:
    alerts = []
    try:
        wind_speed_f = float(wind_speed)
        wind_dir_f = float(wind_dir)
    except (TypeError, ValueError):
        return []
    if not math.isfinite(wind_speed_f) or not math.isfinite(wind_dir_f) or wind_speed_f < 18:
        return []
    for i in range(0, len(segments), 45):
        s = segments[i]
        rel_angle = abs(float(s.get("bearing", 0.0)) - wind_dir_f) % 360
        if rel_angle > 180:
            rel_angle = 360 - rel_angle

        if 60 < rel_angle < 120:
            dist_at = sum(float(x.get("dist", 0.0)) for x in segments[:i]) / 1000
            alerts.append(
                {
                    "km": round(dist_at, 1),
                    "type": "ECHELON RISK",
                    "detail": f"{round(wind_speed_f, 1)}km/h Crosswind",
                }
            )
    return alerts[:4]


def _generate_elevation_plot(segments: List[Dict], target_date: str) -> str:
    x_dist: list[float] = []
    y_ele: list[float] = []
    curr_dist = 0.0

    for s in segments:
        curr_dist += float(s.get("dist", 0.0)) / 1000
        x_dist.append(curr_dist)
        y_ele.append(float(s.get("ele_end", 0.0)))

    save_dir = Path.home() / ".bikescout" / "race"
    save_dir.mkdir(parents=True, exist_ok=True)
    unique_id = uuid.uuid4().hex[:8]
    file_path = save_dir / f"profile_{target_date}_{unique_id}.png"

    fig, ax = plt.subplots(figsize=(10, 3.5))
    try:
        ax.fill_between(x_dist, y_ele, color="steelblue", alpha=0.3)
        ax.plot(x_dist, y_ele, color="midnightblue", linewidth=1.5)
        ax.set_title("Stage Elevation Profile", fontsize=12, fontweight="bold")
        ax.set_xlabel("Distance (km)", fontsize=10)
        ax.set_ylabel("Elevation (m)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(file_path, dpi=150)
    finally:
        plt.close(fig)

    return str(file_path)


def _generate_pdf_report(data: Dict[str, Any], plot_path: str) -> str:
    report_dir = Path.home() / ".bikescout" / "race"
    report_dir.mkdir(parents=True, exist_ok=True)

    unique_id = uuid.uuid4().hex[:6]
    target_date = data.get("target_date", "unknown")
    file_path = report_dir / f"race_report_{target_date}_{unique_id}.pdf"

    class BikeScoutPDF(FPDF):
        def footer(self):
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(
                0, 10, "Produced by BikeScout - https://hifly81.github.io/bikescout/", 0, 0, "C"
            )

    pdf = BikeScoutPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "BikeScout Pro Race Strategy Report", ln=True, align="C")
    pdf.ln(5)

    if os.path.exists(plot_path):
        pdf.image(plot_path, x=10, y=pdf.get_y(), w=190)
        pdf.set_y(pdf.get_y() + 65)
    else:
        pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Technical Director Briefing", ln=True)
    pdf.set_font("Arial", "", 11)

    metrics = data.get("track_metrics", {})
    dist = float(metrics.get("distance_km", 0.0))
    asc = float(metrics.get("total_ascent", 0.0))
    zones = data.get("tactical_action_zones", [])
    weather = (
        data.get("planning_tools", {}).get("weather_forecast", {}).get("reference_conditions", {})
    )

    profile_ratio = asc / dist if dist > 0 else 0
    is_xc_circuit = dist < 15.0 and profile_ratio > 15.0

    if is_xc_circuit:
        intro = f"Team, we are looking at a punchy XC circuit today: {dist} km per lap with {asc} meters of elevation gain. Forget pacing; this requires repeated VO2 max efforts and flawless technical execution on every lap. "
    elif profile_ratio >= 22:
        intro = f"Team, today is a brutal day in the mountains: {dist} km and a massive {asc} meters of elevation. Survival and GC preservation are our primary directives. "
    elif profile_ratio >= 12:
        intro = f"We have {dist} km with {asc} meters of climbing on the menu. It's a leg-breaking, rolling parcours that perfectly favors a strong breakaway or late puncheur attacks. "
    else:
        intro = f"At {dist} km and only {asc} m of climbing, this is ostensibly a flat stage. Staying safe, hiding from the wind, and delivering our sprinter is everything today. "

    temp = weather.get("temp", 20)
    wind = weather.get("wind_speed", 10)
    wx_str = f"Expect conditions around {temp}C with winds at {wind} km/h. "

    if temp >= 30:
        wx_str += "The heat is going to be a major factor; constant hydration and ice packs are mandatory. "
    elif temp <= 10:
        wx_str += "It's going to be freezing out there. Keep your core warm, especially before the technical descents. "
    if wind >= 20:
        wx_str += "Wind speeds are absolutely high enough to split the peloton. Stay vigilant and ride at the front to avoid echelon traps! "

    tactical_str = ""
    if zones:
        sorted_zones = sorted(zones, key=lambda x: x.get("km", 0))
        late_zones = [z for z in sorted_zones if z.get("km", 0) >= (dist * 0.5)]

        if late_zones:
            ignition_zone = max(
                late_zones, key=lambda z: (z.get("difficulty") == "high", abs(z.get("grade", 0)))
            )
        else:
            ignition_zone = max(
                sorted_zones, key=lambda z: (z.get("difficulty") == "high", abs(z.get("grade", 0)))
            )

        ignite_km = ignition_zone.get("km", 0)
        zone_type = ignition_zone.get("type", "sector").lower()
        zone_grade = ignition_zone.get("grade", 0)
        dist_to_go = dist - ignite_km

        if is_xc_circuit:
            tactical_str = f"The primary launchpad for attacks is the {zone_type} around km {ignite_km} ({zone_grade}% grade). Hit it hard every single lap. "
        elif dist_to_go > (dist * 0.4):
            tactical_str = f"Based on the topography, the race will blow apart unusually early, around km {ignite_km}. We cannot afford to be caught sleeping when the {zone_type} starts. From there, it's a pure race of attrition. "
        elif dist_to_go < 15:
            tactical_str = f"It all comes down to a late, explosive finale. The decisive move will likely happen on the {zone_type} at km {ignite_km}, just {round(dist_to_go, 1)} km from the line. It kicks up to {zone_grade}%. Be perfectly positioned before this point. "
        else:
            tactical_str = f"The true battle for the stage begins at km {ignite_km}. That {zone_type} (hitting gradients of {zone_grade}%) is the natural launchpad for the winning move. "

        if not is_xc_circuit:
            tactical_str += "If you have the legs, this is where you commit. "
    else:
        tactical_str = "There are no extreme technical features today. Positioning and tactical awareness will dictate the finale. "

    if is_xc_circuit:
        if temp >= 28:
            closing = "Heat will spike your HR on this circuit. Use the descents for active cooling and hydration."
        else:
            closing = (
                "Nail the start loop to avoid traffic. It's a high-intensity battle from the gun."
            )
    else:
        if wind >= 22:
            closing = "The wind is the real enemy today. Stay tucked in and never be the first to break the line."
        elif profile_ratio >= 20:
            closing = "This is a war of attrition. Save every watt for the final two climbs; nutrition is non-negotiable."
        elif dist > 150:
            closing = "It's a long day. Stay hydrated early so you have the clarity to make the right move in the final 20km."
        else:
            closing = "Positioning is everything today. Communicate with the team and stay in the top 20 before the decisive sectors."

    closing += " Let's go execute."

    briefing = intro + wx_str + tactical_str + closing
    pdf.multi_cell(0, 6, briefing)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detailed Tactical Zones", ln=True)
    pdf.set_font("Arial", "", 10)

    if not zones:
        pdf.cell(0, 6, "No high-risk tactical zones identified.", ln=True)
    for z in zones:
        diff_str = str(z.get("difficulty", "unknown")).upper()
        pdf.cell(
            0,
            6,
            f"- KM {z.get('km', 0)}: {z.get('type', 'Unknown')} | Grade: {z.get('grade', 0)}% [Severity: {diff_str}]",
            ln=True,
        )

    pdf.output(str(file_path))
    # No orphan climb_*.png generated in this module; avoid deleting unrelated files.
    return str(file_path)


service = RaceAnalysisService()
